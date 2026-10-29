from sqlalchemy import (
    Column, Integer, String, ForeignKey, Date, Time, Table,
    UniqueConstraint, Index
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


# M2M: допуск сотрудника в помещение
room_access = Table(
    "room_access", Base.metadata,
    Column("employee_id", Integer, ForeignKey("employees.id", ondelete="CASCADE"), primary_key=True),
    Column("room_id",     Integer, ForeignKey("rooms.id",     ondelete="CASCADE"), primary_key=True),
)


class DepartmentType(Base):
    __tablename__ = "department_types"
    id   = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)

    departments = relationship("Department", back_populates="type")


class EmployeeType(Base):
    __tablename__ = "employee_types"
    id   = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)

    employees = relationship("Employee", back_populates="type")


class Room(Base):
    __tablename__ = "rooms"
    id     = Column(Integer, primary_key=True)
    number = Column(String(50), unique=True, nullable=False)
    name   = Column(String(200))

    # Сотрудники, у которых это помещение — рабочий кабинет
    occupants = relationship("Employee", back_populates="office", foreign_keys="Employee.office_id")


class Department(Base):
    __tablename__ = "departments"
    id        = Column(Integer, primary_key=True)
    name      = Column(String(200), nullable=False)
    type_id   = Column(Integer, ForeignKey("department_types.id", ondelete="SET NULL"))
    head_id   = Column(Integer, ForeignKey("employees.id", ondelete="SET NULL"))
    parent_id = Column(Integer, ForeignKey("departments.id", ondelete="CASCADE"))

    type    = relationship("DepartmentType", back_populates="departments")
    head    = relationship("Employee", foreign_keys=[head_id], post_update=True)
    parent  = relationship("Department", remote_side=[id], backref="children")
    employees = relationship("Employee", back_populates="department", foreign_keys="Employee.department_id")

    __table_args__ = (Index("ix_departments_parent", "parent_id"),)


class Employee(Base):
    __tablename__ = "employees"
    id         = Column(Integer, primary_key=True)
    full_name  = Column(String(300), nullable=False)
    type_id    = Column(Integer, ForeignKey("employee_types.id", ondelete="SET NULL"))
    office_id  = Column(Integer, ForeignKey("rooms.id", ondelete="SET NULL"))
    manager_id = Column(Integer, ForeignKey("employees.id", ondelete="SET NULL"))
    # ДОБАВЛЕНО при анализе БД: сотрудник закрепляется за подразделением,
    # чтобы отчёт мог фильтровать по подразделениям из списка
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="SET NULL"))

    type       = relationship("EmployeeType", back_populates="employees")
    office     = relationship("Room", back_populates="occupants", foreign_keys=[office_id])
    manager    = relationship("Employee", remote_side=[id], backref="subordinates")
    department = relationship("Department", back_populates="employees", foreign_keys=[department_id])
    rooms_access = relationship("Room", secondary=room_access, backref="employees_with_access")
    work_records = relationship("WorkTimeRecord", back_populates="employee",
                                cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_employees_manager", "manager_id"),
        Index("ix_employees_department", "department_id"),
    )


class WorkTimeRecord(Base):
    __tablename__ = "work_time_records"
    id          = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    work_date   = Column(Date, nullable=False)
    start_time  = Column(Time, nullable=False)
    end_time    = Column(Time, nullable=True)
    comment     = Column(String(500))

    employee = relationship("Employee", back_populates="work_records")

    __table_args__ = (
        UniqueConstraint("employee_id", "work_date", "start_time", name="uq_wt_emp_date_start"),
        Index("ix_wt_emp_date", "employee_id", "work_date"),
    )
