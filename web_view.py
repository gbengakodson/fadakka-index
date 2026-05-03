from flask import Flask, jsonify, render_template_string
from services.fadakka_engine import FadakkaEngine
import json
import os

app = Flask(__name__)
engine = FadakkaEngine()

# Load cached data or analyze
cached_results = engine.load_results()

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Fadakka Index</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { background: #0a0a0f; color: #fff; font-family: Arial; padding: 10px; margin: 0; }
        h1 { color: #e6b800; text-align: center; font-size: 18px; margin: 8px 0; }
        .card { background: #1a1a24; padding: 10px; margin: 6px 0; border-radius: 8px; }
        .cheap { border-left: 4px solid #33cc33; }
        .expensive { border-left: 4px solid #ff3333; }
        .symbol { font-weight: bold; font-size: 14px; }
        .price { float: right; font-size: 14px; }
        .diff { font-size: 12px; margin-top: 4px; }
        .green { color: #33cc33; }
        .red { color: #ff3333; }
        .gold { color: #e6b800; }
        button { 
            width: 100%; padding: 12px; background: #e6b800; color: #0a0a0f;
            border: none; border-radius: 8px; font-size: 14px; font-weight: bold; margin: 5px 0;
        }
        .summary { text-align: center; padding: 8px; margin: 8px 0; background: #1a1a24; border-radius: 8px; font-size: 13px; }
        .ohlc { font-size: 10px; color: #888; display: flex; justify-content: space-around; margin: 3px 0; }
        .type-badge { font-size: 10px; color: #666; background: #111; padding: 2px 6px; border-radius: 4px; }
        select, input { 
            background: #1a1a24; color: #fff; border: 1px solid #333; 
            padding: 8px; border-radius: 6px; width: 100%; margin: 5px 0;
        }
    </style>
</head>
<body>
    <h1>📊 FADAKKA INDEX</h1>
    <div class="summary">{{ summary|safe }}</div>
    
    <select onchange="filterType(this.value)">
        <option value="all">All Assets</option>
        <option value="Stock">US Stocks</option>
        <option value="NG Stock">Nigerian Stocks</option>
        <option value="Currency">Currencies</option>
        <option value="Crypto">Crypto</option>
        <option value="Commodity">Commodities</option>
    </select>
    
    <button onclick="location.href='/scan'">🔄 FULL SCAN (Slow)</button>
    <div id="results">{{ results|safe }}</div>
    
    <script>
        function filterType(type) {
            document.querySelectorAll('.card').forEach(card => {
                if (type === 'all' || card.dataset.type === type || card.dataset.type.startsWith(type)) {
                    card.style.display = 'block';
                } else {
                    card.style.display = 'none';
                }
            });
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    global cached_results
    
    results = cached_results
    if not results:
        # Load saved data
        results = engine.load_results()
        if results:
            cached_results = results
        else:
            return "<h2 style='color:#e6b800;text-align:center;padding:20px'>No data yet.<br><a href='/scan' style='color:#fff'>Click to scan</a></h2>"
    
    # Summary
    cheap = [r for r in results if r['status'] == 'CHEAP']
    summary_html = f"🟢 Cheap: {len(cheap)} | 🔴 Expensive: {len(results)-len(cheap)} | Total: {len(results)}"
    
    # Results
    results_html = ""
    for r in results:
        css_class = "cheap" if r['status'] == 'CHEAP' else "expensive"
        diff_class = "green" if r['status'] == 'CHEAP' else "red"
        
        # Get type for filtering
        asset_type = r.get('type', 'Stock')
        
        results_html += f"""
        <div class="card {css_class}" data-type="{asset_type}">
            <div class="symbol">
                {r['symbol']} 
                <span class="type-badge">{asset_type}</span>
                <span class="price">${r['current_price']:.2f}</span>
            </div>
            <div class="diff {diff_class}">
                {r.get('percentage_diff', 0):+.1f}% | 
                Fadakka: <span class="gold">${r.get('fadakka_index', 0):.2f}</span> | 
                {r.get('status', 'N/A')}
            </div>"""
        
        # Add dividend info if available
        if 'dividend' in r and r['dividend']:
            div = r['dividend']
            results_html += f"""
            <div style="font-size:10px;color:#888;margin-top:3px">
                Div: {div.get('dividend_yield', 'N/A')}% | 
                Annual: ${div.get('annual_dividend', 0):.3f} | 
                Grade: {div.get('dividend_grade', 'N/A')}
            </div>"""
        
        # Add interest rate if available
        if 'interest_rate_diff' in r and r['interest_rate_diff']:
            rate = r['interest_rate_diff']
            results_html += f"""
            <div style="font-size:10px;color:#888;margin-top:3px">
                Base: {rate['base_rate']}% | Quote: {rate['quote_rate']}% | 
                Diff: {rate['rate_diff']:+.2f}% | Carry: {rate['carry_direction']}
            </div>"""
        
        results_html += "</div>"
    
    return render_template_string(HTML, summary=summary_html, results=results_html)

@app.route('/scan')
def scan():
    global cached_results
    results = engine.analyze_all()
    if results:
        engine.save_results(results)
        cached_results = results
        return "<h2 style='color:#33cc33;text-align:center;padding:20px'>Scan Complete!<br><a href='/' style='color:#fff'>View Results</a></h2>"
    return "<h2 style='color:#ff3333;text-align:center;padding:20px'>Scan Failed<br><a href='/' style='color:#fff'>Go Back</a></h2>"

if __name__ == '__main__':
    # Try loading saved data first
    saved = engine.load_results()
    if saved:
        cached_results = saved
        print(f"Loaded {len(saved)} cached results")
    else:
        print("No cached data found. Run a scan first.")
    
    print("\nOpen on your phone: http://YOUR_IP:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)