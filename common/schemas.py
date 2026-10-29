from datetime import date, time
from typing import Optional
from pydantic import BaseModel


class TypeIn(BaseModel):
    name: str


class RoomIn(BaseModel):
    number: str
    name: Optional[str] = None


class EmployeeIn(BaseModel):
    full_name: str
    type_id: Optional[int] = None
    office_id: Optional[int] = None
    manager_id: Optional[int] = None
    department_id: Optional[int] = None
    rooms_access: list[int] = []


class DepartmentIn(BaseModel):
    name: str
    type_id: Optional[int] = None
    head_id: Optional[int] = None
    parent_id: Optional[int] = None


class WorkTimeIn(BaseModel):
    employee_id: int
    work_date: date
    start_time: time
    end_time: Optional[time] = None
    comment: Optional[str] = None


class ReportParams(BaseModel):
    department_ids: list[int]
    room_ids: list[int]
    min_hours: float
    days_back: int = 30
