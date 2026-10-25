"""Smoke and contract test to run after docker compose up -d.

Uses Python standard library; does not need pytest.
Usage: python tests/test_calendar_service.py
"""
from urllib.request import urlopen, Request
import json
from datetime import date

BASE = "http://localhost:8080"


def get_json(path):
    with urlopen(BASE + path, timeout=10) as resp:
        return json.load(resp)


def run():
    state = get_json("/api/health")
    assert state["status"] == "ok", state
    result = get_json("/api/calendar?country=RU&year=2026&month=1")
    assert len(result["days"]) == 31
    assert sum(result["summary"].values()) == 31
    jan1 = next(d for d in result["days"] if d["date"] == "2026-01-01")
    assert jan1["day_type"] == "holiday" and jan1["holiday_name"]
    before = get_json("/api/saved?country=RU&year=2026&month=1")
    print("База до сохранения:", before["total"])
    body = json.dumps({"country":"RU","year":2026,"month":1}).encode("utf-8")
    request = Request(BASE + "/api/save-month", data=body, headers={"Content-Type":"application/json"}, method="POST")
    with urlopen(request, timeout=20) as resp:
        saved = json.load(resp)
    assert saved["saved"] == 31
    after = get_json("/api/saved?country=RU&year=2026&month=1")
    assert after["total"] == 31, after
    print("Успех: все 4 контейнера доступны, календарь 31 день, CRUD сохранения в PostgreSQL работает")


if __name__ == "__main__":
    run()
