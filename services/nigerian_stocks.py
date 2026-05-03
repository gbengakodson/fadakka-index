import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
import json
import os
warnings.filterwarnings('ignore')


class NigerianStockData:
    """Nigerian stock data via iTick API - production ready"""
    
    # iTick API configuration
    BASE_URL = "https://api0.itick.org"
    
    # Nigerian stocks on NGX
    STOCKS = {
        'DANGCEM': 'Dangote Cement',
        'MTNN': 'MTN Nigeria',
        'AIRTELAFRI': 'Airtel Africa',
        'BUAFOODS': 'BUA Foods',
        'SEPLAT': 'Seplat Energy',
        'ZENITHBANK': 'Zenith Bank',
        'GTCO': 'Guaranty Trust Holding',
        'STANBIC': 'Stanbic IBTC',
        'UBA': 'United Bank for Africa',
        'ACCESSCORP': 'Access Holdings',
        'FBNH': 'FBN Holdings',
        'FIDELITYBK': 'Fidelity Bank',
        'WAPCO': 'Lafarge Africa',
        'DANGSUGAR': 'Dangote Sugar',
        'NB': 'Nigerian Breweries',
        'GUINNESS': 'Guinness Nigeria',
        'NESTLE': 'Nestle Nigeria',
        'FLOURMILL': 'Flour Mills Nigeria',
        'OKOMUOIL': 'Okomu Oil Palm',
        'PRESCO': 'Presco Plc',
        'TRANSCORP': 'Transcorp Nigeria',
        'CONOIL': 'Conoil Plc',
        'OANDO': 'Oando Plc',
        'TOTAL': 'Total Nigeria',
        'GEREGU': 'Geregu Power',
        'TRANSCOHOT': 'Transcorp Hotels',
        'HONYFLOUR': 'Honeywell Flour Mills',
        'NAHCO': 'Nigerian Aviation Handling',
        'CADBURY': 'Cadbury Nigeria',
        'UNILEVER': 'Unilever Nigeria'
    }
    
    def __init__(self, api_token=None):
        self.api_token = api_token or os.environ.get('ITICK_TOKEN', '')
        self.headers = {
            "accept": "application/json",
            "token": self.api_token
        }
    
    def get_real_time_quote(self, symbol):
        """Get real-time stock quote from iTick API"""
        if not self.api_token:
            return None
            
        try:
            url = f"{self.BASE_URL}/stock/quote"
            params = {
                "region": "ng",
                "code": symbol.upper()
            }
            
            response = requests.get(url, params=params, headers=self.headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 0 and data.get('data'):
                    quote = data['data']
                    return {
                        'symbol': quote.get('s', symbol),
                        'price': float(quote.get('ld', 0)),
                        'open': float(quote.get('o', 0)),
                        'high': float(quote.get('h', 0)),
                        'low': float(quote.get('l', 0)),
                        'previous_close': float(quote.get('p', 0)),
                        'change': float(quote.get('ch', 0)),
                        'change_percent': float(quote.get('chp', 0)),
                        'volume': int(quote.get('v', 0)),
                        'turnover': float(quote.get('tu', 0)),
                        'timestamp': quote.get('t', 0),
                        'source': 'iTick API'
                    }
        except Exception as e:
            print(f"iTick quote error for {symbol}: {e}")
        
        return None
    
    def get_historical_kline(self, symbol, ktype=9, limit=156):
        """Get historical K-line data from iTick API
        
        ktype: 8=daily, 9=weekly, 10=monthly
        limit: number of bars (156 weeks = ~3 years)
        """
        if not self.api_token:
            return None
            
        try:
            url = f"{self.BASE_URL}/stock/kline"
            params = {
                "region": "ng",
                "code": symbol.upper(),
                "kType": ktype,
                "limit": limit,
                "et": int(datetime.now().timestamp() * 1000)
            }
            
            response = requests.get(url, params=params, headers=self.headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 0 and data.get('data'):
                    klines = data['data']
                    
                    # Convert to pandas DataFrame
                    df_data = []
                    for bar in klines:
                        df_data.append({
                            'Open': float(bar.get('o', 0)),
                            'High': float(bar.get('h', 0)),
                            'Low': float(bar.get('l', 0)),
                            'Close': float(bar.get('c', 0)),
                            'Volume': int(bar.get('v', 0)),
                            'Turnover': float(bar.get('tu', 0))
                        })
                    
                    # Create DataFrame with timestamps as index
                    dates = pd.to_datetime([bar.get('t', 0) for bar in klines], unit='ms')
                    df = pd.DataFrame(df_data, index=dates)
                    return df
                    
        except Exception as e:
            print(f"iTick kline error for {symbol}: {e}")
        
        return None
    
    def get_stock_symbol_list(self):
        """Get list of all available Nigerian stocks from iTick"""
        if not self.api_token:
            return None
            
        try:
            url = f"{self.BASE_URL}/symbol/list"
            params = {
                "type": "stock",
                "region": "NG"
            }
            
            response = requests.get(url, params=params, headers=self.headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 0:
                    return data.get('data', [])
        except:
            pass
        
        return None
    
    def get_historical_data(self, symbol):
        """Main method - get historical data for Nigerian stock"""
        
        # Try iTick API first if token is available
        if self.api_token:
            df = self.get_historical_kline(symbol, ktype=9, limit=156)
            if df is not None and not df.empty and len(df) >= 50:
                return df
        
        # Fallback: Try Google Finance
        df = self.try_google_finance(symbol)
        if df is not None and not df.empty:
            return df
        
        # Last resort: Estimated data with clear marking
        return self.get_estimated_data(symbol)
    
    def try_google_finance(self, symbol):
        """Try to get data from Google Finance"""
        try:
            import yfinance as yf
            
            # Try various Yahoo Finance suffixes
            for suffix in ['.LGS', '.NSA']:
                try:
                    ticker = yf.Ticker(f"{symbol}{suffix}")
                    df = ticker.history(period='2y')
                    if not df.empty and len(df) >= 30:
                        return df
                except:
                    continue
        except:
            pass
        
        return None
    
    def get_estimated_data(self, symbol):
        """Generate estimated data based on known price ranges"""
        # Current approximate prices for Nigerian stocks (NGN)
        known_prices = {
            'DANGCEM': 650.0, 'MTNN': 280.0, 'AIRTELAFRI': 1800.0,
            'BUAFOODS': 380.0, 'SEPLAT': 2500.0, 'ZENITHBANK': 45.0,
            'GTCO': 55.0, 'STANBIC': 75.0, 'UBA': 28.0,
            'ACCESSCORP': 30.0, 'FBNH': 25.0, 'FIDELITYBK': 12.0,
            'WAPCO': 40.0, 'DANGSUGAR': 80.0, 'NB': 55.0,
            'GUINNESS': 85.0, 'NESTLE': 1400.0, 'FLOURMILL': 45.0,
            'OKOMUOIL': 280.0, 'PRESCO': 230.0, 'TRANSCORP': 15.0,
            'CONOIL': 120.0, 'OANDO': 10.0, 'TOTAL': 350.0,
            'GEREGU': 450.0, 'TRANSCOHOT': 25.0, 'HONYFLOUR': 10.0,
            'NAHCO': 18.0, 'CADBURY': 16.0, 'UNILEVER': 20.0
        }
        
        current_price = known_prices.get(symbol, 50.0)
        print(f"⚠️  {symbol}: Using estimated data (₦{current_price:,.2f}). Get free API key at itick.org for live data.")
        
        np.random.seed(hash(symbol) % 100000)
        
        weeks = 155  # Match date_range output
        dates = pd.date_range(end=datetime.now(), periods=weeks, freq='W')
        weeks = len(dates)  # Use actual length
        
        # Nigerian market average ~15-20% annual return, higher volatility
        annual_return = 0.15
        weekly_return = annual_return / 52
        volatility = 0.05
        
        returns = np.random.normal(weekly_return, volatility, weeks)
        prices = current_price * np.exp(-np.cumsum(returns[::-1]))[::-1]
        
        data = []
        for price in prices:
            daily_vol = price * 0.03
            data.append({
                'Open': price + np.random.normal(0, daily_vol),
                'High': price + abs(np.random.normal(0, daily_vol)),
                'Low': price - abs(np.random.normal(0, daily_vol)),
                'Close': price,
                'Volume': np.random.randint(50000, 5000000)
            })
        
        return pd.DataFrame(data, index=dates)
    
    def get_stock_info(self, symbol):
        """Get stock information with data source"""
        if self.api_token:
            source = "Live (iTick API)"
        else:
            source = "Estimated (Add iTick API key for live data)"
        
        return {
            'symbol': symbol,
            'name': self.STOCKS.get(symbol, symbol),
            'exchange': 'Nigerian Exchange (NGX)',
            'currency': 'NGN',
            'data_source': source
        }


# Test
if __name__ == '__main__':
    print("Testing iTick-powered Nigerian stock data...")
    print("=" * 50)
    
    # Test without API key (estimated data)
    ns = NigerianStockData()
    
    for symbol in ['DANGCEM', 'ZENITHBANK', 'GTCO']:
        print(f"\n{symbol}:")
        quote = ns.get_real_time_quote(symbol)
        if quote:
            print(f"  ✅ Live: ₦{quote['price']:,.2f}")
        else:
            print(f"  ⚠️  No API key - using estimated data")
            
        df = ns.get_historical_data(symbol)
        if df is not None and not df.empty:
            print(f"  Data points: {len(df)}")
            print(f"  Latest: ₦{df['Close'].iloc[-1]:,.2f}")
    
    print("\n" + "=" * 50)
    print("📌 Get your FREE API key at: https://itick.org")
    print("   Then set: set ITICK_TOKEN=your_key_here")
    print("   Or pass: NigerianStockData(api_token='your_key')")