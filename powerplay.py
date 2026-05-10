import sqlite3
import pandas as pd
import logging

logger = logging.getLogger(__name__)

DB_PATH = "nse_data.db"

# ---------------------------------------------------------
# Power Play + Near 52W High Combined Scan
# ---------------------------------------------------------

QUERY = """
WITH ranked AS (
    SELECT
        symbol,
        date,
        open,
        high,
        low,
        close,

        ROW_NUMBER() OVER (
            PARTITION BY symbol
            ORDER BY date DESC
        ) AS rn
    FROM ohlcv
),

-- ---------------------------------------------------------
-- 52 Week High
-- ---------------------------------------------------------

high_52w AS (
    SELECT
        symbol,
        MAX(high) AS high_52w
    FROM ranked
    WHERE rn <= 52
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
        ((h.high_52w - l.current_price) * 100.0 / h.high_52w) <= 25
),

-- ---------------------------------------------------------
-- Recent 30-session impulse move
-- ---------------------------------------------------------

recent_30 AS (
    SELECT *
    FROM ranked
    WHERE rn <= 30
),

impulse AS (
    SELECT
        symbol,

        MIN(low)  AS impulse_low,
        MAX(high) AS impulse_high,

        ROUND(
            ((MAX(high) - MIN(low)) * 100.0 / MIN(low)),
            2
        ) AS move_pct

    FROM recent_30
    GROUP BY symbol

    HAVING move_pct >= 20
),

-- ---------------------------------------------------------
-- Last 10 candles consolidation
-- ---------------------------------------------------------

consol AS (
    SELECT
        symbol,

        MAX(high) AS consol_high,
        MIN(low)  AS consol_low,
        AVG(close) AS avg_close

    FROM ranked
    WHERE rn <= 10
    GROUP BY symbol
),

-- ---------------------------------------------------------
-- Final Power Play logic
-- ---------------------------------------------------------

powerplay AS (
    SELECT
        i.symbol,

        i.move_pct,

        ROUND(
            ((i.impulse_high - c.consol_low) * 100.0 / i.impulse_high),
            2
        ) AS pullback_pct,

        ROUND(
            ((c.consol_high - c.consol_low) * 100.0 / c.avg_close),
            2
        ) AS range_pct

    FROM impulse i
    JOIN consol c
        ON i.symbol = c.symbol

    WHERE
        ((i.impulse_high - c.consol_low) * 100.0 / i.impulse_high) <= 8
        AND
        ((c.consol_high - c.consol_low) * 100.0 / c.avg_close) <= 6
)

-- ---------------------------------------------------------
-- FINAL MERGED OUTPUT
-- ---------------------------------------------------------

SELECT
    p.symbol,
    p.move_pct,
    p.pullback_pct,
    p.range_pct,

    n.current_price,
    n.high_52w,
    n.away_from_high_pct

FROM powerplay p
JOIN near_high n
    ON p.symbol = n.symbol

ORDER BY
    p.move_pct DESC,
    n.away_from_high_pct ASC;
"""


def scan_powerplay(conn):
    """Scan for PowerPlay patterns."""
    try:
        df = pd.read_sql_query(QUERY, conn)

        if df.empty:
            logger.info("No PowerPlay patterns found")
            return []

        logger.info(f"Found {len(df)} PowerPlay patterns")
        return df.to_dict(orient="records")

    except Exception as e:
        logger.error(f"Error scanning PowerPlay patterns: {e}")
        raise

if __name__ == "__main__":
    scan_powerplay()
