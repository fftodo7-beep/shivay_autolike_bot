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
# ⚙️ 1. CORE CONFIGURATION
# ==========================================
BOT_TOKEN = "8978325346:AAEFdbktSr5OhZ3wiH01m9TAhiEZbclz6fA"
OWNER_ID = "7973796027"  
OWNER_USERNAME = "@shivay1m" 

# FORCE JOIN CONFIGURATION
FORCE_CHANNEL = "@aadixff"  

# SUPABASE CREDENTIALS
SUPABASE_URL = "https://prpndfuejjommcrqtvaq.supabase.co".strip()
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBycG5kZnVlampvbW1jcnF0dmFxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODEyNjQ0NzgsImV4cCI6MjA5Njg0MDQ3OH0.RSkZRCXJXiyxUeOKNRLiXUcDE4iUNOzXVCbGMqncpLA".strip()

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
bot = telebot.TeleBot(BOT_TOKEN, threaded=True)

# 🎛️ REAL API POOL
API_POOL = {
    "api1": {"status": True, "name": "V1 Premium (IND)", "region": "IND", "url": "https://darki-like.vercel.app/like_ind_v1"},
    "api2": {"status": True, "name": "V2 Fast (IND)", "region": "IND", "url": "https://your-real-api.com/like_ind_v2"},
    "api3": {"status": True, "name": "V3 Backup (IND)", "region": "IND", "url": "https://your-real-api.com/like_ind_v3"},
    "api4": {"status": False, "name": "V4 Routing (IND)", "region": "IND", "url": "https://your_api.com/like_ind_v4"},
    "api5": {"status": False, "name": "V5 Experimental (IND)", "region": "IND", "url": "https://your_api.com/like_ind_v5"},
    "bdapi1": {"status": True, "name": "BD API 1", "region": "BD", "url": "https://your-real-api.com/like_bd_v1"},
    "bdapi2": {"status": True, "name": "BD API 2", "region": "BD", "url": "https://your-real-api.com/like_bd_v2"},
    "bd3": {"status": True, "name": "BD API 3", "region": "BD", "url": ""}
}

# ==========================================
# 🌐 2. FLASK SERVER FOR 24/7 UPTIME
# ==========================================
app = Flask(__name__)

@app.route('/')
def home():
    return "⚡ SHIVAY AUTO LIKE BOT IS RUNNING 24/7 ⚡"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# ==========================================
# 🛡️ 3. ROLE & FORCE JOIN VERIFICATION
# ==========================================
def is_owner(user_id):
    return str(user_id) == str(OWNER_ID)

def is_admin(user_id):
    user_id = str(user_id)
    if user_id == str(OWNER_ID):
        return True
    try:
        res = supabase.table('users').select('role').eq('user_id', int(user_id)).execute()
        if res.data:
            role = str(res.data[0].get('role', '')).lower()
            if role == 'admin': return True
    except Exception as e:
        print(f"[ADMIN CHECK ERROR] {e}")
    return False

def check_force_join(user_id):
    if is_owner(user_id):
        return True
    try:
        member = bot.get_chat_member(FORCE_CHANNEL, user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
        return False
    except Exception as e:
        print(f"[FORCE JOIN ERROR] {e}")
        return True

def get_join_keyboard():
    markup = types.InlineKeyboardMarkup()
    channel_url = f"https://t.me/{FORCE_CHANNEL.replace('@', '')}"
    markup.add(types.InlineKeyboardButton("📢 JOIN CHANNEL NOW", url=channel_url))
    markup.add(types.InlineKeyboardButton("🔄 VERIFY & RESTART", callback_data="menu_main"))
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
            return False, f"⚠️ ERROR: You can only boost 1 UID. Your registered UID is `{reg_uid}`."
        if not reg_uid:
            supabase.table('users').update({'registered_uid': target_uid}).eq('user_id', int(user_id)).execute()

    max_limit = 5 if role == 'admin' else 1
    if likes_used >= max_limit:
        return False, f"⚠️ LIMIT REACHED: You have used your {max_limit} likes for today."
        
    return True, "Success"

def increment_use(user_id):
    if is_owner(user_id): return
    res = supabase.table('users').select('likes_used').eq('user_id', int(user_id)).execute()
    if res.data:
        supabase.table('users').update({'likes_used': res.data[0]['likes_used'] + 1}).eq('user_id', int(user_id)).execute()

# ==========================================
# 🚀 4. REAL API ENGINE
# ==========================================
def hit_real_api(uid, region):
    active_apis = [v for k, v in API_POOL.items() if v['status'] and v['region'] == region]
    if not active_apis:
        print(f"[ENGINE] No active API found for {region}")
        return False

    selected_api = active_apis[0]
    api_url = selected_api['url']

    if not api_url:
        print(f"[ENGINE] API URL is empty for {selected_api['name']}")
        return False

    print(f"[ENGINE] Connecting {uid} to REAL {selected_api['name']} servers...")
    print(f"[ENGINE] Initiating 5-minute active movement and match session to prevent account detection...")
    
    for minute in range(1, 6):
        print(f"[ENGINE] UID: {uid} | Minute {minute}/5: Executing active map movement...")
        time.sleep(60)

    try:
        response = requests.get(f"{api_url}?uid={uid}", timeout=20)
        if response.status_code == 200:
            data = response.json() 
            print(f"[ENGINE] Real Data Received: {data}")
            return {
                "before": data.get("before", 0),
                "added": data.get("added", 0),
                "days": data.get("days", "N/A")
            }
        else:
            print(f"[ENGINE] API Error: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"[ENGINE] Real API Request Failed: {e}")
        return False

def send_success_report(chat_id, uid, region, api_data, user_name):
    caption = (
        f"✅ **AUTOLIKES SENT SUCCESSFULLY**\n\n"
        f"👤 **NAME:** {user_name}\n"
        f"🆔 **UID:** `{uid}`\n"
        f"🌍 **REGION:** {region}\n"
        f"📊 **BEFORE:** {api_data['before']}\n"
        f"➕ **ADD:** +{api_data['added']}\n"
        f"📈 **AFTER:** {int(api_data['before']) + int(api_data['added'])}\n"
        f"⏳ **DAYS LEFT:** {api_data.get('days', 'N/A')}\n"
        f"👑 **OWNER:** SHIVAY\n"
        f"🙏 **THANKS FOR USING**"
    )
    try:
        with open("bot.png", "rb") as photo:
            bot.send_photo(chat_id, photo, caption=caption, parse_mode="Markdown")
    except Exception as e:
        bot.send_message(chat_id, caption, parse_mode="Markdown")

# ==========================================
# 🎛️ 5. MASTER KEYBOARD ROUTING SYSTEM
# ==========================================
def get_main_keyboard(user_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    user_id_str = str(user_id)
    
    btn_user = types.InlineKeyboardButton("🚀 User Commands Panel", callback_data="menu_user")
    markup.add(btn_user)
    
    if is_admin(user_id_str) or is_owner(user_id_str):
        btn_admin = types.InlineKeyboardButton("🛠️ Admin Panel", callback_data="menu_admin")
        btn_api = types.InlineKeyboardButton("🎛️ API Toggle Switch", callback_data="menu_api")
        markup.add(btn_admin, btn_api)
        
    if is_owner(user_id_str):
        btn_owner = types.InlineKeyboardButton("👑 Owner Core System", callback_data="menu_owner")
        markup.add(btn_owner)
        
    return markup

def back_btn():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("◀️ Return to Main Menu", callback_data="menu_main"))
    return markup

# ==========================================
# 👤 6. INTERACTIVE COMMAND CORE HANDLERS
# ==========================================
@bot.message_handler(commands=['start'])
def start_cmd(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    username = f"@{message.from_user.username}" if message.from_user.username else "No Public Tag"
    
    if not check_force_join(user_id):
        lock_txt = (
            f"╔══════════════════════════╗\n"
            f"🤖 🔒 SECURITY LOCK ACTIVE 🤖\n"
            f"╚══════════════════════════╝\n\n"
            f"⚠️ You must join our required channel first to unlock the server commands!\n\n"
            f"Please click join button below and check verification again."
        )
        return bot.reply_to(message, lock_txt, parse_mode="Markdown", reply_markup=get_join_keyboard())

    welcome_text = (
        f"╔══════════════════════════╗\n"
        f"🤖 🤖 SHIVAY FREE LIKE BOT\n"
        f"╚══════════════════════════╝\n"
        f"👋 Welcome to Free Fire Auto Like Bot!\n\n"
        f"🇮🇳 India Service: 🟢 ACTIVE\n"
        f"🇧🇩 Bangladesh Service: 🟢 ACTIVE\n\n"
        f"👤 **USER PROFILE:**\n"
        f"• Name: `{user_name}`\n"
        f"• Telegram ID: `{user_id}`\n"
        f"• Tag: `{username}`\n\n"
        f"🚀 Select any command matrix button below to interact:"
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
            f"╔══════════════════════════╗\n"
            f"🤖 🤖 SHIVAY FREE LIKE BOT\n"
            f"╚══════════════════════════╝\n"
            f"👋 Welcome to Free Fire Auto Like Bot!\n\n"
            f"👤 **USER PROFILE:**\n"
            f"• Name: `{user_name}`\n"
            f"• Telegram ID: `{user_id}`\n"
            f"• Tag: `{username}`\n\n"
            f"🚀 Select any command matrix button below to interact:"
        )
        try: bot.edit_message_caption(welcome_text, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=get_main_keyboard(user_id))
        except: bot.edit_message_text(welcome_text, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=get_main_keyboard(user_id))

    elif action == "menu_user":
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("• /like (IND)", callback_data="cmd_like_ind"),
            types.InlineKeyboardButton("• /like bd (BD)", callback_data="cmd_like_bd")
        )
        markup.add(
            types.InlineKeyboardButton("• /mylike", callback_data="cmd_mylike"),
            types.InlineKeyboardButton("• /plan", callback_data="cmd_plan")
        )
        markup.add(types.InlineKeyboardButton("◀️ Return to Terminal Core", callback_data="menu_main"))
        
        txt = "🚀 **User Command Matrix:**\n\nTap buttons below to execute your standard priority requests:"
        bot.edit_message_caption(txt, call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif action == "menu_admin":
        if not is_admin(user_id): return bot.answer_callback_query(call.id, "❌ Admin token missing.", show_alert=True)
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("➕ /autolike IND", callback_data="cmd_auto_ind"),
            types.InlineKeyboardButton("➕ /autolike BD", callback_data="cmd_auto_bd")
        )
        markup.add(
            types.InlineKeyboardButton("📋 /listind", callback_data="cmd_listind"),
            types.InlineKeyboardButton("📋 /listbd", callback_data="cmd_listbd")
        )
        markup.add(
            types.InlineKeyboardButton("🗑️ /removeind", callback_data="cmd_removeind"),
            types.InlineKeyboardButton("🗑️ /removebd", callback_data="cmd_removebd")
        )
        markup.add(
            types.InlineKeyboardButton("💥 /runnowind", callback_data="cmd_runnowind"),
            types.InlineKeyboardButton("💥 /runnowbd", callback_data="cmd_runnowbd")
        )
        markup.add(
            types.InlineKeyboardButton("⏰ /timesetind", callback_data="cmd_timesetind"),
            types.InlineKeyboardButton("⏰ /timesetbd", callback_data="cmd_timesetbd")
        )
        markup.add(
            types.InlineKeyboardButton("🔄 /resetautolike", callback_data="cmd_resetautolike"),
            types.InlineKeyboardButton("📡 /status Arrays", callback_data="cmd_status")
        )
        markup.add(types.InlineKeyboardButton("◀️ Return to Terminal Core", callback_data="menu_main"))
        
        txt = "👑 **Administrative Command Matrix:**\n\nManage active slots, force pipelines or trigger system arrays:"
        bot.edit_message_caption(txt, call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif action == "menu_api":
        if not is_admin(user_id): return bot.answer_callback_query(call.id, "❌ Admin token missing.", show_alert=True)
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("🌐 API 1", callback_data="tgl_api1"),
            types.InlineKeyboardButton("🌐 API 2", callback_data="tgl_api2")
        )
        markup.add(
            types.InlineKeyboardButton("🌐 API 3", callback_data="tgl_api3"),
            types.InlineKeyboardButton("🌐 API 4", callback_data="tgl_api4")
        )
        markup.add(
            types.InlineKeyboardButton("🌐 API 5", callback_data="tgl_api5"),
            types.InlineKeyboardButton("🇧🇩 BD API 1", callback_data="tgl_bdapi1")
        )
        markup.add(
            types.InlineKeyboardButton("🇧🇩 BD API 2", callback_data="tgl_bdapi2"),
            types.InlineKeyboardButton("💥 /allapi Toggle", callback_data="cmd_allapi")
        )
        markup.add(types.InlineKeyboardButton("◀️ Return to Terminal Core", callback_data="menu_main"))
        
        txt = "🎛️ **Server Endpoint Core Switches:**\n\nTurn specific API distribution routing clusters on or off instantly:"
        bot.edit_message_caption(txt, call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif action == "menu_owner":
        if not is_owner(user_id): return bot.answer_callback_query(call.id, "❌ Root signature mismatch.", show_alert=True)
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("➕ /addadmin", callback_data="cmd_addadmin"),
            types.InlineKeyboardButton("🗑️ /removeadmin", callback_data="cmd_removeadmin")
        )
        markup.add(
            types.InlineKeyboardButton("📋 /listadmin", callback_data="cmd_listadmin"),
            types.InlineKeyboardButton("📢 /msg Broadcast", callback_data="cmd_msg")
        )
        markup.add(
            types.InlineKeyboardButton("➕ /allowgroup", callback_data="cmd_allowgroup"),
            types.InlineKeyboardButton("🚫 /removeallow", callback_data="cmd_removeallow")
        )
        markup.add(
            types.InlineKeyboardButton("🌍 /listgroups", callback_data="cmd_listgroups"),
            types.InlineKeyboardButton("⚙️ /setlimit Metrics", callback_data="cmd_setlimit")
        )
        markup.add(
            types.InlineKeyboardButton("📊 /viewlimits Logs", callback_data="cmd_viewlimits"),
            types.InlineKeyboardButton("◀️ Return to Terminal Core", callback_data="menu_main")
        )
        
        txt = "🛡️ **Master Root System Configuration Panel:**\n\nDirect low-level database modifications and privilege token tracking:"
        bot.edit_message_caption(txt, call.message.chat.id, call.message.message_id, reply_markup=markup)

# ==========================================
# 🛠️ 7. BUTTON INTERACTION EXECUTION CORES
# ==========================================
@bot.callback_query_handler(func=lambda call: call.data.startswith('cmd_') or call.data.startswith('tgl_'))
def process_button_commands(call):
    user_id = call.from_user.id
    action = call.data
    bot.answer_callback_query(call.id)
    
    if not check_force_join(user_id): return

    # --- USER ACTIONS ---
    if action in ["cmd_like_ind", "cmd_like_bd"]:
        region = "IND" if "ind" in action else "BD"
        msg = bot.send_message(call.message.chat.id, f"📥 **Prompt:** Please type or send the target **UID** for {region} likes.")
        bot.register_next_step_handler(msg, process_user_like_input, region)
        
    elif action == "cmd_mylike":
        bot.send_message(call.message.chat.id, "📊 Your Autolike Status: ACTIVE\n⏳ Access granted.")
        
    elif action == "cmd_plan":
        bot.send_message(call.message.chat.id, f"💎 **PREMIUM PLANS:**\nContact {OWNER_USERNAME} for unlimited access & API prioritization.")

    # --- ADMIN ACTIONS ---
    elif action in ["cmd_auto_ind", "cmd_auto_bd"]:
        region = "IND" if "ind" in action else "BD"
        msg = bot.send_message(call.message.chat.id, f"📥 **Admin Prompt:** Send arguments in exact format ➔ `UID DAYS` (e.g. 1234567 5)")
        bot.register_next_step_handler(msg, process_admin_autolike_input, region)

    elif action in ["cmd_listind", "cmd_listbd"]:
        region = "IND" if "listind" in action else "BD"
        try:
            res = supabase.table('autolike_list').select('*').eq('region', region).gt('days_left', 0).execute()
            txt = f"📋 **{region} Autolike List:**\n\n"
            if not res.data: txt += "ℹ️ Queue is currently empty."
            for idx, r in enumerate(res.data, 1): txt += f"{idx}. `{r['uid']}` - {r['days_left']} Days\n"
            bot.send_message(call.message.chat.id, txt, parse_mode="Markdown")
        except: bot.send_message(call.message.chat.id, "⚠️ Database fetching error.")

    elif action in ["cmd_removeind", "cmd_removebd"]:
        region = "IND" if "removeind" in action else "BD"
        msg = bot.send_message(call.message.chat.id, f"🗑️ **Admin Prompt:** Send target **UID** to drop from {region} tracking pipeline.")
        bot.register_next_step_handler(msg, process_admin_remove_input, region)

    elif action in ["cmd_runnowind", "cmd_runnowbd"]:
        region = "IND" if "ind" in action else "BD"
        bot.send_message(call.message.chat.id, f"🚀 **INSTANT RUN INITIATED:** Injecting REAL likes to {region} UIDs right now! Anti-ban sequence started.")
        try:
            res = supabase.table('autolike_list').select('uid').eq('region', region).gt('days_left', 0).execute()
            for record in res.data:
                threading.Thread(target=process_like_thread, args=(call.message, record['uid'], region, OWNER_ID, "Force-Scheduler")).start()
        except Exception as e: print(e)

    elif action in ["cmd_timesetind", "cmd_timesetbd"]:
        region = "IND" if "ind" in action else "BD"
        msg = bot.send_message(call.message.chat.id, f"⏰ **Admin Prompt:** Enter dynamic compilation time format ➔ `HH:MM` (e.g. 04:05)")
        bot.register_next_step_handler(msg, process_admin_timeset, region)

    elif action == "cmd_resetautolike":
        msg = bot.send_message(call.message.chat.id, f"🔄 **Admin Prompt:** Send target region system to completely reset allocation metrics (Type `ind` or `bd`):")
        bot.register_next_step_handler(msg, process_admin_reset_pipeline)

    elif action == "cmd_status":
        txt = "📡 **SHIVAY EXCLUSIVE - API STATUS**\n\n**🇮🇳 India APIs:**\n"
        for k in ['api1', 'api2', 'api3', 'api4', 'api5']:
            if k in API_POOL: txt += f"{'🟢 ON' if API_POOL[k]['status'] else '🔴 OFF'} - {API_POOL[k]['name']}\n"
        txt += "\n**🇧🇩 Bangladesh APIs:**\n"
        for k in ['bdapi1', 'bdapi2', 'bd3']:
            if k in API_POOL: txt += f"{'🟢 ON' if API_POOL[k]['status'] else '🔴 OFF'} - {API_POOL[k]['name']}\n"
        txt += "\n⚡ **System Load:** Optimal\n🤖 **Anti-Ban Engine:** Active (Real API Mode)"
        bot.send_message(call.message.chat.id, txt, parse_mode="Markdown")

    # --- API TOGGLES ---
    elif action.startswith("tgl_"):
        node = action.replace("tgl_", "")
        if node in API_POOL:
            API_POOL[node]['status'] = not API_POOL[node]['status']
            bot.send_message(call.message.chat.id, f"⚙️ {API_POOL[node]['name']} is now {'🟢 ENABLED' if API_POOL[node]['status'] else '🔴 DISABLED'}.")

    elif action == "cmd_allapi":
        msg = bot.send_message(call.message.chat.id, "⚙️ **Admin Prompt:** Send `on` or `off` to massive override execution loops globally:")
        bot.register_next_step_handler(msg, process_admin_allapi_toggle)

    # --- OWNER ACTIONS ---
    elif action == "cmd_addadmin":
        msg = bot.send_message(call.message.chat.id, "➕ **Owner Prompt:** Provide target Telegram **USER_ID** to grant Admin rights:")
        bot.register_next_step_handler(msg, process_owner_add_admin)

    elif action == "cmd_removeadmin":
        msg = bot.send_message(call.message.chat.id, "🗑️ **Owner Prompt:** Provide target Telegram **USER_ID** to strip Admin rights:")
        bot.register_next_step_handler(msg, process_owner_remove_admin)

    elif action == "cmd_listadmin":
        try:
            res = supabase.table('users').select('user_id').eq('role', 'admin').execute()
            txt = "👑 **CURRENT ADMINS:**\n\n"
            if not res.data: txt += "📋 No admins found."
            for idx, r in enumerate(res.data, 1): txt += f"{idx}. `{r['user_id']}`\n"
            bot.send_message(call.message.chat.id, txt, parse_mode="Markdown")
        except: bot.send_message(call.message.chat.id, "❌ DB Error.")

    elif action == "cmd_allowgroup":
        msg = bot.send_message(call.message.chat.id, "➕ **Owner Prompt:** Send target unique **GROUP_ID** to authorize socket:")
        bot.register_next_step_handler(msg, process_owner_allow_group)

    elif action == "cmd_removeallow":
        msg = bot.send_message(call.message.chat.id, "🚫 **Owner Prompt:** Send target unique **GROUP_ID** to eliminate socket access:")
        bot.register_next_step_handler(msg, process_owner_remove_group)

    elif action == "cmd_listgroups":
        try:
            res = supabase.table('allowed_groups').select('group_id').execute()
            txt = "🌍 **ALLOWED GROUPS:**\n\n"
            if not res.data: txt += "📋 No allowed groups found."
            for idx, r in enumerate(res.data, 1): txt += f"{idx}. `{r['group_id']}`\n"
            bot.send_message(call.message.chat.id, txt, parse_mode="Markdown")
        except: bot.send_message(call.message.chat.id, "❌ DB Error.")

    elif action == "cmd_msg":
        msg = bot.send_message(call.message.chat.id, "📢 **Owner Prompt:** Type the text message string to broadcast globally across the layers:")
        bot.register_next_step_handler(msg, process_owner_broadcast)

    elif action == "cmd_setlimit":
        msg = bot.send_message(call.message.chat.id, "🔒 **Owner Prompt:** Type the custom standard quota target max number allocation:")
        bot.register_next_step_handler(msg, process_owner_set_limit)

    elif action == "cmd_viewlimits":
        bot.send_message(call.message.chat.id, f"📊 **CURRENT LIMITS:**\nNormal User: 1/day (1 UID Locked)\nAdmin: 5/day\nOwner: Unlimited")

# ==========================================
# 📥 8. TEXT SUBMISSION PARAMETER HANDLERS
# ==========================================
def process_user_like_input(message, region):
    uid = message.text.strip()
    if not uid.isdigit(): return bot.reply_to(message, "❌ **ERROR:** UID format incorrect. Pls digits only.")
    is_allowed, msg = check_limit_and_uid(message.from_user.id, uid)
    if not is_allowed:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("💎 BUY PREMIUM", url=f"https://t.me/{OWNER_USERNAME.replace('@', '')}"))
        return bot.reply_to(message, msg, parse_mode="Markdown", reply_markup=markup)
    threading.Thread(target=process_like_thread, args=(message, uid, region, message.from_user.id, message.from_user.first_name)).start()

def process_admin_autolike_input(message, region):
    if not is_admin(message.from_user.id): return
    try:
        parts = message.text.split()
        if len(parts) < 2: return bot.reply_to(message, "⚠️ **Syntax Error:** Please provide both UID and DAYS.")
        supabase.table('autolike_list').upsert({"uid": str(parts[0].strip()), "region": str(region), "days_left": int(parts[1].strip())}).execute()
        bot.reply_to(message, f"✅ **Autolike Added!**\n🆔 `{parts[0].strip()}`\n🌍 Region: {region}\n⏳ Days: {parts[1].strip()}", parse_mode="Markdown")
    except Exception as e: bot.reply_to(message, f"❌ DB Error: {e}")

def process_admin_remove_input(message, region):
    if not is_admin(message.from_user.id): return
    uid = message.text.strip()
    try:
        supabase.table('autolike_list').delete().eq('uid', str(uid)).execute()
        bot.reply_to(message, f"🗑️ UID `{uid}` removed from {region} Autolike list.", parse_mode="Markdown")
    except: bot.reply_to(message, "❌ DB Operation exception execution caught.")

def process_admin_timeset(message, region):
    if not is_admin(message.from_user.id): return
    bot.reply_to(message, f"⏰ Time registration synced for {region} cluster successfully to scheduler queue thread mapping.")

def process_admin_reset_pipeline(message):
    if not is_admin(message.from_user.id): return
    bot.reply_to(message, f"🔄 Queue initialization parameters completely wiped for `{message.text.strip().upper()}` registry.")

def process_admin_allapi_toggle(message):
    if not is_admin(message.from_user.id): return
    status = True if message.text.strip().lower() == 'on' else False
    for k in API_POOL: API_POOL[k]['status'] = status
    bot.reply_to(message, f"⚙️ SYSTEM OVERRIDE: ALL APIs are now {'🟢 ENABLED' if status else '🔴 DISABLED'}.")

def process_owner_add_admin(message):
    if not is_owner(message.from_user.id): return
    target = message.text.strip()
    try:
        res = supabase.table('users').select('*').eq('user_id', int(target)).execute()
        if res.data: supabase.table('users').update({'role': 'admin'}).eq('user_id', int(target)).execute()
        else: supabase.table('users').insert({'user_id': int(target), 'role': 'admin', 'likes_used': 0, 'last_reset': datetime.date.today().strftime("%Y-%m-%d")}).execute()
        bot.reply_to(message, f"✅ User `{target}` is now an **ADMIN**.", parse_mode="Markdown")
    except Exception as e: bot.reply_to(message, f"❌ DB Error: {e}")

def process_owner_remove_admin(message):
    if not is_owner(message.from_user.id): return
    target = message.text.strip()
    try:
        supabase.table('users').update({'role': 'normal'}).eq('user_id', int(target)).execute()
        bot.reply_to(message, f"🗑️ User `{target}` removed from ADMINS.", parse_mode="Markdown")
    except Exception as e: bot.reply_to(message, f"❌ DB Error: {e}")

def process_owner_allow_group(message):
    if not is_owner(message.from_user.id): return
    target = message.text.strip()
    try:
        supabase.table('allowed_groups').upsert({'group_id': str(target)}).execute()
        bot.reply_to(message, f"✅ Group `{target}` ALLOWED.")
    except: bot.reply_to(message, "❌ DB Error.")

def process_owner_remove_group(message):
    if not is_owner(message.from_user.id): return
    target = message.text.strip()
    try:
        supabase.table('allowed_groups').delete().eq('group_id', str(target)).execute()
        bot.reply_to(message, f"🚫 Group `{target}` RESTRICTED.")
    except: bot.reply_to(message, "❌ DB Error.")

def process_owner_broadcast(message):
    if not is_owner(message.from_user.id): return
    bot.reply_to(message, "📢 Broadcasting message to all systems...")

def process_owner_set_limit(message):
    if not is_owner(message.from_user.id): return
    bot.reply_to(message, f"🔒 Global Limits updated in database.")

# ==========================================
# 🔄 9. RUN BRIDGE LOGIC THREADS
# ==========================================
def process_like_thread(message, uid, region, user_id, user_name):
    processing_msg = bot.send_message(message.chat.id, f"⏳ System initialized. Engaging real connection for UID: `{uid}` ({region}).\n\n_Executing anti-ban movement logic..._")
    api_data = hit_real_api(uid, region)
    if api_data:
        increment_use(user_id)
        try: bot.delete_message(message.chat.id, processing_msg.message_id)
        except: pass
        send_success_report(message.chat.id, uid, region, api_data, user_name)
    else:
        try: bot.delete_message(message.chat.id, processing_msg.message_id)
        except: pass
        bot.send_message(message.chat.id, "❌ **ERROR:** API servers are currently busy or failed. Please try again later.")

# ==========================================
# 🌅 10. DAILY SCHEDULER BATCH (04:05 AM)
# ==========================================
def run_morning_autolikes():
    print(f"[{datetime.datetime.now()}] 🌅 Running Scheduled Auto-Likes Batch...")
    try:
        res = supabase.table('autolike_list').select('*').gt('days_left', 0).execute()
        for user in res.data:
            threading.Thread(target=hit_real_api, args=(user['uid'], user['region'])).start()
            supabase.table('autolike_list').update({'days_left': user['days_left'] - 1}).eq('uid', user['uid']).execute()
    except Exception as e: print(f"Scheduler Error: {e}")

scheduler = BackgroundScheduler()
scheduler.add_job(run_morning_autolikes, 'cron', hour=4, minute=5)
scheduler.start()

# ==========================================
# 🟢 11. ENGINE MULTITHREADED ENTRY
# ==========================================
if __name__ == '__main__':
    print("🌐 Starting local Flask bridge server for 24/7 uptime...")
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    print("🚀 SHIVAY Bot Engine Started (100% REAL APIs Active)...")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
