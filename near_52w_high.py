# near_52w_high.py

import pandas as pd
import logging

logger = logging.getLogger(__name__)

QUERY = """
WITH base_data AS (
    SELECT
        symbol,
        date,
        open,
        high,
        low,
        close,

        -- 52 week high
        MAX(high) OVER (
            PARTITION BY symbol
        ) AS high_52w,

        -- Rolling 20-day high/low
        MAX(high) OVER (
            PARTITION BY symbol
            ORDER BY date
            ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) AS base_high,

        MIN(low) OVER (
            PARTITION BY symbol
            ORDER BY date
            ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) AS base_low,

        -- Recent impulse move check
        MAX(high) OVER (
            PARTITION BY symbol
            ORDER BY date
            ROWS BETWEEN 15 PRECEDING AND CURRENT ROW
        ) AS recent_high,

        MIN(low) OVER (
            PARTITION BY symbol
            ORDER BY date
            ROWS BETWEEN 15 PRECEDING AND CURRENT ROW
        ) AS recent_low,

        ROW_NUMBER() OVER (
            PARTITION BY symbol
            ORDER BY date DESC
        ) AS rn

    FROM ohlcv

    WHERE date >= DATE('now', '-365 days')
)

SELECT
    symbol,
    date,

    ROUND(close, 2) AS close,
    ROUND(high_52w, 2) AS high_52w,

    ROUND(
        ((high_52w - close) / high_52w) * 100,
        2
    ) AS away_from_high_pct,

    ROUND(
        ((base_high - base_low) / base_low) * 100,
        2
    ) AS base_range_pct

FROM base_data

WHERE rn = 1

-- Within 10% of 52W high
AND close >= high_52w * 0.90

-- LONG BASE:
-- 20-day range should be relatively tight
AND ((base_high - base_low) / base_low) <= 0.2


ORDER BY away_from_high_pct ASC,
         base_range_pct ASC;
"""


def scan_52w_high(conn):
    """Scan for stocks near 52-week high."""
    try:
        df = pd.read_sql_query(QUERY, conn)

        if df.empty:
            logger.info("No stocks near 52-week high found")
            return []

        logger.info(f"Found {len(df)} stocks near 52-week high")
        return df.to_dict("records")

    except Exception as e:
        logger.error(f"Error scanning near 52-week high: {e}")
        raise
