# -*- coding: utf-8 -*-
"""ODS layer: simulate business-system source data and write it in full to ODS.

In a real environment, replace `load_source` with extraction logic from the HR / PM / ITSM systems.
"""
import random
from datetime import date, datetime, timedelta

DEPARTMENTS = [(1, "Engineering"), (2, "Product"), (3, "Operations")]
TEAMS = [(101, "Backend", 1), (102, "Frontend", 1), (103, "Data", 1),
         (201, "Platform", 2), (202, "Growth", 2), (301, "Customer Success", 3)]
DOMAINS = [(10, "Engineering"), (20, "Product Design"), (30, "Business Operations"), (40, "Data Intelligence")]
POSITIONS = ["Junior Engineer", "Senior Engineer", "Product Manager", "Operations Specialist", "Data Analyst"]
SEVERITIES = ["P0", "P1", "P2", "P3", "P3"]


def load_source(conn):
    """Rebuild all ODS source data (simulating a daily full sync from business systems)."""
    cur = conn.cursor()
    rng = random.Random(20251124)
    today = date.today()
    start = today - timedelta(days=365)

    employees = []
    eid = 1
    for didx, (did, dname) in enumerate(DEPARTMENTS):
        team_pool = [t for t in TEAMS if t[2] == did]
        for i in range(6):
            tid, tname, _ = team_pool[i % len(team_pool)]
            domain_id, domain_name = DOMAINS[didx]
            employees.append({
                "employee_id": eid,
                "employee_name": "Employee %03d" % eid,
                "department_id": did,
                "department_name": dname,
                "team_id": tid,
                "team_name": tname,
                "domain_id": domain_id,
                "domain_name": domain_name,
                "position": POSITIONS[eid % len(POSITIONS)],
                "job_level": "P%d" % (eid % 4 + 1),
                "employment_status": "Active",
                "join_date": (start - timedelta(days=rng.randint(0, 365))).isoformat(),
                "manager_id": None if eid <= 3 else ((eid - 1) // 6) * 6 + 1,
            })
            eid += 1

    projects = []
    for pid in range(1, 21):
        projects.append({
            "project_id": pid,
            "project_name": "Project-%d" % pid,
            "project_status": rng.choice(["In Progress", "Completed", "Closed"]),
            "owner_employee_id": rng.choice([e["employee_id"] for e in employees]),
            "start_date": (start - timedelta(days=rng.randint(0, 365))).isoformat(),
            "end_date": (today + timedelta(days=rng.randint(30, 365))).isoformat(),
        })

    pr_rows = []
    ec_rows = []
    pr_seq = 100000
    ec_seq = 100000
    batch = datetime.now().strftime("%Y%m%d%H%M%S")

    for emp in employees:
        emp_id = emp["employee_id"]
        for offset in range(366):
            d = start + timedelta(days=offset)
            for _ in range(rng.randint(0, 3)):
                assign = d
                due = assign + timedelta(days=rng.randint(1, 10))
                complete = None
                status = rng.choice(["In Progress", "Completed", "Completed", "Closed"])
                if status in ("Completed", "Closed"):
                    complete = assign + timedelta(days=rng.randint(1, 12))
                rework = 1 if rng.random() < 0.12 else 0
                hours = round(rng.uniform(2, 40), 2)
                pr_rows.append((pr_seq, "Requirement-%d" % rng.randint(1000, 9999),
                                emp_id, rng.randint(1, 20), assign.isoformat(),
                                due.isoformat(), complete.isoformat() if complete else None,
                                status, rework, hours))
                pr_seq += 1
            for _ in range(rng.randint(0, 2)):
                found = datetime.combine(d, datetime.min.time()) + timedelta(hours=rng.randint(0, 20))
                first_response = found + timedelta(minutes=rng.randint(5, 240))
                resolved = first_response + timedelta(minutes=rng.randint(30, 2880)) if rng.random() < 0.9 else None
                ec_rows.append((ec_seq, "Incident-%d" % rng.randint(1000, 9999),
                                emp_id, rng.randint(1, 20), rng.choice(SEVERITIES),
                                found.strftime("%Y-%m-%d %H:%M:%S"),
                                first_response.strftime("%Y-%m-%d %H:%M:%S"),
                                resolved.strftime("%Y-%m-%d %H:%M:%S") if resolved else None,
                                "Resolved" if resolved else "In Progress",
                                1 if rng.random() < 0.08 else 0))
                ec_seq += 1

    cur.execute("DELETE FROM ods_hr_employee")
    cur.execute("DELETE FROM ods_pm_pr")
    cur.execute("DELETE FROM ods_itsm_ec")
    cur.execute("DELETE FROM ods_pm_project")
    for emp in employees:
        cur.execute(
            """INSERT INTO ods_hr_employee
               (employee_id, employee_name, department_id, department_name, team_id, team_name,
                domain_id, domain_name, position, job_level, employment_status, join_date, manager_id,
                etl_load_time, etl_source, etl_batch_id, etl_operation, data_date)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW(),'hr_system',%s,'I',CURDATE())""",
            (emp["employee_id"], emp["employee_name"], emp["department_id"], emp["department_name"],
             emp["team_id"], emp["team_name"], emp["domain_id"], emp["domain_name"],
             emp["position"], emp["job_level"], emp["employment_status"], emp["join_date"],
             emp["manager_id"], batch),
        )
    cur.executemany(
        """INSERT INTO ods_pm_pr
           (pr_id, pr_name, employee_id, project_id, assign_date, due_date, complete_date, status,
            rework_flag, work_hours, etl_load_time, etl_source, etl_batch_id, etl_operation, data_date)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW(),'pm_system',%s,'I',CURDATE())""",
        [row + (batch,) for row in pr_rows],
    )
    cur.executemany(
        """INSERT INTO ods_pm_project
           (project_id, project_name, project_status, owner_employee_id, start_date, end_date,
            etl_load_time, etl_source, etl_batch_id, etl_operation, data_date)
           VALUES (%s,%s,%s,%s,%s,%s,NOW(),'pm_system',%s,'I',CURDATE())""",
        [(p["project_id"], p["project_name"], p["project_status"], p["owner_employee_id"],
          p["start_date"], p["end_date"], batch) for p in projects],
    )
    cur.executemany(
        """INSERT INTO ods_itsm_ec
           (ec_id, ec_title, employee_id, project_id, severity, found_at, first_response_at, resolved_at, status,
            recur_flag, etl_load_time, etl_source, etl_batch_id, etl_operation, data_date)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW(),'itsm_system',%s,'I',CURDATE())""",
        [row + (batch,) for row in ec_rows],
    )
    conn.commit()
    cur.close()
    print("ODS source data loaded: employees %d, projects %d, PR %d, EC %d" % (len(employees), len(projects), len(pr_rows), len(ec_rows)))
