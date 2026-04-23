# 🐸 PepeRush Bot

A full-featured Telegram task & referral bot built with **python-telegram-bot v21 (async)** and **SQLite**.

---

## 📁 Project Structure

```
peperush_bot/
├── main.py                  # Entry point, handler registration
├── config.py                # All constants & env vars
├── database.py              # SQLite layer (WAL mode, thread-safe)
├── channel_checker.py       # getChatMember verification
├── ui.py                    # Keyboards & shared markup
├── requirements.txt
└── handlers/
    ├── start.py             # /start, human captcha, join wall
    ├── join.py              # ✅ Joined button + referral delay
    ├── profile.py           # 📊 Profile
    ├── referral.py          # 👥 Referral info
    ├── daily.py             # 🎁 Daily bonus
    ├── leaderboard.py       # 🏆 Top 10
    ├── wallet.py            # 💼 Wallet set/view
    ├── withdraw.py          # 💸 Withdraw with all guards
    └── admin.py             # Admin commands + broadcast
```

---

## ⚙️ Setup

### 1. Create your bot
1. Open [@BotFather](https://t.me/BotFather) → `/newbot`
2. Copy your **Bot Token**

### 2. Set the token
**Option A — Environment variable (recommended for deployment):**
```bash
export BOT_TOKEN="your_token_here"
```

**Option B — Edit config.py directly:**
```python
BOT_TOKEN = "your_token_here"
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run locally
```bash
python main.py
```

---

## 🔧 Channel Verification Setup

Because the required channels use **private invite links** (`+xxx` format), the bot cannot automatically resolve their chat IDs via `getChat`. You have two options:

### Option A — Make bot admin in each channel (best)
1. Add your bot as **admin** in each Telegram channel
2. Get the **chat_id** for each channel (use [@userinfobot](https://t.me/userinfobot) or forward a message to [@RawDataBot](https://t.me/RawDataBot))
3. Update the `tasks` table manually:
```sql
UPDATE tasks SET chat_id = '-1001234567890' WHERE link = 'https://t.me/+r-RTbZy7RT81NTdk';
```

### Option B — Trust-based (no bot admin needed)
Without chat_ids set, the bot will show the join wall but skip `getChatMember` verification for that channel. Membership is taken on trust.

---

## 🚀 Deploy to Railway

1. Create a [Railway](https://railway.app) account
2. Create new project → **Deploy from GitHub repo**
3. Add environment variable:
   - `BOT_TOKEN` = `your_token`
4. Railway auto-detects Python from `requirements.txt`
5. Set start command: `python main.py`

---

## 🚀 Deploy to Render

1. Create a [Render](https://render.com) account
2. New → **Background Worker** → connect your repo
3. Build command: `pip install -r requirements.txt`
4. Start command: `python main.py`
5. Add env var: `BOT_TOKEN`

For persistence on Render, use a **Render Disk** mounted at `/data` and set:
```bash
DB_PATH=/data/peperush.db
```

---

## 🚀 Deploy to VPS (recommended for production)

```bash
# Clone / upload files
cd /home/user/peperush_bot

# Install deps
pip install -r requirements.txt

# Run with systemd (create /etc/systemd/system/peperush.service):
[Unit]
Description=PepeRush Telegram Bot
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/peperush_bot
ExecStart=/usr/bin/python3 main.py
Restart=always
Environment=BOT_TOKEN=your_token_here

[Install]
WantedBy=multi-user.target

# Enable & start
systemctl daemon-reload
systemctl enable peperush
systemctl start peperush
systemctl status peperush
```

---

## 🤖 Admin Commands

| Command | Description |
|---|---|
| `/admin_stats` | View total users, withdrawals, PEPE paid |
| `/add_task telegram <link>` | Add new required Telegram channel (auto-broadcasts) |
| `/add_task whatsapp <link>` | Add new required WhatsApp group |
| `/remove_task <link>` | Deactivate a task |
| `/add_balance <user_id> <amount>` | Manually credit PEPE to a user |

---

## 💰 Economy Settings (config.py)

| Setting | Default |
|---|---|
| `REFERRAL_REWARD` | 10,000 PEPE |
| `DAILY_BONUS` | 1,000 PEPE |
| `MIN_WITHDRAW` | 50,000 PEPE |
| `DAILY_COOLDOWN` | 86,400s (24h) |
| `WITHDRAW_COOLDOWN` | 3,600s (1h) |
| `REFERRAL_DELAY` | 30s (anti-bot) |

---

## 🛡️ Anti-Fake Features

- ❌ Bots blocked (is_bot check)
- ❌ Users without username blocked
- ✅ Human captcha button required
- ⏱️ 30-second delay before referral reward
- 🚫 Self-referral blocked
- 🚫 Duplicate referral rewards blocked
- 📊 Suspicious activity logged
- 🔒 Live channel re-check on every withdrawal
- 🔁 Spam detection on join checks and withdrawals

---

## ⚠️ Important Notes

1. **WhatsApp links** cannot be verified programmatically — they are shown as required tasks but rely on user honesty.
2. **Private Telegram invite links** require manual `chat_id` setup for `getChatMember` to work.
3. The bot uses **polling** mode. For high traffic, switch to webhooks.
4. **SQLite WAL mode** is enabled for concurrency safety.
