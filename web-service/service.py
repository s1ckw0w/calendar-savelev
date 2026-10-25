"""Standalone domain microservice (variant 28): official public holiday calendar."""
from calendar import monthrange
from datetime import date, timedelta

import holidays
from fastapi import FastAPI, Query

app = FastAPI(title="Calendar of Public Holidays - Variant 28", version="1.0")
COUNTRIES = {"RU": "Россия", "DE": "Германия", "US": "США", "GB": "Великобритания"}


@app.get("/health")
def health():
    return {"status": "ok", "service": "holidays"}


@app.get("/v1/countries")
def countries():
    return [{"code": code, "name": name} for code, name in COUNTRIES.items()]


@app.get("/v1/calendar")
def get_calendar(
    country: str = Query(default="RU", pattern="^(RU|DE|US|GB)$"),
    year: int = Query(default=2026, ge=2020, le=2040),
    month: int = Query(default=1, ge=1, le=12),
):
    """Return monthly days, national public holidays, weekends and workdays.

    Note: this is not an official employment calendar of transferred workdays.
    State/region-specific holidays aren't included (national-level scope only).
    """
    kwargs = {"years": year, "observed": True}
    if country == "RU":
        kwargs["language"] = "ru"
    national_holidays = holidays.country_holidays(country, **kwargs)
    number_of_days = monthrange(year, month)[1]
    result = []
    totals = {"workday": 0, "weekend": 0, "holiday": 0}
    for day in range(1, number_of_days + 1):
        value = date(year, month, day)
        holiday_name = national_holidays.get(value, "")
        if holiday_name:
            day_type = "holiday"
        elif value.weekday() >= 5:
            day_type = "weekend"
        else:
            day_type = "workday"
        totals[day_type] += 1
        result.append({
            "date": value.isoformat(),
            "weekday": value.weekday() + 1,
            "day_type": day_type,
            "holiday_name": holiday_name,
        })
    return {
        "country": country,
        "country_name": COUNTRIES[country],
        "year": year,
        "month": month,
        "days": result,
        "summary": totals,
        "source": "python-holidays (national public holidays; basic 5/2 workweek)",
        "disclaimer": "Не учитываются все официальные переносы рабочих дней и региональные выходные.",
    }
