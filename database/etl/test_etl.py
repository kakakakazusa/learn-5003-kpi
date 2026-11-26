# -*- coding: utf-8 -*-
"""数仓 ETL 分层同步的端到端测试。

在**独立的测试库**中跑完整条链路（ODS → DIM → DWD → DWM → DWS → ADS），
逐层校验数据，跑完自动删库，不会读写生产库 `5003`。

用法（在项目根目录执行）：
    python database/etl/test_etl.py            # 跑完自动删除测试库
    python database/etl/test_etl.py --keep     # 保留测试库，便于人工查数
    python database/etl/test_etl.py -v         # 逐条显示断言

连接参数复用 database/etl/config.py：
    DW_DB_HOST / DW_DB_USER / DW_DB_PASSWORD / DW_DB_PORT
测试库名默认 `dw_etl_test`，可用 DW_TEST_DB 覆盖。

测试覆盖的契约：
    1. ODS 源数据规模（3 部门 × 6 人 = 18，20 个项目）
    2. DIM 日期维覆盖今天且行数正确
    3. DWD 派生字段（is_on_time / process_days）与 ODS 原始值一致
    4. DWD 故障时长（response_minutes / resolve_minutes）与 ODS 时间戳一致
    5. DWS 组织汇总与员工级汇总逐日平衡
    6. ADS 指标口径（完成率 / 准时率 / 平均处理天数）可反算
    7. ADS 周期与组织维度覆盖完整
    8. 重跑保持幂等（行数不变）
    9. DWS 工时汇总与 DWD 已完成需求工时一致（完成侧指标按完成日落日期）
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
    """连到 MySQL 服务本身（不指定库），用于建库/删库。"""
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
    """复用后端 ORM 建 23 张数仓表，与 `flask init-db` 走同一条路径。"""
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

    # ---------- 准备与清理 ----------

    @classmethod
    def setUpClass(cls):
        try:
            _server_conn().close()
        except Exception as exc:  # noqa: BLE001
            raise unittest.SkipTest(
                "MySQL 不可用（%s: %s），跳过集成测试。请先启动 MySQL 并确认 DW_DB_* 配置。"
                % (type(exc).__name__, exc)
            )

        print("\n[setup] 重建测试库 `%s`" % TEST_DB)
        _recreate_database()
        _create_tables()

        # 关键：让 ETL 连到测试库，而不是生产库
        config.SOURCE["database"] = TEST_DB

        cls.conn = get_conn()
        print("[setup] 依次执行：%s" % " → ".join(config.ORDER))
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
            print("\n[teardown] 已保留测试库 `%s`" % TEST_DB)
            return
        try:
            _drop_database()
            print("\n[teardown] 已删除测试库 `%s`" % TEST_DB)
        except Exception as exc:  # noqa: BLE001
            print("\n[teardown] 删除测试库失败：%s" % exc)

    # ---------- 查询辅助 ----------

    def q(self, sql, args=None):
        with self.conn.cursor(pymysql.cursors.DictCursor) as cur:
            cur.execute(sql, args)
            return cur.fetchall()

    def one(self, sql, args=None):
        rows = self.q(sql, args)
        if not rows:
            return None
        return list(rows[0].values())[0]

    # ---------- 1. ODS 规模 ----------

    def test_01_ods_scale(self):
        """3 个部门各 6 人 = 18 名员工；20 个项目；PR / EC 明细非空。"""
        self.assertEqual(18, self.one("SELECT COUNT(*) c FROM ods_hr_employee"))
        self.assertEqual(20, self.one("SELECT COUNT(*) c FROM ods_pm_project"))
        self.assertGreater(self.one("SELECT COUNT(*) c FROM ods_pm_pr"), 0)
        self.assertGreater(self.one("SELECT COUNT(*) c FROM ods_itsm_ec"), 0)

    # ---------- 2. DIM 日期维 ----------

    def test_02_dim_date_covers_today(self):
        """dim_date 覆盖 [去年, 明年] 三年，且包含今天。"""
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

    # ---------- 3. DWD 需求派生字段 ----------

    def test_03_dwd_pr_fields_match_ods(self):
        """准时标记与处理天数必须能从 ODS 原始日期反算出来。"""
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
        self.assertEqual(len(ods), len(dwd), "DWD 行数与抽样的 ODS 行数不一致")

        for row in ods:
            fact = dwd[row["pr_id"]]
            complete = row["complete_date"]
            expected_on_time = 1 if (complete and complete <= row["due_date"]) else 0
            expected_days = (complete - row["assign_date"]).days if complete else None
            self.assertEqual(
                expected_on_time, fact["is_on_time"], "pr_id=%s 准时标记错误" % row["pr_id"]
            )
            self.assertEqual(
                expected_days, fact["process_days"], "pr_id=%s 处理天数错误" % row["pr_id"]
            )

    # ---------- 4. DWD 故障时长 ----------

    def test_04_dwd_ec_minutes_match_ods(self):
        """响应/解决分钟数必须等于 ODS 时间戳之差。"""
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
        self.assertEqual(len(ods), len(dwd), "DWD 行数与抽样的 ODS 行数不一致")

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
                "ec_id=%s 响应分钟数错误" % row["ec_id"],
            )
            self.assertEqual(
                expected_resolve,
                fact["resolve_minutes"],
                "ec_id=%s 解决分钟数错误" % row["ec_id"],
            )

    # ---------- 5. DWS 汇总平衡 ----------

    def test_05_dws_rollup_balances(self):
        """部门 / 团队 / 领域 每一行的汇总，必须等于当日员工级汇总之和。"""
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
            self.assertTrue(base, "dws_pr_org_1d 没有员工级数据")
            for org_type in ("department", "team", "domain"):
                got = totals("dws_pr_org_1d", metric, org_type)
                self.assertEqual(
                    base, got, "%s 的 %s 汇总与员工级不一致" % (org_type, metric)
                )

        for metric in ec_metrics:
            base = totals("dws_ec_org_1d", metric, "employee")
            self.assertTrue(base, "dws_ec_org_1d 没有员工级数据")
            for org_type in ("department", "team", "domain"):
                got = totals("dws_ec_org_1d", metric, org_type)
                self.assertEqual(
                    base, got, "%s 的 %s 汇总与员工级不一致" % (org_type, metric)
                )

    # ---------- 6. ADS 指标口径 ----------

    def test_06_ads_pr_metrics_are_consistent(self):
        """完成率、准时率、平均处理天数必须能从分子分母反算。"""
        rows = self.q(
            """SELECT period_type, period_value, org_type, org_id,
                      pr_assign_cnt, pr_complete_cnt, pr_due_cnt, pr_on_time_cnt,
                      pr_process_days_sum, pr_completion_rate, pr_on_time_rate,
                      pr_avg_process_days
               FROM ads_pr_kpi"""
        )
        self.assertGreater(len(rows), 0, "ads_pr_kpi 为空")

        for row in rows:
            tag = "%s/%s/%s/%s" % (
                row["period_type"], row["period_value"], row["org_type"], row["org_id"],
            )
            if row["pr_assign_cnt"]:
                self.assertAlmostEqual(
                    row["pr_complete_cnt"] / row["pr_assign_cnt"],
                    float(row["pr_completion_rate"]),
                    places=4,
                    msg="完成率口径错误 " + tag,
                )
            if row["pr_due_cnt"]:
                self.assertAlmostEqual(
                    row["pr_on_time_cnt"] / row["pr_due_cnt"],
                    float(row["pr_on_time_rate"]),
                    places=4,
                    msg="准时率口径错误 " + tag,
                )
            if row["pr_complete_cnt"]:
                # ADS 只存两位小数，允许半个末位的舍入误差（如 6.225 存成 6.23）
                computed = row["pr_process_days_sum"] / row["pr_complete_cnt"]
                self.assertLessEqual(
                    abs(float(row["pr_avg_process_days"]) - computed),
                    0.005 + 1e-9,
                    "平均处理天数口径错误 %s：反算 %.4f，库中 %.2f"
                    % (tag, computed, float(row["pr_avg_process_days"])),
                )

    # ---------- 7. ADS 覆盖度 ----------

    def test_07_ads_covers_all_periods_and_org_types(self):
        """5 种周期 × 4 种组织维度都要有数据。"""
        periods = {row["period_type"] for row in self.q(
            "SELECT DISTINCT period_type FROM ads_pr_kpi")}
        self.assertEqual({"week", "month", "quarter", "halfyear", "year"}, periods)

        org_types = {row["org_type"] for row in self.q(
            "SELECT DISTINCT org_type FROM ads_pr_kpi")}
        self.assertEqual({"employee", "team", "domain", "department"}, org_types)

        for table in ("ads_ec_kpi", "ads_pr_project_kpi", "ads_ec_project_kpi"):
            count = self.one("SELECT COUNT(DISTINCT period_type) c FROM %s" % table)
            self.assertEqual(5, count, "%s 周期覆盖不全" % table)

    # ---------- 8. 幂等性 ----------

    def test_08_rerun_is_idempotent(self):
        """重跑 DIM→ADS 后各层行数不变。"""
        tables = ("dim_employee", "dwd_pr_fact", "dwm_pr_emp_1d", "dws_pr_org_1d", "ads_pr_kpi")
        before = {t: self.one("SELECT COUNT(*) c FROM %s" % t) for t in tables}

        for layer in ("dim", "dwd", "dwm", "dws", "ads"):
            LAYERS[layer](self.conn)

        after = {t: self.one("SELECT COUNT(*) c FROM %s" % t) for t in tables}
        self.assertEqual(before, after, "重跑后行数变化，说明同步不是幂等的")

    # ---------- 9. 工时链路 ----------

    def test_09_dws_carries_pr_work_hours(self):
        """DWS 的工时汇总应等于 DWD 已完成需求的工时之和。

        口径说明：DWM/DWS 的完成侧指标（complete_cnt / process_days / work_hours）
        统一按 `complete_date_key` 落日期，未完成的需求没有完成日，不进入该粒度。
        因此基准值只统计 `complete_date_key IS NOT NULL` 的部分。
        """
        detail = float(self.one(
            "SELECT COALESCE(SUM(work_hours), 0) v FROM dwd_pr_fact "
            "WHERE complete_date_key IS NOT NULL") or 0)
        rolled = float(self.one(
            "SELECT COALESCE(SUM(pr_work_hours_sum), 0) v FROM dws_pr_org_1d "
            "WHERE org_type='employee'") or 0)
        self.assertGreater(detail, 0, "DWD 已完成需求工时为 0，源数据异常")
        self.assertAlmostEqual(
            detail, rolled, places=2,
            msg="DWS 工时为 %.2f，DWD 已完成需求工时为 %.2f：DWM 层未聚合 work_hours"
            % (rolled, detail),
        )


if __name__ == "__main__":
    unittest.main(
        argv=[sys.argv[0]] + [arg for arg in sys.argv[1:] if arg != "--keep"],
        verbosity=2,
    )
