"""
PepeRush Bot — Configuration
"""

import os
# ── Bot credentials ───────────────────────────────────────────────────────────
BOT_TOKEN: str ="8715232497:AAHZ5_l_NYoAWy8JxdiKyVtFDm_qa2tyFEY"

# ── Admin ─────────────────────────────────────────────────────────────────────
ADMIN_ID: int = 8309843074

# ── Economy ───────────────────────────────────────────────────────────────────
REFERRAL_REWARD: int    = 10_000   # PEPE per successful referral
DAILY_BONUS: int        = 1_000    # PEPE per day
MIN_WITHDRAW: int       = 50_000   # minimum withdrawal threshold
DAILY_COOLDOWN: int     = 86_400   # 24 hours in seconds
WITHDRAW_COOLDOWN: int  = 3_600    # 1 hour in seconds
REFERRAL_DELAY: int     = 30       # seconds before referral reward granted

# ── Payout notification channel ───────────────────────────────────────────────
PAYOUT_CHANNEL: str = "https://t.me/+H6oH96FgLi44ZDVk"

# ── Database ──────────────────────────────────────────────────────────────────
DB_PATH: str = os.getenv("DB_PATH", "peperush.db")

# ── Warning text shown before join wall ───────────────────────────────────────
WARNING_TEXT: str = (
    "⚠️ <b>WARNING:</b>\n\n"
    "Do not leave any of the required channels after joining.\n"
    "If you leave any channel or group, your withdrawal will <b>NOT</b> be processed."
)
