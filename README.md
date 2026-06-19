# 🚀 LUST Downloader Bot

Bot Telegram professionnel pour télécharger automatiquement des vidéos depuis TikTok, Instagram, YouTube, Facebook, Twitter/X, Pinterest, ou tout lien vidéo direct (.mp4, .mov...).

Construit avec **python-telegram-bot v20+** (async/await), **yt-dlp** et **aiohttp**. Architecture anti-crash : chaque opération est protégée par try/except et toutes les erreurs sont journalisées.

---

## ✨ Fonctionnalités

- Détection automatique des liens dans les messages
- Téléchargement + envoi direct de la vidéo dans Telegram
- Affichage du titre, de la plateforme, de la taille et de la durée
- Sélection de qualité (360p / 480p / 720p / 1080p) quand plusieurs formats existent
- Force Subscribe à 3 canaux obligatoires avant utilisation
- Menu interactif (Télécharger, Historique, Statistiques, Aide, Développeur, Actualiser)
- Historique par utilisateur et statistiques globales (SQLite)
- Anti-spam (cooldown configurable)
- Logs complets, gestion des timeouts, aucun crash en cas de lien invalide

---

## 📁 Structure du projet

```
lust_downloader_bot/
├── bot.py                 # Point d'entrée (lance le bot)
├── handlers.py            # Tous les handlers Telegram
├── messages.py            # Textes affichés par le bot
├── keyboards.py            # Claviers inline
├── config.py               # Configuration (token, canaux, constantes)
├── utils/
│   ├── downloader.py       # Téléchargement (yt-dlp + lien direct)
│   ├── subscribe.py        # Vérification Force Subscribe
│   ├── storage.py          # Base SQLite (historique, stats)
│   └── ratelimit.py        # Anti-spam
├── requirements.txt
├── Dockerfile               # Pour Render/Railway/VPS (inclut ffmpeg)
├── Procfile                 # Pour Railway/Render (process worker)
└── .env.example
```

---

## ⚙️ Installation locale

### 1. Prérequis
- Python 3.10 ou plus récent
- **ffmpeg** installé sur le système (requis par yt-dlp pour fusionner audio/vidéo)
  - Debian/Ubuntu : `sudo apt-get install ffmpeg`
  - macOS : `brew install ffmpeg`
  - Windows : télécharger depuis ffmpeg.org et ajouter au PATH

### 2. Cloner et installer les dépendances
```bash
pip install -r requirements.txt
```

### 3. Configurer les variables d'environnement
Copie `.env.example` en `.env` puis renseigne :
```
BOT_TOKEN=ton_token_botfather
CHANNEL_1_ID=...
CHANNEL_2_ID=@INFERNOxOTP
CHANNEL_3_ID=...
DEV_COMMUNITY_LINK=https://t.me/INFERNOxOTP
```

### 4. Lancer le bot
```bash
python bot.py
```

---

## 🔒 Configurer le Force Subscribe

Le bot doit pouvoir vérifier si un utilisateur est membre de chaque canal via l'API Telegram (`get_chat_member`).

- **Canal public** (ex: `https://t.me/INFERNOxOTP`) → utilise directement `@INFERNOxOTP` comme `chat_id`. Rien à faire de plus.
- **Canal privé** (lien d'invitation type `https://t.me/+xxxxx`) → Telegram ne permet pas de retrouver l'ID à partir du lien :
  1. Ajoute le bot comme **administrateur** du canal privé.
  2. Récupère le `chat_id` réel (un entier négatif, ex: `-1001234567890`) :
     - envoie un message dans le canal, transfère-le à un bot comme `@JsonDumpBot`, ou
     - utilise un utilitaire comme `@username_to_id_bot`.
  3. Renseigne cet ID dans `CHANNEL_1_ID` / `CHANNEL_3_ID` du fichier `.env`.

⚠️ Si le bot n'est pas administrateur d'un canal privé, il ne pourra pas vérifier l'abonnement et bloquera l'accès par sécurité.

---

## ☁️ Déploiement

### Render / Railway (avec Docker — recommandé)
Le `Dockerfile` fourni installe `ffmpeg` automatiquement, indispensable pour fusionner les flux vidéo/audio.

1. Pousse le projet sur un dépôt Git (GitHub/GitLab).
2. Sur Render ou Railway, crée un nouveau service de type **Worker** à partir du Dockerfile.
3. Renseigne les variables d'environnement (`BOT_TOKEN`, `CHANNEL_1_ID`, etc.) dans les paramètres du service.
4. Déploie : le bot tourne en polling, aucune configuration de webhook n'est nécessaire.

### VPS
```bash
git clone <ton-repo>
cd lust_downloader_bot
sudo apt-get update && sudo apt-get install -y ffmpeg python3-pip
pip install -r requirements.txt
cp .env.example .env   # puis édite les valeurs
python3 bot.py
```
Pour le garder actif en permanence, utilise `screen`, `tmux`, ou un service `systemd`.

---

## ⚠️ Limites à connaître

- L'API Bot Telegram classique limite l'envoi de fichiers à **50 Mo**. Pour des vidéos plus volumineuses, il faudrait héberger un **Bot API Server local** (jusqu'à 2 Go) — non inclus par défaut dans ce projet.
- Certaines plateformes (Instagram notamment) peuvent exiger des cookies de session pour les contenus privés ou soumis à restriction ; yt-dlp prend en charge l'ajout de cookies via l'option `cookiefile` si besoin (voir documentation yt-dlp).
- Respecte les conditions d'utilisation des plateformes et les droits d'auteur du contenu téléchargé.

---

## 🛠️ Stack technique

- `python-telegram-bot` v20+ (async)
- `yt-dlp` pour l'extraction multi-plateforme
- `aiohttp` pour les téléchargements directs de fichiers
- `sqlite3` pour l'historique et les statistiques

---

⚡ Powered By LUST 欲 ❤️
