"""
PepeRush Bot — "✅ I have Joined All" button handler
Verifies Telegram channel membership, grants referral rewards after delay.
"""

import asyncio
import logging
import time

from telegram import Update
from telegram.ext import ContextTypes

import database as db
from channel_checker import check_user_in_all_telegram_channels
from config import REFERRAL_REWARD, REFERRAL_DELAY
from ui import MAIN_KEYBOARD

logger = logging.getLogger(__name__)


async def joined_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user  = query.from_user
    await query.answer("Checking membership…")

    db_user = db.get_user(user.id)
    if not db_user:
        await query.answer("Please start the bot first with /start.", show_alert=True)
        return

    if db_user["is_banned"]:
        await query.answer("You are banned.", show_alert=True)
        return

    # ── Spam guard ─────────────────────────────────────────────────────────────
    spam_count = db.get_suspicious_count(user.id, "join_check_spam")
    if spam_count >= 10:
        db.log_suspicious(user.id, "join_check_spam")
        await query.answer("⚠️ Too many attempts. Wait a few minutes.", show_alert=True)
        return
    db.log_suspicious(user.id, "join_check_spam")

    # ── Verify Telegram channels ───────────────────────────────────────────────
    all_joined, failed_links = await check_user_in_all_telegram_channels(
        context.bot, user.id
    )

    if not all_joined and failed_links:
        failed_text = "\n".join(f"• {l}" for l in failed_links)
        await query.answer(
            f"❌ You haven't joined all required channels yet!\n\n{failed_text}",
            show_alert=True
        )
        return

    # ── Mark as joined ─────────────────────────────────────────────────────────
    db.set_joined_channels(user.id)

    await query.edit_message_text(
        "✅ <b>Membership verified!</b>\n\n"
        "Welcome to <b>PepeRush Bot</b> 🐸\n"
        "Use the menu below to earn PEPE!",
        parse_mode="HTML"
    )
    await context.bot.send_message(
        chat_id=user.id,
        text=(
            "🎉 You're in! Here's your dashboard:\n\n"
            f"💰 Balance: <b>{db.get_balance(user.id):,} PEPE</b>"
        ),
        parse_mode="HTML",
        reply_markup=MAIN_KEYBOARD
    )

    # ── Schedule referral reward (30-second delay) ─────────────────────────────
    pending = db.get_referral_pending(user.id)
    if pending and not db.is_referral_rewarded(user.id):
        referrer_id = pending["referrer_id"]
        context.application.create_task(
            _grant_referral_reward_delayed(context, user.id, referrer_id)
        )


async def _grant_referral_reward_delayed(
    context: ContextTypes.DEFAULT_TYPE,
    new_user_id: int,
    referrer_id: int
):
    """Wait REFERRAL_DELAY seconds then credit referrer (anti-fake delay)."""
    await asyncio.sleep(REFERRAL_DELAY)

    # Re-check: user must still have channels joined and not be rewarded
    db_user = db.get_user(new_user_id)
    if not db_user or not db_user["joined_channels"] or db_user["is_banned"]:
        logger.info("Referral reward skipped for new_user %s (invalid state)", new_user_id)
        return

    if db.is_referral_rewarded(new_user_id):
        return  # already rewarded (duplicate guard)

    # Credit referrer
    db.add_balance(referrer_id, REFERRAL_REWARD)
    db.mark_referral_rewarded(new_user_id, referrer_id)

    referrer = db.get_user(referrer_id)
    new_user = db.get_user(new_user_id)

    try:
        await context.bot.send_message(
            chat_id=referrer_id,
            text=(
                f"🎉 <b>New referral joined!</b>\n\n"
                f"👤 {new_user['first_name']} (@{new_user['username'] or 'N/A'}) "
                f"completed all tasks.\n"
                f"💰 You earned <b>{REFERRAL_REWARD:,} PEPE</b>!\n\n"
                f"📊 New balance: <b>{db.get_balance(referrer_id):,} PEPE</b>"
            ),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.warning("Could not notify referrer %s: %s", referrer_id, e)
