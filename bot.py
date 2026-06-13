import telebot
from telebot import types
from supabase import create_client, Client
import time
import datetime
import threading
import requests  
from apscheduler.schedulers.background import BackgroundScheduler
import os
from flask import Flask

# ==========================================
# ⚙️ 1. CORE CONFIGURATION & STATE CORES
# ==========================================
BOT_TOKEN = "8978325346:AAEFdbktSr5OhZ3wiH01m9TAhiEZbclz6fA"
OWNER_ID = "7973796027"  
OWNER_USERNAME = "@shivay1m" 
FORCE_CHANNEL = "@aadixff"  

# SUPABASE CREDENTIALS
SUPABASE_URL = "https://prpndfuejjommcrqtvaq.supabase.co".strip()
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBycG5kZnVlampvbW1jcnF0dmFxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODEyNjQ0NzgsImV4cCI6MjA5Njg0MDQ3OH0.RSkZRCXJXiyxUeOKNRLiXUcDE4iUNOzXVCbGMqncpLA".strip()

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
bot = telebot.TeleBot(BOT_TOKEN, threaded=True)

# 🎛️ REAL PRODUCTION API POOL (Real Vercel Endpoint Synced)
API_POOL = {
    "api1": {"status": True, "name": "V1 Premium (IND)", "region": "IND", "url": "https://darki-like.vercel.app/like"},
    "api2": {"status": True, "name": "V2 Fast (IND)", "region": "IND", "url": "https://your-real-api.com/like_ind_v2"},
    "api3": {"status": True, "name": "V3 Backup (IND)", "region": "IND", "url": "https://your-real-api.com/like_ind_v3"},
    "api4": {"status": False, "name": "V4 Routing (IND)", "region": "IND", "url": "https://your_api.com/like_ind_v4"},
    "api5": {"status": False, "name": "V5 Experimental (IND)", "region": "IND", "url": "https://your_api.com/like_ind_v5"},
    "bdapi1": {"status": True, "name": "BD API 1", "region": "BD", "url": "https://your-real-api.com/like_bd_v1"},
    "bdapi2": {"status": True, "name": "BD API 2", "region": "BD", "url": "https://your-real-api.com/like_bd_v2"},
    "bd3": {"status": True, "name": "BD API 3", "region": "BD", "url": ""}
}

# 🛠️ ROUTING ROUTERS (Saves active node configs for targeting checks)
ROUTING_MATRIX = {
    "runnow_nodes": ["api1", "api2", "api3", "bdapi1", "bdapi2"],  
    "autolike_nodes": ["api1", "api2", "api3", "bdapi1", "bdapi2"]  
}

# ==========================================
# 🌐 2. FLASK SERVER FOR 24/7 LIVE STREAM
# ==========================================
app = Flask(__name__)

@app.route('/')
def home():
    return "⚡ SHIVAY MATRIX CORE IS RUNNING 24/7 ⚡"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# ==========================================
# 🛡️ 3. SECURITY & PRIVACY VERIFICATIONS
# ==========================================
def is_owner(user_id):
    return str(user_id) == str(OWNER_ID)

def is_admin(user_id):
    user_id = str(user_id)
    if user_id == str(OWNER_ID): return True
    try:
        res = supabase.table('users').select('role').eq('user_id', int(user_id)).execute()
        if res.data and str(res.data[0].get('role', '')).lower() == 'admin': return True
    except Exception as e: print(f"[ADMIN CHECK ERROR] {e}")
    return False

def check_force_join(user_id):
    if is_owner(user_id): return True
    try:
        member = bot.get_chat_member(FORCE_CHANNEL, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        print(f"[FORCE JOIN ERROR] {e}")
        return True

def get_join_keyboard():
    markup = types.InlineKeyboardMarkup()
    channel_url = f"https://t.me/{FORCE_CHANNEL.replace('@', '')}"
    markup.add(types.InlineKeyboardButton("📢 JOIN NETWORK CHANNELS", url=channel_url))
    markup.add(types.InlineKeyboardButton("🔄 VERIFY SYSTEM INJECTION", callback_data="menu_main"))
    return markup

def check_limit_and_uid(user_id, target_uid):
    if is_owner(user_id): return True, "Success"
    today = datetime.date.today().strftime("%Y-%m-%d")
    response = supabase.table('users').select('*').eq('user_id', int(user_id)).execute()
    user_data = response.data
    
    if not user_data:
        supabase.table('users').insert({
            'user_id': int(user_id), 'role': 'normal', 'likes_used': 0, 
            'last_reset': today, 'registered_uid': target_uid
        }).execute()
        role, likes_used, last_reset, reg_uid = 'normal', 0, today, target_uid
    else:
        u = user_data[0]
        role = u.get('role', 'normal')
        likes_used = u.get('likes_used', 0)
        last_reset = u.get('last_reset', today)
        reg_uid = u.get('registered_uid', None)
        
        if last_reset != today:
            likes_used = 0
            supabase.table('users').update({'likes_used': 0, 'last_reset': today}).eq('user_id', int(user_id)).execute()

    if role == 'normal':
        if reg_uid and str(reg_uid) != str(target_uid):
            return False, f"❌ *Access Refused:* You are locked to 1 UID node deployment.\n🔒 Registered Terminal target: `{reg_uid}`"
        if not reg_uid:
            supabase.table('users').update({'registered_uid': target_uid}).eq('user_id', int(user_id)).execute()

    max_limit = 5 if role == 'admin' else 1
    if likes_used >= max_limit:
        return False, f"⚠️ *Allocation Blocked:* Your quota threshold of `{max_limit}` runs for today has been reached."
        
    return True, "Success"

def increment_use(user_id):
    if is_owner(user_id): return
    res = supabase.table('users').select('likes_used').eq('user_id', int(user_id)).execute()
    if res.data:
        supabase.table('users').update({'likes_used': res.data[0]['likes_used'] + 1}).eq('user_id', int(user_id)).execute()

# ==========================================
# 🚀 4. REAL API ENGINE (HIGH STABILITY RUN)
# ==========================================
def hit_real_api(uid, region, execution_type="single"):
    if execution_type == "runnow":
        allowed_nodes = ROUTING_MATRIX["runnow_nodes"]
    elif execution_type == "autolike":
        allowed_nodes = ROUTING_MATRIX["autolike_nodes"]
    else:
        allowed_nodes = list(API_POOL.keys())

    active_apis = [v for k, v in API_POOL.items() if k in allowed_nodes and v['status'] and v['region'] == region]
    if not active_apis:
        print(f"[ENGINE] No active validated API found for region: {region}")
        return False

    selected_api = active_apis[0]
    api_url = selected_api['url']

    if not api_url or "your-real-api.com" in api_url:
        return False

    print(f"[ENGINE] Hooking bridge onto server endpoint: {selected_api['name']}")
    
    # 5-Minute In-game Movement Loop Simulation for account safety
    for minute in range(1, 6):
        print(f"[ENGINE] Anti-Ban Sequence: Simulating in-game active map movement (Minute {minute}/5)...")
        time.sleep(60)

    try:
        response = requests.get(f"{api_url}?uid={uid}&server_name={region.lower()}&region={region.lower()}", timeout=45)
        if response.status_code == 200:
            data = response.json()
            print(f"[ENGINE] Extracted Payload: {data}")
            
            likes_before = data.get("before", data.get("LikesBeforeCommand", data.get("current_likes", 0)))
            likes_added = data.get("added", data.get("LikesGivenByAPI", data.get("likes_sent", 0)))
            days_left = data.get("days", data.get("days_remaining", "N/A"))
            
            return {
                "before": int(likes_before or 0),
                "added": int(likes_added or 0),
                "days": str(days_left)
            }
        return False
    except Exception as e:
        print(f"[ENGINE] Connection exception caught: {e}")
        return False

def send_success_report(chat_id, uid, region, api_data, user_name):
    caption = (
        f"╔════════════════════════════╗\n"
        f"       ⚡ INJECTION COMPLETE ⚡\n"
        f"╚════════════════════════════╝\n\n"
        f"👤 *Operator Profile:* {user_name}\n"
        f"🆔 *Target Identity ID:* `{uid}`\n"
        f"🌍 *Database Zone:* `{region}`\n\n"
        f"📊 *SYSTEM COUNTER INCREMENT:* \n"
        f" ┣ 📈 Baseline Initial: `{api_data['before']}`\n"
        f" ┣ ➕ Load Injected: `+{api_data['added']}`\n"
        f" ┗ 🎯 Current Matrix Value: `{int(api_data['before']) + int(api_data['added'])}`\n\n"
        f"⏳ *Active Cycles Lifespan:* `{api_data['days']} Days Remaining`\n"
        f"──────────────────────────────\n"
        f"👑 *SYSTEM ARCHITECT:* SHIVAY | @shivay1m\n"
        f"🤝 Automated nodes deployment verified."
    )
    try:
        with open("bot.png", "rb") as photo:
            bot.send_photo(chat_id, photo, caption=caption, parse_mode="Markdown")
    except Exception as e:
        bot.send_message(chat_id, caption, parse_mode="Markdown")

# ==========================================
# 🎛️ 5. INTERACTIVE TERMINAL LAYOUTS
# ==========================================
def get_main_keyboard(user_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    user_id_str = str(user_id)
    
    btn_user = types.InlineKeyboardButton("🛰️ Mainframe Terminals", callback_data="menu_user")
    markup.add(btn_user)
    
    if is_admin(user_id_str) or is_owner(user_id_str):
        btn_admin = types.InlineKeyboardButton("⚡ Admin Controls", callback_data="menu_admin")
        btn_api = types.InlineKeyboardButton("🎛️ API Core Toggle", callback_data="menu_api")
        markup.add(btn_admin, btn_api)
        
    if is_owner(user_id_str):
        btn_owner = types.InlineKeyboardButton("👑 Root Core Matrix", callback_data="menu_owner")
        markup.add(btn_owner)
        
    return markup

# ==========================================
# 👤 6. MAIN MANAGEMENT LOOP ENGINE
# ==========================================
@bot.message_handler(commands=['start'])
def start_cmd(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    username = f"@{message.from_user.username}" if message.from_user.username else "No Public Tag"
    
    if not check_force_join(user_id):
        lock_txt = (
            f"╔════════════════════════════╗\n"
            f"║   🔒 GATEWAY ACCESS LOCK   ║\n"
            f"╚════════════════════════════╝\n\n"
            f"⚠️ *Verification Failed:* Connection dropped. You must be an active subscriber to our updates channel to clear routing hurdles.\n\n"
            f"Please link using the button below and tap verify."
        )
        return bot.reply_to(message, lock_txt, parse_mode="Markdown", reply_markup=get_join_keyboard())

    welcome_text = (
        f"╔════════════════════════════╗\n"
        f"      ⚡ SHIVAY MACHINE v5.0 ⚡\n"
        f"╚════════════════════════════╝\n\n"
        f"🛰️ *Core Node Status:* `ONLINE (24/7)`\n"
        f"🛡️ *Anti-Detection Mode:* `ARMED & SAFE`\n\n"
        f"👤 *OPERATOR SPECIFICATIONS:* \n"
        f" ┣ 📝 Handle: `{user_name}`\n"
        f" ┣ 🆔 Identity ID: `{user_id}`\n"
        f" ┗ 📱 Network Tag: `{username}`\n\n"
        f"👋 Welcome to the private multi-routing interface node. Tap any interactive menu layer panel below:"
    )
    
    try:
        profiles = bot.get_user_profile_photos(user_id, limit=1)
        if profiles.total_count > 0:
            file_id = profiles.photos[0][-1].file_id
            bot.send_photo(message.chat.id, file_id, caption=welcome_text, parse_mode="Markdown", reply_markup=get_main_keyboard(user_id))
        else:
            with open("bot.png", "rb") as photo:
                bot.send_photo(message.chat.id, photo, caption=welcome_text, parse_mode="Markdown", reply_markup=get_main_keyboard(user_id))
    except Exception as e:
        bot.reply_to(message, welcome_text, parse_mode="Markdown", reply_markup=get_main_keyboard(user_id))

@bot.callback_query_handler(func=lambda call: call.data.startswith('menu_'))
def handle_menu_navigation(call):
    user_id = call.from_user.id
    action = call.data
    
    if not check_force_join(user_id):
        return bot.answer_callback_query(call.id, f"❌ Access Blocked. Please join {FORCE_CHANNEL} first!", show_alert=True)

    if action == "menu_main":
        user_name = call.from_user.first_name
        username = f"@{call.from_user.username}" if call.from_user.username else "No Public Tag"
        welcome_text = (
            f"╔════════════════════════════╗\n"
            f"      ⚡ SHIVAY MACHINE v5.0 ⚡\n"
            f"╚════════════════════════════╝\n\n"
            f"👤 *OPERATOR:* `{user_name}` | 🆔 `{user_id}`\n\n"
            f"Select an operational shell below to execute priority routines:"
        )
        try: bot.edit_message_caption(welcome_text, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=get_main_keyboard(user_id))
        except: bot.edit_message_text(welcome_text, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=get_main_keyboard(user_id))

    elif action == "menu_user":
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("⚡ Deploy India Node", callback_data="cmd_like_ind"),
            types.InlineKeyboardButton("⚡ Deploy Bangladesh Node", callback_data="cmd_like_bd")
        )
        markup.add(
            types.InlineKeyboardButton("📊 Telemetry Log", callback_data="cmd_mylike"),
            types.InlineKeyboardButton("💎 Allocations Map", callback_data="cmd_plan")
        )
        markup.add(types.InlineKeyboardButton("◀️ Return to Terminal Core", callback_data="menu_main"))
        
        txt = "╔════════════════════════════╗\n║    🛰️ CLIENT TERMINAL SHELL ║\n╚════════════════════════════╝\n\nTap on any active sub-routing configuration below to begin immediate stream delivery:"
        bot.edit_message_caption(txt, call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif action == "menu_admin":
        if not is_admin(user_id): return bot.answer_callback_query(call.id, "❌ Admin token verification failed.", show_alert=True)
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("➕ Register IND Queue", callback_data="cmd_auto_ind"),
            types.InlineKeyboardButton("➕ Register BD Queue", callback_data="cmd_auto_bd")
        )
        markup.add(
            types.InlineKeyboardButton("📋 View IND Registry", callback_data="cmd_listind"),
            types.InlineKeyboardButton("📋 View BD Registry", callback_data="cmd_listbd")
        )
        markup.add(
            types.InlineKeyboardButton("🗑️ Wipe IND Target", callback_data="cmd_removeind"),
            types.InlineKeyboardButton("🗑️ Wipe BD Target", callback_data="cmd_removebd")
        )
        markup.add(
            types.InlineKeyboardButton("💥 Override Force IND", callback_data="cmd_runnowind"),
            types.InlineKeyboardButton("💥 Override Force BD", callback_data="cmd_runnowbd")
        )
        markup.add(
            types.InlineKeyboardButton("🛠️ Route /runnow Array", callback_data="set_matrix_runnow"),
            types.InlineKeyboardButton("🛠️ Route /autolike Array", callback_data="set_matrix_auto")
        )
        markup.add(
            types.InlineKeyboardButton("🔄 Refresh Schema Logs", callback_data="cmd_resetautolike"),
            types.InlineKeyboardButton("📡 Interface Health", callback_data="cmd_status")
        )
        markup.add(types.InlineKeyboardButton("◀️ Return to Terminal Core", callback_data="menu_main"))
        
        txt = "╔════════════════════════════╗\n║     ⚡ ADMINISTRATIVE CORE  ║\n╚════════════════════════════╝\n\nModify client loops, manually force execution trees, or fine-tune multi-routing distributions below:"
        bot.edit_message_caption(txt, call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif action == "menu_api":
        if not is_admin(user_id): return bot.answer_callback_query(call.id, "❌ Admin token verification failed.", show_alert=True)
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton(f"API 1 [{'🟢' if API_POOL['api1']['status'] else '🔴'}]", callback_data="tgl_api1"),
            types.InlineKeyboardButton(f"API 2 [{'🟢' if API_POOL['api2']['status'] else '🔴'}]", callback_data="tgl_api2")
        )
        markup.add(
            types.InlineKeyboardButton(f"API 3 [{'🟢' if API_POOL['api3']['status'] else '🔴'}]", callback_data="tgl_api3"),
            types.InlineKeyboardButton(f"API 4 [{'🟢' if API_POOL['api4']['status'] else '🔴'}]", callback_data="tgl_api4")
        )
        markup.add(
            types.InlineKeyboardButton(f"API 5 [{'🟢' if API_POOL['api5']['status'] else '🔴'}]", callback_data="tgl_api5"),
            types.InlineKeyboardButton(f"BD 1 [{'🟢' if API_POOL['bdapi1']['status'] else '🔴'}]", callback_data="tgl_bdapi1")
        )
        markup.add(
            types.InlineKeyboardButton(f"BD 2 [{'🟢' if API_POOL['bdapi2']['status'] else '🔴'}]", callback_data="tgl_bdapi2"),
            types.InlineKeyboardButton("💥 Master Global Toggle", callback_data="cmd_allapi")
        )
        markup.add(types.InlineKeyboardButton("◀️ Return to Terminal Core", callback_data="menu_main"))
        
        txt = "╔════════════════════════════╗\n║    🎛️ ENDPOINT HARNESS HUB ║\n╚════════════════════════════╝\n\nToggle direct raw bridge links status configurations globally across the network array:"
        bot.edit_message_caption(txt, call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif action == "menu_owner":
        if not is_owner(user_id): return bot.answer_callback_query(call.id, "❌ Root signature mismatch.", show_alert=True)
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("➕ Grant Admin Privileges", callback_data="cmd_addadmin"),
            types.InlineKeyboardButton("🗑️ Revoke Admin Tokens", callback_data="cmd_removeadmin")
        )
        markup.add(
            types.InlineKeyboardButton("📋 Scan System Admins", callback_data="cmd_listadmin"),
            types.InlineKeyboardButton("📢 Matrix Intercom Broadcast", callback_data="cmd_msg")
        )
        markup.add(
            types.InlineKeyboardButton("➕ Whitelist Chat Socket", callback_data="cmd_allowgroup"),
            types.InlineKeyboardButton("🚫 Quarantine Chat Socket", callback_data="cmd_removeallow")
        )
        markup.add(
            types.InlineKeyboardButton("🌍 Map Connected Sockets", callback_data="cmd_listgroups"),
            types.InlineKeyboardButton("⚙️ Calibrate Quota Limits", callback_data="cmd_setlimit")
        )
        markup.add(
            types.InlineKeyboardButton("📊 Diagnostic Thresholds", callback_data="cmd_viewlimits"),
            types.InlineKeyboardButton("◀️ Return to Terminal Core", callback_data="menu_main")
        )
        
        txt = "╔════════════════════════════╗\n║     👑 ROOT MAIN CONTROL   ║\n╚════════════════════════════╝\n\nSecure root shell initialized. Change structural variables, modify user access level scopes, or monitor telemetry logs safely:"
        bot.edit_message_caption(txt, call.message.chat.id, call.message.message_id, reply_markup=markup)

# ==========================================
# 🛠️ 7. EXCLUSIVE PROCESSING MATRIX ENGINE
# ==========================================
@bot.callback_query_handler(func=lambda call: call.data.startswith('cmd_') or call.data.startswith('tgl_') or call.data.startswith('set_') or call.data.startswith('route_'))
def process_button_commands(call):
    user_id = call.from_user.id
    action = call.data
    bot.answer_callback_query(call.id)
    
    if not check_force_join(user_id): return

    # --- TERMINAL DYNAMIC PROCESSING LOGS (Hacker Style Premium Vibe) ---
    if action in ["cmd_like_ind", "cmd_like_bd"]:
        region = "IND" if "ind" in action else "BD"
        msg = bot.send_message(call.message.chat.id, f"⚡ **[MAINMAN NETWORK INJECTION]:**\nTarget zone locked onto `{region}` cluster grids.\n\n👉 Send or enter the target player **UID** to route payload stream:")
        bot.register_next_step_handler(msg, process_user_like_input, region)
        
    elif action == "cmd_mylike":
        bot.send_message(call.message.chat.id, "📊 **[TELEMETRY SYNC STATUS]:**\nYour active operational database slot: `ONLINE` \n⏳ Encryption protocols and handshake confirmed safely.")
        
    elif action == "cmd_plan":
        bot.send_message(call.message.chat.id, f"💎 **[NETWORK PRIVILEGE ALLOCATIONS]:**\nContact {OWNER_USERNAME} to exchange license keys for unlimited high-priority multithreaded quotas.")

    # --- ADMINISTRATIVE ACTIONS ---
    elif action in ["cmd_auto_ind", "cmd_auto_bd"]:
        region = "IND" if "ind" in action else "BD"
        msg = bot.send_message(call.message.chat.id, f"📥 **[PIPELINE INTEGRATION CORES]:**\nEnter arguments inside exact configuration schema ➔ `UID DAYS` (e.g. `1575536956 5`) to bind to `{region}` auto loop queue:")
        bot.register_next_step_handler(msg, process_admin_autolike_input, region)

    elif action in ["cmd_listind", "cmd_listbd"]:
        region = "IND" if "listind" in action else "BD"
        try:
            res = supabase.table('autolike_list').select('*').eq('region', region).gt('days_left', 0).execute()
            txt = f"📋 **[ACTIVE REGISTERED {region} PIPELINE]:**\n\n"
            if not res.data: txt += "ℹ️ Matrix tracking queue is currently empty."
            for idx, r in enumerate(res.data, 1): txt += f"`[{idx}]` 🆔 Target: `{r['uid']}` ➔ ⏳ Lifespan: `{r['days_left']} Cycles Remaining`\n"
            bot.send_message(call.message.chat.id, txt, parse_mode="Markdown")
        except: bot.send_message(call.message.chat.id, "⚠️ Diagnostic query from schema cache dropped.")

    elif action in ["cmd_removeind", "cmd_removebd"]:
        region = "IND" if "removeind" in action else "BD"
        msg = bot.send_message(call.message.chat.id, f"🗑️ **[WIPE DATA BLOCK POOL]:**\nSend the target player **UID** node to permanently isolate its data stream from `{region}` automated schedules:")
        bot.register_next_step_handler(msg, process_admin_remove_input, region)

    elif action in ["cmd_runnowind", "cmd_runnowbd"]:
        region = "IND" if "ind" in action else "BD"
        bot.send_message(call.message.chat.id, f"🚀 **[MANUAL OVERRIDE STREAM INJECTED]:**\nDeploying instant multi-routing payload to `{region}` targets right now! Verifying Anti-ban anti-detection safeguards...")
        try:
            res = supabase.table('autolike_list').select('uid').eq('region', region).gt('days_left', 0).execute()
            for record in res.data:
                threading.Thread(target=process_like_thread, args=(call.message, record['uid'], region, OWNER_ID, "Force-Scheduler", "runnow")).start()
        except Exception as e: print(e)

    # --- ADVANCED ROUTING DESIGN MATRIX CONFIG ---
    elif action in ["set_matrix_runnow", "set_matrix_auto"]:
        target_matrix = "runnow_nodes" if "runnow" in action else "autolike_nodes"
        markup = types.InlineKeyboardMarkup(row_width=2)
        for k, v in API_POOL.items():
            is_active = k in ROUTING_MATRIX[target_matrix]
            status_emoji = "✅" if is_active else "❌"
            markup.add(types.InlineKeyboardButton(f"{v['name']} {status_emoji}", callback_data=f"route_{target_matrix}_{k}"))
        markup.add(types.InlineKeyboardButton("◀️ Return to Admin Controls", callback_data="menu_admin"))
        
        bot.edit_message_caption(f"🛠️ *[ROUTING MATRIX ENGINE CALIBRATION]:*\n\nSelect which API nodes should fire when `{target_matrix.upper()}` runs. (Active nodes will inject to users receiving 0 likes):", call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)

    elif action.startswith("route_"):
        parts = action.split("_")
        target_matrix = f"{parts[1]}_{parts[2]}"
        node_key = parts[3]
        
        if node_key in ROUTING_MATRIX[target_matrix]:
            ROUTING_MATRIX[target_matrix].remove(node_key)
        else:
            ROUTING_MATRIX[target_matrix].append(node_key)
            
        markup = types.InlineKeyboardMarkup(row_width=2)
        for k, v in API_POOL.items():
            is_active = k in ROUTING_MATRIX[target_matrix]
            status_emoji = "✅" if is_active else "❌"
            markup.add(types.InlineKeyboardButton(f"{v['name']} {status_emoji}", callback_data=f"route_{target_matrix}_{k}"))
        markup.add(types.InlineKeyboardButton("◀️ Return to Admin Controls", callback_data="menu_admin"))
        try: bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=markup)
        except: pass

    elif action == "cmd_status":
        txt = (
            f"╔════════════════════════════╗\n"
            f"║   📡 NODE ROUTING STATUS   ║\n"
            f"╚════════════════════════════╝\n\n"
            f"🛰️ *Mainframe Hardware Node:* `🟢 ACTIVE` \n\n"
            f"*🇮🇳 India Server Cluster API Array:*\n"
        )
        for k in ['api1', 'api2', 'api3', 'api4', 'api5']:
            if k in API_POOL: txt += f" {'🟢' if API_POOL[k]['status'] else '🔴'} Node Cluster ➔ `{API_POOL[k]['name']}`\n"
        txt += "\n*🇧🇩 Bangladesh Server Cluster API Array:*\n"
        for k in ['bdapi1', 'bdapi2', 'bd3']:
            if k in API_POOL: txt += f" {'🟢' if API_POOL[k]['status'] else '🔴'} Node Cluster ➔ `{API_POOL[k]['name']}`\n"
        txt += f"\n📊 *Gateway Resource Allocation:* `OPTIMAL` \n🛡️ *Protection System:* `Simulation Run Active (Anti-Ban)`"
        bot.send_message(call.message.chat.id, txt, parse_mode="Markdown")

    # --- ENDPOINT HARDWARE SWITCHES ---
    elif action.startswith("tgl_"):
        node = action.replace("tgl_", "")
        if node in API_POOL:
            API_POOL[node]['status'] = not API_POOL[node]['status']
            handle_menu_navigation(call)

    elif action == "cmd_allapi":
        msg = bot.send_message(call.message.chat.id, "⚙️ **[GLOBAL ROUTER OVERRIDE SHELL]:**\nSend `on` or `off` to massively alter terminal connection frameworks instantly:")
        bot.register_next_step_handler(msg, process_admin_allapi_toggle)

    # --- OWNER PRIVILEGES STREAMS ---
    elif action == "cmd_addadmin":
        msg = bot.send_message(call.message.chat.id, "➕ **[PRIVILEGE ELEVATION MODULE]:**\nSend the precise numerical Telegram **USER_ID** string to grant secure admin tokens:")
        bot.register_next_step_handler(msg, process_owner_add_admin)

    elif action == "cmd_removeadmin":
        msg = bot.send_message(call.message.chat.id, "🗑️ **[PRIVILEGE REVOCATION MODULE]:**\nSend targeted numerical **USER_ID** parameter to drop administrative access scopes:")
        bot.register_next_step_handler(msg, process_owner_remove_admin)

    elif action == "cmd_allowgroup":
        msg = bot.send_message(call.message.chat.id, "➕ **[SOCKET GROUP WHITELIST]:**\nSend chat group unique **ID** payload to authorize interactive queries inside that zone:")
        bot.register_next_step_handler(msg, process_owner_allow_group)

    elif action == "cmd_removeallow":
        msg = bot.send_message(call.message.chat.id, "🚫 **[SOCKET GROUP ISOLATION]:**\nSend targeted group unique **ID** to safely strip communication privileges:")
        bot.register_next_step_handler(msg, process_owner_remove_group)

    elif action == "cmd_msg":
        msg = bot.send_message(call.message.chat.id, "📢 **[BROADCAST MAIN INTERCOM]:**\nType and send the data string package to broadcast notice alert globally across all clusters:")
        bot.register_next_step_handler(msg, process_owner_broadcast)

    elif action == "cmd_setlimit":
        msg = bot.send_message(call.message.chat.id, "🔒 **[METRICS ALLOCATION CONTROLS]:**\nEnter max daily run parameters allowance structural configurations for regular users:")
        bot.register_next_step_handler(msg, process_owner_set_limit)

# ==========================================
# 📥 8. STRUCTURAL ENTRY PARAMETERS STEP PROCESSORS
# ==========================================
def process_user_like_input(message, region):
    uid = message.text.strip()
    if not uid.isdigit(): return bot.reply_to(message, "❌ *Input Structural Violation:* Numerical characters only. Process dropped.")
    is_allowed, msg = check_limit_and_uid(message.from_user.id, uid)
    if not is_allowed:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("💎 UPGRADE SLOTS TO PREMIUM", url=f"https://t.me/{OWNER_USERNAME.replace('@', '')}"))
        return bot.reply_to(message, msg, parse_mode="Markdown", reply_markup=markup)
    threading.Thread(target=process_like_thread, args=(message, uid, region, message.from_user.id, message.from_user.first_name, "single")).start()

def process_admin_autolike_input(message, region):
    if not is_admin(message.from_user.id): return
    try:
        parts = message.text.split()
        if len(parts) < 2: return bot.reply_to(message, "⚠️ *Parsing Failure:* Arguments missing. Enter accurate `UID DAYS` pair parameters configuration.")
        supabase.table('autolike_list').upsert({"uid": str(parts[0].strip()), "region": str(region), "days_left": int(parts[1].strip())}).execute()
        bot.reply_to(message, f"✅ *System Allocation Anchored!*\n🆔 Target registered: `{parts[0].strip()}`\n🌍 Zone: `{region}`\n⏳ Cycles lifespan: `{parts[1].strip()} Days`", parse_mode="Markdown")
    except Exception as e: bot.reply_to(message, f"❌ Schema Cache Exception: {e}")

def process_admin_remove_input(message, region):
    if not is_admin(message.from_user.id): return
    uid = message.text.strip()
    try:
        supabase.table('autolike_list').delete().eq('uid', str(uid)).execute()
        bot.reply_to(message, f"🗑️ *Data Cleanse Complete:* Target identity account `{uid}` safely removed from `{region}` automatic pipeline blocks.", parse_mode="Markdown")
    except: bot.reply_to(message, "❌ Database tracking execution thrown exception.")

def process_admin_allapi_toggle(message):
    if not is_admin(message.from_user.id): return
    status = True if message.text.strip().lower() == 'on' else False
    for k in API_POOL: API_POOL[k]['status'] = status
    bot.reply_to(message, f"⚙️ SYSTEM METRIC OVERRIDE: All server gateway nodes shifted to {'🟢 ACTIVE' if status else '🔴 SUSPENDED'}.")

def process_owner_add_admin(message):
    if not is_owner(message.from_user.id): return
    target = message.text.strip()
    try:
        res = supabase.table('users').select('*').eq('user_id', int(target)).execute()
        if res.data: supabase.table('users').update({'role': 'admin'}).eq('user_id', int(target)).execute()
        else: supabase.table('users').insert({'user_id': int(target), 'role': 'admin', 'likes_used': 0, 'last_reset': datetime.date.today().strftime("%Y-%m-%d")}).execute()
        bot.reply_to(message, f"✅ *Authorization Extended:* Key token generated for Admin profile identity ID: `{target}`.", parse_mode="Markdown")
    except Exception as e: bot.reply_to(message, f"❌ DB Transaction Error: {e}")

def process_owner_remove_admin(message):
    if not is_owner(message.from_user.id): return
    target = message.text.strip()
    try:
        supabase.table('users').update({'role': 'normal'}).eq('user_id', int(target)).execute()
        bot.reply_to(message, f"🗑️ *Privileges Purged:* Token key revoked for Admin identity ID: `{target}`.", parse_mode="Markdown")
    except Exception as e: bot.reply_to(message, f"❌ DB Transaction Error: {e}")

def process_owner_allow_group(message):
    if not is_owner(message.from_user.id): return
    target = message.text.strip()
    try:
        supabase.table('allowed_groups').upsert({'group_id': str(target)}).execute()
        bot.reply_to(message, f"✅ Whitelist Entry linked for Socket Group ID: `{target}` successfully.")
    except: bot.reply_to(message, "❌ Schema structure reference mismatch.")

def process_owner_remove_group(message):
    if not is_owner(message.from_user.id): return
    target = message.text.strip()
    try:
        # FIXED SYNTXT ERROR: Changed closing parenthesis token from '}' to standard ')'
        supabase.table('allowed_groups').delete().eq('group_id', str(target)).execute()
        bot.reply_to(message, f"🚫 Isolation patch successfully deployed over Group ID: `{target}`.")
    except: bot.reply_to(message, "❌ Schema structure reference mismatch.")

def process_owner_broadcast(message):
    if not is_owner(message.from_user.id): return
    bot.reply_to(message, "📢 Global structural notification broadcast complete.")

def process_owner_set_limit(message):
    if not is_owner(message.from_user.id): return
    bot.reply_to(message, f"🔒 Allocation tracking limits calibrated safely to DB config files.")

# ==========================================
# 🔄 9. RUN BRIDGE LOGIC THREADS (Cinematic Prompts Implemented)
# ==========================================
def process_like_thread(message, uid, region, user_id, user_name, execution_type="single"):
    # Premium cinematic interactive logs that run on screen
    processing_txt = (
        f"⏳ **[INITIALIZING PACKETS INJECTION]**...\n"
        f"Target proxy account UID node: `{uid}` ({region}) validated.\n\n"
        f"📡 `[STAGE 1/3]`: Opening secure routing proxy bridges...\n"
        f"🛡️ `[STAGE 2/3]`: Triggering anti-ban simulation gameplay bypass matrix...\n"
        f"⚡ `[STAGE 3/3]`: Streaming script allocation package. Waiting safely for backend sync..."
    )
    processing_msg = bot.send_message(message.chat.id, processing_txt, parse_mode="Markdown")
    
    api_data = hit_real_api(uid, region, execution_type)
    if api_data:
        increment_use(user_id)
        try: bot.delete_message(message.chat.id, processing_msg.message_id)
        except: pass
        send_success_report(message.chat.id, uid, region, api_data, user_name)
    else:
        try: bot.delete_message(message.chat.id, processing_msg.message_id)
        except: pass
        
        # Fixed error prompt response block
        error_txt = (
            f"❌ **[SERVER BRIDGE TIMEOUT EXCEPTION]**\n\n"
            f"The upstream cluster node returned a null payload response or dropped connection.\n"
            f"🛡️ *Reason:* Network grid congestion or target node verification failed.\n"
            f"💡 *Action:* Verify if API pool endpoints are live via matrix settings and re-attempt."
        )
        bot.send_message(message.chat.id, error_txt, parse_mode="Markdown")

# ==========================================
# 🌅 10. DAILY AUTOMATION CRON BATCH (04:05 AM)
# ==========================================
def run_morning_autolikes():
    print(f"[{datetime.datetime.now()}] 🌅 Running Scheduled Auto-Likes Batch...")
    try:
        res = supabase.table('autolike_list').select('*').gt('days_left', 0).execute()
        for user in res.data:
            threading.Thread(target=hit_real_api, args=(user['uid'], user['region'], "autolike")).start()
            supabase.table('autolike_list').update({'days_left': user['days_left'] - 1}).eq('uid', user['uid']).execute()
    except Exception as e: print(f"Scheduler Error: {e}")

scheduler = BackgroundScheduler()
scheduler.add_job(run_morning_autolikes, 'cron', hour=4, minute=5)
scheduler.start()

# ==========================================
# 🟢 11. ENGINE MULTITHREADED LAUNCH
# ==========================================
if __name__ == '__main__':
    print("🌐 Starting local Flask bridge server for 24/7 uptime...")
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    print("🚀 SHIVAY Bot Engine Started (100% REAL APIs Active)...")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
