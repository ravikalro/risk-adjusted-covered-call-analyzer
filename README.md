# Risk-Adjusted Covered Call Strategy Analyzer

## Setup
1. Ensure you have the required dependencies installed:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the application:
   ```bash
   streamlit run app.py
   ```

## Usage
1. Enter your **Schwab Client ID** and **Client Secret** in the sidebar.
2. Click **Authenticate**.
3. Enter a Ticker Symbol (e.g., AMZN) in the main area.
4. Click **Analyze Chain**.

## Notes
- This app uses the Schwab Market Data API.
- It fetches the next 5 weekly option chains.
- It calculates the **Efficiency Score** to recommend the best risk-adjusted covered call.
- Calculations for RSI and Support/Resistance are based on 6-month daily price history.
- **CSV Export**: You can download the full OTM Call option chain (Strike > Spot) with all Greeks and IV for further analysis.
