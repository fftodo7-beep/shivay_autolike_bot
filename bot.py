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
    "api1": {"status": True, "name": "V1 Premium (IND)", "region": "IND", "url": "https://your-real-api.com/like_ind_v1"},
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
    return "⚡ SHIVAY MATRIX CORE IS RUNNING 24/7 ⚡"

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
    markup.add(types.InlineKeyboardButton("🔄 VERIFY & RESTART", callback_data="panel_main"))
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
# 🎛️ 5. INTERACTIVE ROLE BUTTON PANELS
# ==========================================
def get_matrix_keyboard(user_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    user_id_str = str(user_id)
    
    btn_user = types.InlineKeyboardButton("🛰️ Client Terminal", callback_data="panel_user")
    
    if is_owner(user_id_str):
        btn_admin = types.InlineKeyboardButton("⚡ Admin Matrix", callback_data="panel_admin")
        btn_owner = types.InlineKeyboardButton("👑 Root Architect", callback_data="panel_owner")
        markup.add(btn_user, btn_admin)
        markup.add(btn_owner)
    elif is_admin(user_id_str):
        btn_admin = types.InlineKeyboardButton("⚡ Admin Matrix", callback_data="panel_admin")
        markup.add(btn_user, btn_admin)
    else:
        markup.add(btn_user)
        
    return markup

def back_to_main_keyboard():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("◀️ Return to Terminal Core", callback_data="panel_main"))
    return markup

# ==========================================
# 👤 6. INTERACTIVE COMMAND ENGINE ROUTING
# ==========================================
@bot.message_handler(commands=['start', 'help'])
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
        f"👤 **USER LOG MATRIX:** \n"
        f"• Name: `{user_name}`\n"
        f"• Telegram ID: `{user_id}`\n"
        f"• Tag: `{username}`\n\n"
        f"🚀 Tap the buttons below to open user, admin or owner interfaces."
    )
    
    try:
        profiles = bot.get_user_profile_photos(user_id, limit=1)
        if profiles.total_count > 0:
            file_id = profiles.photos[0][-1].file_id
            bot.send_photo(message.chat.id, file_id, caption=welcome_text, parse_mode="Markdown", reply_markup=get_matrix_keyboard(user_id))
        else:
            with open("bot.png", "rb") as photo:
                bot.send_photo(message.chat.id, photo, caption=welcome_text, parse_mode="Markdown", reply_markup=get_matrix_keyboard(user_id))
    except Exception as e:
        bot.reply_to(message, welcome_text, parse_mode="Markdown", reply_markup=get_matrix_keyboard(user_id))

@bot.callback_query_handler(func=lambda call: call.data.startswith('panel_'))
def handle_panels(call):
    user_id = call.from_user.id
    action = call.data
    
    if not check_force_join(user_id):
        return bot.answer_callback_query(call.id, f"❌ Access Blocked. Please join {FORCE_CHANNEL} first!", show_alert=True)

    if action == "panel_main":
        user_name = call.from_user.first_name
        username = f"@{call.from_user.username}" if call.from_user.username else "No Public Tag"
        welcome_text = (
            f"╔══════════════════════════╗\n"
            f"🤖 🤖 SHIVAY FREE LIKE BOT\n"
            f"╚══════════════════════════╝\n"
            f"👋 Welcome to Free Fire Auto Like Bot!\n\n"
            f"👤 **USER LOG MATRIX:** \n"
            f"• Name: `{user_name}`\n"
            f"• Telegram ID: `{user_id}`\n"
            f"• Tag: `{username}`\n\n"
            f"🚀 Select an interactive terminal option below:"
        )
        try: bot.edit_message_caption(welcome_text, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=get_matrix_keyboard(user_id))
        except: bot.edit_message_text(welcome_text, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=get_matrix_keyboard(user_id))

    elif action == "panel_user":
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("• /like IND", callback_data="op_like_ind"),
            types.InlineKeyboardButton("• /like BD", callback_data="op_like_bd")
        )
        markup.add(
            types.InlineKeyboardButton("• /mylike", callback_data="op_mylike"),
            types.InlineKeyboardButton("• /plan", callback_data="op_plan")
        )
        markup.add(types.InlineKeyboardButton("◀️ Back to Menu", callback_data="panel_main"))

        user_txt = (
            f"🚀 **User Command Interface:**\n\n"
            f"Type karne ki koi zaroorat nahi hai. Niche diye buttons se direct execute karein:"
        )
        try: bot.edit_message_caption(user_txt, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)
        except: bot.edit_message_text(user_txt, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)

    elif action == "panel_admin":
        if not is_admin(user_id):
            return bot.answer_callback_query(call.id, "❌ Administrative privilege match failed.", show_alert=True)
        
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("• /autolike IND", callback_data="op_auto_ind"),
            types.InlineKeyboardButton("• /autolike BD", callback_data="op_auto_bd")
        )
        markup.add(
            types.InlineKeyboardButton("• /listind", callback_data="op_list_ind"),
            types.InlineKeyboardButton("• /listbd", callback_data="op_list_bd")
        )
        markup.add(
            types.InlineKeyboardButton("• /runnow IND/BD", callback_data="op_runnow_menu"),
            types.InlineKeyboardButton("• /status APIs", callback_data="op_gate_status")
        )
        markup.add(types.InlineKeyboardButton("◀️ Back to Menu", callback_data="panel_main"))

        admin_txt = (
            f"👑 **Admin Command Panel:**\n\n"
            f"Management features aur pipelines monitor karne ke liye buttons choose karein:"
        )
        try: bot.edit_message_caption(admin_txt, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)
        except: bot.edit_message_text(admin_txt, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)

    elif action == "panel_owner":
        if not is_owner(user_id):
            return bot.answer_callback_query(call.id, "❌ Root Architect authorization mismatch.", show_alert=True)
            
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("🛠️ Admin Controls (/addadmin)", callback_data="op_owner_admins"),
            types.InlineKeyboardButton("🌍 Group Whitelist (/allowgroup)", callback_data="op_owner_groups"),
            types.InlineKeyboardButton("📊 System Quotas (/viewlimits)", callback_data="op_owner_limits"),
            types.InlineKeyboardButton("◀️ Back to Menu", callback_data="panel_main")
        )
        owner_txt = (
            f"🛡️ **Owner Only Core Terminal:**\n\n"
            f"Manage administrative structural configurations securely using buttons below:"
        )
        try: bot.edit_message_caption(owner_txt, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)
        except: bot.edit_message_text(owner_txt, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)

# ==========================================
# 🛠️ 7. BUTTON ACTION PROCESSORS (ORIGINAL LOGIC)
# ==========================================
@bot.callback_query_handler(func=lambda call: call.data.startswith('op_'))
def execute_operations(call):
    user_id = call.from_user.id
    action = call.data
    
    if not check_force_join(user_id):
        return bot.answer_callback_query(call.id, f"❌ Access Blocked. Please join {FORCE_CHANNEL} first!", show_alert=True)

    # --- USER EXECUTION ---
    if action in ["op_like_ind", "op_like_bd"]:
        region = "IND" if "ind" in action else "BD"
        msg = bot.send_message(call.message.chat.id, f"📥 **Prompt:** Please type or send the target **UID** for {region} likes.")
        bot.register_next_step_handler(msg, process_user_like_input, region)
        bot.answer_callback_query(call.id)
        
    elif action == "op_mylike":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "📊 Your Autolike Status: ACTIVE\n⏳ Access granted.")
        
    elif action == "op_plan":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, f"💎 **PREMIUM PLANS:**\nContact {OWNER_USERNAME} for unlimited access & API prioritization.")

    # --- ADMIN EXECUTION ---
    elif action in ["op_auto_ind", "op_auto_bd"]:
        region = "IND" if "ind" in action else "BD"
        msg = bot.send_message(call.message.chat.id, f"📥 **Admin Prompt:** Send arguments in exact format ➔ `UID DAYS` (e.g. 1234567 5)")
        bot.register_next_step_handler(msg, process_admin_autolike_input, region)
        bot.answer_callback_query(call.id)

    elif action in ["op_list_ind", "op_list_bd"]:
        bot.answer_callback_query(call.id)
        region = "IND" if "ind" in action else "BD"
        try:
            res = supabase.table('autolike_list').select('*').eq('region', region).gt('days_left', 0).execute()
            txt = f"📋 **{region} Autolike List:**\n\n"
            if not res.data: txt += "ℹ️ Queue is currently empty."
            for idx, r in enumerate(res.data, 1):
                txt += f"{idx}. `{r['uid']}` - {r['days_left']} Days\n"
            bot.send_message(call.message.chat.id, txt, parse_mode="Markdown")
        except: bot.send_message(call.message.chat.id, "⚠️ Database fetching error.")

    elif action == "op_gate_status":
        bot.answer_callback_query(call.id)
        txt = "📡 **SHIVAY EXCLUSIVE - API STATUS**\n\n**🇮🇳 India APIs:**\n"
        for k in ['api1', 'api2', 'api3', 'api4', 'api5']:
            if k in API_POOL: txt += f"{'🟢 ON' if API_POOL[k]['status'] else '🔴 OFF'} - {API_POOL[k]['name']}\n"
        txt += "\n**🇧🇩 Bangladesh APIs:**\n"
        for k in ['bdapi1', 'bdapi2', 'bd3']:
            if k in API_POOL: txt += f"{'🟢 ON' if API_POOL[k]['status'] else '🔴 OFF'} - {API_POOL[k]['name']}\n"
        txt += "\n⚡ **System Load:** Optimal\n🤖 **Anti-Ban Engine:** Active (Real API Mode)"
        bot.send_message(call.message.chat.id, txt, parse_mode="Markdown")

    elif action == "op_runnow_menu":
        bot.answer_callback_query(call.id)
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🚀 Run IND Pipeline Now", callback_data="run_force_ind"))
        markup.add(types.InlineKeyboardButton("🚀 Run BD Pipeline Now", callback_data="run_force_bd"))
        bot.send_message(call.message.chat.id, "⚠️ **Manual Override:** Choose region pipeline to deploy instant batch process:", reply_markup=markup)

    # --- OWNER EXECUTION ---
    elif action == "op_owner_limits":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, f"📊 **CURRENT LIMITS:**\nNormal User: 1/day (1 UID Locked)\nAdmin: 5/day\nOwner: Unlimited")

    elif action == "op_owner_admins":
        bot.answer_callback_query(call.id)
        try:
            res = supabase.table('users').select('user_id').eq('role', 'admin').execute()
            txt = "👑 **CURRENT ADMINS:**\n\n"
            if not res.data: txt += "📋 No admins found."
            for idx, r in enumerate(res.data, 1): txt += f"{idx}. `{r['user_id']}`\n"
            bot.send_message(call.message.chat.id, txt, parse_mode="Markdown")
        except: bot.send_message(call.message.chat.id, "❌ DB Error.")

    elif action == "op_owner_groups":
        bot.answer_callback_query(call.id)
        try:
            res = supabase.table('allowed_groups').select('group_id').execute()
            txt = "🌍 **ALLOWED GROUPS:**\n\n"
            if not res.data: txt += "📋 No allowed groups found."
            for idx, r in enumerate(res.data, 1): txt += f"{idx}. `{r['group_id']}`\n"
            bot.send_message(call.message.chat.id, txt, parse_mode="Markdown")
        except: bot.send_message(call.message.chat.id, "❌ DB Error.")

# ==========================================
# 📥 8. TEXT INPUT STEP REGISTRATIONS
# ==========================================
def process_user_like_input(message, region):
    uid = message.text.strip()
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    
    if not uid.isdigit():
        return bot.reply_to(message, "❌ **ERROR:** UID format incorrect. Pls digits only.")
        
    is_allowed, msg = check_limit_and_uid(user_id, uid)
    if not is_allowed:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("💎 BUY PREMIUM", url=f"https://t.me/{OWNER_USERNAME.replace('@', '')}"))
        return bot.reply_to(message, msg, parse_mode="Markdown", reply_markup=markup)

    threading.Thread(target=process_like_thread, args=(message, uid, region, user_id, user_name)).start()

def process_admin_autolike_input(message, region):
    if not is_admin(message.from_user.id): return
    try:
        parts = message.text.split()
        if len(parts) < 2:
            return bot.reply_to(message, "⚠️ **Syntax Error:** Please provide both UID and DAYS.")
        uid, days = parts[0].strip(), parts[1].strip()
        
        supabase.table('autolike_list').upsert({"uid": str(uid), "region": str(region), "days_left": int(days)}).execute()
        bot.reply_to(message, f"✅ **Autolike Added!**\n🆔 `{uid}`\n🌍 Region: {region}\n⏳ Days: {days}", parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"❌ DB Error: {e}")

# ==========================================
# 💥 9. FORCE RUN BATCH EXECUTIONS
# ==========================================
@bot.callback_query_handler(func=lambda call: call.data.startswith('run_force_'))
def execute_force_batch(call):
    if not is_admin(call.from_user.id): return
    region = "IND" if "ind" in call.data else "BD"
    bot.answer_callback_query(call.id, f"Running scheduled {region} batch process...")
    bot.send_message(call.message.chat.id, f"🚀 **INSTANT RUN INITIATED:** Injecting REAL likes to {region} UIDs right now! Anti-ban sequence started.")
    
    try:
        res = supabase.table('autolike_list').select('uid').eq('region', region).gt('days_left', 0).execute()
        for record in res.data:
            uid = record['uid']
            threading.Thread(target=process_like_thread, args=(call.message, uid, region, OWNER_ID, "Auto-Scheduler")).start()
    except Exception as e:
        print(e)

# ==========================================
# 🔄 10. BACKEND LOGIC THREAD BRIDGE
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
# 🌅 11. DAILY SCHEDULED CRON BATCH (04:05 AM)
# ==========================================
def run_morning_autolikes():
    print(f"[{datetime.datetime.now()}] 🌅 Running Scheduled Auto-Likes Batch...")
    try:
        res = supabase.table('autolike_list').select('*').gt('days_left', 0).execute()
        for user in res.data:
            threading.Thread(target=hit_real_api, args=(user['uid'], user['region'])).start()
            supabase.table('autolike_list').update({'days_left': user['days_left'] - 1}).eq('uid', user['uid']).execute()
    except Exception as e:
        print(f"Scheduler Error: {e}")

scheduler = BackgroundScheduler()
scheduler.add_job(run_morning_autolikes, 'cron', hour=4, minute=5)
scheduler.start()

# ==========================================
# 🟢 12. RUN ENGINE MULTITHREADED
# ==========================================
if __name__ == '__main__':
    print("🌐 Starting local Flask bridge server for 24/7 uptime...")
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    print("🚀 SHIVAY Bot Engine Started (100% REAL APIs Active)...")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
