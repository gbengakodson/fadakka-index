import os
import json
import schedule
import time
from datetime import datetime
from twilio.rest import Client
from services.fadakka_engine import FadakkaEngine

class FadakkaWhatsAppBot:
    """WhatsApp bot for daily Fadakka Index alerts"""
    
    def __init__(self):
        # Twilio credentials - get from twilio.com/console (free trial)
        self.account_sid = os.environ.get('TWILIO_SID', 'YOUR_TWILIO_SID')
        self.auth_token = os.environ.get('TWILIO_TOKEN', 'YOUR_TWILIO_TOKEN')
        self.twilio_whatsapp = 'whatsapp:+14155238886'  # Twilio sandbox number
        self.engine = FadakkaEngine()
        
        # Subscribers database (In production: use SQLite/PostgreSQL)
        self.subscribers_file = 'subscribers.json'
        self.subscribers = self.load_subscribers()
        
    def load_subscribers(self):
        """Load subscriber list"""
        try:
            if os.path.exists(self.subscribers_file):
                with open(self.subscribers_file, 'r') as f:
                    return json.load(f)
        except:
            pass
        return []
    
    def save_subscribers(self):
        """Save subscriber list"""
        with open(self.subscribers_file, 'w') as f:
            json.dump(self.subscribers, f)
    
    def add_subscriber(self, phone_number, name=''):
        """Add a new subscriber"""
        phone = phone_number.replace('+', '').replace(' ', '')
        if phone not in [s['phone'] for s in self.subscribers]:
            self.subscribers.append({
                'phone': phone,
                'name': name,
                'joined': datetime.now().isoformat(),
                'active': True,
                'preferences': {
                    'stocks': True,
                    'crypto': True,
                    'forex': False,
                    'commodities': False,
                    'ng_stocks': True  # Nigerian stocks
                }
            })
            self.save_subscribers()
            return True
        return False
    
    def get_fadakka_alerts(self):
        """Generate Fadakka Index alerts"""
        try:
            results = self.engine.analyze_all()
            self.engine.save_results(results)
        except:
            results = self.engine.load_results()
        
        if not results:
            return None
        
        alerts = {
            'strong_buy': [],  # 50%+ below Fadakka
            'buy': [],         # 20-50% below
            'strong_sell': [], # 50%+ above
            'sell': [],        # 20-50% above
            'market_summary': {}
        }
        
        cheap = [r for r in results if r['status'] == 'CHEAP']
        expensive = [r for r in results if r['status'] == 'EXPENSIVE']
        
        # Market summary
        alerts['market_summary'] = {
            'total': len(results),
            'cheap': len(cheap),
            'expensive': len(expensive),
            'sentiment': '🐻 BEARISH' if len(cheap) > len(expensive) else '🐂 BULLISH'
        }
        
        # Categorize by Fadakka distance
        for r in results:
            diff = abs(r.get('percentage_diff', 0))
            is_cheap = r['status'] == 'CHEAP'
            
            if is_cheap and diff >= 50:
                alerts['strong_buy'].append(r)
            elif is_cheap and diff >= 20:
                alerts['buy'].append(r)
            elif not is_cheap and diff >= 50:
                alerts['strong_sell'].append(r)
            elif not is_cheap and diff >= 20:
                alerts['sell'].append(r)
        
        # Sort by percentage difference
        for key in ['strong_buy', 'buy', 'strong_sell', 'sell']:
            alerts[key].sort(key=lambda x: abs(x['percentage_diff']), reverse=True)
        
        return alerts
    
    def format_alert_message(self, alerts):
        """Format alerts into readable WhatsApp message"""
        if not alerts:
            return "⚠️ Unable to fetch market data. Please try later."
        
        msg = "📊 *FADAKKA INDEX DAILY REPORT*\n"
        msg += f"📅 {datetime.now().strftime('%B %d, %Y')}\n\n"
        
        # Market Summary
        s = alerts['market_summary']
        msg += "*📈 MARKET SENTIMENT:*\n"
        msg += f"{s['sentiment']}\n"
        msg += f"🟢 Cheap: {s['cheap']} | 🔴 Expensive: {s['expensive']}\n"
        msg += f"Total Assets: {s['total']}\n\n"
        
        # Strong Buy Signals
        if alerts['strong_buy']:
            msg += "*🚀 STRONG BUY (50%+ below Fadakka Index):*\n"
            for r in alerts['strong_buy'][:5]:
                currency = '₦' if 'NG' in r.get('type', '') else '$'
                msg += f"• {r['symbol']} - {currency}{r['current_price']:.2f}\n"
                msg += f"  📉 {abs(r['percentage_diff']):.1f}% below Fadakka ({currency}{r['fadakka_index']:.2f})\n"
            msg += "\n"
        
        # Buy Signals
        if alerts['buy']:
            msg += "*✅ BUY (20%+ below Fadakka Index):*\n"
            for r in alerts['buy'][:5]:
                currency = '₦' if 'NG' in r.get('type', '') else '$'
                msg += f"• {r['symbol']} - {currency}{r['current_price']:.2f}\n"
                msg += f"  📉 {abs(r['percentage_diff']):.1f}% below Fadakka\n"
            msg += "\n"
        
        # Strong Sell Signals
        if alerts['strong_sell']:
            msg += "*⚠️ STRONG SELL (50%+ above Fadakka Index):*\n"
            for r in alerts['strong_sell'][:5]:
                currency = '₦' if 'NG' in r.get('type', '') else '$'
                msg += f"• {r['symbol']} - {currency}{r['current_price']:.2f}\n"
                msg += f"  📈 {r['percentage_diff']:.1f}% above Fadakka\n"
            msg += "\n"
        
        # Top Nigerian Stocks
        ng_stocks = [r for r in alerts.get('buy', []) + alerts.get('strong_buy', []) if 'NG' in r.get('type', '')][:3]
        if ng_stocks:
            msg += "*🇳🇬 Nigerian Stock Opportunities:*\n"
            for r in ng_stocks:
                msg += f"• {r['symbol']} - ₦{r['current_price']:.2f} ({abs(r['percentage_diff']):.1f}% below)\n"
            msg += "\n"
        
        msg += "_\n"
        msg += "📱 Fadakka Index - 99-Week EMA Analysis\n"
        msg += "🔗 View full dashboard: http://fadakka.io\n"
        msg += "💬 Reply STOP to unsubscribe_"
        
        return msg
    
    def send_alert_to_subscriber(self, subscriber, message):
        """Send WhatsApp message to a subscriber"""
        try:
            client = Client(self.account_sid, self.auth_token)
            
            message = client.messages.create(
                body=message,
                from_=self.twilio_whatsapp,
                to=f'whatsapp:+{subscriber["phone"]}'
            )
            print(f"✅ Sent to {subscriber['phone']}: {message.sid}")
            return True
        except Exception as e:
            print(f"❌ Failed to send to {subscriber['phone']}: {e}")
            return False
    
    def send_daily_alerts(self):
        """Send daily alerts to all subscribers"""
        print(f"\n{'='*50}")
        print(f"📡 Sending Daily Fadakka Alerts...")
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"👥 {len(self.subscribers)} subscribers")
        print(f"{'='*50}\n")
        
        # Get alerts
        print("🔄 Fetching market data...")
        alerts = self.get_fadakka_alerts()
        
        if not alerts:
            print("❌ No data available")
            return
        
        # Format message
        message = self.format_alert_message(alerts)
        
        # Send to each subscriber
        active_subs = [s for s in self.subscribers if s.get('active', True)]
        sent_count = 0
        
        for subscriber in active_subs:
            if self.send_alert_to_subscriber(subscriber, message):
                sent_count += 1
            time.sleep(1)  # Avoid rate limiting
        
        print(f"\n✅ Sent to {sent_count}/{len(active_subs)} subscribers")
    
    def handle_incoming_message(self, from_number, message_body):
        """Handle incoming WhatsApp messages"""
        phone = from_number.replace('whatsapp:+', '').replace('+', '')
        msg = message_body.lower().strip()
        
        if msg in ['stop', 'unsubscribe', 'cancel']:
            # Remove subscriber
            for sub in self.subscribers:
                if sub['phone'] == phone:
                    sub['active'] = False
                    self.save_subscribers()
                    return "You've been unsubscribed from Fadakka alerts. Send JOIN to resubscribe."
        
        elif msg in ['join', 'subscribe', 'start', 'hi', 'hello']:
            if self.add_subscriber(phone):
                return "✅ Welcome to Fadakka Index! 🎉\n\nYou'll receive daily market alerts with:\n• Strong Buy/Sell signals\n• Nigerian stock opportunities\n• Market sentiment\n\nReply STOP to unsubscribe."
            else:
                return "You're already subscribed! You'll receive daily alerts. Reply STOP to unsubscribe."
        
        elif msg == 'status':
            return "📊 Fetching your subscription status...\n\nReply:\n• JOIN - Subscribe\n• STOP - Unsubscribe\n• STATUS - Check"
        
        elif msg == 'now' or msg == 'report':
            # Send immediate report
            alerts = self.get_fadakka_alerts()
            if alerts:
                return self.format_alert_message(alerts)
            return "⚠️ Unable to fetch data. Try again later."
        
        else:
            return "📊 *Fadakka Index Bot*\n\nCommands:\n• JOIN - Subscribe to daily alerts\n• STOP - Unsubscribe\n• NOW - Get instant report\n• STATUS - Check subscription\n\n💡 Example: 'DANGOTE CEMENT is 25% below Fadakka Index - STRONG BUY'"
    
    def run_scheduler(self):
        """Run the daily scheduler"""
        # Schedule daily at 8:00 AM Lagos time
        schedule.every().day.at("08:00").do(self.send_daily_alerts)
        
        print("🤖 Fadakka WhatsApp Bot Running...")
        print("📅 Daily alerts scheduled for 8:00 AM")
        print("👥 Subscribers:", len(self.subscribers))
        print("\nPress Ctrl+C to stop\n")
        
        # Send an immediate test if it's first run
        self.send_daily_alerts()
        
        while True:
            schedule.run_pending()
            time.sleep(60)


# Flask webhook server for incoming messages
from flask import Flask, request
whatsapp_app = Flask(__name__)
bot = FadakkaWhatsAppBot()

@whatsapp_app.route('/whatsapp', methods=['POST'])
def whatsapp_webhook():
    """Handle incoming WhatsApp messages"""
    from_number = request.form.get('From', '')
    message_body = request.form.get('Body', '')
    
    response = bot.handle_incoming_message(from_number, message_body)
    
    from twilio.twiml.messaging_response import MessagingResponse
    twiml = MessagingResponse()
    twiml.message(response)
    return str(twiml)

@whatsapp_app.route('/send-now', methods=['GET'])
def send_now():
    """Manual trigger for daily alerts"""
    bot.send_daily_alerts()
    return "Alerts sent!"

@whatsapp_app.route('/subscribers', methods=['GET'])
def list_subscribers():
    """View all subscribers"""
    return jsonify(bot.subscribers)


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'webhook':
        # Run as webhook server (for production)
        print("Starting WhatsApp webhook server...")
        whatsapp_app.run(host='0.0.0.0', port=5001, debug=False)
    else:
        # Run as scheduler
        bot.run_scheduler()