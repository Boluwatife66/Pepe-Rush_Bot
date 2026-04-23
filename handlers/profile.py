"""
PepeRush Bot — Profile handler
"""

from telegram import Update
from telegram.ext import ContextTypes

import database as db
from ui import MAIN_KEYBOARD
from config import BOT_TOKEN


async def profile_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user    = update.effective_user
    db_user = db.get_user(user.id)

    if not db_user:
        await update.message.reply_text("Please /start the bot first.")
        return

    balance        = db_user["balance"]
    referral_count = db_user["referral_count"]
    wallet         = db_user["wallet"] or "❌ Not set"
    joined         = "✅ Yes" if db_user["joined_channels"] else "❌ No"

    # Build referral link
    bot_info = await context.bot.get_me()
    bot_username = bot_info.username
    ref_link = f"https://t.me/{bot_username}?start={user.id}"

    await update.message.reply_text(
        f"📊 <b>Your Profile</b>\n\n"
        f"👤 Name: <b>{user.first_name}</b>\n"
        f"🆔 User ID: <code>{user.id}</code>\n"
        f"💰 Balance: <b>{balance:,} PEPE</b>\n"
        f"👥 Referrals: <b>{referral_count}</b>\n"
        f"💼 Wallet: <code>{wallet}</code>\n"
        f"✅ Channels Joined: {joined}\n\n"
        f"🔗 Your referral link:\n<code>{ref_link}</code>",
        parse_mode="HTML",
        reply_markup=MAIN_KEYBOARD
    )
