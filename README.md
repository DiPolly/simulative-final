# ETL грейдера → PostgreSQL → Google Sheets / Email

Учебный pipeline: скачивание статистики с API грейдера, разбор `passback_params`, валидация и загрузка в локальную PostgreSQL с записью стадий в лог. После успешной вставки в БД считаются дневные метрики, опционально выгружаются в Google Sheets и уходит email на mail.ru. Docker не используется.

## Что делает

1. Чистит логи старше 3 дней и пишет новый `logs/YYYY-MM-DD.log`
2. Запрашивает API статистики за период `start`–`end`
3. Разбирает `passback_params` (`ast.literal_eval`), валидирует поля, битые записи пропускает
4. Создаёт таблицу `attempts` (если нет), очищает её (`TRUNCATE`) и вставляет валидные строки
5. Считает дневные метрики (`aggregate.py`)
6. Опционально: строка в Google Sheets и/или письмо на mail.ru (без credentials — WARNING и продолжение)
7. Пишет итоговый summary в лог

Сбои Sheets/email после успешной загрузки в БД логируются как ERROR, но **код выхода остаётся 0** — данные уже в PostgreSQL.

## Структура

```text
simulative-final/
├── main.py              # точка входа
├── config.py            # URL, client, ключи, DSN, даты, Sheets/SMTP
├── api_client.py        # GET /api/statistics
├── transform.py         # разбор passback_params + валидация
├── db.py                # CREATE TABLE, TRUNCATE, INSERT
├── aggregate.py         # дневные метрики
├── sheets_export.py     # выгрузка в Google Sheets
├── email_notify.py      # письмо через mail.ru SMTP
├── logging_setup.py     # логи + ротация за 3 дня
├── credentials/         # JSON service account (не в git)
├── requirements.txt
├── .env.example
├── .env                 # локальные секреты (не в git)
└── logs/                # лог-файлы по дате
```

## Подготовка

### 1. PostgreSQL + DBeaver

Локальный PostgreSQL (тот же, к которому ходите из DBeaver).

1. Подключитесь к серверу (`localhost:5432`).
2. Создайте БД:

```sql
CREATE DATABASE grader_stats;
```

3. В `.env` укажите те же `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, что в DBeaver, и `POSTGRES_DB=grader_stats`.

### 2. Python

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # затем вписать свой пароль PostgreSQL
```

Файл `.env` не коммитить.

### Google Sheets (ручные шаги)

1. Google Cloud Console → создать проект → включить **Google Sheets API**
2. Создать service account → скачать JSON-ключ → сохранить как `credentials/google_service_account.json`
3. Создать Google Spreadsheet → скопировать ID из URL (`/d/<ID>/edit`)
4. Расшарить таблицу на email service account с правом **Editor**
5. В `.env` задать: `GOOGLE_CREDENTIALS_PATH`, `GOOGLE_SHEET_ID`, `GOOGLE_WORKSHEET_NAME` (по умолчанию `daily_stats`)

Без этих переменных ETL пишет WARNING и продолжает работу.

### Email mail.ru (ручные шаги)

1. Создать/использовать почтовый ящик mail.ru
2. Настройки → Безопасность → Пароли для внешних приложений → создать пароль (SMTP)
3. В `.env` задать: `SMTP_USER`, `SMTP_PASSWORD`, `EMAIL_TO` (часто совпадает с отправителем)

По умолчанию: `SMTP_SERVER=smtp.mail.ru`, `SMTP_PORT=465`. Без учётных данных — WARNING и продолжение.

## Запуск

```bash
python main.py
```

Период по умолчанию — `START_DATE` / `END_DATE` из `.env` (в примере: `2023-05-31`).

Опционально:

```bash
python main.py --start "2023-05-31 00:00:00.000000" --end "2023-05-31 23:59:59.999999"
```

Код выхода: `0` при успехе загрузки в БД, `1` при фатальной ошибке (API/БД и т.п.).

## Логи

- Каталог: `logs/`
- Имя файла: `YYYY-MM-DD.log`
- При каждом запуске удаляются `*.log` старше **3 дней**
- Формат: `время УРОВЕНЬ: сообщение`
- Сообщения стадий на русском (скачивание, валидация, заполнение БД, итог, Sheets/email)
- Пароли и JSON private keys **никогда** не пишутся в лог

## Повторный запуск

Каждый полный прогон делает `TRUNCATE attempts` и заливает данные заново за выбранный период. Повторный запуск безопасен: старые строки из таблицы заменяются новой выгрузкой. В Sheets при повторном запуске добавляется новая строка метрик.

## Проверка в DBeaver

Откройте соединение с `grader_stats` и выполните:

```sql
SELECT COUNT(*) FROM attempts;
SELECT * FROM attempts LIMIT 10;
```

## Критерии успеха

- `python main.py` отрабатывает без ошибок (код выхода 0)
- В `logs/YYYY-MM-DD.log` есть стадии: старт, скачивание, валидация, заполнение БД, итог
- В таблице `attempts` есть строки за выбранный период
- Повторный запуск не дублирует данные (truncate + reload)
- Пароли и ключи только в `.env` / `credentials/*.json`, не в коде и не в git
- Без Sheets/email credentials pipeline всё равно завершается успешно (WARNING)
