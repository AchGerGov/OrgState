import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date, time, timedelta
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QTableWidgetItem, QComboBox, QLineEdit, QLabel,
    QFormLayout, QMessageBox, QListWidget, QListWidgetItem, QSpinBox,
    QDoubleSpinBox, QDialog, QDialogButtonBox, QAbstractItemView
)
from PyQt6.QtCore import Qt

from common.database import init_db, get_session
from common.models import (DepartmentType, EmployeeType, Room, Department,
                           Employee, WorkTimeRecord)
from common.services import start_workday, end_workday, build_report


def refresh_table(table: QTableWidget, rows: list[list[str]]):
    table.setRowCount(0)
    for r_idx, row in enumerate(rows):
        table.insertRow(r_idx)
        for c_idx, val in enumerate(row):
            table.setItem(r_idx, c_idx, QTableWidgetItem(str(val)))


# ---------- Вкладка: Сотрудники ----------
class EmployeesTab(QWidget):
    def __init__(self):
        super().__init__()
        self.s = get_session()
        lay = QVBoxLayout(self)

        form = QFormLayout()
        self.fio = QLineEdit()
        self.cb_type = QComboBox()
        self.cb_dep = QComboBox()
        self.cb_office = QComboBox()
        self.cb_manager = QComboBox()
        self.list_rooms = QListWidget()
        self.list_rooms.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.list_rooms.setMaximumHeight(120)
        form.addRow("ФИО:", self.fio)
        form.addRow("Тип:", self.cb_type)
        form.addRow("Подразделение:", self.cb_dep)
        form.addRow("Кабинет:", self.cb_office)
        form.addRow("Начальник:", self.cb_manager)
        form.addRow("Допуски:", self.list_rooms)
        lay.addLayout(form)

        btn = QPushButton("Добавить сотрудника")
        btn.clicked.connect(self.add)
        lay.addWidget(btn)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["ФИО", "Тип", "Подразделение", "Начальник", "Кабинет", "Подчинённых"])
        lay.addWidget(self.table)

        del_btn = QPushButton("Удалить выбранного")
        del_btn.clicked.connect(self.delete)
        lay.addWidget(del_btn)

        self.reload()

    def reload(self):
        self.s.expire_all()
        self.cb_type.clear()
        for t in self.s.query(EmployeeType).all():
            self.cb_type.addItem(t.name, t.id)
        self.cb_dep.clear()
        self.cb_dep.addItem("—", None)
        for d in self.s.query(Department).all():
            self.cb_dep.addItem(d.name, d.id)
        self.cb_office.clear()
        self.cb_office.addItem("—", None)
        for r in self.s.query(Room).all():
            self.cb_office.addItem(r.number, r.id)
        self.cb_manager.clear()
        self.cb_manager.addItem("—", None)
        for e in self.s.query(Employee).all():
            self.cb_manager.addItem(e.full_name, e.id)
        self.list_rooms.clear()
        for r in self.s.query(Room).all():
            it = QListWidgetItem(r.number); it.setData(Qt.ItemDataRole.UserRole, r.id)
            self.list_rooms.addItem(it)

        rows = []
        for e in self.s.query(Employee).all():
            rows.append([
                e.full_name,
                e.type.name if e.type else "",
                e.department.name if e.department else "",
                e.manager.full_name if e.manager else "",
                e.office.number if e.office else "",
                len(e.subordinates),
            ])
        refresh_table(self.table, rows)
        self._ids = [e.id for e in self.s.query(Employee).all()]

    def add(self):
        try:
            emp = Employee(
                full_name=self.fio.text().strip(),
                type_id=self.cb_type.currentData(),
                department_id=self.cb_dep.currentData(),
                office_id=self.cb_office.currentData(),
                manager_id=self.cb_manager.currentData(),
            )
            if not emp.full_name:
                raise ValueError("ФИО обязательно")
            access_ids = [it.data(Qt.ItemDataRole.UserRole)
                          for it in self.list_rooms.selectedItems()]
            emp.rooms_access = self.s.query(Room).filter(Room.id.in_(access_ids)).all() if access_ids else []
            self.s.add(emp); self.s.commit()
            self.fio.clear(); self.reload()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    def delete(self):
        row = self.table.currentRow()
        if row < 0: return
        emp = self.s.get(Employee, self._ids[row])
        if emp:
            for d in self.s.query(Department).filter(Department.head_id == emp.id).all():
                d.head_id = None
            self.s.delete(emp); self.s.commit(); self.reload()


# ---------- Вкладка: Подразделения ----------
class DepartmentsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.s = get_session()
        lay = QVBoxLayout(self)
        form = QFormLayout()
        self.name = QLineEdit()
        self.cb_type = QComboBox()
        self.cb_parent = QComboBox()
        self.cb_head = QComboBox()
        form.addRow("Наименование:", self.name)
        form.addRow("Тип:", self.cb_type)
        form.addRow("Вышестоящее:", self.cb_parent)
        form.addRow("Руководитель:", self.cb_head)
        lay.addLayout(form)
        btn = QPushButton("Добавить подразделение"); btn.clicked.connect(self.add)
        lay.addWidget(btn)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Наименование", "Тип", "Вышестоящее", "Руководитель"])
        lay.addWidget(self.table)
        self.reload()

    def reload(self):
        self.s.expire_all()
        self.cb_type.clear()
        for t in self.s.query(DepartmentType).all():
            self.cb_type.addItem(t.name, t.id)
        self.cb_parent.clear(); self.cb_parent.addItem("—", None)
        for d in self.s.query(Department).all():
            self.cb_parent.addItem(d.name, d.id)
        self.cb_head.clear(); self.cb_head.addItem("—", None)
        for e in self.s.query(Employee).all():
            self.cb_head.addItem(e.full_name, e.id)
        rows = [[d.name, d.type.name if d.type else "",
                 d.parent.name if d.parent else "",
                 d.head.full_name if d.head else ""]
                for d in self.s.query(Department).all()]
        refresh_table(self.table, rows)

    def add(self):
        d = Department(name=self.name.text().strip(),
                       type_id=self.cb_type.currentData(),
                       parent_id=self.cb_parent.currentData(),
                       head_id=self.cb_head.currentData())
        if not d.name:
            QMessageBox.warning(self, "!", "Наименование обязательно"); return
        self.s.add(d); self.s.commit()
        self.name.clear(); self.reload()


# ---------- Вкладка: Помещения ----------
class RoomsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.s = get_session()
        lay = QVBoxLayout(self)
        h = QHBoxLayout()
        self.number = QLineEdit(); self.number.setPlaceholderText("Номер")
        self.name = QLineEdit(); self.name.setPlaceholderText("Название")
        btn = QPushButton("Добавить"); btn.clicked.connect(self.add)
        h.addWidget(self.number); h.addWidget(self.name); h.addWidget(btn)
        lay.addLayout(h)
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Номер", "Название"])
        lay.addWidget(self.table)
        self.reload()

    def reload(self):
        self.s.expire_all()
        refresh_table(self.table, [[r.number, r.name or ""] for r in self.s.query(Room).all()])

    def add(self):
        try:
            self.s.add(Room(number=self.number.text().strip() or None,
                            name=self.name.text().strip() or None))
            self.s.commit(); self.number.clear(); self.name.clear(); self.reload()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))


# ---------- Вкладка: Типы ----------
class TypesTab(QWidget):
    def __init__(self):
        super().__init__()
        self.s = get_session()
        lay = QVBoxLayout(self)
        # типы подразделений
        h1 = QHBoxLayout()
        self.dt_name = QLineEdit(); self.dt_name.setPlaceholderText("Новый тип подразделения")
        b1 = QPushButton("Добавить"); b1.clicked.connect(self.add_dt)
        h1.addWidget(self.dt_name); h1.addWidget(b1)
        lay.addLayout(h1)
        self.dt_table = QTableWidget(0, 1)
        self.dt_table.setHorizontalHeaderLabels(["Типы подразделений"])
        lay.addWidget(self.dt_table)
        # типы сотрудников
        h2 = QHBoxLayout()
        self.et_name = QLineEdit(); self.et_name.setPlaceholderText("Новый тип сотрудника")
        b2 = QPushButton("Добавить"); b2.clicked.connect(self.add_et)
        h2.addWidget(self.et_name); h2.addWidget(b2)
        lay.addLayout(h2)
        self.et_table = QTableWidget(0, 1)
        self.et_table.setHorizontalHeaderLabels(["Типы сотрудников"])
        lay.addWidget(self.et_table)
        self.reload()

    def reload(self):
        self.s.expire_all()
        refresh_table(self.dt_table, [[t.name] for t in self.s.query(DepartmentType).all()])
        refresh_table(self.et_table, [[t.name] for t in self.s.query(EmployeeType).all()])

    def add_dt(self):
        if not self.dt_name.text().strip(): return
        self.s.add(DepartmentType(name=self.dt_name.text().strip()))
        self.s.commit(); self.dt_name.clear(); self.reload()

    def add_et(self):
        if not self.et_name.text().strip(): return
        self.s.add(EmployeeType(name=self.et_name.text().strip()))
        self.s.commit(); self.et_name.clear(); self.reload()


# ---------- Вкладка: Учёт времени ----------
class WorkTimeTab(QWidget):
    def __init__(self):
        super().__init__()
        self.s = get_session()
        lay = QVBoxLayout(self)
        self.cb_emp = QComboBox()
        h = QHBoxLayout()
        h.addWidget(QLabel("Сотрудник:")); h.addWidget(self.cb_emp)
        b_start = QPushButton("Начать день"); b_start.clicked.connect(self.start)
        b_end = QPushButton("Завершить день"); b_end.clicked.connect(self.end)
        h.addWidget(b_start); h.addWidget(b_end)
        lay.addLayout(h)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Сотрудник", "Дата", "Начало", "Конец"])
        lay.addWidget(self.table)
        self.reload()

    def reload(self):
        self.s.expire_all()
        self.cb_emp.clear()
        for e in self.s.query(Employee).all():
            self.cb_emp.addItem(e.full_name, e.id)
        rows = [[r.employee.full_name, str(r.work_date), str(r.start_time), str(r.end_time or "—")]
                for r in (self.s.query(WorkTimeRecord)
                          .order_by(WorkTimeRecord.work_date.desc()).limit(100).all())]
        refresh_table(self.table, rows)

    def start(self):
        try:
            start_workday(self.s, self.cb_emp.currentData()); self.reload()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    def end(self):
        try:
            end_workday(self.s, self.cb_emp.currentData()); self.reload()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))


# ---------- Вкладка: Отчёт ----------
class ReportTab(QWidget):
    def __init__(self):
        super().__init__()
        self.s = get_session()
        lay = QVBoxLayout(self)
        info = QLabel("Сотрудники: ≥3 подчинённых, ≥2 кабинетов из списка, из выбранных подразделений, "
                      "отработавшие ≥ заданного числа часов за последние N дней.")
        info.setWordWrap(True); lay.addWidget(info)

        h1 = QHBoxLayout()
        self.dep_list = QListWidget(); self.dep_list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.room_list = QListWidget(); self.room_list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        h1.addWidget(QLabel("Подразделения:")); h1.addWidget(self.dep_list)
        h1.addWidget(QLabel("Кабинеты:")); h1.addWidget(self.room_list)
        lay.addLayout(h1)

        h2 = QHBoxLayout()
        h2.addWidget(QLabel("Мин. часов:"))
        self.min_hours = QDoubleSpinBox(); self.min_hours.setMaximum(100000); self.min_hours.setValue(100)
        h2.addWidget(self.min_hours)
        h2.addWidget(QLabel("Дней назад:"))
        self.days_back = QSpinBox(); self.days_back.setMaximum(3650); self.days_back.setValue(30)
        h2.addWidget(self.days_back)
        btn = QPushButton("Сформировать"); btn.clicked.connect(self.run)
        h2.addWidget(btn)
        lay.addLayout(h2)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["ФИО", "Подразделение", "Подчинённых", "Кабинетов", "Часов"])
        lay.addWidget(self.table)
        self.reload()

    def reload(self):
        self.s.expire_all()
        self.dep_list.clear()
        for d in self.s.query(Department).all():
            it = QListWidgetItem(d.name); it.setData(Qt.ItemDataRole.UserRole, d.id)
            self.dep_list.addItem(it)
        self.room_list.clear()
        for r in self.s.query(Room).all():
            it = QListWidgetItem(r.number); it.setData(Qt.ItemDataRole.UserRole, r.id)
            self.room_list.addItem(it)

    def run(self):
        dep_ids = [it.data(Qt.ItemDataRole.UserRole) for it in self.dep_list.selectedItems()]
        room_ids = [it.data(Qt.ItemDataRole.UserRole) for it in self.room_list.selectedItems()]
        rows = build_report(self.s, dep_ids, room_ids,
                            self.min_hours.value(), self.days_back.value())
        refresh_table(self.table, [[r["full_name"], r["department"], r["subordinates"],
                                    r["rooms_matched"], r["hours"]] for r in rows])


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Оргструктура — PyQt6")
        self.resize(1100, 750)
        tabs = QTabWidget()
        tabs.addTab(EmployeesTab(), "Сотрудники")
        tabs.addTab(DepartmentsTab(), "Подразделения")
        tabs.addTab(RoomsTab(), "Помещения")
        tabs.addTab(TypesTab(), "Типы")
        tabs.addTab(WorkTimeTab(), "Учёт времени")
        tabs.addTab(ReportTab(), "Отчёт")
        self.setCentralWidget(tabs)


if __name__ == "__main__":
    init_db()
    app = QApplication(sys.argv)
    win = MainWindow(); win.show()
    sys.exit(app.exec())
