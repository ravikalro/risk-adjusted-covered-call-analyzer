import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time

# Import our helper modules
from schwab_wrapper import SchwabAPI
from technicals import calculate_rsi, find_support_resistance

st.set_page_config(page_title="Risk-Adjusted Covered Call Analyzer", layout="wide")

# Custom CSS for aesthetics
st.markdown("""
<style>
    .main {
        background-color: #0e1117;
        color: #fafafa;
    }
    .metric-card {
        background-color: #262730;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 20px;
        border: 1px solid #41444b;
    }
    .best-pick-card {
        background: linear-gradient(135deg, #1f4037 0%, #99f2c8 100%);
        color: #000;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.5);
        margin-bottom: 25px;
    }
    .best-pick-title {
        font-size: 1.5rem;
        font-weight: bold;
        margin-bottom: 10px;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 50px;
        background-color: #ff4b4b;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

st.title("📈 Risk-Adjusted Covered Call Strategy Analyzer")
st.markdown("Identify the optimal covered call candidates using the **Efficiency Score** algorithm.")

# --- Sidebar: Auth ---
st.sidebar.header("🔑 API Configuration")
client_id = st.sidebar.text_input("Schwab Client ID (App Key)", type="password")
client_secret = st.sidebar.text_input("Schwab Client Secret", type="password")
auth_button = st.sidebar.button("Authenticate with Schwab")

if 'schwab_api' not in st.session_state:
    st.session_state.schwab_api = None
if 'is_authenticated' not in st.session_state:
    st.session_state.is_authenticated = False

if auth_button:
    if client_id and client_secret:
        api = SchwabAPI(client_id, client_secret)
        success, msg = api.authenticate()
        if success:
            st.session_state.schwab_api = api
            st.session_state.is_authenticated = True
            st.sidebar.success(msg)
        else:
            st.sidebar.error(msg)
    else:
        st.sidebar.warning("Please enter both Key and Secret.")

# --- Main Logic ---

st.markdown("### ⚙️ Strategy Configuration")
col1, col2, col3 = st.columns(3)
with col1:
    ticker = st.text_input("Ticker Symbol", value="AMZN").upper()
with col2:
    max_delta = st.number_input("Max Delta (Risk Tolerance)", min_value=0.1, max_value=0.5, value=0.31, step=0.01, 
                                help="Maximum delta for low-risk covered calls")
with col3:
    num_weeks = st.number_input("Number of Weeks", min_value=1, max_value=12, value=6, step=1,
                              help="Analyze options for the next N weekly expirations")

analyze_btn = st.button("Analyze Chain")

if analyze_btn:
    if not st.session_state.is_authenticated:
        st.error("Please authenticate first in the sidebar!")
    else:
        api = st.session_state.schwab_api
        with st.spinner(f"Fetching data for {ticker}..."):
            # 1. Fetch Quote (Spot Price & Fundamentals)
            quote_data, q_err = api.get_quote(ticker)
            if q_err:
                st.error(f"Failed to get quote: {q_err}")
                st.stop()
            
            # Extract basic data
            # Schwab quote structure varies. Usually { symbol: { quote: {...}, fundamental: {...} } }
            try:
                if ticker in quote_data:
                    base_data = quote_data[ticker]
                else:
                    # sometimes response is just the object?
                    base_data = list(quote_data.values())[0]
                
                spot_price = base_data.get('quote', {}).get('lastPrice') or base_data.get('quote', {}).get('closePrice')
                if not spot_price:
                    st.error("Could not find spot price in response.")
                    st.stop()
                    
                # Earnings Date
                # usually in fundamental: nextDivPayDate, or similar. Schwab might not give specific earnings date in basic quote.
                # checking docs... 'fundamental': { 'nextEarningsDate': ... }?
                # We'll try to get it safely.
                fund = base_data.get('fundamental', {})
                earnings_date = fund.get('nextEarningsDate', 'N/A')
                
            except Exception as e:
                st.error(f"Error parsing quote data: {e}")
                st.stop()

            # 2. Fetch Price History for Technicals
            hist_data, h_err = api.get_price_history(ticker)
            rsi_val = None
            support_val = None
            resistance_val = None
            
            if not h_err and 'candles' in hist_data:
                # Need to convert to DataFrame
                candles = hist_data['candles']
                df_hist = pd.DataFrame(candles)
                # Schwab candles: 'close', 'datetime', 'high', 'low', 'open', 'volume'
                df_hist['close'] = df_hist['close']
                
                # Calculate RSI
                if len(df_hist) > 14:
                    df_hist['rsi'] = calculate_rsi(df_hist['close'])
                    rsi_val = df_hist['rsi'].iloc[-1]
                
                # Calculate S/R
                support_val, resistance_val = find_support_resistance(df_hist, spot_price)
            else:
                st.warning("Could not fetch price history for technicals.")

            # 3. Fetch Option Chain
            chain_data, c_err = api.get_option_chain(ticker)
            if c_err:
                st.error(f"Failed to get option chain: {c_err}")
                st.stop()

            # --- Display Market Data Header ---
            st.markdown("### 📊 Market Snapshot")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Spot Price", f"${spot_price:.2f}")
            m2.metric("RSI (14)", f"{rsi_val:.2f}" if rsi_val else "N/A")
            # Smaller font for S/R to fit long numbers
            if support_val:
                st.markdown(f"""<div style='text-align: center;'>
                    <p style='color: #888; font-size: 0.8rem; margin-bottom: 0;'>Support / Resist</p>
                    <p style='font-size: 1rem; font-weight: 600; margin-top: 0;'>${support_val:.2f} / ${resistance_val:.2f}</p>
                </div>""", unsafe_allow_html=True)
            else:
                m3.metric("Support / Resist", "N/A")
            m4.metric("Next Earnings", f"{earnings_date}")

            # --- NEW ALGORITHM: Low-Maintenance Covered Call Strategy ---
            st.markdown("---")
            st.markdown("### 🎯 Low-Maintenance Covered Call Analysis")
            
            call_map = chain_data.get('callExpDateMap', {})
            if not call_map:
                st.error("No option chain data found.")
                st.stop()
            
            # Step 1: Select the next N weekly expirations chronologically
            sorted_keys = sorted(call_map.keys())
            target_expiries = sorted_keys[:num_weeks]
            
            if not target_expiries:
                st.warning(f"No expiries found.")
                st.stop()
            
            # Step 2: Collect options from selected expiries and apply filters
            all_candidates = []
            
            for exp_key in target_expiries:
                strikes_map = call_map.get(exp_key, {})
                parts = exp_key.split(':')
                exp_date_str = parts[0]
                dte = int(parts[1]) if len(parts) > 1 else 0
                
                # Handle DTE edge case
                calc_dte = dte if dte > 0 else 0.5
                
                for strike_str, options_list in strikes_map.items():
                    opt = options_list[0]
                    
                    try:
                        delta = float(opt.get('delta', 0) or 0)
                        gamma = float(opt.get('gamma', 0) or 0)
                        theta = float(opt.get('theta', 0) or 0)
                        bid = float(opt.get('bid', 0) or 0)
                        ask = float(opt.get('ask', 0) or 0)
                        strike = float(opt.get('strikePrice', 0))
                        iv = float(opt.get('volatility', 0) or 0)
                        
                        premium = (bid + ask) / 2
                        
                        # Filter 1: Delta <= Max_Delta (risk tolerance)
                        if delta <= 0 or delta > max_delta:
                            continue
                        
                        # Filter 2: Must be OTM
                        if strike <= spot_price:
                            continue
                        
                        # Calculate Metrics
                        # ARIF = (Premium × 365 × 100) / (Stock_Price × DTE)
                        arif = (premium * 365 * 100) / (spot_price * calc_dte)
                        
                        # Stability Score = Theta / Gamma
                        abs_theta = abs(theta)
                        if gamma > 0:
                            stability_score = abs_theta / gamma
                        else:
                            stability_score = 0
                        
                        # Store candidate
                        all_candidates.append({
                            'Expiration': exp_date_str,
                            'DTE': int(calc_dte),
                            'Strike': strike,
                            'Premium': premium,
                            'Delta': delta,
                            'Gamma': gamma,
                            'Theta': theta,
                            'IV': iv * 100,  # Convert to percentage
                            'ARIF': arif,
                            'Stability Score': stability_score,
                            'Bid': bid,
                            'Ask': ask,
                            'Volume': opt.get('totalVolume', 0),
                            'OI': opt.get('openInterest', 0)
                        })
                        
                    except (ValueError, TypeError):
                        continue
            
            if not all_candidates:
                st.warning(f"No options found meeting criteria (Delta ≤ {max_delta}) for the next {num_weeks} weeks.")
                st.stop()
            
            # Step 3: Group by Expiry Date and Select Max Premium per Date
            from collections import defaultdict
            expiry_groups = defaultdict(list)
            
            for candidate in all_candidates:
                expiry_groups[candidate['Expiration']].append(candidate)
            
            # Select the option with max premium from each expiry date
            premium_leaders = []
            for expiry, options in expiry_groups.items():
                # Sort by premium descending and take the first (highest premium)
                options.sort(key=lambda x: x['Premium'], reverse=True)
                premium_leaders.append(options[0])
            
            
            # Step 4: Sort by Stability Score (Descending), then by IV (Descending) as tie-breaker
            premium_leaders.sort(key=lambda x: (x['Stability Score'], x['IV']), reverse=True)
            
            # Step 5: Use All Premium Leaders (one per expiry date)
            all_results = premium_leaders
            
            # Store results in session state to persist across reruns (e.g., when downloading CSV)
            st.session_state.analysis_results = {
                'all_results': all_results,
                'ticker': ticker,
                'spot_price': spot_price,
                'call_map': call_map,
                'num_weeks': num_weeks,
                'max_delta': max_delta,
                'has_results': True
            }

# Display results from session state (persists across reruns)
if st.session_state.get('analysis_results', {}).get('has_results', False):
    results = st.session_state.analysis_results
    all_results = results['all_results']
    ticker = results['ticker']
    spot_price = results['spot_price']
    call_map = results['call_map']
    num_weeks = results['num_weeks']
    max_delta = results['max_delta']
    
    # Display Results
    if all_results:
        best_pick = all_results[0]
        
        # Calculate additional metrics for display
        strike_distance_pct = ((best_pick['Strike'] - spot_price) / spot_price) * 100
        premium_yield_pct = (best_pick['Premium'] / spot_price) * 100
        
        # Highlight Best Pick Card
        st.markdown(f"""
        <div class="best-pick-card">
            <div class="best-pick-title">🏆 Best Low-Maintenance Income Trade</div>
            <p style="font-size: 1.2rem;">
                <b>{ticker} {best_pick['Expiration']} ${best_pick['Strike']:.2f} Call</b><br>
                Strike Distance: <b>{strike_distance_pct:.2f}%</b> | 
                Premium Yield: <b>{premium_yield_pct:.2f}%</b><br>
                Stability Score: <b>{best_pick['Stability Score']:.4f}</b> | 
                ARIF: <b>{best_pick['ARIF']:.2f}%</b> | 
                Delta: <b>{best_pick['Delta']:.3f}</b>
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Find Second Best (from week #2 onwards)
        # Get the first expiration date (week #1)
        first_expiry = min([r['Expiration'] for r in all_results])
        
        # Filter out week #1 options
        week2_plus = [r for r in all_results if r['Expiration'] != first_expiry]
        
        if week2_plus:
            second_best = week2_plus[0]  # Already sorted by stability score
            
            # Calculate metrics for second best
            strike_distance_pct_2 = ((second_best['Strike'] - spot_price) / spot_price) * 100
            premium_yield_pct_2 = (second_best['Premium'] / spot_price) * 100
            
            # Display Second Best Pick Card with different styling
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%); color: #fff; padding: 20px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); margin-bottom: 25px;">
                <div style="font-size: 1.3rem; font-weight: bold; margin-bottom: 10px;">🥈 Second Best Low-Maintenance Income Trade (Week 2+)</div>
                <p style="font-size: 1.1rem;">
                    <b>{ticker} {second_best['Expiration']} ${second_best['Strike']:.2f} Call</b><br>
                    Strike Distance: <b>{strike_distance_pct_2:.2f}%</b> | 
                    Premium Yield: <b>{premium_yield_pct_2:.2f}%</b><br>
                    Stability Score: <b>{second_best['Stability Score']:.4f}</b> | 
                    ARIF: <b>{second_best['ARIF']:.2f}%</b> | 
                    Delta: <b>{second_best['Delta']:.3f}</b>
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        
        # Display All Candidates Table
        st.markdown("### 📊 All Candidates (Ranked by Stability Score)")
        df_all = pd.DataFrame(all_results)
        
        # Reorder columns for clarity
        display_cols = ['Expiration', 'DTE', 'Strike', 'Premium', 'Delta', 'Gamma', 
                       'Theta', 'IV', 'Stability Score', 'ARIF', 'Volume', 'OI']
        df_display = df_all[display_cols].copy()
        
        # Format for display
        df_display['Strike'] = df_display['Strike'].apply(lambda x: f"${x:.2f}")
        df_display['Premium'] = df_display['Premium'].apply(lambda x: f"${x:.2f}")
        df_display['Delta'] = df_display['Delta'].apply(lambda x: f"{x:.3f}")
        df_display['Gamma'] = df_display['Gamma'].apply(lambda x: f"{x:.4f}")
        df_display['Theta'] = df_display['Theta'].apply(lambda x: f"{x:.4f}")
        df_display['IV'] = df_display['IV'].apply(lambda x: f"{x:.1f}%")
        df_display['Stability Score'] = df_display['Stability Score'].apply(lambda x: f"{x:.4f}")
        df_display['ARIF'] = df_display['ARIF'].apply(lambda x: f"{x:.2f}%")
        
        st.dataframe(df_display, use_container_width=True)
    else:
        st.warning("No candidates found.")

    # --- CSV Export Section ---
    st.markdown("### 📥 Download Filtered Options")
    st.markdown(f"Export All Candidates: Next {num_weeks} Weeks | Delta ≤ {max_delta} | Sorted by Stability Score")
    
    # Use the same all_results from main analysis for CSV export
    if all_results:
        # Prepare data for CSV (already filtered and sorted)
        csv_data = []
        
        for candidate in all_results:
            row = {
                "Symbol": ticker,
                "Underlying Price": spot_price,
                "Expiry Date": candidate['Expiration'],
                "DTE": candidate['DTE'],
                "Strike Price": candidate['Strike'],
                "Bid": candidate['Bid'],
                "Ask": candidate['Ask'],
                "Premium (Mid)": candidate['Premium'],
                "Break Even": candidate['Strike'] + candidate['Premium'],
                "ARIF": candidate['ARIF'],
                "Stability Score": candidate['Stability Score'],
                "Volume": candidate['Volume'],
                "Open Interest": candidate['OI'],
                "IV": candidate['IV'] / 100,  # Convert back to decimal
                "Delta": candidate['Delta'],
                "Gamma": candidate['Gamma'],
                "Theta": candidate['Theta'],
                "Vega": candidate.get('Vega', 0),  # These might not exist in dict
                "Rho": candidate.get('Rho', 0),
                "Intrinsic Value": 0  # OTM calls have no intrinsic value
            }
            csv_data.append(row)
                
        if csv_data:
            df_csv = pd.DataFrame(csv_data)
            csv_string = df_csv.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download All Candidates CSV",
                data=csv_string,
                file_name=f"{ticker}_Covered_Calls_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.info("No data to export.")
    else:
        st.warning(f"No options found for export.")

