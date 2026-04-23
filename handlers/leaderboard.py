"""
PepeRush Bot — Leaderboard handler (top 10 inviters)
"""

from telegram import Update
from telegram.ext import ContextTypes

import database as db
from ui import MAIN_KEYBOARD


MEDALS = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]


async def leaderboard_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = db.get_leaderboard(10)

    if not rows:
        await update.message.reply_text(
            "🏆 <b>Leaderboard</b>\n\nNo referrals yet. Be the first! 🐸",
            parse_mode="HTML",
            reply_markup=MAIN_KEYBOARD
        )
        return

    lines = ["🏆 <b>Top 10 Inviters</b>\n"]
    for i, row in enumerate(rows):
        medal    = MEDALS[i] if i < len(MEDALS) else f"{i+1}."
        name     = row["first_name"] or "Unknown"
        username = f"@{row['username']}" if row["username"] else ""
        count    = row["referral_count"]
        lines.append(f"{medal} {name} {username} — <b>{count}</b> referrals")

    await update.message.reply_text(
        "\n".join(lines),
        parse_mode="HTML",
        reply_markup=MAIN_KEYBOARD
    )
