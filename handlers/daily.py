"""
PepeRush Bot — Daily Bonus handler (1,000 PEPE / 24 h)
"""

import time
from telegram import Update
from telegram.ext import ContextTypes

import database as db
from config import DAILY_BONUS, DAILY_COOLDOWN
from ui import MAIN_KEYBOARD


async def daily_bonus_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user    = update.effective_user
    db_user = db.get_user(user.id)

    if not db_user:
        await update.message.reply_text("Please /start first.")
        return

    if not db_user["joined_channels"]:
        await update.message.reply_text(
            "⚠️ Join all required channels first. Use /start."
        )
        return

    now       = time.time()
    last      = db_user["last_daily"] or 0
    elapsed   = now - last
    remaining = DAILY_COOLDOWN - elapsed

    if elapsed < DAILY_COOLDOWN:
        hours   = int(remaining // 3600)
        minutes = int((remaining % 3600) // 60)
        seconds = int(remaining % 60)
        await update.message.reply_text(
            f"⏳ Daily bonus already claimed!\n\n"
            f"Next claim in: <b>{hours:02d}:{minutes:02d}:{seconds:02d}</b>",
            parse_mode="HTML",
            reply_markup=MAIN_KEYBOARD
        )
        return

    db.add_balance(user.id, DAILY_BONUS)
    db.set_last_daily(user.id, now)

    new_balance = db.get_balance(user.id)
    await update.message.reply_text(
        f"🎁 <b>Daily Bonus Claimed!</b>\n\n"
        f"💰 +{DAILY_BONUS:,} PEPE added!\n"
        f"📊 New balance: <b>{new_balance:,} PEPE</b>\n\n"
        f"Come back in 24 hours for your next bonus! 🐸",
        parse_mode="HTML",
        reply_markup=MAIN_KEYBOARD
    )
