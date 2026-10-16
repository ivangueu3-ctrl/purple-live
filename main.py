from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from datetime import datetime, timedelta
import uuid

app = Flask(__name__)
app.secret_key = 'purplelive_secure_2026_final_v1'

# Make current_user available on all pages
@app.context_processor
def inject_current_user():
    username = session.get('user')
    if username and username in users:
        return dict(current_user=users[username])
    return dict(current_user={})

# ========== CONFIG ==========
ADMIN_EMAIL = "ivangueu3@gmail.com"

COIN_PACKS = [
    {"id":1,"coins":100,"bonus":0,"price_gbp":0.30,"name":"Tiny Start 💜"},
    {"id":2,"coins":300,"bonus":50,"price_gbp":1.99,"name":"Little Sparkle ✨"},
    {"id":3,"coins":800,"bonus":200,"price_gbp":4.99,"name":"Bronze Glow 🥉"},
    {"id":4,"coins":1500,"bonus":350,"price_gbp":9.99,"name":"Silver Shine 🥈"},
    {"id":5,"coins":2500,"bonus":600,"price_gbp":15.99,"name":"Golden Gift 🎁"},
    {"id":6,"coins":5000,"bonus":1500,"price_gbp":39.99,"name":"Diamond Star 💎"},
    {"id":7,"coins":30000,"bonus":12000,"price_gbp":99.99,"name":"Royal Crown 👑"},
    {"id":8,"coins":100000,"bonus":60000,"price_gbp":299.99,"name":"Ultimate Legend 🏆"}
]

GIFTS = [
    {"id":1,"emoji":"💜","cost":1,"name":"Purple Heart"},
    {"id":2,"emoji":"🌹","cost":5,"name":"Rose"},
    {"id":3,"emoji":"✨","cost":10,"name":"Sparkle"},
    {"id":4,"emoji":"🎁","cost":25,"name":"Gift Box"},
    {"id":5,"emoji":"💐","cost":50,"name":"Bouquet"},
    {"id":6,"emoji":"🎀","cost":75,"name":"Ribbon"},
    {"id":7,"emoji":"💎","cost":100,"name":"Crystal"},
    {"id":8,"emoji":"👑","cost":250,"name":"Crown"},
    {"id":9,"emoji":"🍰","cost":500,"name":"Sweet Cake"},
    {"id":10,"emoji":"💃","cost":1000,"name":"Microphone"},
    {"id":11,"emoji":"💋","cost":2500,"name":"Diamond Ring"},
    {"id":12,"emoji":"🚀","cost":5000,"name":"Rocket"},
    {"id":13,"emoji":"🌸","cost":1500,"name":"Tropical Flower"},
    {"id":14,"emoji":"🎵","cost":2000,"name":"Music Note"},
    {"id":15,"emoji":"🏩","cost":5000,"name":"House"},
    {"id":16,"emoji":"🎆","cost":10000,"name":"Fireworks"},
    {"id":17,"emoji":"🌈","cost":25000,"name":"Rainbow"},
    {"id":18,"emoji":"🦋","cost":50000,"name":"Butterfly"},
    {"id":19,"emoji":"🔥","cost":100000,"name":"Blazing Fire"},
    {"id":20,"emoji":"🏆","cost":150000,"name":"Golden Trophy"}
]

CALL_RATES_DEFAULT = {
    "first_min": 1000,
    "per_min": 500,
    "host_percent": 70,
    "platform_percent": 30,
    "max_per_min": 2000,
    "min_withdraw_gbp": 20
}

PK_CONFIG = {
    "duration_minutes": 3,
    "win_bonus_coins": 100,
    "participation_bonus": 20
}

# ========== DATA STORAGE ==========
users = {}
host_requests = []
call_logs = []
pk_battles = {}
withdrawals = []
global_host_counter = 1000
public_chat = []
private_chats = {}
busy_hosts = set()
active_calls = {}

# Admin account
users["admin"] = {
    "username":"admin","email":ADMIN_EMAIL,"password":"admin123",
    "coins":999999,"is_host":False,"is_admin":True,"is_verified":True,
    "host_id":None,"host_balance":0.0,"host_request_pending":False,"profile_photo_verified":True,
    "member_since":datetime.now().strftime("%Y-%m-%d"),
    "daily_tasks":{"login_claimed":False,"gifts_sent":0,"gifts_claimed":False,"watch_minutes":0,"watch_claimed":False,"pk_joined":False,"pk_claimed":False}
}

# ========== ROUTES ==========
@app.route('/')
def home():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/signup', methods=['GET','POST'])
def signup():
    if request.method == 'POST':
        u = request.form['username'].strip()
        p = request.form['password']
        email = request.form.get('email','').strip()
        if len(u) < 2:
            return render_template('signup.html', error="Username too short!")
        if u in users:
            return render_template('signup.html', error="Username taken!")
        is_admin = (email == ADMIN_EMAIL)
        users[u] = {
            "username":u,"email":email,"password":p,"coins":100,
            "is_host":False,"is_admin":is_admin,"is_verified":False,
            "host_id":None,"host_balance":0.0,"host_request_pending":False,"profile_photo_verified":True,
            "member_since":datetime.now().strftime("%Y-%m-%d"),
            "daily_tasks":{"login_claimed":False,"gifts_sent":0,"gifts_claimed":False,"watch_minutes":0,"watch_claimed":False,"pk_joined":False,"pk_claimed":False}
        }
        session['user'] = u
        return redirect(url_for('dashboard'))
    return render_template('signup.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        u = request.form['username'].strip()
        p = request.form['password']
        if u in users and users[u]['password'] == p:
            session['user'] = u
            return redirect(url_for('dashboard'))
        return render_template('login.html', error="Wrong login details!")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('home'))

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('home'))
    
    username = session['user']
    
    # Safety check: if user doesn't exist anymore, log them out
    if username not in users:
        session.pop('user', None)
        return redirect(url_for('home'))
    
    current_user = users[username]
    msg = request.args.get('msg', '')
    return render_template('dashboard.html',
        current_user=current_user,
        user=current_user,
        gifts=GIFTS,
        coin_packs=COIN_PACKS,
        call_rates=CALL_RATES_DEFAULT,
        public_chat=public_chat,
        pk_config=PK_CONFIG
    )

@app.route('/send-public-chat', methods=['POST'])
def send_public_chat():
    if 'user' not in session:
        return jsonify({"success":False})
    data = request.get_json()
    msg_text = data.get('message','').strip()
    if not msg_text:
        return jsonify({"success":False})
    public_chat.append({"sender":session['user'],"message":msg_text,"time":datetime.now().strftime("%H:%M")})
    return jsonify({"success":True})

@app.route('/get-public-chat')
def get_public_chat():
    return jsonify({"messages":public_chat[-30:]})

@app.route('/send-private-chat/<target_user>', methods=['POST'])
def send_private_chat(target_user):
    if 'user' not in session:
        return jsonify({"success":False})
    data = request.get_json()
    msg_text = data.get('message','').strip()
    if not msg_text:
        return jsonify({"success":False})
    chat_key = tuple(sorted([session['user'], target_user]))
    if chat_key not in private_chats:
        private_chats[chat_key] = []
    private_chats[chat_key].append({"sender":session['user'],"message":msg_text,"time":datetime.now().strftime("%H:%M")})
    return jsonify({"success":True})

@app.route('/get-private-chat/<target_user>')
def get_private_chat(target_user):
    if 'user' not in session:
        return jsonify({"messages":[]})
    chat_key = tuple(sorted([session['user'], target_user]))
    return jsonify({"messages":private_chats.get(chat_key, [])})

@app.route('/apply-host', methods=['POST'])
def apply_host():
    if 'user' not in session:
        return redirect(url_for('home'))
    u = session['user']
    if users[u]['is_host']:
        return redirect(url_for('dashboard', msg='already_host'))
    if users[u]['host_request_pending']:
        return redirect(url_for('dashboard', msg='pending'))
    users[u]['host_request_pending'] = True
    host_requests.append({"username":u,"time":datetime.now().strftime("%Y-%m-%d %H:%M"),"photo_verified":False})
    return redirect(url_for('dashboard', msg='applied'))

@app.route('/approve-host/<name>')
def approve_host(name):
    if 'user' not in session or not users[session['user']].get('is_admin'):
        return redirect(url_for('dashboard'))
    global global_host_counter
    users[name]['is_host'] = True
    users[name]['is_verified'] = True
    users[name]['host_id'] = f"H-{global_host_counter}"
    global_host_counter += 1
    users[name]['host_request_pending'] = False
    return redirect(url_for('admin'))

@app.route('/reject-host/<name>')
def reject_host(name):
    if 'user' not in session or not users[session['user']].get('is_admin'):
        return redirect(url_for('dashboard'))
    users[name]['host_request_pending'] = False
    return redirect(url_for('admin'))

@app.route('/update-call-rates', methods=['POST'])
def update_call_rates():
    if 'user' not in session or not users[session['user']].get('is_host'):
        return jsonify({"success":False})
    data = request.get_json()
    new_per_min = int(data.get('per_min', CALL_RATES_DEFAULT['per_min']))
    new_per_min = max(CALL_RATES_DEFAULT['first_min'], min(new_per_min, CALL_RATES_DEFAULT['max_per_min']))
    return jsonify({"success":True,"new_rate":new_per_min})

@app.route('/search-host')
def search_host():
    if 'user' not in session:
        return redirect(url_for('home'))
    hid = request.args.get('host_id','').strip()
    if not hid:
        return render_template('search.html')
    found = None
    for u in users:
        if users[u].get('host_id') == hid and users[u].get('is_verified'):
            found = users[u]
            break
    if found:
        return redirect(url_for('public_profile', username=found['username']))
    return redirect(url_for('dashboard', msg='host_not_found'))

@app.route('/profile/<username>')
def profile(username):
    if 'user' not in session:
        return redirect(url_for('home'))
    if username not in users:
        return redirect(url_for('dashboard'))
    return render_template('profile.html', viewer=users[session['user']], user=users[username])

@app.route('/admin')
def admin():
    if 'user' not in session or not users[session['user']].get('is_admin'):
        return redirect(url_for('dashboard'))
    return render_template('admin.html', users=users, requests=host_requests, withdrawals=withdrawals, admin_email=ADMIN_EMAIL)

@app.route('/call-logs')
def call_logs():
    if 'user' not in session or not users[session['user']].get('is_admin'):
        return redirect(url_for('dashboard'))
    return render_template('call_logs.html', logs=call_logs)

@app.route('/notifications')
def notifications():
    return render_template('notifications.html')

@app.route('/leaderboard')
def leaderboard():
    return render_template('leaderboard.html')

@app.route('/public-profile/<username>')
def public_profile(username):
    if username not in users:
        return redirect(url_for('dashboard'))
    return render_template('public_profile.html', host=users[username])

@app.route('/buy-coins', methods=['POST'])
def buy_coins():
    if 'user' not in session:
        return redirect(url_for('home'))
    pid = int(request.form['pack_id'])
    for p in COIN_PACKS:
        if p['id'] == pid:
            users[session['user']]['coins'] += p['coins'] + p['bonus']
            break
    return redirect(url_for('dashboard', msg='coins_bought'))

@app.route('/send-gift', methods=['POST'])
def send_gift():
    if 'user' not in session:
        return jsonify({"success":False,"error":"Login first"})
    data = request.get_json()
    gid = int(data.get('gift_id'))
    target = data.get('to_user')
    if target == session['user']:
        return jsonify({"success":False,"error":"Cannot gift to yourself!"})
    gift = next((g for g in GIFTS if g['id'] == gid), None)
    if not gift:
        return jsonify({"success":False,"error":"Gift not found"})
    if users[session['user']]['coins'] < gift['cost']:
        return jsonify({"success":False,"error":"Not enough coins!"})
    
    users[session['user']]['coins'] -= gift['cost']
    users[target]['coins'] += gift['cost']
    users[session['user']]['daily_tasks']['gifts_sent'] += 1
    
    share = gift['cost'] * CALL_RATES_DEFAULT['host_percent'] // 100
    if users[target].get('is_host'):
        users[target]['host_balance'] += share
    
    return jsonify({"success":True,"new_coins":users[session['user']]['coins'],"gift":gift})

@app.route('/claim-task', methods=['POST'])
def claim_task():
    if 'user' not in session:
        return jsonify({"success":False})
    u = users[session['user']]
    tid = request.get_json().get('task_id')
    if not u['is_host'] and tid != 'login':
        return jsonify({"success":False,"error":"Only hosts can claim this task"})
    
    if tid == 'login' and not u['daily_tasks']['login_claimed']:
        u['coins'] += 10; u['daily_tasks']['login_claimed'] = True
        return jsonify({"success":True,"coins":u['coins']})
    
    if tid == 'gifts' and u['is_host'] and u['daily_tasks']['gifts_sent'] >= 3 and not u['daily_tasks']['gifts_claimed']:
        u['coins'] += 20; u['daily_tasks']['gifts_claimed'] = True
        return jsonify({"success":True,"coins":u['coins']})
    
    if tid == 'watch' and u['is_host'] and u['daily_tasks']['watch_minutes'] >= 10 and not u['daily_tasks']['watch_claimed']:
        u['coins'] += 15; u['daily_tasks']['watch_claimed'] = True
        return jsonify({"success":True,"coins":u['coins']})
    
    if tid == 'pk' and u['is_host'] and pk_battles.get('joined') and not u['daily_tasks']['pk_claimed']:
        u['coins'] += PK_CONFIG['participation_bonus']; u['daily_tasks']['pk_claimed'] = True
        return jsonify({"success":True,"coins":u['coins']})
    
    return jsonify({"success":False})

# ========== PRIVATE CALL SYSTEM ==========
@app.route('/request-private-call', methods=['POST'])
def request_private_call():
    if 'user' not in session:
        return jsonify({"success":False})
    data = request.get_json()
    target_user = data.get('host_username','').strip()
    if not target_user or target_user not in users:
        return jsonify({"success":False,"error":"Host not found"})
    if not users[target_user].get('is_host'):
        return jsonify({"success":False,"error":"Not a host"})
    if target_user in busy_hosts:
        return jsonify({"success":False,"error":"Host is busy on another call"})
    
    call_id = str(uuid.uuid4())[:8]
    active_calls[call_id] = {
        "viewer": session['user'],
        "host": target_user,
        "status": "pending",
        "minutes": 0,
        "total_charged": 0,
        "rates": CALL_RATES_DEFAULT,
        "started_at": None
    }
    return jsonify({"success":True,"call_id":call_id,"first_min_cost":CALL_RATES_DEFAULT['first_min']})

@app.route('/accept-private-call', methods=['POST'])
def accept_private_call():
    if 'user' not in session:
        return jsonify({"success":False})
    data = request.get_json()
    call_id = data.get('call_id','')
    if call_id not in active_calls:
        return jsonify({"success":False})
    call = active_calls[call_id]
    if call['host'] != session['user']:
        return jsonify({"success":False})
    
    call['status'] = 'active'
    call['started_at'] = datetime.now()
    busy_hosts.add(call['host'])
    return jsonify({"success":True,"next_min_cost":call['rates']['per_min']})

@app.route('/decline-private-call', methods=['POST'])
def decline_private_call():
    if 'user' not in session:
        return jsonify({"success":False})
    data = request.get_json()
    call_id = data.get('call_id','')
    if call_id not in active_calls:
        return jsonify({"success":False})
    call = active_calls[call_id]
    busy_hosts.discard(call['host'])
    del active_calls[call_id]
    return jsonify({"success":True})

@app.route('/end-private-call', methods=['POST'])
def end_private_call():
    if 'user' not in session:
        return jsonify({"success":False})
    data = request.get_json()
    call_id = data.get('call_id','')
    if call_id not in active_calls:
        return jsonify({"success":False})
    
    call = active_calls[call_id]
    call['status'] = 'ended'
    call['minutes'] = 1
    call_logs.append({
        "id": call_id,
        "viewer": call['viewer'],
        "host": call['host'],
        "started_at": call['started_at'].strftime("%Y-%m-%d %H:%M") if call['started_at'] else None,
        "minutes": call['minutes'],
        "total_charged": call['rates']['first_min'],
        "status": "completed",
        "video_record_path": f"/records/{call_id}.mp4"
    })
    busy_hosts.discard(call['host'])
    del active_calls[call_id]
    return jsonify({"success":True})

@app.route('/check-call-status/<call_id>')
def check_call_status(call_id):
    if call_id in active_calls:
        return jsonify({"exists":True,"status":active_calls[call_id]['status']})
    return jsonify({"exists":False})

@app.route('/host-pending-calls')
def host_pending_calls():
    if 'user' not in session:
        return jsonify({"calls":[]})
    pending = [{"call_id":cid,"viewer":c['viewer']} for cid,c in active_calls.items() if c['host']==session['user'] and c['status']=='pending']
    return jsonify({"calls":pending})

@app.route('/withdraw', methods=['POST'])
def withdraw():
    if 'user' not in session:
        return redirect(url_for('home'))
    u = users[session['user']]
    if not u.get('is_host'):
        return redirect(url_for('dashboard', msg='not_host'))
    
    amount = float(request.form.get('amount',0))
    if amount < CALL_RATES_DEFAULT['min_withdraw_gbp']:
        return redirect(url_for('dashboard', msg='min_withdraw'))
    if amount > u['host_balance']:
        return redirect(url_for('dashboard', msg='insufficient_balance'))
    
    u['host_balance'] -= amount
    withdrawals.append({
        "username":session['user'],
        "amount":amount,
        "time":datetime.now().strftime("%Y-%m-%d %H:%M"),
        "status":"pending"
    })
    return redirect(url_for('dashboard', msg='withdraw_submitted'))

@app.route('/approve-withdrawal/<int:idx>')
def approve_withdrawal(idx):
    if 'user' not in session or not users[session['user']].get('is_admin'):
        return redirect(url_for('dashboard'))
    if 0 <= idx < len(withdrawals):
        withdrawals[idx]['status'] = 'paid'
    return redirect(url_for('admin'))

# PK BATTLE
@app.route('/start-pk', methods=['POST'])
def start_pk():
    if 'user' not in session or not users[session['user']].get('is_host'):
        return jsonify({"success":False})
    pk_battles['joined'] = True
    return jsonify({"success":True})

if __name__ == '__main__':
    print("💜 PurpleLive — running!")
    app.run(host='0.0.0.0', port=5000, debug=True)
