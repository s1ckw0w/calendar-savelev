-- Database initialized automatically on the first creation of the Postgres volume.
CREATE TABLE IF NOT EXISTS calendar_days (
    id BIGSERIAL PRIMARY KEY,
    country VARCHAR(2) NOT NULL CHECK (country IN ('RU','DE','US','GB')),
    day_date DATE NOT NULL,
    day_type VARCHAR(12) NOT NULL CHECK (day_type IN ('workday','weekend','holiday')),
    holiday_name TEXT NOT NULL DEFAULT '',
    note TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_country_date UNIQUE (country, day_date)
);

CREATE INDEX IF NOT EXISTS idx_calendar_days_country_date
  ON calendar_days(country, day_date);

-- Demonstration rows: initial DB content exists even before the user saves a month.
INSERT INTO calendar_days (country, day_date, day_type, holiday_name, note)
VALUES
  ('RU', '2026-01-01', 'holiday', 'Новый год', 'Пример данных из init.sql'),
  ('RU', '2026-01-07', 'holiday', 'Рождество Христово', ''),
  ('RU', '2026-05-09', 'holiday', 'День Победы', ''),
  ('RU', '2026-10-24', 'weekend', '', 'Пример выходного дня'),
  ('DE', '2026-10-03', 'holiday', 'Tag der Deutschen Einheit', '')
ON CONFLICT (country, day_date) DO NOTHING;
