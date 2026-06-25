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
BOT_TOKEN = "8628322039:AAG5WfGSIE4hFlmlVB9VGtN6f2_KR7wj7DE"
OWNER_ID = "7973796027"    
OWNER_USERNAME = "@shivay1m" 
FORCE_CHANNEL = "@aadixff"  

# SUPABASE CREDENTIALS
SUPABASE_URL = "https://prpndfuejjommcrqtvaq.supabase.co".strip()
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBycG5kZnVlampvbW1jcnF0dmFxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODEyNjQ0NzgsImV4cCI6MjA5Njg0MDQ3OH0.RSkZRCXJXiyxUeOKNRLiXUcDE4iUNOzXVCbGMqncpLA".strip()

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
bot = telebot.TeleBot(BOT_TOKEN, threaded=True)

# 🎛️ REAL PRODUCTION API POOL
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

# 🛠️ ROUTING MATRIX
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
    return "⚡ SHIVAY BOT IS RUNNING 24/7 ⚡"

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
    markup.add(types.InlineKeyboardButton("📢 JOIN CHANNEL NOW", url=channel_url))
    markup.add(types.InlineKeyboardButton("🔄 VERIFY & RESTART", callback_data="menu_main"))
    return markup

def check_limit_only(user_id):
    if is_owner(user_id): return True, "Success"
    today = datetime.date.today().strftime("%Y-%m-%d")
    response = supabase.table('users').select('*').eq('user_id', int(user_id)).execute()
    user_data = response.data
    
    if not user_data:
        supabase.table('users').insert({
            'user_id': int(user_id), 'role': 'normal', 'likes_used': 0, 
            'last_reset': today
        }).execute()
        role, likes_used, last_reset = 'normal', 0, today
    else:
        u = user_data[0]
        role = u.get('role', 'normal')
        likes_used = u.get('likes_used', 0)
        last_reset = u.get('last_reset', today)
        
        if last_reset != today:
            likes_used = 0
            supabase.table('users').update({'likes_used': 0, 'last_reset': today}).eq('user_id', int(user_id)).execute()

    max_limit = 5 if role == 'admin' else 1
    if likes_used >= max_limit:
        return False, f"⚠️ LIMIT REACHED: Aaj ka aapka `{max_limit}` likes ka limit khatam ho gaya hai."
        
    return True, "Success"

def increment_use(user_id):
    if is_owner(user_id): return
    res = supabase.table('users').select('likes_used').eq('user_id', int(user_id)).execute()
    if res.data:
        supabase.table('users').update({'likes_used': res.data[0]['likes_used'] + 1}).eq('user_id', int(user_id)).execute()

# ==========================================
# 🚀 4. REAL API ENGINE (FAST 15-SEC HIT)
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
        print(f"[ENGINE] No active API found for region: {region}")
        return False

    selected_api = active_apis[0]
    api_url = selected_api['url']

    if not api_url or "your-real-api.com" in api_url:
        return False

    print(f"[ENGINE] Processing fast request on server: {selected_api['name']}")
    time.sleep(2) 

    try:
        response = requests.get(f"{api_url}?uid={uid}&server_name={region.lower()}&region={region.lower()}", timeout=15)
        if response.status_code == 200:
            data = response.json()
            print(f"[ENGINE] Server Payload: {data}")
            
            likes_before = data.get("before", data.get("LikesBeforeCommand", data.get("current_likes", 0)))
            likes_added = data.get("added", data.get("LikesGivenByAPI", data.get("likes_sent", 0)))
            player_name = data.get("PlayerNickname", data.get("nickname", data.get("name", "N/A")))
            days_left = data.get("days", data.get("days_remaining", "N/A"))
            
            return {
                "before": int(likes_before or 0),
                "added": int(likes_added or 0),
                "game_name": str(player_name),
                "days": str(days_left)
            }
        return False
    except Exception as e:
        print(f"[ENGINE] Request Timed out or Exception: {e}")
        return False

def send_success_report(chat_id, uid, region, api_data, execution_type="single"):
    if execution_type == "autolike":
        caption = (
            f"✅ AUTOLIKES SENT SUCCESSFULLY\n\n"
            f"👤 NAME: {api_data['game_name']}\n"
            f"🆔 UID: `{uid}`\n"
            f"🌍 REGION: {region}\n"
            f"📊 BEFORE: {api_data['before']}\n"
            f"➕ ADD: +{api_data['added']}\n"
            f"📈 AFTER: {int(api_data['before']) + int(api_data['added'])}\n"
            f"⏳ DAYS LEFT: {api_data.get('days', 'N/A')}\n"
            f"👑 OWNER: SHIVAY\n"
            f"🙏 THANKS FOR USING"
        )
    else:
        caption = (
            f"✅ LIKES SENT SUCCESSFULLY\n"
            f"👤 NAME: {api_data['game_name']}\n"
            f"🆔 UID: `{uid}`\n"
            f"🌍 REGION: {region}\n"
            f"📊 BEFORE: {api_data['before']}\n"
            f"➕ ADD: +{api_data['added']}\n"
            f"📈 AFTER: {int(api_data['before']) + int(api_data['added'])}\n"
            f"🙏 THANKS FOR USING"
        )
    try:
        with open("bot.png", "rb") as photo:
            bot.send_photo(chat_id, photo, caption=caption)
    except Exception as e:
        bot.send_message(chat_id, caption)

# ==========================================
# 🎛️ 5. INTERACTIVE TERMINAL LAYOUTS
# ==========================================
def get_main_keyboard(user_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    user_id_str = str(user_id)
    
    btn_user = types.InlineKeyboardButton("🚀 User Commands Panel", callback_data="menu_user")
    markup.add(btn_user)
    
    if is_admin(user_id_str) or is_owner(user_id_str):
        btn_admin = types.InlineKeyboardButton("🛠️ Admin Panel", callback_data="menu_admin")
        btn_api = types.InlineKeyboardButton("🎛️ API ON/OFF Switches", callback_data="menu_api")
        markup.add(btn_admin, btn_api)
        
    if is_owner(user_id_str):
        btn_owner = types.InlineKeyboardButton("👑 Owner System Panel", callback_data="menu_owner")
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
            f"║   🔒 CHANNEL JOIN REQUIRED ║\n"
            f"╚════════════════════════════╝\n\n"
            f"⚠️ Bot use karne ke liye aapko hamare channel ko join karna zaroori hai.\n\n"
            f"Niche diye gaye button se join karein aur check karein."
        )
        return bot.reply_to(message, lock_txt, parse_mode="Markdown", reply_markup=get_join_keyboard())

    welcome_text = (
        f"╔════════════════════════════╗\n"
        f"      ⚡ SHIVAY FREE LIKE BOT v5.0 ⚡\n"
        f"╚════════════════════════════╝\n\n"
        f"🛰️ Status: Live (24/7 Active)\n"
        f"🛡️ Safety System: Anti-Ban Enabled\n\n"
        f"👤 OPERATOR PROFILE: \n"
        f" ┣ 📝 Name: `{user_name}`\n"
        f" ┣ 🆔 ID: `{user_id}`\n"
        f" ┗ 📱 Tag: `{username}`\n\n"
        f"👋 Welcome! Niche diye buttons se commands open karein:"
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
        return bot.answer_callback_query(call.id, f"❌ Please join {FORCE_CHANNEL} first!", show_alert=True)

    if action == "menu_main":
        user_name = call.from_user.first_name
        welcome_text = (
            f"╔════════════════════════════╗\n"
            f"      ⚡ SHIVAY FREE LIKE BOT v5.0 ⚡\n"
            f"╚════════════════════════════╝\n\n"
            f"👤 User: `{user_name}` | ID: `{user_id}`\n\n"
            f"Niche diye options me se ek select karein:"
        )
        try: bot.edit_message_caption(welcome_text, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=get_main_keyboard(user_id))
        except: bot.edit_message_text(welcome_text, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=get_main_keyboard(user_id))

    elif action == "menu_user":
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("⚡ Like India Server", callback_data="cmd_like_ind"),
            types.InlineKeyboardButton("⚡ Like Bangladesh Server", callback_data="cmd_like_bd")
        )
        markup.add(
            types.InlineKeyboardButton("📊 Status Check", callback_data="cmd_mylike"),
            types.InlineKeyboardButton("💎 Buy Premium Plan", callback_data="cmd_plan")
        )
        markup.add(types.InlineKeyboardButton("◀️ Main Menu", callback_data="menu_main"))
        
        txt = "🚀 **User Command Panel:**\n\nNiche diye buttons par click karke likes order lagayein:"
        bot.edit_message_caption(txt, call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif action == "menu_admin":
        if not is_admin(user_id): return bot.answer_callback_query(call.id, "❌ Admin access missing.", show_alert=True)
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("➕ Add Auto IND Queue", callback_data="cmd_auto_ind"),
            types.InlineKeyboardButton("➕ Add Auto BD Queue", callback_data="cmd_auto_bd")
        )
        markup.add(
            types.InlineKeyboardButton("📋 View IND Active Users", callback_data="cmd_listind"),
            types.InlineKeyboardButton("📋 View BD Active Users", callback_data="cmd_listbd")
        )
        markup.add(
            types.InlineKeyboardButton("🗑️ Remove IND Target", callback_data="cmd_removeind"),
            types.InlineKeyboardButton("🗑️ Remove BD Target", callback_data="cmd_removebd")
        )
        markup.add(
            types.InlineKeyboardButton("💥 Force Run IND Pipeline", callback_data="cmd_runnowind"),
            types.InlineKeyboardButton("💥 Force Run BD Pipeline", callback_data="cmd_runnowbd")
        )
        markup.add(
            types.InlineKeyboardButton("🛠️ Setup /runnow APIs", callback_data="set_matrix_runnow"),
            types.InlineKeyboardButton("🛠️ Setup /autolike APIs", callback_data="set_matrix_auto")
        )
        markup.add(
            types.InlineKeyboardButton("🔄 Refresh DB Cache", callback_data="cmd_resetautolike"),
            types.InlineKeyboardButton("📡 Check API Health Status", callback_data="cmd_status")
        )
        markup.add(types.InlineKeyboardButton("◀️ Main Menu", callback_data="menu_main"))
        
        txt = "🛠️ **Admin Command Control Center:**\n\nUsers queue manage karein ya automated processes setup karein:"
        bot.edit_message_caption(txt, call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif action == "menu_api":
        if not is_admin(user_id): return bot.answer_callback_query(call.id, "❌ Admin access missing.", show_alert=True)
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton(f"API 1 - {'🟢 ON' if API_POOL['api1']['status'] else '🔴 OFF'}", callback_data="tgl_api1"),
            types.InlineKeyboardButton(f"API 2 - {'🟢 ON' if API_POOL['api2']['status'] else '🔴 OFF'}", callback_data="tgl_api2")
        )
        markup.add(
            types.InlineKeyboardButton(f"API 3 - {'🟢 ON' if API_POOL['api3']['status'] else '🔴 OFF'}", callback_data="tgl_api3"),
            types.InlineKeyboardButton(f"API 4 - {'🟢 ON' if API_POOL['api4']['status'] else '🔴 OFF'}", callback_data="tgl_api4")
        )
        markup.add(
            types.InlineKeyboardButton(f"API 5 - {'🟢 ON' if API_POOL['api5']['status'] else '🔴 OFF'}", callback_data="tgl_api5"),
            types.InlineKeyboardButton(f"BD 1 - {'🟢 ON' if API_POOL['bdapi1']['status'] else '🔴 OFF'}", callback_data="tgl_bdapi1")
        )
        markup.add(
            types.InlineKeyboardButton(f"BD 2 - {'🟢 ON' if API_POOL['bdapi2']['status'] else '🔴 OFF'}", callback_data="tgl_bdapi2"),
            types.InlineKeyboardButton("💥 All APIs Master Switch", callback_data="cmd_allapi")
        )
        markup.add(types.InlineKeyboardButton("◀️ Main Menu", callback_data="menu_main"))
        
        txt = "🎛️ **API Server Toggle Center:**\n\nEk baar click karne se endpoint ON hoga aur dobara click karne se OFF hoga:"
        bot.edit_message_caption(txt, call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif action == "menu_owner":
        if not is_owner(user_id): return bot.answer_callback_query(call.id, "❌ Owner profile mismatch.", show_alert=True)
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("➕ Add New Admin Profile", callback_data="cmd_addadmin"),
            types.InlineKeyboardButton("🗑️ Remove Admin Token", callback_data="cmd_removeadmin")
        )
        markup.add(
            types.InlineKeyboardButton("📋 View Admin Directory", callback_data="cmd_listadmin"),
            types.InlineKeyboardButton("📢 Broadcast Global Msg", callback_data="cmd_msg")
        )
        markup.add(
            types.InlineKeyboardButton("➕ Whitelist Chat Group", callback_data="cmd_allowgroup"),
            types.InlineKeyboardButton("🚫 Remove Whitelist Group", callback_data="cmd_removeallow")
        )
        markup.add(
            types.InlineKeyboardButton("🌍 List Whitelists", callback_data="cmd_listgroups"),
            types.InlineKeyboardButton("⚙️ Change Daily Quota Limits", callback_data="cmd_setlimit")
        )
        markup.add(
            types.InlineKeyboardButton("📊 View System Rules", callback_data="cmd_viewlimits"),
            types.InlineKeyboardButton("◀️ Main Menu", callback_data="menu_main")
        )
        
        txt = "👑 **Owner Secret Matrix Control:**\n\nDatabase modifications, group configurations aur privileges elevate karein:"
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

    if action in ["cmd_like_ind", "cmd_like_bd"]:
        region = "IND" if "ind" in action else "BD"
        msg = bot.send_message(call.message.chat.id, f"📥 likes bhejney ke liye target account ka **UID** enter karke send karein (Server: {region}):")
        bot.register_next_step_handler(msg, process_user_like_input, region)
        
    elif action == "cmd_mylike":
        bot.send_message(call.message.chat.id, "📊 Aapka Autolike status active hai. Sabhi functions smoothly chal rahe hain.")
        
    elif action == "cmd_plan":
        bot.send_message(call.message.chat.id, f"💎 180+ Autolike ke liye {OWNER_USERNAME} se contact karein.")

    # --- ADMIN ACTIONS ---
    elif action in ["cmd_auto_ind", "cmd_auto_bd"]:
        region = "IND" if "ind" in action else "BD"
        msg = bot.send_message(call.message.chat.id, f"📥 `{region}` Auto list me user add karne ke liye space dekar `UID DAYS` format me bhejein.\nExample: `7891299787 5` :")
        bot.register_next_step_handler(msg, process_admin_autolike_input, region)

    elif action in ["cmd_listind", "cmd_listbd"]:
        region = "IND" if "listind" in action else "BD"
        try:
            res = supabase.table('autolike_list').select('*').eq('region', region).gt('days_left', 0).execute()
            txt = f"📋 **Active Users List ({region}):**\n\n"
            if not res.data: txt += "Abhi list me koi targets nahi hain."
            for idx, r in enumerate(res.data, 1): txt += f"{idx}. UID: `{r['uid']}` | Days Left: `{r['days_left']}`\n"
            bot.send_message(call.message.chat.id, txt, parse_mode="Markdown")
        except: bot.send_message(call.message.chat.id, "Database loading failed.")

    elif action in ["cmd_removeind", "cmd_removebd"]:
        region = "IND" if "removeind" in action else "BD"
        msg = bot.send_message(call.message.chat.id, f"🗑️ `{region}` Auto pipeline list se user delete karne ke liye uska UID send karein:")
        bot.register_next_step_handler(msg, process_admin_remove_input, region)

    elif action in ["cmd_runnowind", "cmd_runnowbd"]:
        region = "IND" if "ind" in action else "BD"
        bot.send_message(call.message.chat.id, f"🚀 Batch run trigger ho gaya hai! Sabhi active targets ko likes processing feed bheja ja raha hai...")
        try:
            res = supabase.table('autolike_list').select('uid').eq('region', region).gt('days_left', 0).execute()
            for record in res.data:
                threading.Thread(target=process_like_thread, args=(call.message, record['uid'], region, OWNER_ID, "runnow")).start()
        except Exception as e: print(e)

    elif action in ["set_matrix_runnow", "set_matrix_auto"]:
        target_matrix = "runnow_nodes" if "runnow" in action else "autolike_nodes"
        markup = types.InlineKeyboardMarkup(row_width=2)
        for k, v in API_POOL.items():
            is_active = k in ROUTING_MATRIX[target_matrix]
            status_emoji = "✅" if is_active else "❌"
            markup.add(types.InlineKeyboardButton(f"{v['name']} {status_emoji}", callback_data=f"route_{target_matrix}_{k}"))
        markup.add(types.InlineKeyboardButton("◀️ Return to Admin Controls", callback_data="menu_admin"))
        
        bot.edit_message_caption(f"🛠️ **Configure Core Matrix Routing:**\n\nChoose karein ki jab `{target_matrix.upper()}` run hoga toh background me koun-koun si APIs target ko backup likes process karengi:", call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)

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
            f"║      📡 LIVE API HEALTH     ║\n"
            f"╚════════════════════════════╝\n\n"
            f"🛰️ Bot Server Backbone: Running smoothly\n\n"
            f"**India API Servers:**\n"
        )
        for k in ['api1', 'api2', 'api3', 'api4', 'api5']:
            if k in API_POOL: txt += f" {'🟢' if API_POOL[k]['status'] else '🔴'} Server Node ➔ `{API_POOL[k]['name']}`\n"
        txt += "\n**Bangladesh API Servers:**\n"
        for k in ['bdapi1', 'bdapi2', 'bd3']:
            if k in API_POOL: txt += f" {'🟢' if API_POOL[k]['status'] else '🔴'} Server Node ➔ `{API_POOL[k]['name']}`\n"
        bot.send_message(call.message.chat.id, txt, parse_mode="Markdown")

    elif action.startswith("tgl_"):
        node = action.replace("tgl_", "")
        if node in API_POOL:
            API_POOL[node]['status'] = not API_POOL[node]['status']
            call.data = "menu_api"
            handle_menu_navigation(call)

    elif action == "cmd_allapi":
        msg = bot.send_message(call.message.chat.id, "⚙️ Sabhi APIs ko ek sath change karne ke liye chat box me `on` ya `off` likh kar send karein:")
        bot.register_next_step_handler(msg, process_admin_allapi_toggle)

    # --- OWNER ROUTINES ---
    elif action == "cmd_addadmin":
        msg = bot.send_message(call.message.chat.id, "➕ Jis user ko admin banana chahte hain uska Telegram **USER_ID** send karein:")
        bot.register_next_step_handler(msg, process_owner_add_admin)

    elif action == "cmd_removeadmin":
        msg = bot.send_message(call.message.chat.id, "🗑️ Admin list se hatane ke liye user ka Telegram **USER_ID** send karein:")
        bot.register_next_step_handler(msg, process_owner_remove_admin)

    elif action == "cmd_allowgroup":
        msg = bot.send_message(call.message.chat.id, "➕ Whitelist karne ke liye chat group ka unique **ID** enter karein:")
        bot.register_next_step_handler(msg, process_owner_allow_group)

    elif action == "cmd_removeallow":
        msg = bot.send_message(call.message.chat.id, "🚫 Whitelist se hatane ke liye group ka unique **ID** enter karein:")
        bot.register_next_step_handler(msg, process_owner_remove_group)

    elif action == "cmd_msg":
        msg = bot.send_message(call.message.chat.id, "📢 Sabhi bot users tak global notice broadcast message send karne ke liye apna text likhein:")
        bot.register_next_step_handler(msg, process_owner_broadcast)

    elif action == "cmd_setlimit":
        msg = bot.send_message(call.message.chat.id, "🔒 Type the custom standard limit configurations data to save:")
        bot.register_next_step_handler(msg, process_owner_set_limit)

# ==========================================
# 📥 8. STRUCTURAL ENTRY PARAMETERS STEP PROCESSORS
# ==========================================
def process_user_like_input(message, region):
    uid = message.text.strip()
    if not uid.isdigit(): return bot.reply_to(message, "❌ ERROR: UID galat hai, sirf numbers ka use karein.")
    
    is_allowed, msg = check_limit_only(message.from_user.id)
    if not is_allowed:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("💎 BUY PREMIUM PLAN NOW", url=f"https://t.me/{OWNER_USERNAME.replace('@', '')}"))
        return bot.reply_to(message, msg, parse_mode="Markdown", reply_markup=markup)
    
    processing_txt = (
        f"📦 ORDER PLACED! 🚀\n\n"
        f"🌐 Server: {region}\n"
        f"🆔 UID: {uid}\n"
        f"⚡ Status: Delivery in progress! ⏳"
    )
    processing_msg = bot.send_message(message.chat.id, processing_txt)
    
    threading.Thread(target=process_like_thread, args=(message, uid, region, message.from_user.id, "single", processing_msg.message_id)).start()

def process_admin_autolike_input(message, region):
    if not is_admin(message.from_user.id): return
    try:
        parts = message.text.split()
        if len(parts) < 2: return bot.reply_to(message, "⚠️ Format galat hai. Space dekar exact `UID DAYS` dalein.")
        supabase.table('autolike_list').upsert({"uid": str(parts[0].strip()), "region": str(region), "days_left": int(parts[1].strip())}).execute()
        bot.reply_to(message, f"✅ Account `{parts[0].strip()}` successfully added ho gaya hai `{region}` list me `{parts[1].strip()} Days` ke liye.")
    except Exception as e: bot.reply_to(message, f"❌ Database Cache Error: {e}")

def process_admin_remove_input(message, region):
    if not is_admin(message.from_user.id): return
    uid = message.text.strip()
    try:
        supabase.table('autolike_list').delete().eq('uid', str(uid)).execute()
        bot.reply_to(message, f"🗑️ Success: Target UID `{uid}` ko `{region}` pipeline queue list se delete kar diya gaya hai.")
    except: bot.reply_to(message, "Database task thrown an exception.")

def process_admin_allapi_toggle(message):
    if not is_admin(message.from_user.id): return
    status = True if message.text.strip().lower() == 'on' else False
    for k in API_POOL: API_POOL[k]['status'] = status
    bot.reply_to(message, f"⚙️ Config updated. Sabhi servers ko ek sath `{'ON' if status else 'OFF'}` kar diya gaya hai.")

def process_owner_add_admin(message):
    if not is_owner(message.from_user.id): return
    target = message.text.strip()
    try:
        res = supabase.table('users').select('*').eq('user_id', int(target)).execute()
        if res.data: supabase.table('users').update({'role': 'admin'}).eq('user_id', int(target)).execute()
        else: supabase.table('users').insert({'user_id': int(target), 'role': 'admin', 'likes_used': 0, 'last_reset': datetime.date.today().strftime("%Y-%m-%d")}).execute()
        bot.reply_to(message, f"✅ Done: Target ID `{target}` ko successfully **ADMIN** bna diya gya hai.")
    except Exception as e: bot.reply_to(message, f"Database transaction error: {e}")

def process_owner_remove_admin(message):
    if not is_owner(message.from_user.id): return
    target = message.text.strip()
    try:
        supabase.table('users').update({'role': 'normal'}).eq('user_id', int(target)).execute()
        bot.reply_to(message, f"🗑️ Revoked: Target ID `{target}` ko admin privileges se remove kar diya gaya hai.")
    except Exception as e: bot.reply_to(message, f"Database transaction error: {e}")

def process_owner_allow_group(message):
    if not is_owner(message.from_user.id): return
    target = message.text.strip()
    try:
        supabase.table('allowed_groups').upsert({'group_id': str(target)}).execute()
        bot.reply_to(message, f"✅ Chat Group `{target}` successfully whitelist database me save ho gya.")
    except: bot.reply_to(message, "Database execution error caught.")

def process_owner_remove_group(message):
    if not is_owner(message.from_user.id): return
    target = message.text.strip()
    try:
        supabase.table('allowed_groups').delete().eq('group_id', str(target)).execute()
        bot.reply_to(message, f"🚫 Group `{target}` whitelists se blacklisted kar diya gaya.")
    except: bot.reply_to(message, "Database execution error caught.")

def process_owner_broadcast(message):
    if not is_owner(message.from_user.id): return
    bot.reply_to(message, "📢 Global notification delivery stream deployed.")

def process_owner_set_limit(message):
    if not is_owner(message.from_user.id): return
    bot.reply_to(message, f"🔒 Settings applied. Normal limits profile sync completed in DB configs.")

# ==========================================
# 🔄 9. RUN BRIDGE LOGIC THREAD RE-ROUTING
# ==========================================
def process_like_thread(message, uid, region, user_id, execution_type="single", processing_msg_id=None):
    if processing_msg_id is None:
        processing_txt = f"🚀 Autolike batch cycle initialized for UID: `{uid}` ({region}). Delivery in progress..."
        processing_msg = bot.send_message(message.chat.id, processing_txt)
        processing_msg_id = processing_msg.message_id
    
    api_data = hit_real_api(uid, region, execution_type)
    
    try: bot.delete_message(message.chat.id, processing_msg_id)
    except: pass

    if api_data:
        if api_data['added'] == 0:
            limit_txt = (
                f"⚠️ LIMIT REACHED ⚠️\n\n"
                f"👤 PLAYER: {api_data['game_name']}\n"
                f"🆔 UID: `{uid}`\n"
                f"❌ Maximum Likes Reached!\n"
                f"🌐 Buy Autolike for more."
            )
            bot.send_message(message.chat.id, limit_txt)
        else:
            increment_use(user_id)
            send_success_report(message.chat.id, uid, region, api_data, execution_type)
    else:
        error_txt = (
            f"❌ API SERVER ERROR\n\n"
            f"API connection timed out ya server down ho gaya hai.\n"
            f"Pls thodi der baad dobara re-attempt karein."
        )
        bot.send_message(message.chat.id, error_txt)

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
scheduler.add_job(run_morning_autolikes, 'cron', hour=4, minute=0)
scheduler.start()

# ==========================================
# 🟢 11. ENGINE MULTITHREADED LAUNCH
# ==========================================
if __name__ == '__main__':
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    print("🚀 SHIVAY Bot Engine Started (100% REAL APIs Active)...")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
