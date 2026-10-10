from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from datetime import datetime
import uuid

app = Flask(__name__)
app.secret_key = 'purplelive_secure_2026_final_v1'

# ========= CONFIG — YOUR SETTINGS =========
ADMIN_EMAIL = "ivangueu3@gmail.com"
COIN_PACKS = [
    {"id":1,"coins":100,"bonus":0,"price_gbp":0.30,"name":"Tiny Start 💜"},
    {"id":2,"coins":300,"bonus":30,"price_gbp":1.99,"name":"Little Sparkle ✨"},
    {"id":3,"coins":500,"bonus":80,"price_gbp":3.99,"name":"Bronze Glow 🥉"},
    {"id":4,"coins":1000,"bonus":200,"price_gbp":6.99,"name":"Silver Shine 🥈"},
    {"id":5,"coins":1500,"bonus":350,"price_gbp":9.99,"name":"Perfect Value 💫"},
    {"id":6,"coins":2500,"bonus":600,"price_gbp":14.99,"name":"Popular Choice 🔥"},
    {"id":7,"coins":5000,"bonus":1500,"price_gbp":23.99,"name":"Golden Gift 🥇"},
    {"id":8,"coins":8000,"bonus":2500,"price_gbp":30.99,"name":"Premium 💎"},
    {"id":9,"coins":15000,"bonus":5000,"price_gbp":55.99,"name":"Platinum 👑"},
    {"id":10,"coins":30000,"bonus":12000,"price_gbp":99.99,"name":"Diamond Star ⭐"},
    {"id":11,"coins":50000,"bonus":25000,"price_gbp":125.99,"name":"Royal Crown 🌟"},
    {"id":12,"coins":100000,"bonus":60000,"price_gbp":399.99,"name":"Ultimate Legend 🏆"}
]

GIFTS = [
    {"id":1,"emoji":"💜","cost":1,"name":"Purple Heart"},
    {"id":2,"emoji":"🌹","cost":2,"name":"Rose"},
    {"id":3,"emoji":"✨","cost":5,"name":"Sparkle"},
    {"id":4,"emoji":"🎁","cost":10,"name":"Gift Box"},
    {"id":5,"emoji":"💐","cost":25,"name":"Bouquet"},
    {"id":6,"emoji":"⭐","cost":40,"name":"Glowing Star"},
    {"id":7,"emoji":"💎","cost":75,"name":"Crystal"},
    {"id":8,"emoji":"🎀","cost":100,"name":"Ribbon Bow"},
    {"id":9,"emoji":"👑","cost":150,"name":"Crown"},
    {"id":10,"emoji":"🎂","cost":200,"name":"Sweet Cake"},
    {"id":11,"emoji":"🎤","cost":300,"name":"Microphone"},
    {"id":12,"emoji":"💍","cost":500,"name":"Diamond Ring"},
    {"id":13,"emoji":"🚀","cost":1000,"name":"Rocket"},
    {"id":14,"emoji":"🌺","cost":1500,"name":"Tropical Flower"},
    {"id":15,"emoji":"💃","cost":2000,"name":"Dancer"},
    {"id":16,"emoji":"🌙","cost":3000,"name":"Moon"},
    {"id":17,"emoji":"☀️","cost":5000,"name":"Sun"},
    {"id":18,"emoji":"🌈","cost":7500,"name":"Rainbow"},
    {"id":19,"emoji":"🔥","cost":10000,"name":"Blazing Fire"},
    {"id":20,"emoji":"🏆","cost":15000,"name":"Golden Trophy"}
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

# ========= DATA STORAGE =========
users = {}
host_requests = []
call_logs = []
pk_battles = []
withdrawals = []
host_counter = 1001
public_chat = []
active_calls = {}
private_chats = {}
busy_hosts = set()

# ADMIN — YOUR EMAIL
users['admin'] = {
    "username":"admin","email":ADMIN_EMAIL,"password":"admin123","coins":999999,
    "is_admin":True,"is_host":True,"is_verified":True,
    "host_id":"HP-ADMIN","host_balance":0.00,
    "host_request_pending":False,"profile_photo_verified":True,
    "call_rates": CALL_RATES_DEFAULT.copy(),
    "member_since":datetime.now().strftime("%Y-%m-%d %H:%M"),
    "daily_tasks":{"login_claimed":False,"gifts_sent":0,"gifts_claimed":False,"watch_minutes":0,"watch_claimed":False,"pk_joined":False,"pk_claimed":False}
}

# ========= ROUTES =========
@app.route('/')
def home():
    if 'user' in session: return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/signup', methods=['GET','POST'])
def signup():
    if request.method == 'POST':
        u = request.form['username'].strip()
        p = request.form['password']
        email = request.form.get('email','').strip()
        if len(u) < 2: return render_template('signup.html', error="Username too short!")
        if u in users: return render_template('signup.html', error="Username taken!")
        is_admin = (email == ADMIN_EMAIL)
        users[u] = {
            "username":u,"email":email,"password":p,"coins":1000,
            "is_admin":is_admin,"is_host":False,"is_verified":False,
            "host_id":None,"host_balance":0.00,"host_request_pending":False,
            "profile_photo_verified":False,"call_rates": CALL_RATES_DEFAULT.copy(),
            "member_since":datetime.now().strftime("%Y-%m-%d %H:%M"),
            "daily_tasks":{"login_claimed":False,"gifts_sent":0,"gifts_claimed":False,"watch_minutes":0,"watch_claimed":False,"pk_joined":False,"pk_claimed":False}
        }
        session['user'] = u
        return redirect(url_for('dashboard'))
    return render_template('Signup.html')

@app.route('/login', methods=['POST'])
def login():
    u = request.form['username'].strip()
    p = request.form['password']
    if u in users and users[u]['password'] == p:
        session['user'] = u
        users[u]['daily_tasks']['login_claimed'] = True
        users[u]['coins'] += 10
        return redirect(url_for('dashboard'))
    return render_template('login.html', error="❌ Wrong login details!")

@app.route('/logout')
def logout():
    session.pop('user',None)
    return redirect(url_for('home'))

@app.route('/dashboard')
def dashboard():
    if 'user' not in session: return redirect(url_for('home'))
    current_user = users[session['user']]
    msg = request.args.get('msg','')
    return render_template('dashboard.html',
        user=current_user, gifts=GIFTS, packs=COIN_PACKS,
        msg=msg, call_rates=current_user['call_rates'],
        public_chat=public_chat[-30:], pk_config=PK_CONFIG)

@app.route('/send-public-chat', methods=['POST'])
def send_public_chat():
    if 'user' not in session: return jsonify({"success":False})
    data = request.get_json()
    msg_text = data.get('message','').strip()
    if not msg_text: return jsonify({"success":False})
    public_chat.append({"sender":session['user'],"message":msg_text,"time":datetime.now().strftime("%H:%M")})
    return jsonify({"success":True})

@app.route('/get-public-chat')
def get_public_chat():
    return jsonify({"messages":public_chat[-30:]})

@app.route('/send-private-chat', methods=['POST'])
def send_private_chat():
    if 'user' not in session: return jsonify({"success":False})
    data = request.get_json()
    target = data.get('to_user','')
    msg_text = data.get('message','').strip()
    if not target or not msg_text: return jsonify({"success":False})
    chat_key = tuple(sorted([session['user'], target]))
    if chat_key not in private_chats: private_chats[chat_key] = []
    private_chats[chat_key].append({"sender":session['user'],"message":msg_text,"time":datetime.now().strftime("%H:%M")})
    return jsonify({"success":True})

@app.route('/get-private-chat/<target_user>')
def get_private_chat(target_user):
    if 'user' not in session: return jsonify({"messages":[]})
    return jsonify({"messages":private_chats.get(tuple(sorted([session['user'], target_user])), [])})

@app.route('/apply-host', methods=['POST'])
def apply_host():
    if 'user' not in session: return redirect(url_for('home'))
    u = session['user']
    if users[u]['is_host']: return redirect(url_for('dashboard',msg='already_host'))
    if users[u]['host_request_pending']: return redirect(url_for('dashboard',msg='pending'))
    users[u]['host_request_pending'] = True
    host_requests.append({"username":u,"time":datetime.now().strftime("%Y-%m-%d %H:%M"),"status":"pending","photo_verified":False})
    return redirect(url_for('dashboard',msg='applied'))

@app.route('/approve-host/<name>')
def approve_host(name):
    if 'user' not in session or not users[session['user']].get('is_admin'): return redirect(url_for('dashboard'))
    global host_counter
    users[name]['is_host'] = True
    users[name]['is_verified'] = True
    users[name]['profile_photo_verified'] = True
    users[name]['host_id'] = f"HP-{host_counter}"
    host_counter += 1
    users[name]['host_request_pending'] = False
    return redirect(url_for('admin'))

@app.route('/reject-host/<name>')
def reject_host(name):
    if 'user' not in session or not users[session['user']].get('is_admin'): return redirect(url_for('dashboard'))
    users[name]['host_request_pending'] = False
    return redirect(url_for('admin'))

@app.route('/update-call-rates', methods=['POST'])
def update_call_rates():
    if 'user' not in session or not users[session['user']].get('is_host'): return jsonify({"success":False})
    u = users[session['user']]
    data = request.get_json()
    new_per_min = int(data.get('per_min', CALL_RATES_DEFAULT['per_min']))
    if new_per_min > CALL_RATES_DEFAULT['max_per_min']:
        return jsonify({"success":False,"error":f"Cannot exceed {CALL_RATES_DEFAULT['max_per_min']} coins/min"})
    u['call_rates']['per_min'] = new_per_min
    return jsonify({"success":True,"new_rate":new_per_min})

@app.route('/search-host')
def search_host():
    if 'user' not in session: return redirect(url_for('home'))
    hid = request.args.get('host_id','').strip()
    if not hid: return redirect(url_for('dashboard'))
    found = next((u for u in users.values() if u.get('host_id')==hid and u.get('is_verified')), None)
    if found: return redirect(url_for('profile',username=found['username']))
    return redirect(url_for('dashboard',msg='host_not_found'))

@app.route('/profile/<username>')
def profile(username):
    if 'user' not in session: return redirect(url_for('home'))
    if username not in users: return redirect(url_for('dashboard'))
    return render_template('profile.html',
        host=users[username], viewer=users[session['user']],
        call_rates=users[username]['call_rates'])

@app.route('/admin')
def admin():
    if 'user' not in session or not users[session['user']].get('is_admin'): return redirect(url_for('dashboard'))
    return render_template('admin.html', users=users, requests=host_requests,
        withdrawals=withdrawals, call_logs=call_logs, admin_email=ADMIN_EMAIL)

@app.route('/call_logs')
def call_logs_page():
    if 'user' not in session or not users[session['user']].get('is_admin'): return redirect(url_for('dashboard'))
    return render_template('call_logs.html', call_logs=call_logs)

@app.route('/notifications')
def notifications():
    return render_template('notifications.html')

@app.route('/leaderboard')
def leaderboard():
    return render_template('leaderboard.html')

@app.route('/public_profile/<username>')
def public_profile(username):
    if username not in users: return redirect(url_for('dashboard'))
    return render_template('public_profile.html', host=users[username])

@app.route('/buy-coins', methods=['POST'])
def buy_coins():
    if 'user' not in session: return redirect(url_for('home'))
    pid = int(request.form['pack_id'])
    for p in COIN_PACKS:
        if p['id'] == pid:
            users[session['user']]['coins'] += p['coins'] + p['bonus']
            break
    return redirect(url_for('dashboard',msg='coins_bought'))

@app.route('/send-gift', methods=['POST'])
def send_gift():
    if 'user' not in session: return jsonify({"success":False,"error":"Login first"})
    data = request.get_json()
    gid = int(data['gift_id'])
    target = data.get('to_user','')
    gift = next((g for g in GIFTS if g['id']==gid), None)
    if not gift: return jsonify({"success":False,"error":"Gift not found"})
    if target == session['user']: return jsonify({"success":False,"error":"Cannot gift to yourself!"})
    if users[session['user']]['coins'] < gift['cost']:
        return jsonify({"success":False,"error":"Not enough coins!"})
    
    users[session['user']]['coins'] -= gift['cost']
    users[session['user']]['daily_tasks']['gifts_sent'] += 1
    
    if target in users and users[target].get('is_host'):
        share = gift['cost'] * users[target]['call_rates']['host_percent'] // 100
        users[target]['coins'] += share
        users[target]['host_balance'] += share
    
    return jsonify({"success":True,"new_coins":users[session['user']]['coins'],"gift":gift})

@app.route('/claim-task', methods=['POST'])
def claim_task():
    if 'user' not in session: return jsonify({"success":False})
    data = request.get_json()
    tid = data['task_id']
    u = users[session['user']]
    if not u['is_host'] and tid != 'login':
        return jsonify({"success":False,"error":"Only hosts can claim this task"})
    if tid == 'login' and not u['daily_tasks']['login_claimed']:
        u['coins'] += 10; u['daily_tasks']['login_claimed'] = True
        return jsonify({"success":True,"coins":u['coins']})
    if tid == 'gifts' and u['is_host'] and u['daily_tasks']['gifts_sent'] >= 3 and not u['daily_tasks']['gifts_claimed']:
        u['coins'] += 20; u['daily_tasks']['gifts_claimed'] = True
        return jsonify({"success":True,"coins":u['coins']})
    if tid == 'watch10' and u['is_host'] and u['daily_tasks']['watch_minutes'] >= 10 and not u['daily_tasks']['watch_claimed']:
        u['coins'] += 15; u['daily_tasks']['watch_claimed'] = True
        return jsonify({"success":True,"coins":u['coins']})
    if tid == 'pk' and u['is_host'] and u['daily_tasks']['pk_joined'] and not u['daily_tasks']['pk_claimed']:
        u['coins'] += PK_CONFIG['win_bonus_coins']; u['daily_tasks']['pk_claimed'] = True
        return jsonify({"success":True,"coins":u['coins']})
    return jsonify({"success":False})

# ===== PRIVATE CALL SYSTEM =====
@app.route('/request-private-call', methods=['POST'])
def request_private_call():
    if 'user' not in session: return jsonify({"success":False})
    data = request.get_json()
    host_id = data.get('host_id','').strip()
    host_user = next((name for name, info in users.items() if info.get('host_id')==host_id and info.get('is_verified')), None)
    if not host_user: return jsonify({"success":False,"error":"Host not found"})
    if host_user in busy_hosts: return jsonify({"success":False,"error":"host_busy"})
    rates = users[host_user]['call_rates']
    if users[session['user']]['coins'] < rates['first_min']:
        return jsonify({"success":False,"error":f"Need {rates['first_min']} coins to start"})
    call_id = str(uuid.uuid4())[:8]
    active_calls[call_id] = {
        "viewer":session['user'],"host":host_user,"status":"pending",
        "minutes":0,"total_charged":0,"rates":rates,"started_at":None
    }
    busy_hosts.add(host_user)
    return jsonify({"success":True,"call_id":call_id})

@app.route('/accept-private-call', methods=['POST'])
def accept_private_call():
    if 'user' not in session: return jsonify({"success":False})
    data = request.get_json()
    call_id = data.get('call_id','')
    if call_id not in active_calls or active_calls[call_id]['host'] != session['user']:
        return jsonify({"success":False})
    call = active_calls[call_id]
    viewer = call['viewer']
    rates = call['rates']
    users[viewer]['coins'] -= rates['first_min']
    share = rates['first_min'] * rates['host_percent'] // 100
    users[session['user']]['coins'] += share
    users[session['user']]['host_balance'] += share
    call['status'] = 'active'; call['started_at'] = datetime.now().strftime("%Y-%m-%d %H:%M")
    call['minutes'] = 1; call['total_charged'] = rates['first_min']
    call_logs.append({
        "id":call_id,"viewer":viewer,"host":session['user'],
        "started_at":call['started_at'],"minutes":1,"total_charged":rates['first_min'],
        "per_min_rate":rates['per_min'],"status":"active",
        "video_recorded":True,"record_path":f"records/{call_id}.mp4"
    })
    return jsonify({"success":True,"next_min_cost":rates['per_min']})

@app.route('/decline-private-call', methods=['POST'])
def decline_private_call():
    if 'user' not in session: return jsonify({"success":False})
    data = request.get_json()
    call_id = data.get('call_id','')
    if call_id in active_calls:
        host = active_calls[call_id]['host']
        if host in busy_hosts: busy_hosts.remove(host)
        del active_calls[call_id]
    return jsonify({"success":True})

@app.route('/end-private-call', methods=['POST'])
def end_private_call():
    if 'user' not in session: return jsonify({"success":False})
    data = request.get_json()
    call_id = data.get('call_id','')
    if call_id in active_calls:
        host = active_calls[call_id]['host']
        if host in busy_hosts: busy_hosts.remove(host)
        del active_calls[call_id]
    return jsonify({"success":True})

@app.route('/check-call-status/<call_id>')
def check_call_status(call_id):
    if call_id in active_calls:
        return jsonify({"exists":True,"status":active_calls[call_id]['status']})
    return jsonify({"exists":False})

@app.route('/host-pending-calls')
def host_pending_calls():
    if 'user' not in session: return jsonify({"calls":[]})
    pending = [{"call_id":cid,"viewer":c['viewer']} for cid,c in active_calls.items() if c['host']==session['user'] and c['status']=='pending']
    return jsonify({"calls":pending})

@app.route('/withdraw', methods=['POST'])
def withdraw():
    if 'user' not in session: return redirect(url_for('home'))
    u = users[session['user']]
    if not u.get('is_host'): return redirect(url_for('dashboard',msg='not_host'))
    amount = float(request.form.get('amount',0))
    if amount < u['call_rates']['min_withdraw_gbp']: return redirect(url_for('dashboard',msg='min_withdraw'))
    if amount > u['host_balance']: return redirect(url_for('dashboard',msg='insufficient_balance'))
    u['host_balance'] -= amount
    withdrawals.append({"user":session['user'],"amount_gbp":amount,"time":datetime.now().strftime("%Y-%m-%d %H:%M"),"status":"pending"})
    return redirect(url_for('dashboard',msg='withdraw_submitted'))

@app.route('/approve-withdraw/<int:idx>')
def approve_withdraw(idx):
    if 'user' not in session or not users[session['user']].get('is_admin'): return redirect(url_for('dashboard'))
    if 0 <= idx < len(withdrawals): withdrawals[idx]['status'] = 'paid'
    return redirect(url_for('admin'))

# PK BATTLE
@app.route('/start-pk', methods=['POST'])
def start_pk():
    if 'user' not in session or not users[session['user']].get('is_host'): return jsonify({"success":False})
    users[session['user']]['daily_tasks']['pk_joined'] = True
    return jsonify({"success":True})

if __name__ == "__main__":
    print("💜 PurpleLive → http://127.0.0.1:8888")
    app.run(host='0.0.0.0', port=8888, debug=True)
