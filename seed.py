from datetime import date, time, timedelta
from common.database import init_db, get_session
from common.models import (DepartmentType, EmployeeType, Room, Department,
                           Employee, WorkTimeRecord, room_access)

init_db()
s = get_session()

if s.query(EmployeeType).count() == 0:
    dt_dir = DepartmentType(name="Дирекция")
    dt_dev = DepartmentType(name="Разработка")
    s.add_all([dt_dir, dt_dev])

    et_mgr  = EmployeeType(name="Руководитель")
    et_dev  = EmployeeType(name="Разработчик")
    et_qa   = EmployeeType(name="Тестировщик")
    s.add_all([et_mgr, et_dev, et_qa])

    r101, r102, r103, r201 = Room(number="101"), Room(number="102"), Room(number="103"), Room(number="201")
    s.add_all([r101, r102, r103, r201])

    d1 = Department(name="Генеральный директор", type_id=dt_dir.id)
    d2 = Department(name="Отдел разработки",   type_id=dt_dev.id)
    s.add_all([d1, d2])
    s.commit()
    d2.parent_id = d1.id

    boss = Employee(full_name="Иванов И.И.", type_id=et_mgr.id,
                    office_id=r101.id, department_id=d1.id)
    s.add(boss); s.commit()
    d1.head_id = boss.id

    lead = Employee(full_name="Петров П.П.", type_id=et_mgr.id,
                    office_id=r101.id, manager_id=boss.id, department_id=d2.id)
    s.add(lead); s.commit()
    d2.head_id = lead.id

    subs = [
        Employee(full_name="Сидоров С.С.", type_id=et_dev.id, office_id=r102.id, manager_id=lead.id, department_id=d2.id),
        Employee(full_name="Кузнецов К.К.", type_id=et_dev.id, office_id=r102.id, manager_id=lead.id, department_id=d2.id),
        Employee(full_name="Орлов О.О.",   type_id=et_qa.id,  office_id=r103.id, manager_id=lead.id, department_id=d2.id),
    ]
    s.add_all(subs); s.commit()

    lead.rooms_access = [r101, r102, r103]
    for u in subs:
        u.rooms_access = [r102]
    s.commit()

    today = date.today()
    for i in range(1, 20):
        d = today - timedelta(days=i)
        s.add(WorkTimeRecord(employee_id=lead.id, work_date=d,
                             start_time=time(9, 0), end_time=time(19, 0)))  # 10ч * 19 = 190ч
    s.commit()

print("Seed OK")
