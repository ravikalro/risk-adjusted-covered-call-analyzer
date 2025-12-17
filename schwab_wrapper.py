import requests
import base64
import json
import pandas as pd
from datetime import datetime, timedelta

class SchwabAPI:
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = "https://api.schwabapi.com/marketdata/v1"
        self.token_url = "https://api.schwabapi.com/v1/oauth/token"
        self.access_token = None

    def authenticate(self):
        """
        Authenticates using Client Credentials flow or similar.
        Note: Schwab often requires a refresh token for full access, 
        but we'll try client_credentials as implied by 'Client ID and Secret'.
        """
        headers = {
            'Authorization': f'Basic {base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        data = {'grant_type': 'client_credentials'}
        
        # If the user provides a refresh token flow in reality, we might need to adjust.
        # For now, sticking to the simplest interpretation of "Client ID + Secret".
        
        response = requests.post(self.token_url, headers=headers, data=data)
        if response.status_code == 200:
            self.access_token = response.json().get('access_token')
            return True, "Authenticated successfully"
        else:
            return False, f"Auth Failed: {response.text}"

    def get_option_chain(self, symbol):
        """
        Fetches option chain for the symbol.
        Filters will be applied in the application logic, but we can pre-filter here if API allows.
        We strictly need data for the next 5 weeks.
        """
        if not self.access_token:
            return None, "Not authenticated"

        endpoint = f"{self.base_url}/chains"
        
        # Strategy: CALL
        # Range: ALL (we need to filter by delta 0.3 later, so we need OTM/ITM boundary)
        # However, Delta 0.30 for a Call is OTM (At the money is ~0.50). 
        # So 'OTM' range might be efficient.
        # But to be safe, we'll fetch 'ALL' or 'OTM'. 
        
        params = {
            'symbol': symbol,
            'contractType': 'CALL',
            'includeUnderlyingQuote': 'TRUE',
            'range': 'OTM',  # 0.30 delta is OTM for calls
             # We might need to handle dates. API allows fromDate/toDate.
             # We'll fetch all and filter in Python to ensure we get exactly 5 weeks.
        }
        
        headers = {'Authorization': f'Bearer {self.access_token}'}
        
        response = requests.get(endpoint, headers=headers, params=params)
        if response.status_code == 200:
            return response.json(), None
        else:
            return None, f"Error fetching chains: {response.text}"

    def get_price_history(self, symbol):
        """
        Fetches price history for Technical Analysis (RSI, Support/Resistance).
        We'll fetch Daily data for the last 6 months.
        """
        if not self.access_token:
            return None, "Not authenticated"
            
        endpoint = f"{self.base_url}/pricehistory"
        
        # Yahoo-style params often used, but Schwab has specific ones.
        # periodType=month, period=6, frequencyType=daily, frequency=1
        params = {
            'symbol': symbol,
            'periodType': 'month',
            'period': 6,
            'frequencyType': 'daily',
            'frequency': 1
        }
        
        headers = {'Authorization': f'Bearer {self.access_token}'}
        
        response = requests.get(endpoint, headers=headers, params=params)
        if response.status_code == 200:
            return response.json(), None
        else:
            return None, f"Error fetching history: {response.text}"

    def get_quote(self, symbol):
        """
        Get real-time quote for the underlying.
        """
        if not self.access_token:
            return None, "Not authenticated"
            
        endpoint = f"{self.base_url}/{symbol}/quotes"
        headers = {'Authorization': f'Bearer {self.access_token}'}
        
        response = requests.get(endpoint, headers=headers)
        if response.status_code == 200:
            return response.json(), None
        else:
            return None, f"Error fetching quote: {response.text}"
