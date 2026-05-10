import sqlite3
import pandas as pd
import logging

logger = logging.getLogger(__name__)

DB_PATH = "nse_data.db"

# ---------------------------------------------------------
# VCP (Volatility Contraction Pattern) SCANNER
# ---------------------------------------------------------
#
# Core Idea:
#
# 1. Strong stock near 52W high
# 2. Multiple volatility contractions
# 3. Price range shrinking over time
# 4. Tight recent structure
# 5. Volume drying up (optional)
#
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
        volume,

        ROW_NUMBER() OVER (
            PARTITION BY symbol
            ORDER BY date DESC
        ) AS rn

    FROM ohlcv
),

-- ---------------------------------------------------------
-- 52 WEEK HIGH
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
        ((h.high_52w - l.current_price) * 100.0 / h.high_52w) <= 20
),

-- ---------------------------------------------------------
-- VOLATILITY WINDOWS
-- ---------------------------------------------------------

range_15 AS (
    SELECT
        symbol,

        MAX(high) AS high_15,
        MIN(low)  AS low_15,
        AVG(close) AS avg_15

    FROM ranked
    WHERE rn <= 15
    GROUP BY symbol
),

range_10 AS (
    SELECT
        symbol,

        MAX(high) AS high_10,
        MIN(low)  AS low_10,
        AVG(close) AS avg_10

    FROM ranked
    WHERE rn <= 10
    GROUP BY symbol
),

range_5 AS (
    SELECT
        symbol,

        MAX(high) AS high_5,
        MIN(low)  AS low_5,
        AVG(close) AS avg_5

    FROM ranked
    WHERE rn <= 5
    GROUP BY symbol
),

-- ---------------------------------------------------------
-- VOLUME CONTRACTION
-- ---------------------------------------------------------

volumes AS (
    SELECT
        symbol,

        AVG(
            CASE
                WHEN rn BETWEEN 1 AND 5
                THEN volume
            END
        ) AS recent_volume,

        AVG(
            CASE
                WHEN rn BETWEEN 6 AND 20
                THEN volume
            END
        ) AS old_volume

    FROM ranked
    WHERE rn <= 20
    GROUP BY symbol
),

-- ---------------------------------------------------------
-- FINAL VCP FILTER
-- ---------------------------------------------------------

final AS (
    SELECT
        n.symbol,

        n.current_price,
        n.high_52w,
        n.away_from_high_pct,

        ROUND(
            ((r15.high_15 - r15.low_15) * 100.0 / r15.avg_15),
            2
        ) AS range_15_pct,

        ROUND(
            ((r10.high_10 - r10.low_10) * 100.0 / r10.avg_10),
            2
        ) AS range_10_pct,

        ROUND(
            ((r5.high_5 - r5.low_5) * 100.0 / r5.avg_5),
            2
        ) AS range_5_pct,

        ROUND(
            (v.recent_volume * 100.0 / v.old_volume),
            2
        ) AS volume_ratio_pct

    FROM near_high n

    JOIN range_15 r15
        ON n.symbol = r15.symbol

    JOIN range_10 r10
        ON n.symbol = r10.symbol

    JOIN range_5 r5
        ON n.symbol = r5.symbol

    JOIN volumes v
        ON n.symbol = v.symbol

    WHERE

        -- Volatility contraction
        ((r15.high_15 - r15.low_15) * 100.0 / r15.avg_15)
            >
        ((r10.high_10 - r10.low_10) * 100.0 / r10.avg_10)

        AND

        ((r10.high_10 - r10.low_10) * 100.0 / r10.avg_10)
            >
        ((r5.high_5 - r5.low_5) * 100.0 / r5.avg_5)

        -- Tight recent structure
        AND ((r5.high_5 - r5.low_5) * 100.0 / r5.avg_5) <= 5

        -- Volume drying up
        AND v.recent_volume < v.old_volume
)

SELECT *
FROM final

ORDER BY
    range_5_pct ASC,
    away_from_high_pct ASC;
"""


def scan_vcp(conn):
    """Scan for VCP (Volatility Contraction Pattern) patterns."""
    try:
        df = pd.read_sql_query(QUERY, conn)

        if df.empty:
            logger.info("No VCP patterns found")
            return []

        logger.info(f"Found {len(df)} VCP patterns")
        return df.to_dict(orient="records")

    except Exception as e:
        logger.error(f"Error scanning VCP patterns: {e}")
        raise


if __name__ == "__main__":
    scan_vcp()
