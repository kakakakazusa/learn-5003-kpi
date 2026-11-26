# -*- coding: utf-8 -*-
"""End-to-end test for the layered warehouse ETL sync.

Runs the full pipeline (ODS -> DIM -> DWD -> DWM -> DWS -> ADS) in a
**separate test database**, verifies the data at each layer, and drops the
database automatically when finished. It never reads or writes the production
database `5003`.

Usage (from the project root):
    python database/etl/test_etl.py            # drop the test database when done
    python database/etl/test_etl.py --keep     # keep the test database for manual inspection
    python database/etl/test_etl.py -v         # show each assertion

Connection settings are reused from database/etl/config.py:
    DW_DB_HOST / DW_DB_USER / DW_DB_PASSWORD / DW_DB_PORT
The test database defaults to `dw_etl_test`; override it with DW_TEST_DB.

Contracts covered by the tests:
    1. ODS source data scale (3 departments x 6 people = 18, 20 projects)
    2. DIM date dimension covers today with the correct row count
    3. DWD derived fields (is_on_time / process_days) match the original ODS values
    4. DWD incident durations (response_minutes / resolve_minutes) match ODS timestamps
    5. DWS organization rollups balance with employee-level rollups day by day
    6. ADS metric definitions (completion rate / on-time rate / average processing days) can be recomputed
    7. ADS periods and organization dimensions are fully covered
    8. Reruns are idempotent (row counts unchanged)
    9. DWS work-hour rollups match DWD work hours for completed requirements (completion-side metrics are dated by completion date)
"""
import os
import sys
import unittest
from datetime import date
from pathlib import Path
from urllib.parse import quote_plus

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
for _path in (str(ROOT), str(BACKEND)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

import pymysql  # noqa: E402

from database.etl import config  # noqa: E402
from database.etl.db import get_conn  # noqa: E402
from database.etl.runner import LAYERS  # noqa: E402

TEST_DB = os.getenv("DW_TEST_DB", "dw_etl_test")
KEEP_DB = "--keep" in sys.argv


def _server_conn():
    """Connect to the MySQL server itself (no database specified), for creating/dropping databases."""
    params = {k: v for k, v in config.SOURCE.items() if k != "database"}
    params["autocommit"] = True
    return pymysql.connect(**params)


def _recreate_database():
    conn = _server_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("DROP DATABASE IF EXISTS `%s`" % TEST_DB)
            cur.execute(
                "CREATE DATABASE `%s` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci" % TEST_DB
            )
    finally:
        conn.close()


def _drop_database():
    conn = _server_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("DROP DATABASE IF EXISTS `%s`" % TEST_DB)
    finally:
        conn.close()


def _create_tables():
    """Reuse the backend ORM to create the 23 warehouse tables, following the same path as `flask init-db`."""
    src = config.SOURCE
    url = "mysql+pymysql://%s:%s@%s:%s/%s?charset=utf8mb4" % (
        src["user"], quote_plus(src["password"]), src["host"], src["port"], TEST_DB,
    )
    os.environ["DW_DATABASE_URL"] = url
    os.environ["DATABASE_URL"] = url

    from app import create_app  # noqa: PLC0415
    from extensions import db  # noqa: PLC0415

    application = create_app()
    with application.app_context():
        db.create_all()


class EtlPipelineTest(unittest.TestCase):
    conn = None

    # ---------- Setup and teardown ----------

    @classmethod
    def setUpClass(cls):
        try:
            _server_conn().close()
        except Exception as exc:  # noqa: BLE001
            raise unittest.SkipTest(
                "MySQL unavailable (%s: %s), skipping integration tests. "
                "Please start MySQL and check the DW_DB_* configuration."
                % (type(exc).__name__, exc)
            )

        print("\n[setup] Recreating test database `%s`" % TEST_DB)
        _recreate_database()
        _create_tables()

        # Important: make the ETL connect to the test database, not the production database
        config.SOURCE["database"] = TEST_DB

        cls.conn = get_conn()
        print("[setup] Running in order: %s" % " -> ".join(config.ORDER))
        for layer in config.ORDER:
            LAYERS[layer](cls.conn)

    @classmethod
    def tearDownClass(cls):
        if cls.conn is not None:
            try:
                cls.conn.close()
            except Exception:  # noqa: BLE001
                pass
        if KEEP_DB:
            print("\n[teardown] Kept test database `%s`" % TEST_DB)
            return
        try:
            _drop_database()
            print("\n[teardown] Dropped test database `%s`" % TEST_DB)
        except Exception as exc:  # noqa: BLE001
            print("\n[teardown] Failed to drop test database: %s" % exc)

    # ---------- Query helpers ----------

    def q(self, sql, args=None):
        with self.conn.cursor(pymysql.cursors.DictCursor) as cur:
            cur.execute(sql, args)
            return cur.fetchall()

    def one(self, sql, args=None):
        rows = self.q(sql, args)
        if not rows:
            return None
        return list(rows[0].values())[0]

    # ---------- 1. ODS scale ----------

    def test_01_ods_scale(self):
        """3 departments x 6 people = 18 employees; 20 projects; PR / EC details are non-empty."""
        self.assertEqual(18, self.one("SELECT COUNT(*) c FROM ods_hr_employee"))
        self.assertEqual(20, self.one("SELECT COUNT(*) c FROM ods_pm_project"))
        self.assertGreater(self.one("SELECT COUNT(*) c FROM ods_pm_pr"), 0)
        self.assertGreater(self.one("SELECT COUNT(*) c FROM ods_itsm_ec"), 0)

    # ---------- 2. DIM date dimension ----------

    def test_02_dim_date_covers_today(self):
        """dim_date covers three years [last year, next year] and includes today."""
        today = date.today()
        expected = (date(today.year + 1, 12, 31) - date(today.year - 1, 1, 1)).days + 1
        self.assertEqual(expected, self.one("SELECT COUNT(*) c FROM dim_date"))
        self.assertEqual(
            1,
            self.one(
                "SELECT COUNT(*) c FROM dim_date WHERE date_key=%s",
                (int(today.strftime("%Y%m%d")),),
            ),
        )

    # ---------- 3. DWD requirement derived fields ----------

    def test_03_dwd_pr_fields_match_ods(self):
        """The on-time flag and processing days must be recomputable from the original ODS dates."""
        ods = self.q(
            """SELECT pr_id, assign_date, due_date, complete_date
               FROM ods_pm_pr ORDER BY pr_id LIMIT 300"""
        )
        ids = [row["pr_id"] for row in ods]
        placeholders = ",".join(["%s"] * len(ids))
        dwd = {
            row["pr_id"]: row
            for row in self.q(
                "SELECT pr_id, is_on_time, process_days FROM dwd_pr_fact "
                "WHERE pr_id IN (%s)" % placeholders,
                ids,
            )
        }
        self.assertEqual(len(ods), len(dwd), "DWD row count differs from the sampled ODS row count")

        for row in ods:
            fact = dwd[row["pr_id"]]
            complete = row["complete_date"]
            expected_on_time = 1 if (complete and complete <= row["due_date"]) else 0
            expected_days = (complete - row["assign_date"]).days if complete else None
            self.assertEqual(
                expected_on_time, fact["is_on_time"], "pr_id=%s on-time flag is wrong" % row["pr_id"]
            )
            self.assertEqual(
                expected_days, fact["process_days"], "pr_id=%s processing days are wrong" % row["pr_id"]
            )

    # ---------- 4. DWD incident durations ----------

    def test_04_dwd_ec_minutes_match_ods(self):
        """Response/resolve minutes must equal the difference of ODS timestamps."""
        ods = self.q(
            """SELECT ec_id, found_at, first_response_at, resolved_at
               FROM ods_itsm_ec ORDER BY ec_id LIMIT 300"""
        )
        ids = [row["ec_id"] for row in ods]
        placeholders = ",".join(["%s"] * len(ids))
        dwd = {
            row["ec_id"]: row
            for row in self.q(
                "SELECT ec_id, response_minutes, resolve_minutes FROM dwd_ec_fact "
                "WHERE ec_id IN (%s)" % placeholders,
                ids,
            )
        }
        self.assertEqual(len(ods), len(dwd), "DWD row count differs from the sampled ODS row count")

        for row in ods:
            fact = dwd[row["ec_id"]]
            expected_response = int(
                (row["first_response_at"] - row["found_at"]).total_seconds() // 60
            )
            expected_resolve = None
            if row["resolved_at"] is not None:
                expected_resolve = int(
                    (row["resolved_at"] - row["found_at"]).total_seconds() // 60
                )
            self.assertEqual(
                expected_response,
                fact["response_minutes"],
                "ec_id=%s response minutes are wrong" % row["ec_id"],
            )
            self.assertEqual(
                expected_resolve,
                fact["resolve_minutes"],
                "ec_id=%s resolve minutes are wrong" % row["ec_id"],
            )

    # ---------- 5. DWS rollup balance ----------

    def test_05_dws_rollup_balances(self):
        """Each department / team / domain rollup row must equal the sum of employee-level rollups for that day."""
        pr_metrics = ("pr_assign_cnt", "pr_complete_cnt", "pr_due_cnt", "pr_on_time_cnt")
        ec_metrics = ("ec_found_cnt", "ec_resolved_cnt", "ec_recur_cnt", "ec_severe_cnt")

        def totals(table, metric, org_type):
            sql = (
                "SELECT stat_date, SUM({m}) v FROM {t} "
                "WHERE org_type=%s GROUP BY stat_date"
            ).format(m=metric, t=table)
            return {row["stat_date"]: int(row["v"]) for row in self.q(sql, (org_type,))}

        for metric in pr_metrics:
            base = totals("dws_pr_org_1d", metric, "employee")
            self.assertTrue(base, "dws_pr_org_1d has no employee-level data")
            for org_type in ("department", "team", "domain"):
                got = totals("dws_pr_org_1d", metric, org_type)
                self.assertEqual(
                    base, got, "%s rollup of %s differs from employee-level" % (org_type, metric)
                )

        for metric in ec_metrics:
            base = totals("dws_ec_org_1d", metric, "employee")
            self.assertTrue(base, "dws_ec_org_1d has no employee-level data")
            for org_type in ("department", "team", "domain"):
                got = totals("dws_ec_org_1d", metric, org_type)
                self.assertEqual(
                    base, got, "%s rollup of %s differs from employee-level" % (org_type, metric)
                )

    # ---------- 6. ADS metric definitions ----------

    def test_06_ads_pr_metrics_are_consistent(self):
        """Completion rate, on-time rate, and average processing days must be recomputable from numerator and denominator."""
        rows = self.q(
            """SELECT period_type, period_value, org_type, org_id,
                      pr_assign_cnt, pr_complete_cnt, pr_due_cnt, pr_on_time_cnt,
                      pr_process_days_sum, pr_completion_rate, pr_on_time_rate,
                      pr_avg_process_days
               FROM ads_pr_kpi"""
        )
        self.assertGreater(len(rows), 0, "ads_pr_kpi is empty")

        for row in rows:
            tag = "%s/%s/%s/%s" % (
                row["period_type"], row["period_value"], row["org_type"], row["org_id"],
            )
            if row["pr_assign_cnt"]:
                self.assertAlmostEqual(
                    row["pr_complete_cnt"] / row["pr_assign_cnt"],
                    float(row["pr_completion_rate"]),
                    places=4,
                    msg="Incorrect completion rate definition " + tag,
                )
            if row["pr_due_cnt"]:
                self.assertAlmostEqual(
                    row["pr_on_time_cnt"] / row["pr_due_cnt"],
                    float(row["pr_on_time_rate"]),
                    places=4,
                    msg="Incorrect on-time rate definition " + tag,
                )
            if row["pr_complete_cnt"]:
                # ADS only stores two decimals; allow half a last-digit rounding error (e.g. 6.225 stored as 6.23)
                computed = row["pr_process_days_sum"] / row["pr_complete_cnt"]
                self.assertLessEqual(
                    abs(float(row["pr_avg_process_days"]) - computed),
                    0.005 + 1e-9,
                    "Incorrect average processing days definition %s: recomputed %.4f, stored %.2f"
                    % (tag, computed, float(row["pr_avg_process_days"])),
                )

    # ---------- 7. ADS coverage ----------

    def test_07_ads_covers_all_periods_and_org_types(self):
        """All 5 periods x 4 organization dimensions must have data."""
        periods = {row["period_type"] for row in self.q(
            "SELECT DISTINCT period_type FROM ads_pr_kpi")}
        self.assertEqual({"week", "month", "quarter", "halfyear", "year"}, periods)

        org_types = {row["org_type"] for row in self.q(
            "SELECT DISTINCT org_type FROM ads_pr_kpi")}
        self.assertEqual({"employee", "team", "domain", "department"}, org_types)

        for table in ("ads_ec_kpi", "ads_pr_project_kpi", "ads_ec_project_kpi"):
            count = self.one("SELECT COUNT(DISTINCT period_type) c FROM %s" % table)
            self.assertEqual(5, count, "%s does not cover all periods" % table)

    # ---------- 8. Idempotency ----------

    def test_08_rerun_is_idempotent(self):
        """Row counts at each layer stay the same after rerunning DIM->ADS."""
        tables = ("dim_employee", "dwd_pr_fact", "dwm_pr_emp_1d", "dws_pr_org_1d", "ads_pr_kpi")
        before = {t: self.one("SELECT COUNT(*) c FROM %s" % t) for t in tables}

        for layer in ("dim", "dwd", "dwm", "dws", "ads"):
            LAYERS[layer](self.conn)

        after = {t: self.one("SELECT COUNT(*) c FROM %s" % t) for t in tables}
        self.assertEqual(before, after, "Row counts changed after rerun; the sync is not idempotent")

    # ---------- 9. Work-hour chain ----------

    def test_09_dws_carries_pr_work_hours(self):
        """DWS work-hour rollups should equal the sum of DWD work hours for completed requirements.

        Definition note: the completion-side metrics in DWM/DWS (complete_cnt / process_days / work_hours)
        are all dated by `complete_date_key`. Incomplete requirements have no completion date and are
        excluded at that granularity. The baseline therefore only counts rows where
        `complete_date_key IS NOT NULL`.
        """
        detail = float(self.one(
            "SELECT COALESCE(SUM(work_hours), 0) v FROM dwd_pr_fact "
            "WHERE complete_date_key IS NOT NULL") or 0)
        rolled = float(self.one(
            "SELECT COALESCE(SUM(pr_work_hours_sum), 0) v FROM dws_pr_org_1d "
            "WHERE org_type='employee'") or 0)
        self.assertGreater(detail, 0, "DWD work hours for completed requirements are 0; source data is abnormal")
        self.assertAlmostEqual(
            detail, rolled, places=2,
            msg="DWS work hours are %.2f, DWD completed-requirement work hours are %.2f: "
                "DWM layer did not aggregate work_hours"
            % (rolled, detail),
        )


if __name__ == "__main__":
    unittest.main(
        argv=[sys.argv[0]] + [arg for arg in sys.argv[1:] if arg != "--keep"],
        verbosity=2,
    )
