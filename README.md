# AI-Trader
Stock market momentum trading AI using Alpaca, Google Sheets, and GitHub Actions

## Overview

This automated trading assistant uses momentum-based strategies to analyze stocks, generate trade suggestions, and execute approved trades. It integrates with:

- **Alpaca Markets** - For market data and trade execution
- **Google Sheets** - For configuration, trade approvals, and state tracking
- **GitHub Actions** - For automated scheduled execution

## Features

- **Momentum Analysis**: Calculates 3-month and 6-month momentum for ranking tickers
- **ATR-based Risk Management**: Uses Average True Range for stop-loss calculations
- **Automated Suggestions**: Proposes BUY/SELL trades with 50% portfolio allocation
- **Manual Approval**: Execute only approved trades from Google Sheets
- **Peak Tracking**: Monitors position peaks and implements trailing stops
- **Scheduled Execution**: Runs automatically via GitHub Actions

## Architecture

```
AI-Trader/
├── main.py                 # Main entry point
├── modules/
│   ├── sheets.py          # Google Sheets integration
│   ├── alpaca_client.py   # Alpaca API client
│   ├── momentum.py        # Momentum calculations
│   ├── risk.py            # ATR and stop-loss logic
│   ├── ranking.py         # Ticker ranking
│   ├── executor.py        # Trade execution
│   └── state.py           # Position state management
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
└── .github/workflows/
    └── trader.yml        # GitHub Actions workflow

```

## Google Sheets Setup

Create a Google Sheet with the following tabs:

### 1. Universe Tab
List of ticker symbols to analyze (one per row):

| Ticker |
|--------|
| AAPL   |
| MSFT   |
| GOOGL  |
| AMZN   |
| ...    |

### 2. TradeSuggestions Tab
Auto-populated with trade suggestions. To approve a trade, change "Approved" from "NO" to "YES":

| Ticker | Action | Quantity | Price | Reason | Approved | Timestamp |
|--------|--------|----------|-------|--------|----------|-----------|
| AAPL   | BUY    | 10       | 150.0 | Rank #1| YES      | 2024-... |

### 3. State Tab
Auto-populated with position tracking data:

| Ticker | Position | EntryPrice | Peak | ATRStop | LastUpdated |
|--------|----------|------------|------|---------|-------------|
| AAPL   | 10       | 150.0      | 155.0| 145.0   | 2024-...    |

## Setup Instructions

### 1. Alpaca Account Setup

1. Sign up for an Alpaca account at [alpaca.markets](https://alpaca.markets)
2. Generate API keys (use paper trading for testing)
3. Note your API Key and Secret Key

### 2. Google Cloud Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project
3. Enable Google Sheets API
4. Create a Service Account:
   - Go to "IAM & Admin" → "Service Accounts"
   - Create a new service account
   - Generate a JSON key file
5. Share your Google Sheet with the service account email

### 3. Local Installation

```bash
# Clone the repository
git clone https://github.com/ProLoser/AI-Trader.git
cd AI-Trader

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials

# Place Google service account JSON as credentials.json
cp /path/to/your-service-account.json credentials.json

# Run the trader
python main.py
```

### 4. GitHub Actions Setup

Configure the following secrets in your GitHub repository (Settings → Secrets and variables → Actions):

- `ALPACA_API_KEY` - Your Alpaca API key
- `ALPACA_SECRET_KEY` - Your Alpaca secret key
- `ALPACA_BASE_URL` - Alpaca API URL (paper or live)
- `GOOGLE_SHEET_ID` - Your Google Sheet ID (from the URL)
- `GOOGLE_CREDENTIALS_JSON` - Contents of your service account JSON file
- `PORTFOLIO_ALLOCATION` - Portfolio allocation per trade (e.g., 0.5 for 50%)

The workflow runs automatically on weekdays at 9:00 AM EST. You can also trigger it manually from the Actions tab.

## Configuration

### Environment Variables

- `ALPACA_API_KEY` - Alpaca API key
- `ALPACA_SECRET_KEY` - Alpaca secret key
- `ALPACA_BASE_URL` - API endpoint (paper: `https://paper-api.alpaca.markets`)
- `GOOGLE_SHEET_ID` - Google Sheet ID from the URL
- `PORTFOLIO_ALLOCATION` - Percentage of portfolio per trade (default: 0.5)

### Trading Parameters

Modify in the code as needed:
- **Momentum periods**: 3 months and 6 months (in `modules/momentum.py`)
- **ATR period**: 14 days (in `modules/risk.py`)
- **ATR multiplier**: 2.0x for stops (in `modules/risk.py`)
- **Max positions**: 10 (in `modules/ranking.py`)
- **Rank threshold**: 20 (in `modules/ranking.py`)

## Workflow

1. **Read Universe**: Fetches ticker list from Google Sheets
2. **Calculate Momentum**: Computes 3-month and 6-month momentum
3. **Rank Tickers**: Sorts by combined momentum score
4. **Generate Suggestions**: 
   - BUY top-ranked tickers not in portfolio
   - SELL poorly-ranked or stopped-out positions
5. **Write to Sheets**: Updates TradeSuggestions tab
6. **Execute Trades**: Processes approved suggestions
7. **Update State**: Tracks positions, peaks, and stops

## Safety Features

- **Paper Trading**: Test with Alpaca paper account
- **Manual Approval**: Trades require "YES" in Approved column
- **Stop Losses**: ATR-based trailing stops
- **Position Limits**: Maximum 10 positions
- **Allocation Control**: 50% allocation per suggestion

## Monitoring

Check the following:
- **GitHub Actions logs**: View execution history and errors
- **Google Sheets**: Review suggestions and state
- **Alpaca Dashboard**: Monitor account and positions

## Troubleshooting

### No data for tickers
- Verify ticker symbols are valid
- Check Alpaca API access
- Ensure market is open (for real-time data)

### Google Sheets errors
- Verify service account has edit access
- Check Sheet ID is correct
- Ensure credentials.json is valid

### Trade execution failures
- Check Alpaca account status
- Verify sufficient buying power
- Review order logs in Alpaca dashboard

## License

MIT License - See LICENSE file for details

## Disclaimer

This software is for educational purposes only. Use at your own risk. Past performance does not guarantee future results. Always test with paper trading before using real money.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.
