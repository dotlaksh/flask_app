# Stock Screener Web App

A full-fledged Flask web application for scanning and analyzing stock patterns in the NSE market. The app provides multiple technical analysis scanners to identify potential trading opportunities.

## Features

- **5 Technical Scanners:**
  - **PowerPlay**: Identifies stocks with recent impulse moves followed by consolidation
  - **Darvas Box**: Detects Darvas box patterns near 52-week highs
  - **VCP (Volatility Contraction Pattern)**: Finds stocks with shrinking volatility ranges
  - **NR7 (Narrow Range 7)**: Identifies narrow range candles indicating potential breakouts
  - **52W High**: Scans for stocks trading near their 52-week highs

- **Modern Web Interface:**
  - Clean, responsive UI with dark theme
  - Loading states for better UX
  - Error handling and user feedback
  - Results display with tabular data

- **API Endpoints:**
  - RESTful API for AJAX-based scanning
  - JSON response format for integration

- **Production-Ready Features:**
  - Comprehensive error handling
  - Logging configuration
  - Config management
  - Database connection pooling

## Prerequisites

- Python 3.8 or higher
- SQLite database (nse_data.db) with OHLCV data
- pip package manager

## Installation

1. **Clone or navigate to the project directory:**
   ```bash
   cd /home/laksh/Public/flask-app
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Database Setup

The application expects a SQLite database file named `nse_data.db` in the project root. The database should contain an `ohlcv` table with the following structure:

```sql
CREATE TABLE ohlcv (
    symbol TEXT,
    date DATE,
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    volume INTEGER
);
```

Ensure your database is populated with NSE stock data before running the application.

## Configuration

The application uses `config.py` for configuration. You can customize settings by setting environment variables:

- `SECRET_KEY`: Flask secret key (default: dev-secret-key-change-in-production)
- `DEBUG`: Enable debug mode (default: False)
- `DB_PATH`: Path to SQLite database (default: nse_data.db)
- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 5000)
- `LOG_LEVEL`: Logging level (default: INFO)
- `RESULTS_PER_PAGE`: Pagination results per page (default: 50)

Example:
```bash
export DEBUG=True
export PORT=8080
```

## Running the Application

### Development Mode

Run the Flask development server:
```bash
python app.py
```

The application will be available at `http://localhost:5000`

### Production Mode

For production deployment, use Gunicorn:
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## Usage

1. **Open the web interface:**
   Navigate to `http://localhost:5000` in your browser

2. **Select a scanner:**
   Click on any of the scanner buttons (PowerPlay, Darvas, VCP, NR7, 52W High)

3. **View results:**
   The scanner will run and display matching stocks in a table

4. **API Usage:**
   Use the REST API endpoint for programmatic access:
   ```bash
   curl http://localhost:5000/api/scan/powerplay
   ```

   Response format:
   ```json
   {
     "success": true,
     "results": [...],
     "count": 10
   }
   ```

## Project Structure

```
flask-app/
├── app.py                 # Main Flask application
├── config.py              # Configuration management
├── requirements.txt       # Python dependencies
├── darvas.py             # Darvas box scanner
├── powerplay.py          # PowerPlay scanner
├── vcp.py                # VCP scanner
├── nr7.py                # NR7 scanner
├── near_52w_high.py      # 52-week high scanner
├── static/
│   └── style.css         # Stylesheet
├── templates/
│   └── index.html        # Main HTML template
├── nse_data.db           # SQLite database
└── symbols.json          # Stock symbols reference
```

## Scanner Descriptions

### PowerPlay
Identifies stocks that have made a significant move (20%+) in the last 30 sessions and are now consolidating in a tight range, indicating potential continuation moves.

### Darvas Box
Detects stocks trading in a tight range (box) near their 52-week highs with multiple tests of resistance, suggesting potential breakouts.

### VCP (Volatility Contraction Pattern)
Finds stocks with progressively shrinking volatility ranges over 15, 10, and 5-day periods, indicating accumulation before a potential breakout.

### NR7 (Narrow Range 7)
Identifies candles with the narrowest range in the last 7 sessions, which often precede explosive moves.

### 52W High
Scans for stocks trading within 10% of their 52-week highs with tight consolidation, indicating strength and potential breakout setups.

## Error Handling

The application includes comprehensive error handling:
- Database connection errors are logged and displayed
- Invalid scanner requests return appropriate error messages
- 404 and 500 error handlers are configured
- All scanner errors are caught and logged

## Logging

Logs are written to console with the following format:
```
YYYY-MM-DD HH:MM:SS - app - LEVEL - Message
```

Log level can be configured via the `LOG_LEVEL` environment variable.

## Development

To add a new scanner:

1. Create a new Python module (e.g., `new_scanner.py`)
2. Implement a function that takes a database connection and returns a list of dictionaries
3. Add the scanner to the `SCANNERS` dictionary in `app.py`
4. Add a button to the HTML template in `templates/index.html`

## Troubleshooting

**Database not found:**
- Ensure `nse_data.db` exists in the project root
- Check the `DB_PATH` configuration

**No results:**
- Verify the database has recent data
- Check if the scanner criteria are too strict
- Review the logs for any errors

**Import errors:**
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check that all scanner modules are in the project directory

## License

This project is provided as-is for educational and trading analysis purposes.

## Disclaimer

This software is for educational purposes only. Stock market trading involves significant risk. Always do your own research and consult with a financial advisor before making trading decisions.
