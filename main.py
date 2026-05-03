from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.progressbar import MDProgressBar
from kivymd.uix.card import MDCard
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.dialog import MDDialog
from kivymd.uix.selectioncontrol import MDSwitch
from kivymd.uix.textfield import MDTextField
from kivy.clock import Clock
from kivy.uix.scrollview import ScrollView
from kivy.uix.boxlayout import BoxLayout
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.core.window import Window
from services.fadakka_engine import FadakkaEngine
from threading import Thread
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from io import BytesIO
from kivy.core.image import Image as CoreImage
from kivy.uix.image import Image
import numpy as np
import json
import os

# Mobile-friendly window
Window.size = (400, 700)


class PriceChart(BoxLayout):
    """Mini chart widget"""
    
    def __init__(self, weekly_prices, fadakka_value, current_price, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.height = dp(70)
        self.orientation = 'vertical'
        self.padding = [dp(2), dp(1), dp(2), dp(1)]
        self.create_chart(weekly_prices, fadakka_value, current_price)
    
    def create_chart(self, weekly_prices, fadakka_value, current_price):
        try:
            plt.clf()
            fig, ax = plt.subplots(figsize=(3.5, 1.0), facecolor='#0d0d12')
            
            if weekly_prices and len(weekly_prices) > 1:
                dates = list(range(len(weekly_prices)))
                ax.plot(dates, weekly_prices, color='#4da6ff', linewidth=1.2)
                ax.axhline(y=fadakka_value, color='#e6b800', linewidth=0.8, linestyle='--')
                ax.fill_between(dates, weekly_prices, fadakka_value,
                               where=(np.array(weekly_prices) >= fadakka_value),
                               color='#ff3333', alpha=0.10)
                ax.fill_between(dates, weekly_prices, fadakka_value,
                               where=(np.array(weekly_prices) < fadakka_value),
                               color='#33cc33', alpha=0.10)
                dot_color = '#33cc33' if current_price < fadakka_value else '#ff3333'
                ax.scatter([len(dates)-1], [current_price], color=dot_color, s=20, zorder=5)
            
            ax.set_facecolor('#0d0d12')
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['bottom'].set_color('#2a2a2a')
            ax.spines['left'].set_color('#2a2a2a')
            ax.tick_params(colors='#555555', labelsize=5, pad=1)
            ax.set_xticks([])
            plt.tight_layout(pad=0.2)
            
            buf = BytesIO()
            plt.savefig(buf, format='png', dpi=80, facecolor='#0d0d12', edgecolor='none', bbox_inches='tight')
            buf.seek(0)
            img = CoreImage(buf, ext='png')
            self.add_widget(Image(texture=img.texture, size_hint_y=1))
            plt.close()
        except:
            self.add_widget(MDLabel(text="Chart loading...", halign="center", theme_text_color="Custom", text_color=(0.5,0.5,0.5,1)))


class AssetCard(MDCard):
    """Compact asset card"""
    
    def __init__(self, result, engine, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.height = dp(140)
        self.padding = dp(6)
        self.radius = dp(8)
        self.elevation = 2
        self.md_bg_color = (0.09, 0.09, 0.12, 1)
        
        if result['status'] == 'CHEAP':
            accent = (0.2, 0.85, 0.2, 1)
            status_txt = "CHEAP"
        else:
            accent = (0.95, 0.25, 0.25, 1)
            status_txt = "EXPENSIVE"
        
        currency = '₦' if 'NG' in result.get('type', '') else '$'
        
        main = MDBoxLayout(orientation='vertical', spacing=dp(2))
        
        # Row 1: Symbol + Status + Price
        row1 = MDBoxLayout(orientation='horizontal', spacing=dp(3), size_hint_y=0.18)
        
        sym_box = MDBoxLayout(orientation='vertical', size_hint_x=0.35)
        sym_box.add_widget(MDLabel(
            text=result['symbol'], font_style="Subtitle2", bold=True,
            theme_text_color="Custom", text_color=(1, 1, 1, 1), shorten=True
        ))
        sym_box.add_widget(MDLabel(
            text=result['type'], font_style="Overline",
            theme_text_color="Custom", text_color=(0.4, 0.4, 0.4, 1), shorten=True
        ))
        
        stat_box = MDBoxLayout(orientation='vertical', size_hint_x=0.3)
        stat_box.add_widget(MDLabel(
            text=f"{result['percentage_diff']:+.1f}%", font_style="Subtitle2", bold=True,
            theme_text_color="Custom", text_color=accent, halign="center"
        ))
        stat_box.add_widget(MDLabel(
            text=status_txt, font_style="Overline", bold=True,
            theme_text_color="Custom", text_color=accent, halign="center"
        ))
        
        price_box = MDBoxLayout(orientation='vertical', size_hint_x=0.35)
        price_box.add_widget(MDLabel(
            text=f"{currency}{result['current_price']:.2f}", font_style="Subtitle2",
            theme_text_color="Custom", text_color=(1, 1, 1, 1), halign="right"
        ))
        price_box.add_widget(MDLabel(
            text=f"Fadakka: {currency}{result['fadakka_index']:.2f}", font_style="Overline",
            theme_text_color="Custom", text_color=(0.9, 0.7, 0.2, 1), halign="right"
        ))
        
        row1.add_widget(sym_box)
        row1.add_widget(stat_box)
        row1.add_widget(price_box)
        main.add_widget(row1)
        
        # Row 2: OHLC
        row2 = MDBoxLayout(orientation='horizontal', spacing=dp(2), size_hint_y=0.14)
        ohlc_vals = {'O': None, 'H': None, 'L': None, 'C': None}
        try:
            ticker = engine.get_ticker(result['symbol'])
            df = ticker.history(period='5d')
            if not df.empty and len(df) >= 1:
                ohlc_vals = {
                    'O': df['Open'].iloc[-1], 'H': df['High'].iloc[-1],
                    'L': df['Low'].iloc[-1],
                    'C': df['Close'].iloc[-2] if len(df) > 1 else None
                }
        except:
            pass
        
        for label, value, col in [
            ('O', ohlc_vals['O'], (0.6,0.6,0.6,1)),
            ('H', ohlc_vals['H'], (0.2,0.85,0.2,1)),
            ('L', ohlc_vals['L'], (0.95,0.25,0.25,1)),
            ('C', ohlc_vals['C'], (0.6,0.6,0.6,1))
        ]:
            item = MDBoxLayout(orientation='vertical', size_hint_x=0.25)
            item.add_widget(MDLabel(text=label, font_style="Overline",
                theme_text_color="Custom", text_color=(0.35,0.35,0.35,1), halign="center", font_size="7sp"))
            item.add_widget(MDLabel(text=f"{value:.2f}" if value else "-", font_style="Caption",
                theme_text_color="Custom", text_color=col, halign="center", font_size="8sp"))
            row2.add_widget(item)
        main.add_widget(row2)
        
        # Row 3: Chart (simplified - just show if available)
        if result.get('_chart_data'):
            chart = PriceChart(result['_chart_data'], result['fadakka_index'], result['current_price'])
            main.add_widget(chart)
        else:
            placeholder = MDBoxLayout(size_hint_y=0.4)
            placeholder.add_widget(MDLabel(text="...", halign="center", theme_text_color="Custom", text_color=(0.3,0.3,0.3,1)))
            main.add_widget(placeholder)
        
        # Row 4: Progress bar
        bar_box = MDBoxLayout(orientation='horizontal', spacing=dp(2), size_hint_y=0.05)
        bar_box.add_widget(MDLabel(text="Distance:", font_style="Overline",
            theme_text_color="Custom", text_color=(0.4,0.4,0.4,1), size_hint_x=0.2, font_size="6sp"))
        bar_box.add_widget(MDProgressBar(value=min(abs(result.get('percentage_diff', 0)), 100), color=accent, size_hint_x=0.8))
        main.add_widget(bar_box)
        
        self.add_widget(main)


class HomeScreen(MDScreen):
    """Main Dashboard - Mobile Optimized"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.engine = FadakkaEngine()
        self.all_results = []
        self.is_cancelled = False
        self.current_page = 0
        self.per_page = 3
        self.auto_refresh_enabled = False
        self.refresh_interval = 30
        self.refresh_event = None
        self.is_loading = False
        
        with self.canvas.before:
            Color(0.04, 0.04, 0.06, 1)
            self.rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_rect, pos=self._update_rect)
        
        # Main layout
        self.layout = BoxLayout(
            orientation='vertical',
            padding=[dp(8), dp(10), dp(8), dp(8)],
            spacing=dp(4)
        )
        
        # Header
        header = MDBoxLayout(orientation='vertical', size_hint_y=0.08, spacing=dp(1))
        header.add_widget(MDLabel(
            text="FADAKKA INDEX", halign="center", font_style="H6", bold=True,
            theme_text_color="Custom", text_color=(0.9, 0.7, 0.2, 1)
        ))
        header.add_widget(MDLabel(
            text="99-Week EMA Analysis", halign="center", font_style="Overline",
            theme_text_color="Custom", text_color=(0.4, 0.4, 0.4, 1)
        ))
        self.layout.add_widget(header)
        
        # Summary
        self.summary_card = MDCard(
            size_hint_y=0.04, padding=dp(5), radius=dp(6), elevation=1,
            md_bg_color=(0.1, 0.1, 0.13, 1)
        )
        self.summary_label = MDLabel(
            text="Loading...", halign="center", font_style="Caption",
            theme_text_color="Custom", text_color=(0.5, 0.5, 0.5, 1)
        )
        self.summary_card.add_widget(self.summary_label)
        self.layout.add_widget(self.summary_card)
        
        # Dropdown
        self.dropdown_btn = MDFlatButton(
            text="Select Asset  ▼", size_hint_y=0.04,
            theme_text_color="Custom", text_color=(0.9, 0.7, 0.2, 1),
            on_release=self.open_dropdown
        )
        self.layout.add_widget(self.dropdown_btn)
        self.dropdown_menu = None
        
        # Status & Progress
        self.status_label = MDLabel(
            text="Initializing...", halign="center", font_style="Overline",
            theme_text_color="Custom", text_color=(0.35, 0.35, 0.35, 1), size_hint_y=0.025
        )
        self.layout.add_widget(self.status_label)
        
        self.progress = MDProgressBar(
            size_hint_x=0.9, pos_hint={'center_x': 0.5}, size_hint_y=0.008,
            color=(0.9, 0.7, 0.2, 1)
        )
        self.progress.value = 0
        self.layout.add_widget(self.progress)
        
        # Asset details
        self.scroll = ScrollView(size_hint_y=0.67, bar_color=(0.2, 0.2, 0.2, 1))
        self.detail_layout = MDBoxLayout(
            orientation='vertical', spacing=dp(5), padding=[0, dp(2), 0, 0], size_hint_y=None
        )
        self.detail_layout.bind(minimum_height=self.detail_layout.setter('height'))
        self.scroll.add_widget(self.detail_layout)
        self.layout.add_widget(self.scroll)
        
        # Navigation
        nav_row = MDBoxLayout(orientation='horizontal', size_hint_y=0.05, spacing=dp(3))
        self.prev_btn = MDRaisedButton(
            text="< PREV", size_hint_x=0.3, md_bg_color=(0.12, 0.12, 0.17, 1),
            font_style="Caption", on_release=self.prev_page
        )
        self.page_label = MDLabel(
            text="Page 1", halign="center", font_style="Caption",
            theme_text_color="Custom", text_color=(0.5, 0.5, 0.5, 1), size_hint_x=0.4
        )
        self.next_btn = MDRaisedButton(
            text="NEXT >", size_hint_x=0.3, md_bg_color=(0.12, 0.12, 0.17, 1),
            font_style="Caption", on_release=self.next_page
        )
        nav_row.add_widget(self.prev_btn)
        nav_row.add_widget(self.page_label)
        nav_row.add_widget(self.next_btn)
        self.layout.add_widget(nav_row)
        
        # Scan button
        self.scan_btn = MDRaisedButton(
            text="SCAN MARKET", size_hint=(0.9, 0.06),
            pos_hint={'center_x': 0.5},
            md_bg_color=(0.9, 0.7, 0.2, 1), text_color=(0.05, 0.05, 0.07, 1),
            font_style="Button", on_release=self.start_analysis
        )
        self.layout.add_widget(self.scan_btn)
        
        self.add_widget(self.layout)
        
        # Safe startup - load 3 default assets first
        Clock.schedule_once(lambda dt: self.startup_load(), 0.5)
    
    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size
    
    def startup_load(self):
        """Load default assets first, then cached data"""
        self.status_label.text = "Loading default assets..."
        
        # Load 3 quick default assets
        defaults = [
            ('AAPL', 'Stock'),
            ('BTC-USD', 'Crypto'),
            ('GC=F', 'Commodity (Gold)')
        ]
        
        def load_defaults():
            for symbol, atype in defaults:
                try:
                    result = self.engine.analyze_single_asset(symbol, atype)
                    if result:
                        self.all_results.append(result)
                except:
                    pass
            
            # Show them immediately
            Clock.schedule_once(lambda dt: self.show_page())
            Clock.schedule_once(lambda dt: self.load_cached_or_scan(), 1)
        
        Thread(target=load_defaults, daemon=True).start()
    
    def load_cached_or_scan(self):
        """Load cached data or prompt user to scan"""
        try:
            saved = self.engine.load_results()
            if saved and len(saved) > 5:
                # Merge saved data
                existing_symbols = {r['symbol'] for r in self.all_results}
                for r in saved:
                    if r['symbol'] not in existing_symbols:
                        self.all_results.append(r)
                
                summary = self.engine.get_summary(self.all_results)
                if summary:
                    self.summary_label.text = f"{summary['total']} assets | Cheap: {summary['cheap_count']} | Expensive: {summary['expensive_count']}"
                    self.status_label.text = "Loaded cached data"
                    self.current_page = 0
                    Clock.schedule_once(lambda dt: self.show_page(), 0.3)
            else:
                self.summary_label.text = "Press SCAN to analyze market"
                self.status_label.text = f"Ready - {len(self.all_results)} assets loaded"
        except:
            self.status_label.text = "Ready"
    
    def open_dropdown(self, instance):
        if not self.all_results:
            return
        
        menu_items = []
        types_order = ['Stock', 'NG Stock', 'Currency', 'Crypto']
        grouped = {}
        
        for res in self.all_results:
            t = res['type']
            if t not in grouped:
                grouped[t] = []
            grouped[t].append(res)
        
        for asset_type in types_order:
            if asset_type in grouped:
                label = asset_type.upper()
                menu_items.append({
                    "text": f"--- {label} ---",
                    "viewclass": "OneLineListItem",
                    "disabled": True
                })
                for res in grouped[asset_type]:
                    cheap_mark = "[CHEAP]" if res['status'] == 'CHEAP' else "[EXP]"
                    menu_items.append({
                        "text": f"{cheap_mark} {res['symbol']}  {res['percentage_diff']:+.1f}%",
                        "viewclass": "OneLineListItem",
                        "on_release": lambda x=res: self.jump_to_asset(self.all_results.index(x)),
                    })
        
        # Other types
        for key in grouped:
            if key not in types_order:
                menu_items.append({
                    "text": f"--- {key.upper()} ---",
                    "viewclass": "OneLineListItem",
                    "disabled": True
                })
                for res in grouped[key]:
                    cheap_mark = "[CHEAP]" if res['status'] == 'CHEAP' else "[EXP]"
                    menu_items.append({
                        "text": f"{cheap_mark} {res['symbol']}  {res['percentage_diff']:+.1f}%",
                        "viewclass": "OneLineListItem",
                        "on_release": lambda x=res: self.jump_to_asset(self.all_results.index(x)),
                    })
        
        self.dropdown_menu = MDDropdownMenu(
            caller=instance, items=menu_items, width_mult=4, max_height=dp(300)
        )
        self.dropdown_menu.open()
    
    def jump_to_asset(self, index):
        if self.dropdown_menu:
            self.dropdown_menu.dismiss()
        self.current_page = index // self.per_page
        self.show_page()
    
    def next_page(self, instance):
        max_page = max(0, (len(self.all_results) - 1) // self.per_page)
        if self.current_page < max_page:
            self.current_page += 1
            self.show_page()
    
    def prev_page(self, instance):
        if self.current_page > 0:
            self.current_page -= 1
            self.show_page()
    
    def show_page(self):
        self.detail_layout.clear_widgets()
        if not self.all_results:
            return
        
        start = self.current_page * self.per_page
        end = min(start + self.per_page, len(self.all_results))
        
        for i in range(start, end):
            card = AssetCard(self.all_results[i], self.engine)
            self.detail_layout.add_widget(card)
        
        max_page = max(0, (len(self.all_results) - 1) // self.per_page)
        self.page_label.text = f"Page {self.current_page + 1}/{max_page + 1}"
        self.detail_layout.height = (end - start) * dp(148)
        self.scroll.scroll_y = 1
    
    def start_analysis(self, instance):
        self.scan_btn.disabled = True
        self.scan_btn.text = "SCANNING..."
        self.status_label.text = "Fetching market data..."
        self.progress.value = 0
        self.is_cancelled = False
        self.detail_layout.clear_widgets()
        self.all_results = []
        self.current_page = 0
        
        Thread(target=self.run_analysis, daemon=True).start()
    
    def run_analysis(self):
        all_assets = self.engine.get_all_asset_list()
        total = len(all_assets)
        
        for i, asset in enumerate(all_assets):
            if self.is_cancelled:
                break
            self.update_status(f"[{i+1}/{total}] {asset['symbol']}")
            result = self.engine.analyze_single_asset(asset['symbol'], asset['type'])
            if result:
                self.all_results.append(result)
            self.update_progress(i + 1, total)
        
        Clock.schedule_once(lambda dt: self.display_results())
    
    def update_status(self, msg):
        Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', msg))
    
    def update_progress(self, current, total):
        value = (current / total) * 100
        Clock.schedule_once(lambda dt: setattr(self.progress, 'value', value))
    
    def display_results(self):
        self.scan_btn.disabled = False
        self.scan_btn.text = "REFRESH"
        self.progress.value = 100
        
        if not self.all_results:
            self.summary_label.text = "No data. Check connection."
            self.status_label.text = "Failed"
            return
        
        summary = self.engine.get_summary(self.all_results)
        color = (0.2, 0.85, 0.2, 1) if summary['market_sentiment'] == 'BEARISH' else (0.95, 0.25, 0.25, 1)
        
        self.summary_label.text = (
            f"{summary['market_sentiment']} | Cheap: {summary['cheap_count']} | "
            f"Expensive: {summary['expensive_count']} | Total: {summary['total']}"
        )
        self.summary_label.text_color = color
        self.status_label.text = f"Updated: {datetime.now().strftime('%H:%M')}"
        
        self.current_page = 0
        self.show_page()
        
        # Save in background
        Thread(target=lambda: self.engine.save_results(self.all_results), daemon=True).start()


class FadakkaApp(MDApp):
    """Fadakka Index App"""
    
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Amber"
        self.title = "Fadakka Index"
        return HomeScreen()


if __name__ == "__main__":
    from datetime import datetime
    FadakkaApp().run()