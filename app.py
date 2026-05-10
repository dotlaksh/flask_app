from flask import Flask, render_template, jsonify
import sqlite3
import logging
from functools import wraps

from powerplay import scan_powerplay
from darvas import scan_darvas
from vcp import scan_vcp
from nr7 import scan_nr7
from near_52w_high import scan_52w_high

app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DB_PATH = "nse_data.db"


def get_connection():
    """Get database connection with error handling."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        logger.error(f"Database connection error: {e}")
        raise


SCANNERS = {
    "powerplay": scan_powerplay,
    "darvas": scan_darvas,
    "vcp": scan_vcp,
    "nr7": scan_nr7,
    "52wh": scan_52w_high,
}


@app.route("/")
def home():
    """Home page with scanner selection."""
    return render_template(
        "index.html",
        results=[],
        active=""
    )


@app.route("/scan/<setup>")
def run_scan(setup):
    """Run selected scanner and display results."""
    scanner = SCANNERS.get(setup)

    if not scanner:
        logger.warning(f"Invalid scanner requested: {setup}")
        return render_template(
            "index.html",
            results=[],
            active="",
            error=f"Invalid scanner: {setup}"
        )

    conn = None
    results = []
    error = None

    try:
        conn = get_connection()
        results = scanner(conn)
        logger.info(f"Scan {setup} completed with {len(results)} results")

    except sqlite3.Error as e:
        logger.error(f"Database error during {setup} scan: {e}")
        error = f"Database error: {str(e)}"

    except Exception as e:
        logger.error(f"Error during {setup} scan: {e}")
        error = f"Scan error: {str(e)}"

    finally:
        if conn:
            conn.close()

    return render_template(
        "index.html",
        results=results,
        active=setup,
        error=error
    )


@app.route("/api/scan/<setup>")
def api_scan(setup):
    """API endpoint for AJAX scanning."""
    scanner = SCANNERS.get(setup)

    if not scanner:
        logger.warning(f"Invalid API scanner requested: {setup}")
        return jsonify({
            "success": False,
            "error": f"Invalid scanner: {setup}",
            "results": []
        }), 400

    conn = None
    results = []

    try:
        conn = get_connection()
        results = scanner(conn)
        logger.info(f"API scan {setup} completed with {len(results)} results")

        return jsonify({
            "success": True,
            "results": results,
            "count": len(results)
        })

    except sqlite3.Error as e:
        logger.error(f"Database error during API {setup} scan: {e}")
        return jsonify({
            "success": False,
            "error": f"Database error: {str(e)}",
            "results": []
        }), 500

    except Exception as e:
        logger.error(f"Error during API {setup} scan: {e}")
        return jsonify({
            "success": False,
            "error": f"Scan error: {str(e)}",
            "results": []
        }), 500

    finally:
        if conn:
            conn.close()


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return render_template(
        "index.html",
        results=[],
        active="",
        error="Page not found"
    ), 404


@app.route("/api/stock/<symbol>")
def get_stock_data(symbol):
    """API endpoint to fetch OHLCV data for a specific symbol."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        query = """
        SELECT date, open, high, low, close, volume
        FROM ohlcv
        WHERE symbol = ?
        ORDER BY date ASC
        LIMIT 365
        """
        
        cursor.execute(query, (symbol,))
        rows = cursor.fetchall()
        
        data = []
        for row in rows:
            # Convert date to YYYY-MM-DD format for TradingView
            date_str = row['date']
            if isinstance(date_str, str):
                # Already a string, ensure it's in YYYY-MM-DD format
                time_val = date_str
            else:
                # Convert to string
                time_val = str(date_str)
            
            data.append({
                'time': time_val,
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['close']),
                'volume': int(row['volume'])
            })
        
        logger.info(f"Fetched {len(data)} data points for symbol {symbol}")
        
        return jsonify({
            'success': True,
            'symbol': symbol,
            'data': data
        })
        
    except sqlite3.Error as e:
        logger.error(f"Database error fetching stock data for {symbol}: {e}")
        return jsonify({
            'success': False,
            'error': f"Database error: {str(e)}",
            'data': []
        }), 500
        
    except Exception as e:
        logger.error(f"Error fetching stock data for {symbol}: {e}")
        return jsonify({
            'success': False,
            'error': f"Error: {str(e)}",
            'data': []
        }), 500
        
    finally:
        if conn:
            conn.close()


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return render_template(
        "index.html",
        results=[],
        active="",
        error="Page not found"
    ), 404


@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors."""
    logger.error(f"Server error: {error}")
    return render_template(
        "index.html",
        results=[],
        active="",
        error="Internal server error"
    ), 500


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
