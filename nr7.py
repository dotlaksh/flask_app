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

        -- Daily range %
        ((high - low) / close) * 100 AS range_pct,

        -- Previous day high/low
        LAG(high) OVER (
            PARTITION BY symbol
            ORDER BY date
        ) AS prev_high,

        LAG(low) OVER (
            PARTITION BY symbol
            ORDER BY date
        ) AS prev_low,

        -- Previous close
        LAG(close) OVER (
            PARTITION BY symbol
            ORDER BY date
        ) AS prev_close,

        -- NR7 condition
        MIN((high - low)) OVER (
            PARTITION BY symbol
            ORDER BY date
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ) AS min_7day_range,

        ROW_NUMBER() OVER (
            PARTITION BY symbol
            ORDER BY date DESC
        ) AS rn

    FROM ohlcv
),

filtered AS (
    SELECT
        *,
        
        -- Absolute daily move %
        ABS(((close - prev_close) / prev_close) * 100) AS daily_move_pct

    FROM ranked
)

SELECT
    symbol,
    date,
    ROUND(close, 2) AS close,

    ROUND(range_pct, 2) AS range_pct

FROM filtered

WHERE rn = 1

-- NR7
AND (high - low) = min_7day_range

-- No candle > 2% move in last 6 sessions
AND symbol NOT IN (

    SELECT symbol
    FROM (
        SELECT
            symbol,
            date,
            ABS(((close - prev_close) / prev_close) * 100) AS move_pct,

            ROW_NUMBER() OVER (
                PARTITION BY symbol
                ORDER BY date DESC
            ) AS rnk

        FROM filtered
    )
    WHERE rnk <= 6
    AND move_pct > 2
)

ORDER BY range_pct ASC;
"""


def scan_nr7(conn):
    """Scan for NR7 (Narrow Range 7) patterns."""
    try:
        df = pd.read_sql_query(QUERY, conn)

        if df.empty:
            logger.info("No NR7 patterns found")
            return []

        logger.info(f"Found {len(df)} NR7 patterns")
        return df.to_dict("records")

    except Exception as e:
        logger.error(f"Error scanning NR7 patterns: {e}")
        raise

if __name__ == "__main__":
    scan_nr7()
