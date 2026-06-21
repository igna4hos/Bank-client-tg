import httpx

from app.config import settings

_API_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

# Описание схемы всех таблиц mart для подачи в промт
SCHEMA_PROMPT = """
Ты — аналитик данных банковской платформы. У тебя есть доступ к ClickHouse, база данных bank_marts.

ТАБЛИЦЫ И ПОЛЯ:

bank_marts.daily_turnover — дневные обороты бизнеса (МСБ)
  date Date, business_id UUID, inflow_sum Decimal, outflow_sum Decimal,
  inflow_count UInt32, outflow_count UInt32, tx_count UInt32, avg_tx_amount Decimal,
  unique_counterparties UInt32, active_day UInt8, cash_withdrawal_sum Decimal,
  balance_avg Decimal, balance_min Decimal, balance_volatility Decimal

bank_marts.monthly_turnover — месячные обороты бизнеса
  month Date, business_id UUID, inflow_sum Decimal, outflow_sum Decimal,
  tx_count UInt32, avg_balance Decimal, unique_counterparties UInt32

bank_marts.business_baseline — базовые показатели бизнеса (для детекции аномалий)
  business_id UUID, baseline_period String (значения: '30d','90d'), metric String,
  mean_value Float64, std_deviation Float64, p25 Float64, p75 Float64, calculated_at DateTime

bank_marts.daily_service_usage — использование сервисов клиентами по дням
  date Date, client_id UUID, service_id UUID, session_count UInt32,
  event_count UInt32, tx_sum Decimal, tx_count UInt32, cancel_count UInt32

bank_marts.monthly_service_usage — использование сервисов по месяцам
  month Date, client_id UUID, service_id UUID, active_days UInt32,
  session_count UInt32, tx_sum Decimal, unique_services_used UInt32

bank_marts.client_service_baseline — базовые показатели использования сервисов
  client_id UUID, baseline_period String, metric String,
  mean_value Float64, std_deviation Float64, p25 Float64, p75 Float64, calculated_at DateTime

bank_marts.daily_friction_stats — UX-метрики воронок по дням
  date Date, client_id UUID, funnel_id UUID, friction_event_count UInt32,
  rage_click_count UInt32, idle_count UInt32, ui_error_count UInt32,
  exit_without_action_count UInt32, session_count UInt32, completed_session_count UInt32,
  funnel_success_rate Float64, avg_task_duration_sec Float64,
  ux_tickets_count UInt32, is_active_day UInt8

bank_marts.client_friction_baseline — базовые UX-показатели
  client_id UUID, baseline_period String, metric String,
  mean_value Float64, std_deviation Float64, p25 Float64, p75 Float64, calculated_at DateTime

bank_marts.anomaly_alerts — алёрты об аномалиях
  alert_id UUID, detected_at DateTime, anomaly_type LowCardinality(String),
  entity_type LowCardinality(String) (значения: 'business','client'),
  entity_id UUID, metric_name String, metric_value Float64,
  baseline_mean Float64, baseline_std Float64, deviation_sigma Float64,
  severity LowCardinality(String) (значения: 'low','medium','high','critical'),
  details String, is_resolved UInt8

bank_marts.dim_funnels — справочник воронок (JOIN с daily_friction_stats по funnel_id)
  funnel_id UUID, funnel_name String, service_id UUID,
  target_event String, benchmark_duration_sec Float64, is_active UInt8, synced_at DateTime

bank_marts.dim_services — справочник сервисов (JOIN с daily_service_usage по service_id)
  service_id UUID, service_name String, service_type String, is_active UInt8, synced_at DateTime

ПРАВИЛА:
- Верни ТОЛЬКО SQL-запрос, без пояснений, без markdown-блоков
- Используй только SELECT
- Применяй LIMIT 50, если пользователь не просит иного
- Для дат используй функции ClickHouse: today(), yesterday(), toDate(), toStartOfMonth()
- UUID можно сравнивать через toString()
- Таблицы связывать через JOIN по полям service_id и funnel_id
""".strip()


async def _call(messages: list[dict], temperature: float) -> str:
    payload = {
        "modelUri": f"gpt://{settings.yandex_folder_id}/{settings.yandex_model}",
        "completionOptions": {
            "stream": False,
            "temperature": temperature,
            "maxTokens": 2000,
        },
        "messages": messages,
    }
    async with httpx.AsyncClient(timeout=60.0) as c:
        r = await c.post(
            _API_URL,
            json=payload,
            headers={"Authorization": f"Api-Key {settings.yandex_api_key}"},
        )
        r.raise_for_status()
        return r.json()["result"]["alternatives"][0]["message"]["text"].strip()


async def generate_sql(question: str) -> str:
    messages = [
        {"role": "system", "text": SCHEMA_PROMPT},
        {"role": "user", "text": question},
    ]
    return await _call(messages, temperature=0.1)


async def fix_sql(question: str, bad_sql: str, error: str) -> str:
    messages = [
        {"role": "system", "text": SCHEMA_PROMPT},
        {"role": "user", "text": question},
        {"role": "assistant", "text": bad_sql},
        {
            "role": "user",
            "text": f"Запрос вернул ошибку: {error}\nИсправь SQL. Верни только исправленный запрос.",
        },
    ]
    return await _call(messages, temperature=0.1)


async def generate_answer(question: str, sql: str, columns: list[str], rows: list) -> str:
    table_lines = [" | ".join(str(c) for c in columns)]
    table_lines += [" | ".join(str(v) for v in row) for row in rows[:50]]
    table_str = "\n".join(table_lines)

    truncated = f"\n(показаны первые 50 из {len(rows)} строк)" if len(rows) > 50 else ""

    user_text = (
        f"Вопрос: {question}\n\n"
        f"Выполненный SQL:\n{sql}\n\n"
        f"Результат ({len(rows)} строк):{truncated}\n{table_str}\n\n"
        f"Дай краткий аналитический ответ на вопрос на основе этих данных. Отвечай по-русски."
    )
    messages = [
        {
            "role": "system",
            "text": "Ты аналитик банковских данных. Отвечай кратко и по делу, используй числа из данных.",
        },
        {"role": "user", "text": user_text},
    ]
    return await _call(messages, temperature=0.3)
