# Лабораторна робота 5. Модульний моноліт

![tests](https://github.com/Callibri/lab5/actions/workflows/tests.yml/badge.svg)

Система розділена на три модулі в одному застосунку:

- `core` фільми, звіти, користувачі, автентифікація;
- `analytics` метрики, які будуються з подій `core` (власні таблиці, власна модель);
- `audit` журнал подій.

Модулі спілкуються через події. Кожен споживач має власний ACL, який перетворює події `core` на внутрішні команди модуля.

## Встановлення

Потрібен Python 3.11 або новіший.

Windows (PowerShell):

```
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Linux / macOS:

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Запуск

```
uvicorn boxoffice.main:app --app-dir src --reload
```

Документація в браузері: http://127.0.0.1:8000/docs.

Змінна `ANALYTICS_LAG_MS` штучно затримує обробку подій в Analytics. Приклад (PowerShell):

```
$env:ANALYTICS_LAG_MS="3000"
uvicorn boxoffice.main:app --app-dir src --reload
```

Після додавання звіту `GET /movies/{id}` одразу показує нові дані, а `GET /movies/{id}/summary` показує їх із затримкою.

## Тести

```
pytest -v
```

- `tests/core`, `tests/analytics`, `tests/audit`, `tests/shared` тести окремих модулів;
- `tests/e2e` сильна й відкладена узгодженість, збій одного модуля не ламає інші;
- `tests/test_architecture.py` модулі імпортують один одного тільки через `contract`, імпорт чужого контракту дозволений лише в `infrastructure/acl` і `module.py`.

## Структура

```
src/boxoffice/
  shared/       базова подія, шина подій, налаштування бази, перевірка токена
  modules/
    core/       contract/ domain/ application/ infrastructure/ presentation/ module.py
    analytics/  contract/ domain/ application/ infrastructure/ (acl/) presentation/ module.py
    audit/      contract/ domain/ application/ infrastructure/ (acl/) presentation/ module.py
  bootstrap.py  складання модулів
```

## Документи

- `docs/ADR-001-bounded-contexts.md` межі контекстів;
- `docs/analysis/lab5.md` аналіз лабораторної 5 та ретроспектива курсу;
