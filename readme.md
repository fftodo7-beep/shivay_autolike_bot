# 🚀 ROCK X ANIRBAN - PREMIUM AUTO-LIKE BOT (Setup Guide)

Bhai, sabse pehle toh congratulations! Yeh koi normal free wala bot nahi hai. Yeh ekdam professional, Anti-Ban system aur asli APIs ke sath aane wala bot hai. 

Isko set karna bohot aasan hai. Bas agle 5 minute meri baat dhyan se follow karo, aur tumhara bot daudne lagega!

---

### 👉 Step 1: Computer ko Ready Karna (Requirements)
Sabse pehle hume bot chalane ke liye kuch zaroori tools install karne honge. 
1. Apne computer/VPS mein **Terminal** ya **Command Prompt (cmd)** kholo.
2. Yeh line wahan copy-paste karo aur **Enter** daba do:
   `pip install pyTelegramBotAPI supabase apscheduler requests httpx==0.27.2`
*(Yeh command bot ke dimaag ko internet aur database se connect karne ki files download kar legi. 1-2 minute lagenge).*

---

### 🗄️ Step 2: Database Banana (Jahan logo ka data save hoga)
Bot ko yaad rakhna hota hai ki kisne kitne likes liye hain. Iske liye hum **Supabase** ka use karenge (Yeh bilkul free hai).
1. **Supabase.com** par jao, Google se login karo aur ek naya Project bana lo.
2. Screen ke left side mein ek **SQL Editor** ka option hoga, us par click karo.
3. Niche diya hua code wahan paste kar do:

CREATE TABLE users (
  user_id BIGINT PRIMARY KEY,
  role TEXT,
  likes_used INT,
  last_reset TEXT,
  registered_uid TEXT
);
CREATE TABLE autolike_list (
  uid TEXT PRIMARY KEY,
  region TEXT,
  days_left INT
);
CREATE TABLE allowed_groups (
  group_id TEXT PRIMARY KEY
);

4. 🚨 **SABSE ZAROORI BAAT:** Code paste karne ke baad **"Run without RLS"** wale button par click karna. Agar ye nahi karoge toh bot data save nahi kar payega aur error dega!

---

### ⚙️ Step 3: Code ke andar Apni Details daalna
Ab apni `bot.py` file ko kisi bhi text editor (jaise Notepad ya VS Code) mein kholo. Shuru ki 30 lines mein tumhe apni details daalni hain:

* **BOT_TOKEN:** Apna Telegram bot ka token daalo (Jo @BotFather deta hai).
* **OWNER_ID:** Apna khud ka Telegram ID (Numbers wala) daalo taaki bot tumhe 'Malik' maan le aur saari powers de de.
* **SUPABASE_URL:** Supabase mein "Settings > API" mein jao. Wahan se "Project URL" copy karke yahan daalo.
* **SUPABASE_KEY:** Usi "Settings > API" page par ek bohot lambi key hogi jiske aage `anon public` likha hoga (Ye `eyJ...` se shuru hoti hai). Usko yahan paste karo.

🚨 **ASLI LIKES KE LIYE (Real APIs):**
Code mein thoda niche aao jahan `API_POOL` likha hai. Wahan `"url": ""` ke andar apni ASLI auto-like website/API ka link daalna zaroori hai. Nakli link daloge toh likes nahi jayenge aur bot "Error" bol dega.

---

### 🖼️ Step 4: Photo lagana (Premium Look ke liye)
Jab bot start hota hai ya likes bhejta hai, toh ek badhiya si photo aati hai. 
1. Apni pasand ki photo lo aur uska naam exact **`bot.png`** rakh do (Spelling dhyan rakhna).
2. Is photo ko utha kar bilkul usi folder mein rakh do jahan tumhari `bot.py` file rakhi hai. 

---

### 🚀 Step 5: Bot Chalu Karein!
Bas, itna hi karna tha! Ab wapas apne Terminal/CMD mein aao aur type karo:
`python bot.py`

Jaise hi tum enter maroge, likha aayega: **"🚀 ROCK X ANIRBAN Bot Engine Started..."**
Iska matlab tumhara bot internet par live ho chuka hai! Jao aur Telegram par apne bot ko `/start` bhej kar dekho.

---

### 👑 Pura Control Tumhare Hath Mein Hai (Admin Commands)
Bot chalu hone ke baad, tum Telegram par hi yeh commands use kar sakte ho:
* `/autolike 123456789 30` : Kisi user ki UID ko 30 din ke liye auto-like par laga dega (Roz subah 6 baje apne aap likes milenge).
* `/addadmin USER_ID` : Kisi apne dost ko bot ka admin banane ke liye.
* `/runnowind` : Agar subah 6 baje ka wait nahi karna, toh yeh command dalo aur bot abhi ke abhi sabko likes bhej dega!

Agar aur kuch dekhna ho toh bot ko Telegram par `/help` likh kar bhej dena, wo sab bata dega. Enjoy!