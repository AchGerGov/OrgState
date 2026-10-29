# Оргштатная структура предприятия

## Запуск

```bash
pip install fastapi uvicorn jinja2 sqlalchemy pydantic python-multipart PyQt6
python seed.py              # демо-данные
uvicorn web.main:app --reload    # веб на http://127.0.0.1:8000
python -m desktop.app            # десктоп
```

## Анализ структуры БД (после генерации ИИ) и исправления

Первичная генерация ИИ дала модели без следующих критичных моментов:

| Проблема | Исправление |
|---|---|
| Не было связи «Сотрудник → Подразделение» (по ТЗ связь неочевидна), из-за чего отчёт по подразделениям невозможен | Добавлено поле `Employee.department_id` (FK на `departments`, `ON DELETE SET NULL`) |
| У M2M `room_access` отсутствовали `ondelete=CASCADE` | Добавлены `ondelete="CASCADE"` на оба FK |
| `Department.parent_id` без каскада — при удалении родителя «висели» потомки | `ondelete="CASCADE"` |
| `Employee.manager_id` без каскада — удаление руководителя ломало дерево | `ondelete="SET NULL"` |
| Нет индексов по `manager_id`, `parent_id`, `department_id` — медленный отчёт | Добавлены индексы |
| Не было `WorkTimeRecord` | Добавлена сущность + `UniqueConstraint(employee_id, work_date, start_time)` и валидация `end_time > start_time` |
| Наименование помещения не было уникальным | `Room.number UNIQUE` |
| `Department.head_id` создавал циклическую зависимость при вставке | `post_update=True` в relationship + `ON DELETE SET NULL` |

Все правки внесены в `common/models.py`. Исходный код ИИ (без правок) сохранён в истории коммитов для проверки.

## Учёт времени

`common/services.py`: `start_workday` / `end_workday` — одна запись на сотрудника в день (без переработок), проверка «конец > начало».

## Отчёт

`build_report(department_ids, room_ids, min_hours, days_back=30)`:
- сотрудник в одном из выбранных подразделений;
- `count(subordinates) >= 3`;
- пересечение `rooms_access` со списком `room_ids` содержит ≥ 2 элемента;
- суммарная длительность смен за последние `days_back` дней ≥ `min_hours`.

«Последний месяц» реализован как скользящее окно `days_back=30` (параметр). Доступно в вебе и в PyQt.

## Сценарии из ТЗ

1. **Новый тип сотрудника** → `/types` или вкладка «Типы».
2. **Добавить подразделение в дерево** → `/departments` (выбор `parent_id`).
3. **Сотрудник нового типа** → `/employees`.
4. **Изменение данных для отчёта** → редактирование допусков/часов.
5. **Формирование отчёта** → `/report`.
