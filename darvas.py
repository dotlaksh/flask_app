import sqlite3
import pandas as pd
import logging

logger = logging.getLogger(__name__)

DB_PATH = "nse_data.db"

QUERY = """
WITH ranked AS (
    SELECT
        symbol,
        date,
        open,
        high,
        low,
        close,
        volume,

        ROW_NUMBER() OVER (
            PARTITION BY symbol
            ORDER BY date DESC
        ) AS rn

    FROM ohlcv
),

-- ---------------------------------------------------------
-- 52W HIGH
-- ---------------------------------------------------------

high_52w AS (
    SELECT
        symbol,
        MAX(high) AS high_52w
    FROM ranked
    WHERE rn <= 252
    GROUP BY symbol
),

latest AS (
    SELECT
        symbol,
        close AS current_price
    FROM ranked
    WHERE rn = 1
),

near_high AS (
    SELECT
        l.symbol,
        l.current_price,
        h.high_52w,

        ROUND(
            ((h.high_52w - l.current_price) * 100.0 / h.high_52w),
            2
        ) AS away_from_high_pct

    FROM latest l
    JOIN high_52w h
        ON l.symbol = h.symbol

    WHERE
        ((h.high_52w - l.current_price) * 100.0 / h.high_52w) <= 15
),

-- ---------------------------------------------------------
-- LAST 15 CANDLES
-- ---------------------------------------------------------

recent_box AS (
    SELECT *
    FROM ranked
    WHERE rn <= 15
),

-- ---------------------------------------------------------
-- BOX LEVELS
-- ---------------------------------------------------------

box_levels AS (
    SELECT
        symbol,

        MAX(high) AS box_high,
        MIN(low)  AS box_low,
        AVG(close) AS avg_close,
        COUNT(*) AS candles

    FROM recent_box
    GROUP BY symbol
),

-- ---------------------------------------------------------
-- RESISTANCE TOUCH COUNT
-- ---------------------------------------------------------

touches AS (
    SELECT
        r.symbol,

        COUNT(*) AS resistance_touches

    FROM recent_box r

    JOIN box_levels b
        ON r.symbol = b.symbol

    WHERE
        r.close >= b.box_high * 0.98

    GROUP BY r.symbol
),

-- ---------------------------------------------------------
-- FINAL DARVAS FILTER
-- ---------------------------------------------------------

final AS (
    SELECT
        b.symbol,

        b.box_high,
        b.box_low,

        ROUND(
            ((b.box_high - b.box_low) * 100.0 / b.avg_close),
            2
        ) AS box_range_pct,

        t.resistance_touches,

        n.current_price,
        n.high_52w,
        n.away_from_high_pct

    FROM box_levels b

    JOIN touches t
        ON b.symbol = t.symbol

    JOIN near_high n
        ON b.symbol = n.symbol

    WHERE
        b.candles >= 5

        -- Tight range
        AND ((b.box_high - b.box_low) * 100.0 / b.avg_close) <= 8

        -- Multiple resistance tests
        AND t.resistance_touches >= 3
)

SELECT *
FROM final

ORDER BY
    away_from_high_pct ASC,
    box_range_pct ASC;
"""


def scan_darvas(conn):
    """Scan for Darvas box patterns."""
    try:
        df = pd.read_sql_query(QUERY, conn)

        if df.empty:
            logger.info("No Darvas patterns found")
            return []

        logger.info(f"Found {len(df)} Darvas patterns")
        return df.to_dict(orient="records")

    except Exception as e:
        logger.error(f"Error scanning Darvas patterns: {e}")
        raise

if __name__ == "__main__":
    scan_darvas()
