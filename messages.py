"""
Tous les textes affichés par le bot. Chaque message inclut le footer
obligatoire "⚡ Powered By LUST 欲 ❤️" via with_footer().
"""

from config import FOOTER


def with_footer(text: str) -> str:
    return f"{text}{FOOTER}"


WELCOME = with_footer(
    "╔════════════════╗\n"
    "🚀 LUST DOWNLOADER BOT\n"
    "╚════════════════╝\n\n"
    "⚡ Télécharge facilement les vidéos depuis TikTok, Instagram, YouTube et bien plus.\n\n"
    "📥 Envoie simplement un lien.\n\n"
    "🔥 Rapide  🛡️ Stable  ⚙️ Optimisé  🚫 Sans crash\n\n"
    "Développé avec ❤️ par LUST 欲"
)

FORCE_SUB_MESSAGE = with_footer(
    "🚫 Vous devez rejoindre tous les canaux avant d'utiliser le bot."
)

ACCESS_GRANTED = with_footer("✅ Accès autorisé. Tu peux maintenant envoyer un lien !")

ASK_LINK = with_footer("📥 Envoie-moi le lien de la vidéo que tu veux télécharger.")

HELP_TEXT = with_footer(
    "ℹ️ AIDE — LUST DOWNLOADER BOT\n\n"
    "1️⃣ Rejoins les canaux obligatoires.\n"
    "2️⃣ Envoie un lien TikTok, Instagram, YouTube, Facebook, Twitter/X, "
    "Pinterest ou un lien vidéo direct (.mp4, .mov...).\n"
    "3️⃣ Choisis la qualité si plusieurs sont disponibles.\n"
    "4️⃣ Reçois ta vidéo directement dans Telegram !\n\n"
    "📜 /start — Revenir au menu principal\n"
    "📥 Télécharger Vidéo — Lancer un téléchargement\n"
    "📜 Historique — Voir tes derniers téléchargements\n"
    "📊 Statistiques — Voir les statistiques du bot"
)

DEV_TEXT = with_footer(
    "👨‍💻 Développeur : LUST 欲\n\n"
    "❤️ Merci d'utiliser LUST Downloader Bot."
)

NO_HISTORY = with_footer("📜 Tu n'as encore téléchargé aucune vidéo.")

ANALYZING = with_footer("🔎 Analyse du lien en cours, merci de patienter...")

DOWNLOADING = with_footer("⬇️ Téléchargement en cours, merci de patienter...")

UPLOADING = with_footer("📤 Envoi de la vidéo vers Telegram...")

INVALID_LINK = with_footer(
    "❌ Vidéo introuvable.\n\n"
    "Vérifie que le lien est correct et provient d'une plateforme supportée "
    "(TikTok, Instagram, YouTube, Facebook, Twitter/X, Pinterest) ou d'un "
    "lien vidéo direct."
)

GENERIC_ERROR = with_footer(
    "⚠️ Une erreur est survenue. Réessaie dans quelques instants."
)

FILE_TOO_LARGE = with_footer(
    "⚠️ La vidéo est trop volumineuse pour être envoyée via Telegram. "
    "Réessaie avec une qualité plus basse."
)

NOT_A_LINK = with_footer(
    "📥 Envoie-moi un lien valide (TikTok, Instagram, YouTube, Facebook, "
    "Twitter/X, Pinterest ou vidéo directe)."
)


def video_caption(title: str, platform: str, size_mb: float, duration: str) -> str:
    return with_footer(
        f"🎬 Titre : {title}\n"
        f"🌐 Plateforme : {platform}\n"
        f"💾 Taille : {size_mb} Mo\n"
        f"⏱️ Durée : {duration}"
    )
