"""
PepeRush Bot — UI Utilities (keyboards, shared markup)
"""

from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton


# ─────────────────────────────────────────────────────────────────────────────
# Main reply keyboard
# ─────────────────────────────────────────────────────────────────────────────

MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["📊 Profile", "👥 Referral"],
        ["🎁 Daily Bonus", "🏆 Leaderboard"],
        ["💼 Wallet", "💸 Withdraw"],
    ],
    resize_keyboard=True,
    one_time_keyboard=False,
)


# ─────────────────────────────────────────────────────────────────────────────
# Inline keyboards
# ─────────────────────────────────────────────────────────────────────────────

def human_check_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ I am Human", callback_data="human_check")]
    ])


def joined_keyboard(tasks: list) -> InlineKeyboardMarkup:
    """Build join-wall keyboard with task buttons + Joined check."""
    buttons = []
    for task in tasks:
        label = "📢 Join Channel" if task["platform"] == "telegram" else "💬 Join WhatsApp"
        buttons.append([InlineKeyboardButton(label, url=task["link"])])
    buttons.append([InlineKeyboardButton("✅ I have Joined All", callback_data="joined")])
    return InlineKeyboardMarkup(buttons)


def withdraw_confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Confirm",  callback_data="withdraw_confirm"),
            InlineKeyboardButton("❌ Cancel",   callback_data="withdraw_cancel"),
        ]
    ])
