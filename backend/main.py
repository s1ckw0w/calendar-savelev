"""REST API gateway: calls web-service and implements Postgres CRUD."""
from calendar import monthrange
from contextlib import contextmanager
from datetime import date
import os

import httpx
import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

app = FastAPI(title="Holiday Calendar Backend - Variant 28", version="1.0")
SERVICE_URL = os.getenv("HOLIDAY_SERVICE_URL", "http://web-service:8001").rstrip("/")


@contextmanager
def db_connection():
    connection = psycopg2.connect(
        host=os.getenv("DB_HOST", "db"),
        port=int(os.getenv("DB_PORT", "5432")),
        dbname=os.getenv("DB_NAME", "holiday_calendar"),
        user=os.getenv("DB_USER", "holiday_app"),
        password=os.getenv("DB_PASSWORD", "local_demo_password_change_me"),
        connect_timeout=5,
    )
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


class CalendarSelection(BaseModel):
    country: str = Field(default="RU", pattern="^(RU|DE|US|GB)$")
    year: int = Field(default=2026, ge=2020, le=2040)
    month: int = Field(default=1, ge=1, le=12)


class NoteUpdate(BaseModel):
    note: str = Field(max_length=350)


async def fetch_month(country: str, year: int, month: int):
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                f"{SERVICE_URL}/v1/calendar",
                params={"country": country, "year": year, "month": month},
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail="Сервис праздников недоступен") from exc


@app.get("/api/health")
def api_health():
    try:
        with db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
    except psycopg2.Error as exc:
        raise HTTPException(status_code=503, detail="База данных недоступна") from exc
    return {"status": "ok", "database": "connected"}


@app.get("/api/calendar")
async def calendar(
    country: str = Query(default="RU", pattern="^(RU|DE|US|GB)$"),
    year: int = Query(default=2026, ge=2020, le=2040),
    month: int = Query(default=1, ge=1, le=12),
):
    return await fetch_month(country, year, month)


@app.get("/api/saved")
def list_saved(
    country: str = Query(default="RU", pattern="^(RU|DE|US|GB)$"),
    year: int = Query(default=2026, ge=2020, le=2040),
    month: int = Query(default=1, ge=1, le=12),
):
    date_from = date(year, month, 1)
    date_to = date(year, month, monthrange(year, month)[1])
    try:
        with db_connection() as connection:
            with connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT id, country, day_date, day_type, holiday_name, note, updated_at
                    FROM calendar_days
                    WHERE country = %s AND day_date BETWEEN %s AND %s
                    ORDER BY day_date
                """, (country, date_from, date_to))
                rows = cursor.fetchall()
    except psycopg2.Error as exc:
        raise HTTPException(status_code=503, detail="Ошибка чтения из PostgreSQL") from exc
    return {"total": len(rows), "entries": rows}


@app.post("/api/save-month")
async def save_month(selection: CalendarSelection):
    data = await fetch_month(selection.country, selection.year, selection.month)
    try:
        with db_connection() as connection:
            with connection.cursor() as cursor:
                for day in data["days"]:
                    cursor.execute("""
                        INSERT INTO calendar_days
                            (country, day_date, day_type, holiday_name)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (country, day_date) DO UPDATE SET
                            day_type = EXCLUDED.day_type,
                            holiday_name = EXCLUDED.holiday_name,
                            updated_at = NOW()
                        -- note is intentionally preserved for existing entries
                    """, (
                        selection.country, day["date"], day["day_type"], day["holiday_name"]
                    ))
    except psycopg2.Error as exc:
        raise HTTPException(status_code=503, detail="Ошибка сохранения в PostgreSQL") from exc
    return {"saved": len(data["days"]), "country": selection.country,
            "year": selection.year, "month": selection.month}


@app.patch("/api/saved/{entry_id}")
def update_note(entry_id: int, payload: NoteUpdate):
    try:
        with db_connection() as connection:
            with connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    UPDATE calendar_days SET note = %s, updated_at = NOW()
                    WHERE id = %s
                    RETURNING id, note
                """, (payload.note.strip(), entry_id))
                changed = cursor.fetchone()
    except psycopg2.Error as exc:
        raise HTTPException(status_code=503, detail="Ошибка обновления PostgreSQL") from exc
    if not changed:
        raise HTTPException(status_code=404, detail="Запись не найдена")
    return changed


@app.delete("/api/saved/{entry_id}")
def delete_saved(entry_id: int):
    try:
        with db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM calendar_days WHERE id = %s RETURNING id", (entry_id,))
                deleted = cursor.fetchone()
    except psycopg2.Error as exc:
        raise HTTPException(status_code=503, detail="Ошибка удаления из PostgreSQL") from exc
    if not deleted:
        raise HTTPException(status_code=404, detail="Запись не найдена")
    return {"deleted": entry_id}
