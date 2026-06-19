from __future__ import annotations

"""
Logique de téléchargement vidéo : détection de plateforme, extraction des
informations (titre, durée, formats disponibles) et téléchargement réel
du fichier, via yt-dlp pour les plateformes supportées ou un téléchargement
direct (aiohttp) pour les liens pointant vers un fichier vidéo brut
(.mp4, .mov, etc.).
"""

import os
import re
import logging
import asyncio
import uuid

import aiohttp
import yt_dlp

from config import DOWNLOAD_DIR, SUPPORTED_QUALITIES

logger = logging.getLogger(__name__)

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

DIRECT_VIDEO_EXTENSIONS = (".mp4", ".mov", ".mkv", ".webm", ".avi")

PLATFORM_PATTERNS = {
    "TikTok": r"(tiktok\.com)",
    "Instagram": r"(instagram\.com)",
    "YouTube": r"(youtube\.com|youtu\.be)",
    "Facebook": r"(facebook\.com|fb\.watch)",
    "Twitter / X": r"(twitter\.com|x\.com)",
    "Pinterest": r"(pinterest\.com|pin\.it)",
}

URL_REGEX = re.compile(r"https?://[^\s]+")


class DownloadError(Exception):
    """Exception levée lorsqu'une vidéo ne peut pas être récupérée."""
    pass


def extract_url(text: str) -> str | None:
    """Extrait la première URL trouvée dans un message."""
    match = URL_REGEX.search(text or "")
    return match.group(0) if match else None


def detect_platform(url: str) -> str:
    """Détermine la plateforme d'origine à partir de l'URL."""
    for platform, pattern in PLATFORM_PATTERNS.items():
        if re.search(pattern, url, re.IGNORECASE):
            return platform
    if url.lower().split("?")[0].endswith(DIRECT_VIDEO_EXTENSIONS):
        return "Lien direct"
    return "Inconnu"


def is_direct_video_link(url: str) -> bool:
    clean = url.lower().split("?")[0]
    return clean.endswith(DIRECT_VIDEO_EXTENSIONS)


def _format_duration(seconds) -> str:
    if not seconds:
        return "N/A"
    seconds = int(seconds)
    minutes, sec = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}h{minutes:02d}m{sec:02d}s"
    return f"{minutes}m{sec:02d}s"


async def fetch_video_info(url: str) -> dict:
    """
    Récupère les informations d'une vidéo (titre, durée, formats disponibles)
    sans la télécharger. Lève DownloadError si la vidéo est introuvable.
    """
    if is_direct_video_link(url):
        return {
            "title": url.split("/")[-1].split("?")[0] or "video",
            "duration": "N/A",
            "platform": "Lien direct",
            "direct": True,
            "qualities": [],
        }

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "noplaylist": True,
        "socket_timeout": 20,
    }

    loop = asyncio.get_event_loop()

    def _extract():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=False)

    try:
        info = await loop.run_in_executor(None, _extract)
    except Exception as e:
        logger.error(f"Erreur extraction info ({url}) : {e}")
        raise DownloadError("Vidéo introuvable ou lien invalide.") from e

    if not info:
        raise DownloadError("Vidéo introuvable ou lien invalide.")

    # Détection des hauteurs de vidéo disponibles -> on les regroupe par
    # palier de qualité standard (360/480/720/1080)
    available_heights = set()
    for fmt in info.get("formats", []) or []:
        height = fmt.get("height")
        if height:
            for q in SUPPORTED_QUALITIES:
                if abs(height - q) <= 60:
                    available_heights.add(q)

    qualities = sorted(available_heights) if available_heights else []

    return {
        "title": info.get("title") or "Sans titre",
        "duration": _format_duration(info.get("duration")),
        "platform": detect_platform(url),
        "direct": False,
        "qualities": qualities,
    }


async def download_video(url: str, quality: int | None = None) -> dict:
    """
    Télécharge réellement la vidéo (qualité demandée si fournie) et
    retourne le chemin du fichier local + métadonnées.
    """
    filename = uuid.uuid4().hex

    if is_direct_video_link(url):
        return await _download_direct_file(url, filename)

    output_template = os.path.join(DOWNLOAD_DIR, f"{filename}.%(ext)s")

    format_selector = "bestvideo+bestaudio/best"
    if quality:
        format_selector = f"bestvideo[height<={quality}]+bestaudio/best[height<={quality}]"

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "outtmpl": output_template,
        "format": format_selector,
        "noplaylist": True,
        "merge_output_format": "mp4",
        "socket_timeout": 30,
    }

    loop = asyncio.get_event_loop()

    def _download():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            path = ydl.prepare_filename(info)
            if not os.path.exists(path):
                base, _ = os.path.splitext(path)
                mp4_path = base + ".mp4"
                if os.path.exists(mp4_path):
                    path = mp4_path
            return info, path

    try:
        info, path = await loop.run_in_executor(None, _download)
    except Exception as e:
        logger.error(f"Erreur téléchargement ({url}) : {e}")
        raise DownloadError("Échec du téléchargement de la vidéo.") from e

    if not os.path.exists(path):
        raise DownloadError("Le fichier vidéo n'a pas pu être créé.")

    size_mb = os.path.getsize(path) / (1024 * 1024)

    return {
        "path": path,
        "title": info.get("title") or "Sans titre",
        "duration": _format_duration(info.get("duration")),
        "platform": detect_platform(url),
        "size_mb": round(size_mb, 2),
    }


async def _download_direct_file(url: str, filename: str) -> dict:
    """Télécharge un fichier vidéo brut (.mp4, .mov, etc.) via aiohttp."""
    ext = url.lower().split("?")[0].split(".")[-1]
    if ext not in ("mp4", "mov", "mkv", "webm", "avi"):
        ext = "mp4"
    path = os.path.join(DOWNLOAD_DIR, f"{filename}.{ext}")

    try:
        timeout = aiohttp.ClientTimeout(total=60)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as response:
                if response.status != 200:
                    raise DownloadError("Le fichier vidéo distant est inaccessible.")
                with open(path, "wb") as f:
                    async for chunk in response.content.iter_chunked(1024 * 256):
                        f.write(chunk)
    except aiohttp.ClientError as e:
        logger.error(f"Erreur téléchargement direct ({url}) : {e}")
        raise DownloadError("Échec du téléchargement du fichier vidéo.") from e

    if not os.path.exists(path) or os.path.getsize(path) == 0:
        raise DownloadError("Le fichier vidéo n'a pas pu être téléchargé.")

    size_mb = os.path.getsize(path) / (1024 * 1024)

    return {
        "path": path,
        "title": filename,
        "duration": "N/A",
        "platform": "Lien direct",
        "size_mb": round(size_mb, 2),
    }


def cleanup_file(path: str):
    """Supprime le fichier temporaire après envoi."""
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except Exception as e:
        logger.warning(f"Impossible de supprimer {path} : {e}")

