# Итоговый проект: статистика грейдера

Скрипт забирает данные об попытках студентов из API, чистит их, кладёт в локальный PostgreSQL, пишет лог, считает простую сводку за день и отправляет её в Google Sheets + на почту.

## Как запускается

1. Запрос к API (`requests`)
2. Разбор `passback_params` и проверка полей — кривые записи пропускаю и пишу в лог
3. Загрузка в таблицу `attempts`
4. Подсчёт метрик (попытки, успехи, уникальные юзеры и т.п.)
5. Строка в Google Sheets
6. Письмо на mail.ru, что прогон прошёл

Логи лежат в `logs/`, имя файла — сегодняшняя дата. Старые логи (старше 3 дней) удаляются при старте.

## Файлы

- `main.py` — запуск всего пайплайна
- `api_client.py` — скачивание с API
- `transform.py` — разбор и валидация
- `db.py` — таблица и вставка в PostgreSQL
- `logging_setup.py` — логи
- `aggregate.py` — дневная сводка
- `sheets_export.py` — выгрузка в Sheets
- `email_notify.py` — письмо через SMTP
- `config.py` — настройки из `.env`
- `.env.example` — пример настроек (без реальных паролей)

## Как поднять у себя

### База
В DBeaver создать базу `grader_stats`, в `.env` прописать те же host/port/user/password, что в подключении.

### Python
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```
Дальше заполнить `.env` своими значениями.

### Google Sheets
1. В Google Cloud включить Sheets API (и Drive API)
2. Создать service account, скачать json → положить в `credentials/google_service_account.json`
3. Создать таблицу, расшарить на email из json (Редактор)
4. В `.env` указать `GOOGLE_SHEET_ID`

### Почта
На mail.ru сделать пароль для внешних приложений (SMTP) и прописать в `.env`:
`SMTP_USER`, `SMTP_PASSWORD`, `EMAIL_TO`.

## Запуск

```bash
python main.py
```

Даты берутся из `.env` (`START_DATE` / `END_DATE`). Можно так:
```bash
python main.py --start "2023-05-31 00:00:00.000000" --end "2023-05-31 23:59:59.999999"
```

Перед вставкой таблица очищается (`TRUNCATE`), так что повторный запуск не размножает строки. В Sheets каждый раз добавляется новая строка сводки.

## Как проверить

В DBeaver:
```sql
SELECT COUNT(*) FROM attempts;
SELECT * FROM attempts LIMIT 10;
```

Ещё: лог в `logs/`, новая строка в Google Sheets, письмо на почту.

Часть записей из API приходит с пустым `lis_outcome_service_url` — их скрипт специально пропускает (это видно в логе как WARNING). Так и задумано.
