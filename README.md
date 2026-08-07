# Итоговый проект: статистика грейдера

Скрипт скачивает попытки студентов из API, чистит данные, пишет в PostgreSQL,
считает сводку за день, отправляет её в Google Sheets и на почту. Лог пишется в файл.

## Файлы

- `main.py` — весь скрипт (функции + запуск)
- `config.py` — настройки из `.env`
- `.env.example` — пример настроек
- `requirements.txt` — библиотеки

## Запуск

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Заполнить `.env` (пароль PostgreSQL, Google Sheet ID, почта). Потом:

```bash
python main.py
```

## Проверка

```sql
SELECT COUNT(*) FROM attempts;
SELECT * FROM attempts LIMIT 10;
```

Ещё: файл в `logs/`, строка в Google Sheets, письмо на mail.ru.
