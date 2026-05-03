from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.card import MDCard
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.progressbar import MDProgressBar
from kivy.clock import Clock
from kivy.uix.scrollview import ScrollView
from kivy.uix.boxlayout import BoxLayout
from kivy.metrics import dp
from threading import Thread
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')


class FadakkaEngine:
    """Lightweight engine for mobile"""
    
    def __init__(self):
        self.stocks = ['AAPL','MSFT','GOOGL','AMZN','TSLA','META','NVDA','JPM','V','JNJ',
                       'WMT','PG','MA','UNH','HD','BAC','DIS','ADBE','NFLX','CRM',
                       'XOM','CVX','KO','PEP','TMO','ABT','NKE','ORCL','CSCO','INTC']
        self.cryptos = ['BTC-USD','ETH-USD','BNB-USD','XRP-USD','ADA-USD','SOL-USD','DOGE-USD',
                        'DOT-USD','MATIC-USD','SHIB-USD','TRX-USD','AVAX-USD','UNI-USD']
        self.commodities = {'Oil':'CL=F','Gold':'GC=F'}
    
    def calculate_99ema(self, df):
        weekly = df['Close'].resample('W').last().dropna()
        if len(weekly) < 99:
            return None
        return weekly.ewm(span=99, adjust=False).mean().iloc[-1]
    
    def analyze_single(self, symbol, asset_type='Stock'):
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period='2y')
            if df.empty:
                return None
            price = df['Close'].iloc[-1]
            fi = self.calculate_99ema(df)
            if fi is None:
                return None
            diff = ((price - fi) / fi) * 100
            return {
                'symbol': symbol,
                'type': asset_type,
                'current_price': round(price, 2),
                'fadakka_index': round(fi, 2),
                'percentage_diff': round(diff, 2),
                'status': 'CHEAP' if diff < 0 else 'EXPENSIVE'
            }
        except:
            return None
    
    def analyze_all(self, progress_callback=None):
        results = []
        all_assets = [(s, 'Stock') for s in self.stocks] + \
                     [(c, 'Crypto') for c in self.cryptos] + \
                     [(s, f'Commodity ({n})') for n, s in self.commodities.items()]
        
        total = len(all_assets)
        for i, (symbol, atype) in enumerate(all_assets):
            r = self.analyze_single(symbol, atype)
            if r:
                results.append(r)
            if progress_callback:
                progress_callback(i+1, total)
        return results


class ResultCard(MDCard):
    def __init__(self, result, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.height = dp(50)
        self.padding = dp(10)
        self.radius = dp(8)
        self.md_bg_color = (0.12, 0.12, 0.15, 1)
        
        color = (0.2, 0.8, 0.2, 1) if result['status'] == 'CHEAP' else (0.95, 0.3, 0.3, 1)
        
        box = MDBoxLayout(orientation='horizontal', spacing=dp(8))
        
        box.add_widget(MDLabel(
            text=result['symbol'],
            font_style="Subtitle2",
            bold=True,
            theme_text_color="Custom",
            text_color=(1,1,1,1),
            size_hint_x=0.3
        ))
        
        box.add_widget(MDLabel(
            text=f"{result['percentage_diff']:+.1f}%",
            font_style="Subtitle2",
            bold=True,
            theme_text_color="Custom",
            text_color=color,
            size_hint_x=0.25,
            halign="center"
        ))
        
        box.add_widget(MDLabel(
            text=result['status'],
            font_style="Caption",
            bold=True,
            theme_text_color="Custom",
            text_color=color,
            size_hint_x=0.2,
            halign="center"
        ))
        
        box.add_widget(MDLabel(
            text=f"${result['current_price']:.2f}",
            font_style="Body1",
            theme_text_color="Custom",
            text_color=(0.8,0.8,0.8,1),
            size_hint_x=0.25,
            halign="right"
        ))
        
        self.add_widget(box)


class HomeScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.engine = FadakkaEngine()
        self.results = []
        
        self.layout = BoxLayout(orientation='vertical', padding=dp(12), spacing=dp(8))
        
        # Title
        self.layout.add_widget(MDLabel(
            text="FADAKKA INDEX",
            halign="center",
            font_style="H5",
            bold=True,
            theme_text_color="Custom",
            text_color=(0.9, 0.7, 0.2, 1),
            size_hint_y=0.08
        ))
        
        # Status
        self.status_label = MDLabel(
            text="Press SCAN to begin",
            halign="center",
            font_style="Caption",
            theme_text_color="Custom",
            text_color=(0.5,0.5,0.5,1),
            size_hint_y=0.05
        )
        self.layout.add_widget(self.status_label)
        
        # Progress
        self.progress = MDProgressBar(
            size_hint_x=0.9,
            pos_hint={'center_x': 0.5},
            size_hint_y=0.02,
            color=(0.9, 0.7, 0.2, 1)
        )
        self.layout.add_widget(self.progress)
        
        # Results scroll
        self.scroll = ScrollView(size_hint_y=0.7)
        self.results_layout = MDBoxLayout(
            orientation='vertical',
            spacing=dp(5),
            size_hint_y=None
        )
        self.results_layout.bind(minimum_height=self.results_layout.setter('height'))
        self.scroll.add_widget(self.results_layout)
        self.layout.add_widget(self.scroll)
        
        # Scan button
        self.scan_btn = MDRaisedButton(
            text="SCAN MARKET",
            size_hint=(0.9, 0.07),
            pos_hint={'center_x': 0.5},
            md_bg_color=(0.9, 0.7, 0.2, 1),
            text_color=(0.05, 0.05, 0.07, 1),
            on_release=self.start_scan
        )
        self.layout.add_widget(self.scan_btn)
        
        self.add_widget(self.layout)
    
    def start_scan(self, instance):
        self.scan_btn.disabled = True
        self.scan_btn.text = "SCANNING..."
        self.status_label.text = "Fetching data..."
        self.progress.value = 0
        self.results_layout.clear_widgets()
        
        Thread(target=self.run_scan, daemon=True).start()
    
    def run_scan(self):
        self.results = self.engine.analyze_all(
            progress_callback=lambda c, t: Clock.schedule_once(
                lambda dt, a=c, b=t: setattr(self.progress, 'value', (a/b)*100)
            )
        )
        Clock.schedule_once(lambda dt: self.show_results())
    
    def show_results(self):
        self.scan_btn.disabled = False
        self.scan_btn.text = "REFRESH"
        self.progress.value = 100
        
        if not self.results:
            self.status_label.text = "No data. Check internet."
            return
        
        cheap = [r for r in self.results if r['status'] == 'CHEAP']
        self.status_label.text = f"Cheap: {len(cheap)} | Expensive: {len(self.results)-len(cheap)} | Total: {len(self.results)}"
        
        self.results_layout.clear_widgets()
        for r in self.results:
            self.results_layout.add_widget(ResultCard(r))
        
        self.results_layout.height = len(self.results) * dp(55)


class FadakkaApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Amber"
        self.title = "Fadakka Index"
        return HomeScreen()


if __name__ == "__main__":
    FadakkaApp().run()