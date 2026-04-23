"""
PepeRush Bot — Main Entry Point
python-telegram-bot v20+ async
"""

import logging
import asyncio
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters
)

from config import BOT_TOKEN
from database import init_db
from handlers.start import start_handler, human_verification_handler
from handlers.referral import referral_callback
from handlers.join import joined_button_handler
from handlers.profile import profile_handler
from handlers.daily import daily_bonus_handler
from handlers.leaderboard import leaderboard_handler
from handlers.wallet import wallet_handler, wallet_input_handler
from handlers.withdraw import withdraw_handler, withdraw_confirm_handler
from handlers.admin import (
    admin_stats_handler, add_task_handler,
    remove_task_handler, add_balance_handler
)

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def main():
    init_db()
    logger.info("Database initialised.")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # ── Core ──────────────────────────────────────────────
    app.add_handler(CommandHandler("start", start_handler))

    # ── Admin commands ────────────────────────────────────
    app.add_handler(CommandHandler("admin_stats", admin_stats_handler))
    app.add_handler(CommandHandler("add_task", add_task_handler))
    app.add_handler(CommandHandler("remove_task", remove_task_handler))
    app.add_handler(CommandHandler("add_balance", add_balance_handler))

    # ── Inline / callback buttons ─────────────────────────
    app.add_handler(CallbackQueryHandler(human_verification_handler, pattern="^human_check$"))
    app.add_handler(CallbackQueryHandler(joined_button_handler,       pattern="^joined$"))
    app.add_handler(CallbackQueryHandler(withdraw_confirm_handler,    pattern="^withdraw_confirm$"))
    app.add_handler(CallbackQueryHandler(withdraw_confirm_handler,    pattern="^withdraw_cancel$"))

    # ── Reply keyboard ────────────────────────────────────
    app.add_handler(MessageHandler(filters.Regex(r"^📊 Profile$"),      profile_handler))
    app.add_handler(MessageHandler(filters.Regex(r"^👥 Referral$"),     referral_callback))
    app.add_handler(MessageHandler(filters.Regex(r"^🎁 Daily Bonus$"),  daily_bonus_handler))
    app.add_handler(MessageHandler(filters.Regex(r"^🏆 Leaderboard$"),  leaderboard_handler))
    app.add_handler(MessageHandler(filters.Regex(r"^💼 Wallet$"),       wallet_handler))
    app.add_handler(MessageHandler(filters.Regex(r"^💸 Withdraw$"),     withdraw_handler))

    # ── Wallet address capture ────────────────────────────
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & ~filters.Regex(
            r"^(📊 Profile|👥 Referral|🎁 Daily Bonus|🏆 Leaderboard|💼 Wallet|💸 Withdraw)$"
        ),
        wallet_input_handler
    ))

    logger.info("PepeRush Bot starting…")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
