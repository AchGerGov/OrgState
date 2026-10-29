# Оргштатная структура предприятия

Учёт подразделений, сотрудников, помещений, допусков, подчинённости, рабочего времени и отчётность.

**Две реализации:**
- **Веб:** Python + FastAPI + Jinja2 + Bootstrap + SQLite
- **Десктоп:** Python + PyQt6 + SQLite

Общая бизнес-логика и модели — в пакете `common/`.

---

## Содержание

1. [Требования](#1-требования)
2. [Установка](#2-установка)
3. [Запуск](#3-запуск)
4. [Пересборка](#4-пересборка)
5. [Docker (опционально)](#5-docker-опционально)
6. [PyQt6 на Linux](#6-pyqt6-на-linux)
7. [Типовые ошибки](#7-типовые-ошибки)
8. [Сценарии ТЗ](#8-сценарии-тз)
9. [Структура проекта](#9-структура-проекта)
10. [Анализ структуры БД](#10-анализ-структуры-бд)
11. [Структура БД](#11-Структура-БД)
12. [Журнал промптов](#12-журнал-промптов)

---

## 1. Требования

- Python **3.10+** (используется синтаксис `list[int]`, `int | None`)
- pip, venv
- Windows 10/11, Linux, macOS
- Для PyQt6 на Linux — системные библиотеки (см. §6)

Проверка:

```bash
python --version     # или python3 --version
```

---

## 2. Установка

### 2.1 Windows (CMD)

```cmd
cd %USERPROFILE%
git clone https://github.com/AchGerGov/OrgState.git
cd OrgState
python -m venv .venv
.venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
python seed.py
```

### 2.2 Windows (PowerShell)

```powershell
cd $HOME
git clone https://github.com/AchGerGov/OrgState.git
cd OrgState
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python seed.py
```

Если PowerShell блокирует активацию:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

### 2.3 Linux / macOS

```bash
cd ~
git clone https://github.com/AchGerGov/OrgState.git
cd OrgState
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python seed.py
```

### 2.4 `requirements.txt`

```txt
sqlalchemy>=2.0
pydantic>=2.5
fastapi>=0.110
uvicorn[standard]>=0.27
jinja2>=3.1
python-multipart>=0.0.9
PyQt6>=6.6
```

Только веб (без PyQt6):

```bash
pip install sqlalchemy pydantic fastapi "uvicorn[standard]" jinja2 python-multipart
```

### 2.5 Ожидаемый результат установки

- Активирован venv (в приглашении `(.venv)`)
- `python seed.py` печатает `Seed OK`
- В корне появился `org.db`

---

## 3. Запуск

Нужно **два терминала**: один держит веб-сервер, второй — десктоп (второй не обязателен, если проверяете только веб).

### 3.1 Веб-сервер (FastAPI + Uvicorn)

**Windows CMD:**

```cmd
cd %USERPROFILE%\OrgState
.venv\Scripts\activate.bat
uvicorn web.main:app --port 8000
```

**Windows PowerShell:**

```powershell
cd $HOME\OrgState
.\.venv\Scripts\Activate.ps1
uvicorn web.main:app --port 8000
```

**Linux / macOS:**

```bash
cd ~/OrgState
source .venv/bin/activate
uvicorn web.main:app --port 8000
```

Ожидаемый вывод:

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

Страницы:

| URL | Раздел |
|---|---|
| http://127.0.0.1:8000/ | Главная |
| http://127.0.0.1:8000/employees | Сотрудники |
| http://127.0.0.1:8000/departments | Подразделения |
| http://127.0.0.1:8000/rooms | Помещения |
| http://127.0.0.1:8000/types | Типы (справочники) |
| http://127.0.0.1:8000/worktime | Учёт рабочего времени |
| http://127.0.0.1:8000/report | Отчёт |
| http://127.0.0.1:8000/docs | Swagger / OpenAPI |

Остановить сервер: `Ctrl+C` в терминале.

### 3.2 Десктоп (PyQt6)

Запускать **из корня проекта** и **в активированном venv**, в отдельном терминале.

**Windows CMD:**

```cmd
cd %USERPROFILE%\OrgState
.venv\Scripts\activate.bat
python -m desktop.app
```

**Windows PowerShell:**

```powershell
cd $HOME\OrgState
.\.venv\Scripts\Activate.ps1
python -m desktop.app
```

**Linux / macOS:**

```bash
cd ~/OrgState
source .venv/bin/activate
python -m desktop.app
```

Откроется окно с вкладками: *Сотрудники, Подразделения, Помещения, Типы, Учёт времени, Отчёт*.

---

## 4. Пересборка

### 4.1 Только БД (после правки `common/models.py`)

Миграций (Alembic) нет — схема создаётся с нуля при `seed.py`. Любое изменение моделей требует пересоздания `org.db`.

**CMD:**

```cmd
cd %USERPROFILE%\OrgState
.venv\Scripts\activate.bat
del org.db
python seed.py
uvicorn web.main:app --port 8000
```

**PowerShell:**

```powershell
cd $HOME\OrgState
.\.venv\Scripts\Activate.ps1
Remove-Item org.db -ErrorAction SilentlyContinue
python seed.py
uvicorn web.main:app --port 8000
```

**Linux / macOS:**

```bash
cd ~/OrgState
source .venv/bin/activate
rm -f org.db
python seed.py
uvicorn web.main:app --port 8000
```

### 4.2 Пересоздать venv (после смены `requirements.txt`)

**CMD:**

```cmd
taskkill /IM python.exe /F
cd %USERPROFILE%\OrgState
rmdir /s /q .venv
del org.db
python -m venv .venv
.venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
python seed.py
uvicorn web.main:app --port 8000
```

**PowerShell:**

```powershell
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
cd $HOME\OrgState
Remove-Item -Recurse -Force .venv
Remove-Item org.db -ErrorAction SilentlyContinue
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python seed.py
uvicorn web.main:app --port 8000
```

**Linux / macOS:**

```bash
pkill -f uvicorn || true
pkill -f "python -m desktop" || true
cd ~/OrgState
rm -rf .venv org.db
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python seed.py
uvicorn web.main:app --port 8000
```

### 4.3 Полный сброс (клон заново)

**CMD:**

```cmd
cd %USERPROFILE%
rmdir /s /q OrgState
git clone https://github.com/AchGerGov/OrgState.git
cd OrgState
python -m venv .venv
.venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
python seed.py
```

**PowerShell:**

```powershell
cd $HOME
Remove-Item -Recurse -Force OrgState
git clone https://github.com/AchGerGov/OrgState.git
cd OrgState
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python seed.py
```

**Linux / macOS:**

```bash
cd ~
rm -rf OrgState
git clone https://github.com/AchGerGov/OrgState.git
cd OrgState
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python seed.py
```

### 4.4 Сброс только кэша Python (без пересоздания venv)

**CMD:**

```cmd
cd %USERPROFILE%\OrgState
for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"
```

**PowerShell:**

```powershell
cd $HOME\OrgState
Get-ChildItem -Recurse -Directory -Filter __pycache__ | Remove-Item -Recurse -Force
```

**Linux / macOS:**

```bash
cd ~/OrgState
find . -type d -name __pycache__ -exec rm -rf {} +
```

---

## 5. Docker (опционально)

`Dockerfile`:

```dockerfile
FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN python seed.py
EXPOSE 8000
CMD ["uvicorn", "web.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

`docker-compose.yml`:

```yaml
services:
  web:
    build: .
    container_name: org_web
    ports:
      - "8000:8000"
    volumes:
      - ./org.db:/app/org.db
    restart: unless-stopped
```

Запуск:

```bash
docker compose build
docker compose up -d
docker compose logs -f web
# http://localhost:8000/
```

Полная пересборка:

```bash
docker compose down -v
docker compose build --no-cache
docker compose up -d
```

> PyQt6 в контейнере без X-сервера не работает — десктоп-часть через Docker не демонстрируется.

---

## 6. PyQt6 на Linux

Без системных библиотек PyQt6 не запустится даже при успешной установке через pip.

```bash
# Debian / Ubuntu
sudo apt-get update
sudo apt-get install -y libgl1 libegl1 libxkbcommon0 libdbus-1-3 \
    libfontconfig1 libxrender1 libxi6 libxcursor1 libxrandr2

# Fedora
sudo dnf install mesa-libGL mesa-libEGL libxkbcommon dbus-libs fontconfig \
    libXrender libXi libXcursor libXrandr

# Arch
sudo pacman -S mesa libxkbcommon dbus fontconfig libxrender libxi libxcursor libxrandr
```

Если GUI недоступен (headless-сервер, WSL без WSLg) — используйте только веб-часть, либо:

```bash
sudo apt-get install -y xvfb
xvfb-run -a python -m desktop.app
```

macOS — дополнительных библиотек не требуется, PyQt6 ставится через pip «из коробки».

---

## 7. Типовые ошибки

| Симптом | Причина / решение |
|---|---|
| `500 Internal Server Error` + `TypeError: unhashable type: 'dict'` в трейсбеке | Несовместимость сигнатуры `TemplateResponse` в Starlette ≥ 0.29. В `web/main.py` должно быть `TemplateResponse(request, "name.html", {…})` (request первым аргументом). Если код старый — либо правьте `main.py`, либо откатите: `pip install "starlette<0.29"`. |
| `ModuleNotFoundError: No module named 'common'` | Запуск не из корня проекта. `cd` в `OrgState/` (где лежат `common/`, `web/`, `desktop/`). |
| `ModuleNotFoundError: No module named 'PyQt6'` | `pip install PyQt6` в активированном venv. |
| `Form data requires "python-multipart"` | `pip install python-multipart`. |
| `sqlalchemy.exc.OperationalError: no such table` | Не запускали `python seed.py`, либо `org.db` в другом рабочем каталоге. |
| `no such column: employees.department_id` | Старая `org.db` после правки моделей. Удалить `org.db` → `python seed.py`. |
| `Address already in use` (порт 8000) | Порт занят старым процессом. См. ниже. Либо `uvicorn … --port 8001`. |
| `'.venv\Scripts\activate' не является внутренней командой` | В CMD активатор — `activate.bat`; в PowerShell — `Activate.ps1`; `activate` без расширения — только Unix. |
| PowerShell: `выполнение сценариев отключено` | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`. |
| PyQt-окно не появляется, процесс висит | Нет GUI-сессии. Используйте веб или `xvfb-run python -m desktop.app` на Linux. |
| `ValueError: Запись за сегодня уже существует` | Норма: одна смена в день. Сначала «Завершить день», потом «Начать день» на следующий. |
| macOS: `qt.qpa.plugin: Could not find the Qt platform plugin "cocoa"` | Обычно из-за несовпадения архитектур (arm64 vs x86_64). Используйте нативный `python` соответствующей арх. |

### Убить зависшие процессы и освободить порт

**CMD:**

```cmd
netstat -ano | findstr :8000
taskkill /PID <PID_из_вывода> /F

:: все python-процессы
taskkill /IM python.exe /F
```

**PowerShell:**

```powershell
$pid = (Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue).OwningProcess
if ($pid) { Stop-Process -Id $pid -Force }

# все python-процессы
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
```

**Linux / macOS:**

```bash
# только процесс на порту 8000
lsof -ti :8000 | xargs -r kill -9

# все uvicorn / PyQt процессы
pkill -f uvicorn || true
pkill -f "python -m desktop" || true
```

---

## 8. Сценарии ТЗ

| # | Сценарий | Где |
|---|---|---|
| 1 | Новый тип сотрудника | `/types` или вкладка «Типы» в PyQt |
| 2 | Новое подразделение в дерево | `/departments` — задать «Вышестоящее» |
| 3 | Сотрудник нового типа | `/employees` — выбрать новый тип |
| 4 | Правка данных для отчёта | `/employees` (допуски, подразделение) и `/worktime` (часы) |
| 5 | Формирование отчёта | `/report` (веб) или вкладка «Отчёт» (PyQt) |
| 6 | Учёт времени | `/worktime`: «Начать день» / «Завершить день» |

Демо-данные из `seed.py` уже содержат Петрова П.П. с 3 подчинёнными, допусками в 3 кабинета и ~190 часами за последние 19 дней — отчёт по умолчанию (`min_hours=100`, `days_back=30`) его находит.

---

## 9. Структура проекта

```
OrgState/
├── common/
│   ├── __init__.py
│   ├── database.py      # engine, SessionLocal, init_db
│   ├── models.py        # SQLAlchemy-модели
│   ├── schemas.py       # Pydantic-схемы
│   └── services.py      # учёт времени + отчёт
├── web/
│   ├── main.py          # FastAPI
│   └── templates/       # Jinja2 + Bootstrap
├── desktop/
│   └── app.py           # PyQt6
├── seed.py              # демо-данные
├── requirements.txt
├── PROMPTS.md           # журнал промптов ИИ
├── README.md
└── org.db               # создаётся seed.py
```

---

## 10. Анализ структуры БД

После генерации ИИ схема была проверена вручную. Найденные проблемы и исправления:

| Проблема | Исправление |
|---|---|
| Не было связи «Сотрудник → Подразделение», из-за чего отчёт по подразделениям невозможен | Добавлено поле `Employee.department_id` (FK на `departments`, `ON DELETE SET NULL`) |
| У M2M `room_access` отсутствовали `ondelete=CASCADE` | Добавлены `ondelete="CASCADE"` на оба FK |
| `Department.parent_id` без каскада — при удалении родителя «висели» потомки | `ondelete="CASCADE"` |
| `Employee.manager_id` без каскада — удаление руководителя ломало дерево | `ondelete="SET NULL"` |
| Нет индексов по `manager_id`, `parent_id`, `department_id` — медленный отчёт | Добавлены индексы |
| Не было `WorkTimeRecord` | Добавлена сущность + `UniqueConstraint(employee_id, work_date, start_time)` и валидация `end_time > start_time` |
| Наименование помещения не было уникальным | `Room.number UNIQUE` |
| `Department.head_id` создавал циклическую зависимость при вставке | `post_update=True` в relationship + `ON DELETE SET NULL` |

Все правки внесены в `common/models.py`. Исходный код ИИ (до правок) сохранён в истории коммитов для проверки.

### Учёт рабочего времени

`common/services.py`: `start_workday` / `end_workday` — одна запись на сотрудника в день, проверка «конец > начало».

### Отчёт

`build_report(department_ids, room_ids, min_hours, days_back=30)`:

- сотрудник в одном из выбранных подразделений;
- `count(subordinates) >= 3`;
- пересечение `rooms_access` со списком `room_ids` содержит ≥ 2 элемента;
- суммарная длительность смен за последние `days_back` дней ≥ `min_hours`.

«Последний месяц» реализован как скользящее окно `days_back=30` (параметр). Доступен в вебе и в PyQt.

---

### 11. Структура БД (ER, текстом)

| Таблица | Поля | Связи |
|---|---|---|
| `department_types` | id, name | 1→N `departments` |
| `employee_types` | id, name | 1→N `employees` |
| `rooms` | id, number (UQ), name | 1→N `employees` (office); M2M с `employees` |
| `departments` | id, name, type_id FK, head_id FK, parent_id FK (self) | →`department_types`, →`employees`(head), self |
| `employees` | id, full_name, type_id FK, office_id FK, manager_id FK (self), department_id FK | →`employee_types`, →`rooms`, self, →`departments` |
| `room_access` | employee_id PK/FK, room_id PK/FK | M2M `employees`↔`rooms` |
| `work_time_records` | id, employee_id FK, work_date, start_time, end_time, comment; UQ(employee_id, work_date, start_time) | →`employees` |

---

## 12. Журнал промптов

Все использованные промпты и краткие результаты — в `PROMPTS.md` (требование ТЗ, проверяется на защите).
