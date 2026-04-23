"""
PepeRush Bot — Referral info handler
"""

from telegram import Update
from telegram.ext import ContextTypes

import database as db
from ui import MAIN_KEYBOARD
from config import REFERRAL_REWARD


async def referral_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user    = update.effective_user
    db_user = db.get_user(user.id)

    if not db_user or not db_user["joined_channels"]:
        await update.message.reply_text(
            "⚠️ You need to join all required channels first.\nUse /start to begin."
        )
        return

    bot_info     = await context.bot.get_me()
    ref_link     = f"https://t.me/{bot_info.username}?start={user.id}"
    ref_count    = db_user["referral_count"]
    earned       = ref_count * REFERRAL_REWARD

    await update.message.reply_text(
        f"👥 <b>Referral System</b>\n\n"
        f"🔗 Your link:\n<code>{ref_link}</code>\n\n"
        f"💰 Reward per referral: <b>{REFERRAL_REWARD:,} PEPE</b>\n"
        f"👥 Total referrals: <b>{ref_count}</b>\n"
        f"💎 Total earned from referrals: <b>{earned:,} PEPE</b>\n\n"
        f"📌 <b>Rules:</b>\n"
        f"• Your friend must join ALL required channels\n"
        f"• They must click ✅ Joined\n"
        f"• Reward is credited after {30} seconds (anti-bot delay)\n"
        f"• Self-referral is blocked",
        parse_mode="HTML",
        reply_markup=MAIN_KEYBOARD
    )
