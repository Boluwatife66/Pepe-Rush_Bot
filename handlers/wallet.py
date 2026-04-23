"""
PepeRush Bot — Wallet handler
State machine: user taps 💼 Wallet → prompted → sends address
"""

import logging
from telegram import Update, ForceReply
from telegram.ext import ContextTypes

import database as db
from ui import MAIN_KEYBOARD

logger = logging.getLogger(__name__)

AWAITING_WALLET = "awaiting_wallet"


async def wallet_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user    = update.effective_user
    db_user = db.get_user(user.id)

    if not db_user or not db_user["joined_channels"]:
        await update.message.reply_text("⚠️ Join all channels first. Use /start.")
        return

    current = db_user["wallet"] or "❌ Not set"
    context.user_data[AWAITING_WALLET] = True

    await update.message.reply_text(
        f"💼 <b>Wallet Settings</b>\n\n"
        f"Current wallet: <code>{current}</code>\n\n"
        f"Enter Your BONK\SOL wallet address\n"
        f"⚠️ PEPE (Ethereum) addresses are NOT supported.Only Solana Wallets Accepted.\n"
        f"(or type /cancel to go back):",
        parse_mode="HTML",
        reply_markup=ForceReply(selective=True)
    )


async def wallet_input_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Capture wallet address when user is in wallet-input state."""
    user = update.effective_user

    if not context.user_data.get(AWAITING_WALLET):
        return  # Not in wallet-setting mode — ignore

    text = update.message.text.strip()

    if text == "/cancel":
        context.user_data.pop(AWAITING_WALLET, None)
        await update.message.reply_text("❌ Wallet update cancelled.", reply_markup=MAIN_KEYBOARD)
        return

    # Basic validation: non-empty, reasonable length
    if len(text) < 10 or len(text) > 200:
        await update.message.reply_text(
            "⚠️ That doesn't look like a valid wallet address. Try again or /cancel."
        )
        return

    db.set_wallet(user.id, text)
    context.user_data.pop(AWAITING_WALLET, None)

    await update.message.reply_text(
        f"✅ <b>Wallet saved!</b>\n\n"
        f"<code>{text}</code>",
        parse_mode="HTML",
        reply_markup=MAIN_KEYBOARD
    )
