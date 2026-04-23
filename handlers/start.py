"""
PepeRush Bot — /start handler
Handles: new user registration, human captcha, referral tracking, join wall
"""

import asyncio
import logging
import time

from telegram import Update
from telegram.ext import ContextTypes

import database as db
from config import WARNING_TEXT, REFERRAL_DELAY, REFERRAL_REWARD
from ui import MAIN_KEYBOARD, human_check_keyboard, joined_keyboard

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# /start
# ─────────────────────────────────────────────────────────────────────────────

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    # ── Anti-fake: block bots ─────────────────────────────────────────────────
    if user.is_bot:
        return

    # ── Anti-fake: require username ───────────────────────────────────────────
    if not user.username:
        await update.message.reply_text(
            "❌ You must have a Telegram <b>username</b> set before using PepeRush Bot.\n\n"
            "Go to <i>Settings → Edit Profile → Username</i> and come back.",
            parse_mode="HTML"
        )
        return

    # ── Register / update user ────────────────────────────────────────────────
    db.upsert_user(user.id, user.username, user.first_name)
    db_user = db.get_user(user.id)

    if db_user["is_banned"]:
        await update.message.reply_text("🚫 You are banned from PepeRush Bot.")
        return

    # ── Parse referral payload ────────────────────────────────────────────────
    args = context.args
    if args:
        try:
            referrer_id = int(args[0])
            if referrer_id != user.id:  # no self-referral
                referrer = db.get_user(referrer_id)
                if referrer and not db_user["referrer_id"]:
                    db.set_referrer(user.id, referrer_id)
                    db.add_referral_pending(user.id, referrer_id)
            else:
                db.log_suspicious(user.id, "self_referral_attempt")
        except (ValueError, TypeError):
            pass

    # ── Human captcha (first-time only) ──────────────────────────────────────
    if not db_user["human_verified"]:
        await update.message.reply_text(
            "👋 Welcome to <b>PepeRush Bot</b>!\n\n"
            "Before we start, please confirm you are human:",
            parse_mode="HTML",
            reply_markup=human_check_keyboard()
        )
        return

    # ── Join wall ─────────────────────────────────────────────────────────────
    if not db_user["joined_channels"]:
        await _show_join_wall(update, context)
        return

    # ── Already fully onboarded ───────────────────────────────────────────────
    await update.message.reply_text(
        f"👋 Welcome back, <b>{user.first_name}</b>!\n\n"
        f"💰 Balance: <b>{db.get_balance(user.id):,} PEPE</b>\n\n"
        "Use the menu below 👇",
        parse_mode="HTML",
        reply_markup=MAIN_KEYBOARD
    )


# ─────────────────────────────────────────────────────────────────────────────
# ✅ I am Human — callback
# ─────────────────────────────────────────────────────────────────────────────

async def human_verification_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user  = query.from_user
    await query.answer()

    if user.is_bot or not user.username:
        await query.edit_message_text("❌ You must have a Telegram username to use this bot.")
        return

    db.set_human_verified(user.id)
    db_user = db.get_user(user.id)

    if not db_user["joined_channels"]:
        await query.edit_message_text("✅ Verification passed! Now join the required channels:")
        await _show_join_wall_via_bot(context.bot, user.id, query.message.chat_id)
    else:
        await query.edit_message_text(
            "✅ You're all set!",
            reply_markup=None
        )
        await context.bot.send_message(
            chat_id=user.id,
            text=f"👋 Welcome back, <b>{user.first_name}</b>!",
            parse_mode="HTML",
            reply_markup=MAIN_KEYBOARD
        )


# ─────────────────────────────────────────────────────────────────────────────
# Join wall helpers
# ─────────────────────────────────────────────────────────────────────────────

async def _show_join_wall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tasks = db.get_active_tasks()
    await update.message.reply_text(WARNING_TEXT, parse_mode="HTML")
    await update.message.reply_text(
        "📋 <b>You must join ALL channels and groups below</b> to use PepeRush Bot.\n\n"
        "After joining everything, tap <b>✅ I have Joined All</b>.",
        parse_mode="HTML",
        reply_markup=joined_keyboard(tasks)
    )


async def _show_join_wall_via_bot(bot, user_id: int, chat_id: int):
    tasks = db.get_active_tasks()
    await bot.send_message(
        chat_id=chat_id,
        text=WARNING_TEXT,
        parse_mode="HTML"
    )
    await bot.send_message(
        chat_id=chat_id,
        text=(
            "📋 <b>You must join ALL channels and groups below</b> to use PepeRush Bot.\n\n"
            "After joining everything, tap <b>✅ I have Joined All</b>."
        ),
        parse_mode="HTML",
        reply_markup=joined_keyboard(tasks)
    )
