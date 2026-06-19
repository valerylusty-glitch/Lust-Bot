"""
Tous les handlers Telegram (commandes, callbacks, messages texte) du
LUST Downloader Bot. Architecture asynchrone, anti-crash : chaque handler
est protégé par un try/except qui logue l'erreur et informe l'utilisateur
proprement, sans jamais faire planter le bot.
"""

import logging
import uuid

from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import TelegramError

import messages
import keyboards
from utils.subscribe import is_user_subscribed, build_subscribe_keyboard
from utils.ratelimit import is_rate_limited, seconds_remaining
from utils.storage import (
    register_user, add_download, get_user_history,
    get_global_stats, get_user_download_count,
)
from utils.downloader import (
    extract_url, fetch_video_info, download_video,
    cleanup_file, DownloadError,
)
from config import MAX_TELEGRAM_FILE_SIZE_MB

logger = logging.getLogger(__name__)

# Stockage temporaire en mémoire des analyses en attente de choix de qualité
# token -> {"url": str}
PENDING_DOWNLOADS = {}


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

async def _require_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Vérifie l'abonnement et envoie le message de blocage si nécessaire.
    Retourne True si l'utilisateur peut continuer."""
    user = update.effective_user
    try:
        subscribed = await is_user_subscribed(context.bot, user.id)
    except Exception as e:
        logger.error(f"Erreur vérification abonnement : {e}")
        subscribed = False

    if not subscribed:
        await update.effective_message.reply_text(
            messages.FORCE_SUB_MESSAGE,
            reply_markup=build_subscribe_keyboard(),
        )
        return False
    return True


async def _safe_error_reply(update: Update):
    try:
        if update.effective_message:
            await update.effective_message.reply_text(messages.GENERIC_ERROR)
    except Exception:
        pass


# --------------------------------------------------------------------------
# Commandes
# --------------------------------------------------------------------------

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        register_user(user.id, user.username or user.first_name or "inconnu")

        if not await _require_subscription(update, context):
            return

        await update.effective_message.reply_text(
            messages.WELCOME,
            reply_markup=keyboards.main_menu_keyboard(),
        )
    except Exception as e:
        logger.error(f"Erreur start_command : {e}")
        await _safe_error_reply(update)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not await _require_subscription(update, context):
            return
        await update.effective_message.reply_text(
            messages.HELP_TEXT, reply_markup=keyboards.back_to_menu_keyboard()
        )
    except Exception as e:
        logger.error(f"Erreur help_command : {e}")
        await _safe_error_reply(update)


# --------------------------------------------------------------------------
# Callback Query (boutons inline)
# --------------------------------------------------------------------------

async def callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
        data = query.data

        if data == "check_subscription":
            await _handle_check_subscription(query, context)
        elif data == "menu_refresh":
            await query.edit_message_text(
                messages.WELCOME, reply_markup=keyboards.main_menu_keyboard()
            )
        elif data == "menu_download":
            await query.edit_message_text(
                messages.ASK_LINK, reply_markup=keyboards.back_to_menu_keyboard()
            )
        elif data == "menu_help":
            await query.edit_message_text(
                messages.HELP_TEXT, reply_markup=keyboards.back_to_menu_keyboard()
            )
        elif data == "menu_dev":
            await query.edit_message_text(
                messages.DEV_TEXT, reply_markup=keyboards.developer_keyboard()
            )
        elif data == "menu_history":
            await _handle_history(query, context)
        elif data == "menu_stats":
            await _handle_stats(query, context)
        elif data.startswith("quality_"):
            await _handle_quality_choice(query, context, data)
        else:
            logger.warning(f"Callback inconnu reçu : {data}")
    except Exception as e:
        logger.error(f"Erreur callback_router ({query.data if query else '?'}) : {e}")
        try:
            await query.message.reply_text(messages.GENERIC_ERROR)
        except Exception:
            pass


async def _handle_check_subscription(query, context):
    user_id = query.from_user.id
    subscribed = await is_user_subscribed(context.bot, user_id)
    if subscribed:
        await query.edit_message_text(
            messages.ACCESS_GRANTED, reply_markup=keyboards.main_menu_keyboard()
        )
    else:
        await query.edit_message_text(
            messages.FORCE_SUB_MESSAGE, reply_markup=build_subscribe_keyboard()
        )


async def _handle_history(query, context):
    history = get_user_history(query.from_user.id, limit=10)
    if not history:
        await query.edit_message_text(
            messages.NO_HISTORY, reply_markup=keyboards.back_to_menu_keyboard()
        )
        return

    lines = ["📜 TON HISTORIQUE\n"]
    for platform, title, created_at in history:
        date = created_at.split("T")[0] if created_at else "?"
        safe_title = (title or "Sans titre")[:40]
        lines.append(f"• [{platform}] {safe_title} — {date}")

    text = messages.with_footer("\n".join(lines))
    await query.edit_message_text(text, reply_markup=keyboards.back_to_menu_keyboard())


async def _handle_stats(query, context):
    stats = get_global_stats()
    user_count = get_user_download_count(query.from_user.id)
    text = messages.with_footer(
        "📊 STATISTIQUES\n\n"
        f"👥 Utilisateurs : {stats['total_users']}\n"
        f"📥 Téléchargements totaux : {stats['total_downloads']}\n"
        f"🔥 Plateforme la plus utilisée : {stats['top_platform']}\n\n"
        f"🙋 Tes téléchargements : {user_count}"
    )
    await query.edit_message_text(text, reply_markup=keyboards.back_to_menu_keyboard())


async def _handle_quality_choice(query, context, data: str):
    # format attendu : quality_{token}_{quality}
    try:
        _, token, quality_str = data.split("_", 2)
    except ValueError:
        await query.message.reply_text(messages.GENERIC_ERROR)
        return

    pending = PENDING_DOWNLOADS.pop(token, None)
    if not pending:
        await query.edit_message_text(messages.GENERIC_ERROR)
        return

    quality = None if quality_str == "best" else int(quality_str)
    await query.edit_message_text(messages.DOWNLOADING)
    await _process_download(query.message, context, pending["url"], quality, query.from_user)


# --------------------------------------------------------------------------
# Messages texte (détection automatique de liens)
# --------------------------------------------------------------------------

async def text_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        register_user(user.id, user.username or user.first_name or "inconnu")

        if not await _require_subscription(update, context):
            return

        if is_rate_limited(user.id):
            wait = round(seconds_remaining(user.id), 1)
            await update.message.reply_text(
                messages.with_footer(f"⏳ Merci d'attendre encore {wait}s avant une nouvelle requête.")
            )
            return

        text = update.message.text or ""
        url = extract_url(text)

        if not url:
            await update.message.reply_text(messages.NOT_A_LINK)
            return

        await _handle_new_link(update.message, context, url, user)
    except Exception as e:
        logger.error(f"Erreur text_message_handler : {e}")
        await _safe_error_reply(update)


async def _handle_new_link(message, context, url, user):
    status_msg = await message.reply_text(messages.ANALYZING)

    try:
        info = await fetch_video_info(url)
    except DownloadError:
        await status_msg.edit_text(messages.INVALID_LINK)
        return
    except Exception as e:
        logger.error(f"Erreur fetch_video_info ({url}) : {e}")
        await status_msg.edit_text(messages.GENERIC_ERROR)
        return

    qualities = info.get("qualities") or []

    if len(qualities) > 1:
        token = uuid.uuid4().hex[:12]
        PENDING_DOWNLOADS[token] = {"url": url}
        text = messages.with_footer(
            f"🎬 {info['title']}\n🌐 {info['platform']}\n⏱️ {info['duration']}\n\n"
            "📊 Choisis une qualité :"
        )
        await status_msg.edit_text(text, reply_markup=keyboards.quality_keyboard(qualities, token))
        return

    await status_msg.edit_text(messages.DOWNLOADING)
    await _process_download(status_msg, context, url, None, user)


async def _process_download(status_msg, context, url, quality, user):
    path = None
    try:
        result = await download_video(url, quality=quality)
    except DownloadError:
        await status_msg.edit_text(messages.INVALID_LINK)
        return
    except Exception as e:
        logger.error(f"Erreur download_video ({url}) : {e}")
        await status_msg.edit_text(messages.GENERIC_ERROR)
        return

    path = result["path"]
    try:
        if result["size_mb"] > MAX_TELEGRAM_FILE_SIZE_MB:
            await status_msg.edit_text(messages.FILE_TOO_LARGE)
            return

        await status_msg.edit_text(messages.UPLOADING)

        caption = messages.video_caption(
            result["title"], result["platform"], result["size_mb"], result["duration"]
        )

        with open(path, "rb") as video_file:
            await context.bot.send_video(
                chat_id=status_msg.chat_id,
                video=video_file,
                caption=caption,
                supports_streaming=True,
                read_timeout=120,
                write_timeout=120,
                connect_timeout=60,
            )

        add_download(
            user.id, user.username or user.first_name or "inconnu",
            result["platform"], result["title"], url,
            result["size_mb"], result["duration"],
        )

        try:
            await status_msg.delete()
        except Exception:
            pass

    except TelegramError as e:
        logger.error(f"Erreur envoi Telegram ({url}) : {e}")
        await status_msg.edit_text(messages.GENERIC_ERROR)
    except Exception as e:
        logger.error(f"Erreur _process_download ({url}) : {e}")
        await status_msg.edit_text(messages.GENERIC_ERROR)
    finally:
        if path:
            cleanup_file(path)


# --------------------------------------------------------------------------
# Gestion globale des erreurs (anti-crash)
# --------------------------------------------------------------------------

async def global_error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Exception non gérée : {context.error}", exc_info=context.error)
    try:
        if isinstance(update, Update) and update.effective_message:
            await update.effective_message.reply_text(messages.GENERIC_ERROR)
    except Exception:
        pass
