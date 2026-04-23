"""
PepeRush Bot — Withdraw handler
Guards: min balance, 1-hr cooldown, 1 pending max, wallet required, channels joined
"""

import time
import logging

from telegram import Update
from telegram.ext import ContextTypes

import database as db
from config import MIN_WITHDRAW, WITHDRAW_COOLDOWN, ADMIN_ID
from ui import MAIN_KEYBOARD, withdraw_confirm_keyboard
from channel_checker import check_user_in_all_telegram_channels

logger = logging.getLogger(__name__)

WITHDRAW_AMOUNT_KEY = "pending_withdraw_amount"


async def withdraw_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user    = update.effective_user
    db_user = db.get_user(user.id)

    if not db_user:
        await update.message.reply_text("Please /start first.")
        return

    # ── Spam guard ─────────────────────────────────────────────────────────────
    spam = db.get_suspicious_count(user.id, "withdraw_attempt")
    if spam >= 5:
        db.log_suspicious(user.id, "withdraw_spam")
        await update.message.reply_text(
            "⚠️ Too many withdrawal attempts. Please wait before trying again."
        )
        return
    db.log_suspicious(user.id, "withdraw_attempt")

    # ── Must have joined channels ──────────────────────────────────────────────
    if not db_user["joined_channels"]:
        await update.message.reply_text("⚠️ Join all required channels first. Use /start.")
        return

    # ── Live channel re-check ─────────────────────────────────────────────────
    all_joined, failed = await check_user_in_all_telegram_channels(context.bot, user.id)
    if not all_joined and failed:
        db.log_suspicious(user.id, "withdraw_channel_bypass")
        await update.message.reply_text(
            "❌ <b>Withdrawal blocked!</b>\n\n"
            "You have left one or more required channels.\n"
            "Re-join all channels and try again.\n\n"
            "⚠️ Leaving channels after joining will block your withdrawal.",
            parse_mode="HTML",
            reply_markup=MAIN_KEYBOARD
        )
        return

    # ── Wallet required ────────────────────────────────────────────────────────
    wallet = db_user["wallet"]
    if not wallet:
        await update.message.reply_text(
            "❌ You haven't set a wallet address yet.\nTap 💼 Wallet to set one.",
            reply_markup=MAIN_KEYBOARD
        )
        return

    # ── Min balance ────────────────────────────────────────────────────────────
    balance = db_user["balance"]
    if balance < MIN_WITHDRAW:
        needed = MIN_WITHDRAW - balance
        await update.message.reply_text(
            f"❌ <b>Insufficient balance!</b>\n\n"
            f"💰 Your balance: <b>{balance:,} PEPE</b>\n"
            f"📉 Minimum: <b>{MIN_WITHDRAW:,} PEPE</b>\n"
            f"🔜 You need <b>{needed:,} more PEPE</b>",
            parse_mode="HTML",
            reply_markup=MAIN_KEYBOARD
        )
        return

    # ── 1-hour cooldown ────────────────────────────────────────────────────────
    now       = time.time()
    last_wd   = db_user["last_withdraw"] or 0
    elapsed   = now - last_wd
    remaining = WITHDRAW_COOLDOWN - elapsed

    if elapsed < WITHDRAW_COOLDOWN:
        mins = int(remaining // 60)
        secs = int(remaining % 60)
        await update.message.reply_text(
            f"⏳ Withdrawal cooldown active.\n\nTry again in <b>{mins}m {secs}s</b>.",
            parse_mode="HTML",
            reply_markup=MAIN_KEYBOARD
        )
        return

    # ── Only 1 pending withdrawal ──────────────────────────────────────────────
    if db.has_pending_withdrawal(user.id):
        await update.message.reply_text(
            "⏳ You already have a <b>pending withdrawal</b>.\n"
            "Wait for it to be processed before requesting another.",
            parse_mode="HTML",
            reply_markup=MAIN_KEYBOARD
        )
        return

    # ── Confirmation prompt ────────────────────────────────────────────────────
    context.user_data[WITHDRAW_AMOUNT_KEY] = balance

    await update.message.reply_text(
        f"💸 <b>Withdrawal Confirmation</b>\n\n"
        f"💰 Amount: <b>{balance:,} PEPE</b>\n"
        f"💼 Wallet: <code>{wallet}</code>\n\n"
        f"Confirm your withdrawal?",
        parse_mode="HTML",
        reply_markup=withdraw_confirm_keyboard()
    )


# ─────────────────────────────────────────────────────────────────────────────
# Confirm / Cancel callback
# ─────────────────────────────────────────────────────────────────────────────

async def withdraw_confirm_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query   = update.callback_query
    user    = query.from_user
    data    = query.data
    await query.answer()

    if data == "withdraw_cancel":
        context.user_data.pop(WITHDRAW_AMOUNT_KEY, None)
        await query.edit_message_text("❌ Withdrawal cancelled.", reply_markup=None)
        return

    # ── Confirm ────────────────────────────────────────────────────────────────
    db_user = db.get_user(user.id)
    if not db_user:
        await query.edit_message_text("Session expired. Please /start again.")
        return

    amount = context.user_data.pop(WITHDRAW_AMOUNT_KEY, None)
    wallet = db_user["wallet"]

    if not amount or not wallet:
        await query.edit_message_text("❌ Invalid session. Please try again.")
        return

    # Re-validate balance (race condition guard)
    if db_user["balance"] < MIN_WITHDRAW:
        await query.edit_message_text(
            f"❌ Insufficient balance: {db_user['balance']:,} PEPE", reply_markup=None
        )
        return

    # ── Execute withdrawal ─────────────────────────────────────────────────────
    db.deduct_balance(user.id, amount)
    db.set_last_withdraw(user.id, time.time())
    wd_id = db.create_withdrawal(user.id, amount, wallet)

    # Notify admin
    joined_status = "✅ Joined" if db_user["joined_channels"] else "❌ Not joined"
    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=(
                f"💸 <b>New Withdrawal Request</b>\n\n"
                f"🆔 User ID: <code>{user.id}</code>\n"
                f"👤 Username: @{user.username or 'N/A'}\n"
                f"💰 Amount: <b>{amount:,} PEPE</b>\n"
                f"💼 Wallet: <code>{wallet}</code>\n"
                f"✅ Channels Joined: {joined_status}\n"
                f"📋 Withdrawal ID: #{wd_id}"
            ),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error("Failed to notify admin of withdrawal: %s", e)

    await query.edit_message_text(
        "✅ <b>Withdrawal request sent.</b>\n\n"
        "💸 Payment will be processed within 1 hour.\n\n"
        "⚠️ Do NOT leave any required channels or your payment will be cancelled.",
        parse_mode="HTML",
        reply_markup=None
    )
    await context.bot.send_message(
        chat_id=user.id,
        text=f"📊 Remaining balance: <b>{db.get_balance(user.id):,} PEPE</b>",
        parse_mode="HTML",
        reply_markup=MAIN_KEYBOARD
    )
