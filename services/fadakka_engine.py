import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
import json
import os
from services.nigerian_stocks import NigerianStockData
warnings.filterwarnings('ignore')


class FadakkaEngine:
    """Core engine that calculates Fadakka Index for all assets"""
    
    def __init__(self):
        # 30 US Stocks
        self.stocks = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'JPM', 'V', 'JNJ',
            'WMT', 'PG', 'MA', 'UNH', 'HD', 'BAC', 'DIS', 'ADBE', 'NFLX', 'CRM',
            'XOM', 'CVX', 'KO', 'PEP', 'TMO', 'ABT', 'NKE', 'ORCL', 'CSCO', 'INTC'
        ]
        
        # 30 Nigerian Stocks
        self.nigerian_stocks = [
            'DANGCEM', 'MTNN', 'AIRTELAFRI', 'BUAFOODS', 'SEPLAT',
            'ZENITHBANK', 'GTCO', 'STANBIC', 'UBA', 'ACCESSCORP',
            'FBNH', 'FIDELITYBK', 'WAPCO', 'DANGSUGAR', 'NB',
            'GUINNESS', 'NESTLE', 'FLOURMILL', 'OKOMUOIL', 'PRESCO',
            'TRANSCORP', 'CONOIL', 'OANDO', 'TOTAL', 'GEREGU',
            'TRANSCOHOT', 'HONYFLOUR', 'NAHCO', 'CADBURY', 'UNILEVER'
        ]
        
        # 30 Currency Pairs
        self.currencies = [
            'EURUSD=X', 'GBPUSD=X', 'USDJPY=X', 'USDCHF=X', 'AUDUSD=X', 'USDCAD=X', 'NZDUSD=X',
            'EURGBP=X', 'EURJPY=X', 'EURCHF=X', 'GBPJPY=X', 'GBPCHF=X', 'AUDJPY=X',
            'AUDNZD=X', 'CADJPY=X', 'CHFJPY=X', 'NZDJPY=X', 'EURCAD=X', 'EURAUD=X',
            'GBPAUD=X', 'GBPCAD=X', 'EURNZD=X', 'AUDCAD=X', 'NZDCAD=X', 'EURSEK=X',
            'USDSEK=X', 'USDNOK=X', 'USDDKK=X', 'USDSGD=X', 'USDHKD=X'
        ]
        
        # 30 Cryptocurrencies
        self.cryptos = [
            'BTC-USD', 'ETH-USD', 'BNB-USD', 'XRP-USD', 'ADA-USD', 'SOL-USD', 'DOGE-USD',
            'DOT-USD', 'MATIC-USD', 'SHIB-USD', 'TRX-USD', 'AVAX-USD', 'UNI-USD',
            'ATOM-USD', 'LINK-USD', 'ETC-USD', 'XLM-USD', 'BCH-USD', 'ALGO-USD', 'VET-USD',
            'ICP-USD', 'FIL-USD', 'SAND-USD', 'AXS-USD', 'THETA-USD', 'FTM-USD', 'MANA-USD',
            'GRT-USD', 'EGLD-USD', 'AAVE-USD'
        ]
        
        # Commodities
        self.commodities = {
            'Oil': 'CL=F',
            'Gas': 'NG=F',
            'Gold': 'GC=F'
        }
        
        # Interest rates for major currencies (approximate central bank rates)
        self.interest_rates = {
            'USD': 5.50, 'EUR': 4.50, 'GBP': 5.25, 'JPY': 0.25,
            'CHF': 1.75, 'AUD': 4.35, 'NZD': 5.50, 'CAD': 5.00,
            'SEK': 4.00, 'NOK': 4.50, 'DKK': 3.75, 'SGD': 3.50,
            'HKD': 5.75
        }
    
    def get_interest_rate_diff(self, symbol):
        """Calculate interest rate differential for currency pair"""
        try:
            # Parse currency pair (e.g., 'EURUSD=X' -> 'EUR', 'USD')
            base = symbol[:3]
            quote = symbol[3:6]
            
            base_rate = self.interest_rates.get(base, None)
            quote_rate = self.interest_rates.get(quote, None)
            
            if base_rate and quote_rate:
                diff = base_rate - quote_rate
                carry_trade = "LONG" if diff > 0 else "SHORT"
                return {
                    'base_rate': base_rate,
                    'quote_rate': quote_rate,
                    'rate_diff': round(diff, 2),
                    'carry_direction': carry_trade,
                    'annual_carry_return': round(abs(diff), 2)
                }
        except:
            pass
        return None
    
    def get_dividend_info(self, symbol):
        """Get dividend information for a stock"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            dividend_yield = info.get('dividendYield', None)
            dividend_rate = info.get('dividendRate', None)
            payout_ratio = info.get('payoutRatio', None)
            ex_dividend_date = info.get('exDividendDate', None)
            five_year_avg_dividend_yield = info.get('fiveYearAvgDividendYield', None)
            
            # Convert dates
            if ex_dividend_date:
                from datetime import datetime as dt
                ex_dividend_date = dt.fromtimestamp(ex_dividend_date).strftime('%Y-%m-%d')
            
            # Get dividend history
            dividends = ticker.dividends
            annual_dividend = 0
            if len(dividends) > 0:
                # Sum last 4 quarters or all if less
                recent_divs = dividends.tail(4)
                annual_dividend = recent_divs.sum()
            
            dividend_yield_pct = None
            if dividend_yield:
                dividend_yield_pct = round(dividend_yield * 100, 2)
            elif annual_dividend > 0:
                current_price = info.get('currentPrice', info.get('regularMarketPrice', None))
                if current_price:
                    dividend_yield_pct = round((annual_dividend / current_price) * 100, 2)
            
            if dividend_yield_pct or annual_dividend > 0:
                return {
                    'dividend_yield': dividend_yield_pct,
                    'annual_dividend': round(float(annual_dividend), 4),
                    'payout_ratio': round(payout_ratio * 100, 2) if payout_ratio else None,
                    'ex_dividend_date': ex_dividend_date,
                    'five_year_avg_yield': round(five_year_avg_dividend_yield * 100, 2) if five_year_avg_dividend_yield else None,
                    'dividend_grade': self.grade_dividend(dividend_yield_pct, payout_ratio)
                }
        except:
            pass
        return None
    
    def grade_dividend(self, dividend_yield, payout_ratio):
        """Grade dividend quality"""
        if not dividend_yield:
            return None
        if dividend_yield >= 4 and (payout_ratio is None or payout_ratio < 60):
            return "EXCELLENT"
        elif dividend_yield >= 2.5 and (payout_ratio is None or payout_ratio < 80):
            return "GOOD"
        elif dividend_yield > 0:
            return "MODERATE"
        return "NONE"
    
    def get_buy_recommendation(self, percentage_diff, asset_type):
        """Get buy recommendation based on percentage difference from Fadakka Index"""
        abs_diff = abs(percentage_diff)
        is_cheap = percentage_diff < 0
        
        if is_cheap:
            if abs_diff >= 50:
                return {
                    'action': 'STRONG BUY',
                    'level': 'DEEP VALUE',
                    'color': (0.1, 0.9, 0.1, 1),
                    'message': f'Price is {abs_diff:.0f}% below Fadakka Index. Deep value opportunity!'
                }
            elif abs_diff >= 20:
                return {
                    'action': 'BUY',
                    'level': 'VALUE',
                    'color': (0.2, 0.8, 0.2, 1),
                    'message': f'Price is {abs_diff:.0f}% below Fadakka Index. Good entry point.'
                }
            elif abs_diff >= 10:
                return {
                    'action': 'ACCUMULATE',
                    'level': 'MODEST VALUE',
                    'color': (0.4, 0.8, 0.4, 1),
                    'message': f'Price is {abs_diff:.0f}% below Fadakka Index. Consider accumulating.'
                }
            else:
                return {
                    'action': 'WATCH',
                    'level': 'SLIGHTLY CHEAP',
                    'color': (0.6, 0.8, 0.6, 1),
                    'message': f'Price slightly below Fadakka Index. Monitor for better entry.'
                }
        else:
            if abs_diff >= 50:
                return {
                    'action': 'STRONG SELL',
                    'level': 'EXTREME OVERVALUED',
                    'color': (1, 0.1, 0.1, 1),
                    'message': f'Price is {abs_diff:.0f}% above Fadakka Index. Consider taking profits.'
                }
            elif abs_diff >= 20:
                return {
                    'action': 'SELL',
                    'level': 'OVERVALUED',
                    'color': (1, 0.3, 0.3, 1),
                    'message': f'Price is {abs_diff:.0f}% above Fadakka Index. Overvalued territory.'
                }
            elif abs_diff >= 10:
                return {
                    'action': 'REDUCE',
                    'level': 'MODEST PREMIUM',
                    'color': (1, 0.5, 0.3, 1),
                    'message': f'Price is {abs_diff:.0f}% above Fadakka Index. Consider reducing position.'
                }
            else:
                return {
                    'action': 'HOLD',
                    'level': 'FAIR VALUE',
                    'color': (0.9, 0.7, 0.2, 1),
                    'message': 'Price near Fadakka Index. Hold position.'
                }
    
    def calculate_99ema(self, df):
        """Calculate 99-period EMA on weekly closing prices"""
        weekly = df['Close'].resample('W').last().dropna()
        if len(weekly) < 99:
            return None
        ema = weekly.ewm(span=99, adjust=False).mean()
        return ema.iloc[-1]
    
    def analyze_single_asset(self, symbol, asset_type='Stock'):
        """Analyze one asset and return its Fadakka Index data"""
        try:
            # For Nigerian stocks, use alternative data source
            if asset_type == 'NG Stock':
                return self.analyze_nigerian_stock(symbol)
            
            ticker = yf.Ticker(symbol)
            df = ticker.history(period='3y')
            
            if df.empty:
                return None
            
            current_price = df['Close'].iloc[-1]
            fadakka_index = self.calculate_99ema(df)
            
            if fadakka_index is None or fadakka_index == 0:
                return None
            
            percentage_diff = ((current_price - fadakka_index) / fadakka_index) * 100
            status = 'CHEAP' if current_price < fadakka_index else 'EXPENSIVE'
            
            result = {
                'symbol': symbol,
                'type': asset_type,
                'current_price': round(current_price, 4),
                'fadakka_index': round(fadakka_index, 4),
                'percentage_diff': round(percentage_diff, 2),
                'status': status,
                'buy_recommendation': self.get_buy_recommendation(percentage_diff, asset_type),
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Add dividend info for stocks
            if asset_type == 'Stock':
                div_info = self.get_dividend_info(symbol)
                if div_info:
                    result['dividend'] = div_info
            
            # Add interest rate differential for currencies
            if asset_type == 'Currency':
                rate_info = self.get_interest_rate_diff(symbol)
                if rate_info:
                    result['interest_rate_diff'] = rate_info
            
            return result
            
        except Exception as e:
            print(f"Error fetching {symbol}: {e}")
            return None
    
    def analyze_nigerian_stock(self, symbol):
        """Analyze a Nigerian stock using real data sources"""
        try:
            ns = NigerianStockData()
            df = ns.get_historical_data(symbol)
        
            if df is None or df.empty:
                return None
        
            current_price = df['Close'].iloc[-1]
            fadakka_index = self.calculate_99ema(df)
        
            if fadakka_index is None or fadakka_index == 0:
                return None
        
            percentage_diff = ((current_price - fadakka_index) / fadakka_index) * 100
            status = 'CHEAP' if current_price < fadakka_index else 'EXPENSIVE'
        
            # Get real stock info
            stock_info = ns.get_stock_info(symbol)
        
            return {
                'symbol': symbol,
                'type': 'NG Stock',
                'current_price': round(float(current_price), 2),
                'fadakka_index': round(float(fadakka_index), 2),
                'percentage_diff': round(percentage_diff, 2),
                'status': status,
                'buy_recommendation': self.get_buy_recommendation(percentage_diff, 'Stock'),
                'data_source': stock_info.get('data_source', 'Estimated'),
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        except Exception as e:
            print(f"Error with Nigerian stock {symbol}: {e}")
            return None
    
    def get_ticker(self, symbol):
        """Get ticker/data for a symbol"""
        if symbol in self.nigerian_stocks:
            return NigerianStockData()
        return yf.Ticker(symbol)
    
    def analyze_all(self, progress_callback=None):
        """Analyze all assets and return results"""
        all_results = []
        total_assets = len(self.stocks) + len(self.nigerian_stocks) + len(self.currencies) + len(self.cryptos) + len(self.commodities)
        count = 0
        
        for symbol in self.stocks:
            result = self.analyze_single_asset(symbol, 'Stock')
            if result:
                all_results.append(result)
            count += 1
            if progress_callback:
                progress_callback(count, total_assets)
        
        for symbol in self.nigerian_stocks:
            result = self.analyze_single_asset(symbol, 'NG Stock')
            if result:
                all_results.append(result)
            count += 1
            if progress_callback:
                progress_callback(count, total_assets)
        
        for symbol in self.currencies:
            result = self.analyze_single_asset(symbol, 'Currency')
            if result:
                all_results.append(result)
            count += 1
            if progress_callback:
                progress_callback(count, total_assets)
        
        for symbol in self.cryptos:
            result = self.analyze_single_asset(symbol, 'Crypto')
            if result:
                all_results.append(result)
            count += 1
            if progress_callback:
                progress_callback(count, total_assets)
        
        for name, symbol in self.commodities.items():
            result = self.analyze_single_asset(symbol, f'Commodity ({name})')
            if result:
                all_results.append(result)
            count += 1
            if progress_callback:
                progress_callback(count, total_assets)
        
        return all_results
    
    def get_summary(self, results):
        """Generate summary statistics"""
        if not results:
            return None
        
        cheap = [r for r in results if r['status'] == 'CHEAP']
        expensive = [r for r in results if r['status'] == 'EXPENSIVE']
        
        # Count buy recommendations
        strong_buy = [r for r in results if r.get('buy_recommendation', {}).get('action') == 'STRONG BUY']
        buy = [r for r in results if r.get('buy_recommendation', {}).get('action') == 'BUY']
        
        return {
            'total': len(results),
            'cheap_count': len(cheap),
            'expensive_count': len(expensive),
            'cheap_percentage': round(len(cheap) / len(results) * 100, 1),
            'strong_buy_count': len(strong_buy),
            'buy_count': len(buy),
            'market_sentiment': 'BEARISH' if len(cheap) > len(expensive) else 'BULLISH'
        }
    
    def get_all_asset_list(self):
        """Return complete list of all assets"""
        all_assets = []
        for symbol in self.stocks:
            all_assets.append({'symbol': symbol, 'type': 'Stock'})
        for symbol in self.nigerian_stocks:
            all_assets.append({'symbol': symbol, 'type': 'NG Stock'})
        for symbol in self.currencies:
            all_assets.append({'symbol': symbol, 'type': 'Currency'})
        for symbol in self.cryptos:
            all_assets.append({'symbol': symbol, 'type': 'Crypto'})
        for name, symbol in self.commodities.items():
            all_assets.append({'symbol': symbol, 'type': f'Commodity ({name})'})
        return all_assets
    
    def save_results(self, results, filename='fadakka_data.json'):
        """Save analysis results to JSON file"""
        filepath = os.path.join(os.path.dirname(os.path.dirname(__file__)), filename)
        try:
            with open(filepath, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            return True
        except Exception as e:
            print(f"Error saving data: {e}")
            return False
    
    def load_results(self, filename='fadakka_data.json'):
        """Load saved analysis results"""
        filepath = os.path.join(os.path.dirname(os.path.dirname(__file__)), filename)
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading data: {e}")
        return None