"""
PepeRush Bot — Channel Verification Utilities
"""

import logging
from telegram import Bot
from telegram.error import TelegramError
import database as db

logger = logging.getLogger(__name__)


async def check_user_in_all_telegram_channels(bot: Bot, user_id: int) -> tuple[bool, list[str]]:
    """
    Returns (all_joined: bool, failed_links: list[str]).
    Only checks tasks that have a known chat_id.
    WhatsApp tasks are skipped (unverifiable).
    """
    tasks = db.get_telegram_tasks()
    failed = []

    for task in tasks:
        chat_id = task["chat_id"]
        if not chat_id:
            # No chat_id resolved yet — skip (benefit of doubt during early setup)
            continue
        try:
            member = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
            if member.status in ("left", "kicked", "banned"):
                failed.append(task["link"])
        except TelegramError as e:
            logger.warning("getChatMember error for %s / %s: %s", chat_id, user_id, e)
            # If bot isn't admin in that channel, skip gracefully
            continue

    all_joined = len(failed) == 0
    return all_joined, failed


async def resolve_task_chat_ids(bot: Bot):
    """
    Attempt to resolve invite-link → chat_id for Telegram tasks that don't
    have a chat_id yet.  Requires bot to be admin in those channels.
    Note: Private invite links (+xxx) can't be resolved via getChat easily,
    so admins should set chat_ids manually or the bot will skip verification.
    """
    tasks = db.get_telegram_tasks()
    for task in tasks:
        if task["chat_id"]:
            continue
        try:
            # Works only if the link is a public username (@channel)
            chat = await bot.get_chat(task["link"])
            db.update_task_chat_id(task["id"], str(chat.id))
            logger.info("Resolved chat_id %s for %s", chat.id, task["link"])
        except TelegramError:
            pass  # Private invite link — needs manual admin registration
