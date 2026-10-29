from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pathlib import Path

from common.database import init_db, get_session
from common.models import (DepartmentType, EmployeeType, Room,
                           Department, Employee, WorkTimeRecord)
from common.services import start_workday, end_workday, build_report

init_db()
app = FastAPI(title="Оргструктура")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


def db():
    s = get_session()
    try:
        yield s
    finally:
        s.close()


# ---------- Главная ----------
@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(request, "index.html", {})


# ---------- Справочники типов ----------
@app.get("/types", response_class=HTMLResponse)
def types_page(request: Request, s: Session = Depends(db)):
    return templates.TemplateResponse(request, "types.html", {
        "dtypes": s.query(DepartmentType).all(),
        "etypes": s.query(EmployeeType).all(),
    })


@app.post("/types/department")
def add_dtype(name: str = Form(...), s: Session = Depends(db)):
    s.add(DepartmentType(name=name)); s.commit()
    return RedirectResponse("/types", status_code=303)


@app.post("/types/employee")
def add_etype(name: str = Form(...), s: Session = Depends(db)):
    s.add(EmployeeType(name=name)); s.commit()
    return RedirectResponse("/types", status_code=303)


# ---------- Помещения ----------
@app.get("/rooms", response_class=HTMLResponse)
def rooms_page(request: Request, s: Session = Depends(db)):
    return templates.TemplateResponse(request, "rooms.html", {
        "rooms": s.query(Room).all()
    })


@app.post("/rooms")
def add_room(number: str = Form(...), name: str = Form(""), s: Session = Depends(db)):
    s.add(Room(number=number, name=name or None)); s.commit()
    return RedirectResponse("/rooms", status_code=303)


@app.post("/rooms/{room_id}/delete")
def del_room(room_id: int, s: Session = Depends(db)):
    r = s.get(Room, room_id)
    if r:
        s.delete(r); s.commit()
    return RedirectResponse("/rooms", status_code=303)


# ---------- Подразделения ----------
@app.get("/departments", response_class=HTMLResponse)
def departments_page(request: Request, s: Session = Depends(db)):
    return templates.TemplateResponse(request, "departments.html", {
        "departments": s.query(Department).all(),
        "dtypes": s.query(DepartmentType).all(),
        "employees": s.query(Employee).all(),
    })


@app.post("/departments")
def add_dep(name: str = Form(...),
            type_id: int | None = Form(None),
            parent_id: int | None = Form(None),
            head_id: int | None = Form(None),
            s: Session = Depends(db)):
    s.add(Department(name=name, type_id=type_id, parent_id=parent_id, head_id=head_id))
    s.commit()
    return RedirectResponse("/departments", status_code=303)


# ---------- Сотрудники ----------
@app.get("/employees", response_class=HTMLResponse)
def employees_page(request: Request, s: Session = Depends(db)):
    return templates.TemplateResponse(request, "employees.html", {
        "employees": s.query(Employee).all(),
        "etypes": s.query(EmployeeType).all(),
        "rooms": s.query(Room).all(),
        "departments": s.query(Department).all(),
    })


@app.post("/employees")
def add_employee(full_name: str = Form(...),
                 type_id: int | None = Form(None),
                 office_id: int | None = Form(None),
                 manager_id: int | None = Form(None),
                 department_id: int | None = Form(None),
                 rooms_access: list[int] = Form(default=[]),
                 s: Session = Depends(db)):
    emp = Employee(full_name=full_name, type_id=type_id, office_id=office_id,
                   manager_id=manager_id, department_id=department_id)
    if rooms_access:
        emp.rooms_access = s.query(Room).filter(Room.id.in_(rooms_access)).all()
    s.add(emp); s.commit()
    return RedirectResponse("/employees", status_code=303)


@app.post("/employees/{emp_id}/delete")
def del_employee(emp_id: int, s: Session = Depends(db)):
    e = s.get(Employee, emp_id)
    if e:
        for d in s.query(Department).filter(Department.head_id == emp_id).all():
            d.head_id = None
        s.delete(e); s.commit()
    return RedirectResponse("/employees", status_code=303)


# ---------- Учёт времени ----------
@app.get("/worktime", response_class=HTMLResponse)
def worktime_page(request: Request, s: Session = Depends(db)):
    return templates.TemplateResponse(request, "worktime.html", {
        "employees": s.query(Employee).all(),
        "records": (s.query(WorkTimeRecord)
                     .order_by(WorkTimeRecord.work_date.desc(),
                               WorkTimeRecord.start_time.desc())
                     .limit(200).all()),
    })


@app.post("/worktime/start")
def wt_start(employee_id: int = Form(...), s: Session = Depends(db)):
    try:
        start_workday(s, employee_id)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return RedirectResponse("/worktime", status_code=303)


@app.post("/worktime/end")
def wt_end(employee_id: int = Form(...), s: Session = Depends(db)):
    try:
        end_workday(s, employee_id)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return RedirectResponse("/worktime", status_code=303)


# ---------- Отчёт ----------
@app.get("/report", response_class=HTMLResponse)
def report_page(request: Request, s: Session = Depends(db)):
    return templates.TemplateResponse(request, "report.html", {
        "departments": s.query(Department).all(),
        "rooms": s.query(Room).all(),
        "rows": None,
    })


@app.post("/report", response_class=HTMLResponse)
def report_run(request: Request,
               department_ids: list[int] = Form(default=[]),
               room_ids: list[int] = Form(default=[]),
               min_hours: float = Form(0),
               days_back: int = Form(30),
               s: Session = Depends(db)):
    rows = build_report(s, department_ids, room_ids, min_hours, days_back)
    return templates.TemplateResponse(request, "report.html", {
        "departments": s.query(Department).all(),
        "rooms": s.query(Room).all(),
        "rows": rows,
        "selected_dept": department_ids,
        "selected_rooms": room_ids,
        "min_hours": min_hours,
        "days_back": days_back,
    })
