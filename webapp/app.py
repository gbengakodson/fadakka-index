from flask import Flask, render_template_string, jsonify
import sys, os

sys.path.insert(0, os.getcwd())
from services.fadakka_engine import FadakkaEngine

app = Flask(__name__)
engine = FadakkaEngine()

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="theme-color" content="#0a0a0f">
    <title>Fadakka Index</title>
    <style>
        :root {
            --bg: #0a0a0f; --card: #151520; --gold: #e6b800;
            --green: #33cc33; --red: #ff3333; --text: #fff; --muted: #888; --border: #222233;
        }
        * { margin:0; padding:0; box-sizing:border-box; }
        body { background:var(--bg); color:var(--text); font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif; min-height:100vh; padding-bottom:80px; }
        .header { background:linear-gradient(180deg,#111118,var(--bg)); padding:20px 16px 16px; text-align:center; position:sticky; top:0; z-index:100; border-bottom:2px solid var(--gold); }
        .header h1 { color:var(--gold); font-size:20px; letter-spacing:1px; }
        .header .sub { color:var(--muted); font-size:10px; margin-top:3px; }
        
        .sentiment { margin:12px 10px 0; padding:12px; background:var(--card); border-radius:10px; display:flex; justify-content:space-around; flex-wrap:wrap; gap:6px; }
        .sent-item { text-align:center; }
        .sent-val { font-size:20px; font-weight:bold; }
        .sent-lbl { font-size:9px; color:var(--muted); text-transform:uppercase; }
        
        .controls { display:flex; gap:6px; padding:10px; position:sticky; top:100px; z-index:99; background:var(--bg); }
        .controls select { flex:1; padding:10px; background:var(--card); color:var(--text); border:1px solid var(--border); border-radius:8px; font-size:13px; outline:none; }
        .controls button { padding:10px 14px; border:none; border-radius:8px; font-size:13px; font-weight:bold; cursor:pointer; }
        .btn-outline { background:var(--card); color:var(--text); border:1px solid var(--border); }
        .btn-gold { background:var(--gold); color:var(--bg); position:relative; overflow:hidden; }
        
        /* Animated scan loader */
        .btn-gold.scanning { pointer-events:none; }
        .btn-gold.scanning::after {
            content:''; position:absolute; top:0; left:-100%; width:100%; height:100%;
            background:linear-gradient(90deg,transparent,rgba(255,255,255,0.3),transparent);
            animation:scanPulse 1.5s infinite;
        }
        @keyframes scanPulse {
            0% { left:-100%; }
            100% { left:100%; }
        }
        .scan-spinner { display:none; width:16px; height:16px; border:2px solid var(--bg); border-top-color:transparent; border-radius:50%; animation:spin 0.8s linear infinite; margin-right:6px; vertical-align:middle; }
        .scanning .scan-spinner { display:inline-block; }
        @keyframes spin { to { transform:rotate(360deg); } }
        
        .card { background:var(--card); margin:12px 10px; padding:14px; border-radius:10px; border-left:4px solid var(--border); }
        .card.cheap { border-left-color:var(--green); }
        .card.expensive { border-left-color:var(--red); }
        .card-top { display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:8px; }
        .symbol { font-weight:600; font-size:14px; }
        .type-tag { font-size:8px; background:var(--bg); padding:2px 6px; border-radius:3px; color:var(--muted); margin-left:5px; }
        .price { font-weight:bold; font-size:14px; }
        .fi-row { display:flex; justify-content:space-between; font-size:11px; color:var(--muted); margin-bottom:4px; }
        .gold { color:var(--gold); }
        
        .diff-row { display:flex; justify-content:space-between; align-items:center; padding-top:6px; border-top:1px solid var(--border); }
        .diff-badge { padding:3px 8px; border-radius:5px; font-size:11px; font-weight:bold; }
        .diff-badge.cheap { background:rgba(51,204,51,0.15); color:var(--green); }
        .diff-badge.expensive { background:rgba(255,51,51,0.15); color:var(--red); }
        .diff-bar { flex:1; height:3px; background:var(--border); border-radius:2px; margin:0 8px; overflow:hidden; }
        .diff-bar-fill { height:100%; border-radius:2px; }
        .diff-bar-fill.cheap { background:var(--green); }
        .diff-bar-fill.expensive { background:var(--red); }
        
        .mini-chart { width:100%; height:75px; margin-top:8px; border-radius:4px; display:block; }
        
        .extra { font-size:9px; color:var(--muted); margin-top:4px; display:flex; gap:8px; flex-wrap:wrap; }
        .rec { display:inline-block; padding:2px 7px; border-radius:4px; font-size:9px; font-weight:bold; }
        .rec-strong-buy,.rec-STRONG-BUY,.rec-STRONG_BUY { background:rgba(0,255,0,0.2); color:#0f0; }
        .rec-buy,.rec-BUY { background:rgba(51,204,51,0.15); color:#3c3; }
        .rec-accumulate,.rec-ACCUMULATE { background:rgba(153,204,51,0.15); color:#9c3; }
        .rec-watch,.rec-WATCH { background:rgba(204,204,51,0.15); color:#cc3; }
        .rec-hold,.rec-HOLD { background:rgba(204,170,51,0.15); color:#ca3; }
        .rec-reduce,.rec-REDUCE { background:rgba(255,153,51,0.15); color:#f93; }
        .rec-sell,.rec-SELL { background:rgba(255,51,51,0.15); color:#f33; }
        .rec-strong-sell,.rec-STRONG-SELL,.rec-STRONG_SELL { background:rgba(255,0,0,0.2); color:#f00; }
        .rec-cheap,.rec-expensive { background:rgba(255,255,255,0.05); color:var(--muted); }
        
        .trade-links { display:flex; gap:8px; margin-top:8px; padding-top:8px; border-top:1px solid var(--border); }
        .trade-links a { color:var(--muted); text-decoration:none; background:rgba(255,255,255,0.05); padding:5px 10px; border-radius:5px; font-size:10px; display:flex; align-items:center; gap:4px; transition:all 0.2s; }
        .trade-links a:hover { background:rgba(255,255,255,0.1); color:#fff; }
        
        .pages { display:flex; justify-content:center; gap:3px; padding:12px; flex-wrap:wrap; }
        .pages button { padding:7px 11px; border:1px solid var(--border); background:var(--card); color:var(--text); border-radius:6px; font-size:12px; cursor:pointer; min-width:32px; }
        .pages button.on { background:var(--gold); color:var(--bg); font-weight:bold; border-color:var(--gold); }
        
        .bottom-nav { position:fixed; bottom:0; left:0; right:0; background:var(--card); border-top:1px solid var(--border); display:flex; z-index:100; }
        .bottom-nav button { flex:1; padding:10px; border:none; background:none; color:var(--muted); font-size:10px; cursor:pointer; display:flex; flex-direction:column; align-items:center; gap:2px; }
        .bottom-nav .ico { font-size:18px; }
        
        .toast { position:fixed; top:15px; left:50%; transform:translateX(-50%); background:#333; color:#fff; padding:10px 20px; border-radius:8px; z-index:999; display:none; font-size:13px; white-space:nowrap; }
    </style>
</head>
<body>
    <div class="toast" id="toast"></div>
    
    <div class="header">
        <h1>📊 FADAKKA INDEX</h1>
        <div class="sub">99-WEEK EMA MARKET ANALYSIS</div>
    </div>
    
    <div class="sentiment">
        <div class="sent-item"><div class="sent-val" id="total">-</div><div class="sent-lbl">Assets</div></div>
        <div class="sent-item"><div class="sent-val" style="color:var(--green)" id="cheap">-</div><div class="sent-lbl">Cheap</div></div>
        <div class="sent-item"><div class="sent-val" style="color:var(--red)" id="exp">-</div><div class="sent-lbl">Expensive</div></div>
        <div class="sent-item"><div class="sent-val" style="color:var(--gold)" id="sent">-</div><div class="sent-lbl">Sentiment</div></div>
    </div>
    
    <div class="controls">
        <select id="filter" onchange="goPage(0)">
            <option value="all">📋 All Assets</option>
            <option value="Stock">🇺🇸 US Stocks</option>
            <option value="NG Stock">🇳🇬 Nigerian Stocks</option>
            <option value="Currency">💱 Currencies</option>
            <option value="Crypto">₿ Cryptocurrencies</option>
            <option value="Commodity">🏭 Commodities</option>
        </select>
        <button class="btn-outline" onclick="location.reload()">🔄</button>
        <button class="btn-gold" id="scanBtn" onclick="scanMarket()"><span class="scan-spinner"></span>📡</button>
    </div>
    
    <div id="cards"></div>
    <div class="pages" id="pages"></div>
    
    <div class="bottom-nav">
        <button onclick="location.reload()"><span class="ico">📊</span>Dashboard</button>
        <button onclick="scanMarket()"><span class="ico">📡</span>Scan</button>
        <button onclick="shareApp()"><span class="ico">📤</span>Share</button>
        <button onclick="showAbout()"><span class="ico">ℹ️</span>About</button>
    </div>

<script>
var all=[], page=0, per=12;

fetch('/api/data').then(function(r){return r.json()}).then(function(d){
    all=d; updateStats(); goPage(0);
}).catch(function(e){
    document.getElementById('cards').innerHTML='<p style="text-align:center;padding:40px;color:#f33">Error loading data</p>';
});

function updateStats(){
    var cheap=all.filter(function(r){return r.status=='CHEAP'});
    var exp=all.filter(function(r){return r.status=='EXPENSIVE'});
    document.getElementById('total').textContent=all.length;
    document.getElementById('cheap').textContent=cheap.length;
    document.getElementById('exp').textContent=exp.length;
    var s='NEUTRAL',c='var(--gold)';
    if(cheap.length>exp.length*1.3){s='🐻 BEARISH';c='var(--green)';}
    else if(exp.length>cheap.length*1.3){s='🐂 BULLISH';c='var(--red)';}
    document.getElementById('sent').textContent=s;
    document.getElementById('sent').style.color=c;
}

function getTradeLinks(r){
    var t=r.type||'';
    var s=r.symbol;
    var h='';
    
    if(t.indexOf('Stock')>=0||t.indexOf('NG Stock')>=0){
        h+='<a href="https://www.tradingview.com/chart/?symbol='+encodeURIComponent(s)+'" target="_blank">📈 Chart</a>';
        h+='<a href="https://finance.yahoo.com/quote/'+encodeURIComponent(s)+'" target="_blank">💹 Yahoo</a>';
        h+='<a href="https://www.investing.com/search/?q='+encodeURIComponent(s)+'" target="_blank">📊 Invest</a>';
    } else if(t.indexOf('Crypto')>=0){
        var cs=s.replace('-USD','');
        h+='<a href="https://www.tradingview.com/chart/?symbol=COINBASE:'+encodeURIComponent(cs)+'USD" target="_blank">📈 Chart</a>';
        h+='<a href="https://www.binance.com/en/trade/'+encodeURIComponent(cs)+'_USDT" target="_blank">🔶 Trade</a>';
        h+='<a href="https://coinmarketcap.com/currencies/'+encodeURIComponent(cs.toLowerCase())+'" target="_blank">📊 Info</a>';
    } else if(t.indexOf('Currency')>=0){
        var ps=s.replace('=X','');
        h+='<a href="https://www.tradingview.com/chart/?symbol=FX:'+encodeURIComponent(ps)+'" target="_blank">📈 Chart</a>';
        h+='<a href="https://www.investing.com/currencies/'+encodeURIComponent(ps.toLowerCase())+'" target="_blank">💱 Info</a>';
        h+='<a href="https://www.xe.com/currencyconverter/convert/?From='+encodeURIComponent(ps.substring(0,3))+'&To='+encodeURIComponent(ps.substring(3,6))+'" target="_blank">🏦 Convert</a>';
    } else if(t.indexOf('Commodity')>=0){
        var cm=s.replace('=F','');
        h+='<a href="https://www.tradingview.com/chart/?symbol='+encodeURIComponent(s)+'" target="_blank">📈 Chart</a>';
        h+='<a href="https://finance.yahoo.com/quote/'+encodeURIComponent(s)+'" target="_blank">💹 Yahoo</a>';
        h+='<a href="https://www.investing.com/commodities/'+encodeURIComponent(cm.toLowerCase())+'" target="_blank">📊 Invest</a>';
    }
    
    return h?'<div class="trade-links">'+h+'</div>':'';
}

function goPage(p){
    page=p;
    var type=document.getElementById('filter').value;
    var data=type=='all'?all:all.filter(function(r){return r.type&&r.type.indexOf(type)>=0});
    var total=Math.ceil(data.length/per);
    var items=data.slice(page*per,(page+1)*per);
    
    var h='';
    items.forEach(function(r,i){
        var isCheap=r.status=='CHEAP';
        var cls=isCheap?'cheap':'expensive';
        var dc=isCheap?'cheap':'expensive';
        var curr=r.type&&r.type.indexOf('NG')>=0?'₦':'$';
        var rec=r.buy_recommendation||{};
        var act=rec.action||(isCheap?'CHEAP':'EXPENSIVE');
        var rc='rec-'+act.toLowerCase().replace(/[ _]/g,'-');
        
        var extra='';
        if(r.dividend) extra+='<span>💵 Div: '+(r.dividend.dividend_yield||'N/A')+'%</span><span>⭐ '+(r.dividend.dividend_grade||'N/A')+'</span>';
        if(r.interest_rate_diff) extra+='<span>📈 '+(r.interest_rate_diff.rate_diff>0?'+':'')+r.interest_rate_diff.rate_diff+'%</span><span>🔺 Go '+r.interest_rate_diff.carry_direction+'</span>';
        
        var cid='ch'+page+'-'+i;
        
        h+='<div class="card '+cls+'">';
        h+='<div class="card-top"><div><span class="symbol">'+r.symbol+'</span><span class="type-tag">'+r.type+'</span></div><div class="price">'+curr+ (+r.current_price).toFixed(2)+'</div></div>';
        h+='<div class="fi-row"><span>Fadakka: <span class="gold">'+curr+ (+r.fadakka_index).toFixed(2)+'</span></span><span class="rec '+rc+'">'+act+'</span></div>';
        h+='<div class="diff-row"><span class="diff-badge '+dc+'">'+(r.percentage_diff>=0?'+':'')+(+r.percentage_diff).toFixed(1)+'%</span><div class="diff-bar"><div class="diff-bar-fill '+dc+'" style="width:'+Math.min(Math.abs(r.percentage_diff||0),100)+'%"></div></div><span style="font-size:10px">'+r.status+'</span></div>';
        if(extra) h+='<div class="extra">'+extra+'</div>';
        if(rec.message) h+='<div style="font-size:9px;color:var(--muted);margin-top:3px">💡 '+rec.message+'</div>';
        if(r._chart&&r._chart.length>1) h+='<canvas class="mini-chart" id="'+cid+'"></canvas>';
        h+=getTradeLinks(r);
        h+='</div>';
    });
    
    document.getElementById('cards').innerHTML=h||'<p style="text-align:center;padding:40px;color:var(--muted)">No assets</p>';
    
    setTimeout(function(){
        items.forEach(function(r,i){
            if(r._chart&&r._chart.length>1){
                drawChart('ch'+page+'-'+i, r._chart, r.fadakka_index, r.current_price);
            }
        });
    },50);
    
    var pgs='';
    for(var j=0;j<total;j++) pgs+='<button class="'+(j==page?'on':'')+'" onclick="goPage('+j+')">'+(j+1)+'</button>';
    document.getElementById('pages').innerHTML=pgs;
    window.scrollTo(0,0);
}

function drawChart(id, prices, fi, current){
    var c=document.getElementById(id);
    if(!c)return;
    var w=c.parentElement.clientWidth-28;
    var h=75;
    c.width=w; c.height=h;
    var ctx=c.getContext('2d');
    
    var all=prices.concat([fi,current]);
    var min=Math.min.apply(null,all)*0.97;
    var max=Math.max.apply(null,all)*1.03;
    var range=max-min||1;
    
    ctx.fillStyle='#0d0d12';
    ctx.fillRect(0,0,w,h);
    
    var fy=h-((fi-min)/range)*h;
    ctx.strokeStyle='rgba(230,184,0,0.5)';
    ctx.lineWidth=1;
    ctx.setLineDash([4,3]);
    ctx.beginPath(); ctx.moveTo(0,fy); ctx.lineTo(w,fy); ctx.stroke();
    ctx.setLineDash([]);
    
    ctx.strokeStyle='#4da6ff';
    ctx.lineWidth=1.5;
    ctx.beginPath();
    for(var i=0;i<prices.length;i++){
        var x=(i/(prices.length-1))*w;
        var y=h-((prices[i]-min)/range)*h;
        if(i==0)ctx.moveTo(x,y);else ctx.lineTo(x,y);
    }
    ctx.stroke();
    
    var dx=w-5, dy=h-((current-min)/range)*h;
    ctx.fillStyle=current<fi?'#33cc33':'#ff3333';
    ctx.beginPath(); ctx.arc(dx,dy,3.5,0,Math.PI*2); ctx.fill();
}

function scanMarket(){
    var btn=document.getElementById('scanBtn');
    if(btn.classList.contains('scanning')) return;
    
    if(!confirm('Full scan takes 2-5 minutes. Continue?'))return;
    
    btn.classList.add('scanning');
    btn.innerHTML='<span class="scan-spinner"></span> Scanning';
    document.getElementById('cards').innerHTML='<p style="text-align:center;padding:50px;color:var(--gold)"><span style="display:inline-block;width:30px;height:30px;border:3px solid var(--border);border-top-color:var(--gold);border-radius:50%;animation:spin 1s linear infinite;margin-bottom:15px;"></span><br>Scanning 123 assets...<br><small>Please wait...</small></p>';
    
    fetch('/api/scan').then(function(r){return r.json()}).then(function(d){
        btn.classList.remove('scanning');
        btn.innerHTML='<span class="scan-spinner"></span>📡';
        if(d&&d.length>0){all=d;updateStats();goPage(0);toast('✅ '+d.length+' assets scanned');}
        else toast('❌ Scan failed');
    }).catch(function(){
        btn.classList.remove('scanning');
        btn.innerHTML='<span class="scan-spinner"></span>📡';
        toast('❌ Network error');
    });
}

function toast(m){
    var t=document.getElementById('toast');
    t.textContent=m; t.style.display='block';
    setTimeout(function(){t.style.display='none'},3000);
}
function shareApp(){
    if(navigator.share) navigator.share({title:'Fadakka Index',text:'99-Week EMA Market Analysis',url:location.href});
    else toast('📋 '+location.href);
}
function showAbout(){
    alert('📊 Fadakka Index v1.0\\n\\n99-Week EMA Market Analysis\\n\\n📌 123 Assets:\\n• 30 US Stocks\\n• 30 Nigerian Stocks\\n• 30 Currencies\\n• 30 Cryptos\\n• 3 Commodities\\n\\n🔗 Trade links to TradingView, Yahoo Finance, Binance & more');
}
</script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML)

@app.route('/api/data')
def api_data():
    data = engine.load_results()
    return jsonify(data or [])

@app.route('/api/scan')
def api_scan():
    try:
        results = engine.analyze_all()
        if results:
            engine.save_results(results)
        return jsonify(results or [])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/manifest.json')
def manifest():
    return jsonify({
        "name": "Fadakka Index", "short_name": "Fadakka",
        "start_url": "/", "display": "standalone", "orientation": "portrait",
        "background_color": "#0a0a0f", "theme_color": "#e6b800",
        "icons": [{"src":"/icon-192.png","sizes":"192x192","type":"image/png"},{"src":"/icon-512.png","sizes":"512x512","type":"image/png"}]
    })

if __name__ == '__main__':
    saved = engine.load_results()
    print(f"✅ {len(saved) if saved else 0} assets cached")
    print(f"\n📱 http://192.168.0.42:5000\n")
    app.run(host='0.0.0.0', port=5000, debug=False)