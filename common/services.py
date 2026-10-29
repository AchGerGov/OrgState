from datetime import date, datetime, time, timedelta
from typing import Optional
from sqlalchemy import func
from sqlalchemy.orm import Session

from .models import Employee, WorkTimeRecord, Department, Room


# -------- Учёт рабочего времени --------

def start_workday(session: Session, employee_id: int, when: Optional[time] = None) -> WorkTimeRecord:
    today = date.today()
    when = when or datetime.now().time().replace(microsecond=0)
    existing = (session.query(WorkTimeRecord)
                .filter(WorkTimeRecord.employee_id == employee_id,
                        WorkTimeRecord.work_date == today)
                .first())
    if existing:
        raise ValueError("Запись за сегодня уже существует")
    rec = WorkTimeRecord(employee_id=employee_id, work_date=today, start_time=when)
    session.add(rec)
    session.commit()
    return rec


def end_workday(session: Session, employee_id: int, when: Optional[time] = None) -> WorkTimeRecord:
    today = date.today()
    when = when or datetime.now().time().replace(microsecond=0)
    rec = (session.query(WorkTimeRecord)
           .filter(WorkTimeRecord.employee_id == employee_id,
                   WorkTimeRecord.work_date == today)
           .first())
    if not rec:
        raise ValueError("Нет открытой смены на сегодня")
    if when <= rec.start_time:
        raise ValueError("Время окончания должно быть позже времени начала")
    rec.end_time = when
    session.commit()
    return rec


# -------- Отчёт --------

def _hours_in_window(session: Session, employee_id: int, cutoff: date) -> float:
    rows = (session.query(WorkTimeRecord)
            .filter(WorkTimeRecord.employee_id == employee_id,
                    WorkTimeRecord.work_date >= cutoff,
                    WorkTimeRecord.end_time.isnot(None))
            .all())
    total = 0.0
    for r in rows:
        s = datetime.combine(r.work_date, r.start_time)
        e = datetime.combine(r.work_date, r.end_time)
        total += (e - s).total_seconds() / 3600.0
    return total


def build_report(session: Session,
                 department_ids: list[int],
                 room_ids: list[int],
                 min_hours: float,
                 days_back: int = 30) -> list[dict]:
    """
    Сотрудники, у которых:
      * не менее 3-х подчинённых;
      * допущены не менее чем в 2 кабинета из заданного списка;
      * числятся в подразделениях из заданного списка;
      * отработали >= min_hours за последние days_back дней.
    """
    if not department_ids or not room_ids:
        return []

    cutoff = date.today() - timedelta(days=days_back)
    room_set = set(room_ids)

    candidates = (session.query(Employee)
                  .filter(Employee.department_id.in_(department_ids))
                  .all())

    result = []
    for emp in candidates:
        sub_count = (session.query(func.count(Employee.id))
                     .filter(Employee.manager_id == emp.id)
                     .scalar() or 0)
        if sub_count < 3:
            continue

        access = {r.id for r in emp.rooms_access}
        matching = access & room_set
        if len(matching) < 2:
            continue

        hours = _hours_in_window(session, emp.id, cutoff)
        if hours < min_hours:
            continue

        result.append({
            "id": emp.id,
            "full_name": emp.full_name,
            "department": emp.department.name if emp.department else "",
            "subordinates": sub_count,
            "rooms_matched": len(matching),
            "hours": round(hours, 2),
        })

    result.sort(key=lambda r: (-r["hours"], r["full_name"]))
    return result
