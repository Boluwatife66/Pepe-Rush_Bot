"""
PepeRush Bot — Admin Commands
/admin_stats, /add_task, /remove_task, /add_balance
"""

import asyncio
import logging
import time

from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import TelegramError

import database as db
from config import ADMIN_ID
from ui import MAIN_KEYBOARD

logger = logging.getLogger(__name__)


def _is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID


# ─────────────────────────────────────────────────────────────────────────────
# /admin_stats
# ─────────────────────────────────────────────────────────────────────────────

async def admin_stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Unauthorised.")
        return

    stats = db.get_stats()
    tasks = db.get_active_tasks()

    tg_tasks = [t for t in tasks if t["platform"] == "telegram"]
    wa_tasks = [t for t in tasks if t["platform"] == "whatsapp"]

    await update.message.reply_text(
        f"📊 <b>PepeRush Admin Stats</b>\n\n"
        f"👥 Total Users: <b>{stats['total_users']:,}</b>\n"
        f"💸 Total Withdrawals: <b>{stats['total_withdrawals']:,}</b>\n"
        f"⏳ Pending Withdrawals: <b>{stats['pending_withdrawals']:,}</b>\n"
        f"💰 Total PEPE Paid Out: <b>{stats['total_pepe_out']:,}</b>\n\n"
        f"📢 Telegram Tasks: {len(tg_tasks)}\n"
        f"💬 WhatsApp Tasks: {len(wa_tasks)}\n\n"
        f"<b>Active Tasks:</b>\n" +
        "\n".join(f"• [{t['platform'].upper()}] {t['link']}" for t in tasks),
        parse_mode="HTML"
    )


# ─────────────────────────────────────────────────────────────────────────────
# /add_task <platform> <link>
# ─────────────────────────────────────────────────────────────────────────────

async def add_task_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Unauthorised.")
        return

    args = context.args
    if len(args) < 2:
        await update.message.reply_text(
            "Usage:\n"
            "/add_task telegram <link>\n"
            "/add_task whatsapp <link>"
        )
        return

    platform = args[0].lower()
    link     = args[1]

    if platform not in ("telegram", "whatsapp"):
        await update.message.reply_text("❌ Platform must be 'telegram' or 'whatsapp'.")
        return

    db.add_task(platform, link)
    await update.message.reply_text(
        f"✅ Task added!\n\nPlatform: {platform}\nLink: {link}"
    )

    # ── Auto-broadcast for new Telegram channels ──────────────────────────────
    if platform == "telegram":
        await update.message.reply_text("📢 Broadcasting new channel to all users…")
        user_ids = db.get_all_user_ids()
        sent, failed = 0, 0
        for uid in user_ids:
            try:
                await context.bot.send_message(
                    chat_id=uid,
                    text=(
                        f"📢 <b>New Channel Added!</b>\n\n"
                        f"Join now to remain eligible for withdrawals:\n"
                        f"{link}\n\n"
                        "⚠️ <b>This is now required.</b> Not joining will block your withdrawal."
                    ),
                    parse_mode="HTML"
                )
                sent += 1
            except TelegramError:
                failed += 1
            await asyncio.sleep(0.05)  # rate-limit friendly

        # Mark all verified users as needing re-verification
        # (reset joined_channels so they see join wall again)
        import sqlite3
        from database import get_conn
        with get_conn() as conn:
            conn.execute(
                "UPDATE users SET joined_channels=0 WHERE human_verified=1 AND is_banned=0"
            )

        await update.message.reply_text(
            f"✅ Broadcast complete.\n📨 Sent: {sent} | ❌ Failed: {failed}\n"
            f"🔒 All users must re-verify channel membership."
        )


# ─────────────────────────────────────────────────────────────────────────────
# /remove_task <link>
# ─────────────────────────────────────────────────────────────────────────────

async def remove_task_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Unauthorised.")
        return

    args = context.args
    if not args:
        await update.message.reply_text("Usage: /remove_task <link>")
        return

    link = args[0]
    db.remove_task(link)
    await update.message.reply_text(f"✅ Task removed:\n{link}")


# ─────────────────────────────────────────────────────────────────────────────
# /add_balance <user_id> <amount>
# ─────────────────────────────────────────────────────────────────────────────

async def add_balance_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Unauthorised.")
        return

    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Usage: /add_balance <user_id> <amount>")
        return

    try:
        target_id = int(args[0])
        amount    = int(args[1])
    except ValueError:
        await update.message.reply_text("❌ user_id and amount must be integers.")
        return

    if amount <= 0:
        await update.message.reply_text("❌ Amount must be positive.")
        return

    target = db.get_user(target_id)
    if not target:
        await update.message.reply_text(f"❌ User {target_id} not found.")
        return

    db.add_balance(target_id, amount)
    new_balance = db.get_balance(target_id)

    await update.message.reply_text(
        f"✅ Added <b>{amount:,} PEPE</b> to user <code>{target_id}</code>.\n"
        f"New balance: <b>{new_balance:,} PEPE</b>",
        parse_mode="HTML"
    )

    try:
        await context.bot.send_message(
            chat_id=target_id,
            text=(
                f"🎁 <b>Admin Balance Top-Up!</b>\n\n"
                f"+{amount:,} PEPE added to your account.\n"
                f"New balance: <b>{new_balance:,} PEPE</b> 🐸"
            ),
            parse_mode="HTML"
        )
    except TelegramError:
        pass
