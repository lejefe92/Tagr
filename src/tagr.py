#!/usr/bin/env python3
"""Tagr — Audio Metadata Editor (PyQt6)"""

import sys, os, io, json, threading, subprocess, urllib.request, urllib.parse, shutil
from pathlib import Path
from PIL import Image as PILImage
from mutagen.id3 import ID3, TIT2, TPE1, TALB, APIC, TDRC, TCON, TBPM, ID3NoHeaderError
from mutagen.flac import FLAC
from mutagen.mp4 import MP4
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QLineEdit, QScrollArea, QFrame, QFileDialog,
    QDialog, QGridLayout, QSizePolicy, QComboBox, QSlider, QRubberBand
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QUrl, QSize, QRect, QPoint
from PyQt6.QtGui  import (QPixmap, QImage, QPainter, QColor, QPen, QBrush,
                           QKeySequence, QShortcut, QPainterPath)

# ── Config ────────────────────────────────────────────────────────────────────
CONFIG_PATH = Path.home() / ".tagr_config.json"

# ── Traductions / Translations ────────────────────────────────────────────────
_TRANSLATIONS = {
    "fr": {
        "app_title": "Tagr — Éditeur de tags audio",
        "Tagr": "Tagr",
        "Fermer": "Fermer", "Annuler": "Annuler", "Changer": "Changer",
        "Appliquer": "Appliquer", "Utiliser": "Utiliser", "Renommer": "Renommer",
        "Convertir": "Convertir", "Réessayer": "Réessayer", "Normaliser": "Normaliser",
        "Statistiques": "Statistiques", "Tout sélectionner": "Tout sélectionner",
        "Retirer de la liste": "Retirer de la liste",
        "Tout": "Tout", "Artiste": "Artiste", "Album": "Album", "Titre": "Titre",
        "A → Z": "A → Z",
        "hint_drop": "Glisse des fichiers audio\nou un dossier entier ici\n\nMP3  FLAC  M4A  AAC  OGG",
        "Ajouter des fichiers…": "Ajouter des fichiers…",
        "Ajouter un dossier…": "Ajouter un dossier…",
        "TITRE": "TITRE", "ARTISTE": "ARTISTE", "ALBUM": "ALBUM",
        "Cliquer ou glisser une image": "Cliquer ou glisser une image",
        "Ajouter\nune pochette": "Ajouter\nune pochette",
        "Recadrer": "Recadrer", "Recadrer la pochette": "Recadrer la pochette",
        "POCHETTE": "POCHETTE", "Recherche de pochette": "Recherche de pochette",
        "Exporter la pochette": "Exporter la pochette",
        "LECTURE": "LECTURE", "Ecouter": "Ecouter",
        "OUTILS AUDIO": "OUTILS AUDIO", "Outils audio…": "Outils audio…",
        "Sauvegarder": "Sauvegarder", "Tout sauvegarder": "Tout sauvegarder",
        "Sauvegarder + fichier suivant": "Sauvegarder + fichier suivant",
        "Sauvegarder + problème suivant": "Sauvegarder + problème suivant",
        "Modifications non sauvegardées": "Modifications non sauvegardées",
        "Couper le morceau": "Couper le morceau",
        "Normaliser le volume (-14 LUFS)": "Normaliser le volume (-14 LUFS)",
        "Avant / Apres normalisation": "Avant / Apres normalisation",
        "Convertir le format": "Convertir le format",
        "Télécharger depuis URL": "Télécharger depuis URL",
        "Télécharger un fichier audio": "Télécharger un fichier audio",
        "sc_bandcamp": "YouTube · SoundCloud · Bandcamp · et + de 1000 sites",
        "URL :": "URL :", "Format :": "Format :", "Dossier :": "Dossier :",
        "yt_not_found": "yt-dlp introuvable — brew install yt-dlp",
        "Télécharger": "Télécharger", "Téléchargement...": "Téléchargement...",
        "Téléchargement en cours...": "Téléchargement en cours...",
        "Entre une URL valide": "Entre une URL valide",
        "Annulation en cours...": "Annulation en cours...",
        "Meilleure qualité (natif)": "Meilleure qualité (natif)", "MP3 320k": "MP3 320k",
        "placeholder_url": "https://www.youtube.com/watch?v=...",
        "Raccourcis clavier": "Raccourcis clavier",
        "Prêt Spotify": "Prêt Spotify", "Export Spotify Ready": "Export Spotify Ready",
        "Appliquer le découpage": "Appliquer le découpage",
        "Découpage en cours…": "Découpage en cours…", "Stop": "Stop", "Zoom": "Zoom",
        "Déposer ici": "Déposer ici",
        "Normalisation rapide en cours...": "Normalisation rapide en cours...",
        "Erreur normalisation": "Erreur normalisation",
        "Lecture : Original": "Lecture : Original",
        "Lecture : Normalise (-14 LUFS)": "Lecture : Normalise (-14 LUFS)",
        "▶  Original": "▶  Original", "▶  Normalise": "▶  Normalise",
        "Clique sur Original ou Normalise pour ecouter": "Clique sur Original ou Normalise pour ecouter",
        "Aperçu du renommage": "Aperçu du renommage",
        "Champs en lot": "Champs en lot", "Renommer par lot": "Renommer par lot",
        "Fichier introuvable": "Fichier introuvable",
        "Doublons possibles": "Doublons possibles",
        "Aller au prochain problème": "Aller au prochain problème",
        "⏹  Stop": "⏹  Stop", "▶  Écouter la sélection": "▶  Écouter la sélection",
        "Résultats automatiques :": "Résultats automatiques :",
        "Chargement des résultats...": "Chargement des résultats...",
        "Chargement de l'image...": "Chargement de l'image...",
        "Sélection trop courte": "Sélection trop courte",
        "Statistiques de la bibliotheque": "Statistiques de la bibliotheque",
        "select_file": "Sélectionne un fichier",
        "Vue album": "Vue album", "Vue liste": "Vue liste",
        "Erreur": "Erreur",
        "Écraser le fichier": "Écraser le fichier",
        "Créer un nouveau fichier": "Créer un nouveau fichier",
        "Comment sauvegarder les modifications ?": "Comment sauvegarder les modifications ?",
        "Exporter les prêts": "Exporter les prêts",
        "Exporter tout": "Exporter tout",
        "Ignorer": "Ignorer",
        "Quitter sans sauvegarder": "Quitter sans sauvegarder",
        "Sauvegarder et quitter": "Sauvegarder et quitter",
        "spotify_confirm": "Créer les copies prêtes pour Spotify ?",
        "spotify_save_tags": "Sauvegarder les tags avant l'export Spotify ?",
        "Statut Spotify": "Statut Spotify",
        "img_url_placeholder": "Coller une URL d'image directement (https://...)",
        "ffmpeg_not_found": "ffmpeg introuvable — brew install ffmpeg",
        "Normaliser le volume": "Normaliser le volume",
        "Statistiques": "Statistiques",
        "Doublons possibles": "Doublons possibles",
        "Avant / Apres normalisation": "Avant / Apres normalisation",
        "Champs en lot": "Champs en lot",
        "Renommer par lot": "Renommer par lot",
        "Aperçu du renommage": "Aperçu du renommage",
        "Contrôle Spotify": "Contrôle Spotify",
        "Convertir le format": "Convertir le format",
        "Couper le morceau": "Couper le morceau",
        "Sauvegarder": "Sauvegarder",
        "Raccourcis clavier": "Raccourcis clavier",
        "Recadrer la pochette": "Recadrer la pochette",
        "Recherche de pochette": "Recherche de pochette",
        "Export Spotify Ready": "Export Spotify Ready",
        "Modifications non sauvegardées": "Modifications non sauvegardées",
        "dl_tooltip": "Télécharger depuis URL (YouTube, SoundCloud…)",
        "img_astuce": "Astuce : clic droit sur une image dans Chrome → Copier l'adresse de l'image",
        "trim_hint": "Glisse les poignées vertes pour sélectionner · Déplace la sélection par le centre",
        "crop_hint": "Scroll pour zoomer · Glisser pour déplacer · Sortie carrée 640x640",
        "mp3_info": "MP3 320 kbps. Le fichier original est conserve.",
        "Statut Spotify": "Statut Spotify",
        "À vérifier Spotify : ": "À vérifier Spotify : ",
        "Aucun problème Spotify restant": "Aucun problème Spotify restant",
        "Choisir le dossier Spotify Ready": "Choisir le dossier Spotify Ready",
        "Normalisation a -14 LUFS (standard Spotify / Apple Music)": "Normalisation a -14 LUFS (standard Spotify / Apple Music)",
        "n_unsaved": "{n} fichier(s) non sauvegardé(s).",
        "save_before_quit": "Sauvegarder avant de quitter ?",
        "export_note": "L'export copie les fichiers tels qu'ils sont sur disque.",
        "n_renames": "{n} renommage(s) prévu(s)",
        "file_modified": "Fichier modifié : {name}",
        "Haute qualité": "Haute qualité",
        "Bonne qualité": "Bonne qualité",
        "Qualité standard": "Qualité standard",
        "Basse qualité": "Basse qualité",
        "dl_file_not_found": "Fichier introuvable après téléchargement",
        "dl_cancelled": "Téléchargement annulé",
        "dl_timeout": "Timeout — téléchargement trop long",
        "dl_cancelled2": "Téléchargement annulé",
        "duration_error": "Impossible de lire la durée du fichier",
        "Année": "Année",
        "num_tracks_hint": "Numéroter les pistes dans l'ordre de la liste",
        "yt_not_found2": "yt-dlp introuvable — installe les dépendances Tagr",
        "lang_toggle": "English", "lang_name": "Français",
        "lang_restart": "Redémarrez Tagr pour appliquer la langue.",
        "lang_title": "Langue / Language",
        "empty_title": "Sélectionne un fichier",
        "empty_hint": "↑ ↓ pour naviguer · Cmd+S pour sauvegarder · Entrée pour sauvegarder",
        "unknown_artist": "Artiste inconnu",
        "cover_sources": "Sources : Deezer · iTunes · MusicBrainz · Priorité artiste",
        "cover_no_results": "Aucun résultat trouvé automatiquement.\nColle une URL d'image ci-dessus.",
        "ffmpeg_preview_error": "Erreur ffmpeg preview",
        "duration_label": "Durée : {duration}",
        "start_time": "Début (m:ss.s)",
        "end_time": "Fin (m:ss.s)",
        "file_label": "Fichier : {name}",
        "target_format": "Format cible :",
        "apply_from_selected": "Appliquer depuis le morceau sélectionné :",
        "rename_pattern": "Pattern de renommage :",
        "rename_variables": "Variables : {titre}  {artiste}  {album}  {piste}  {annee}",
        "apply_all_files": "Appliquer a tous les fichiers de la liste",
        "overwrite_original": "Ecraser le fichier original",
        "stats_total_files": "Fichiers total",
        "stats_no_cover": "Sans pochette",
        "stats_missing_tags": "Tags incomplets",
        "stats_formats": "Formats :",
        "stats_quality": "Qualite :",
        "spotify_ready_review": "{ready} prêt(s) · {review} à vérifier",
        "spotify_check": "A vérifier",
        "missing_artist": "artiste manquant",
        "missing_title": "titre manquant",
        "missing_cover": "pochette manquante",
        "not_mp3": "format non MP3",
        "possible_duplicate": "doublon possible",
        "file_previous_next": "Fichier precedent / suivant",
        "remove_current_file": "Retirer le fichier de la liste",
        "shortcuts_audio_tools": "Couper, Normaliser, Convertir, Renommer",
        "shortcuts_spotify_export": "Exporter les copies prêtes pour Spotify",
        "preview_compare": "Ecoute comparee : Original vs Normalise (-14 LUFS)",
    },
    "en": {
        "app_title": "Tagr — Audio Tag Editor",
        "Tagr": "Tagr",
        "Fermer": "Close", "Annuler": "Cancel", "Changer": "Change",
        "Appliquer": "Apply", "Utiliser": "Use", "Renommer": "Rename",
        "Convertir": "Convert", "Réessayer": "Retry", "Normaliser": "Normalize",
        "Statistiques": "Statistics", "Tout sélectionner": "Select all",
        "Retirer de la liste": "Remove from list",
        "Tout": "All", "Artiste": "Artist", "Album": "Album", "Titre": "Title",
        "A → Z": "A → Z",
        "hint_drop": "Drop audio files\nor a folder here\n\nMP3  FLAC  M4A  AAC  OGG",
        "Ajouter des fichiers…": "Add files…",
        "Ajouter un dossier…": "Add folder…",
        "TITRE": "TITLE", "ARTISTE": "ARTIST", "ALBUM": "ALBUM",
        "Cliquer ou glisser une image": "Click or drag an image",
        "Ajouter\nune pochette": "Add\ncover art",
        "Recadrer": "Crop", "Recadrer la pochette": "Crop cover art",
        "POCHETTE": "COVER ART", "Recherche de pochette": "Search cover art",
        "Exporter la pochette": "Export cover art",
        "LECTURE": "PLAYBACK", "Ecouter": "Listen",
        "OUTILS AUDIO": "AUDIO TOOLS", "Outils audio…": "Audio tools…",
        "Sauvegarder": "Save", "Tout sauvegarder": "Save all",
        "Sauvegarder + fichier suivant": "Save + next file",
        "Sauvegarder + problème suivant": "Save + next issue",
        "Modifications non sauvegardées": "Unsaved changes",
        "Couper le morceau": "Trim audio",
        "Normaliser le volume (-14 LUFS)": "Normalize volume (-14 LUFS)",
        "Avant / Apres normalisation": "Before / After normalization",
        "Convertir le format": "Convert format",
        "Télécharger depuis URL": "Download from URL",
        "Télécharger un fichier audio": "Download an audio file",
        "sc_bandcamp": "YouTube · SoundCloud · Bandcamp · and 1000+ sites",
        "URL :": "URL:", "Format :": "Format:", "Dossier :": "Folder:",
        "yt_not_found": "yt-dlp not found — brew install yt-dlp",
        "Télécharger": "Download", "Téléchargement...": "Downloading...",
        "Téléchargement en cours...": "Downloading...",
        "Entre une URL valide": "Enter a valid URL",
        "Annulation en cours...": "Cancelling...",
        "Meilleure qualité (natif)": "Best quality (native)", "MP3 320k": "MP3 320k",
        "placeholder_url": "https://www.youtube.com/watch?v=...",
        "Raccourcis clavier": "Keyboard shortcuts",
        "Prêt Spotify": "Spotify Ready", "Export Spotify Ready": "Export Spotify Ready",
        "Appliquer le découpage": "Apply trim",
        "Découpage en cours…": "Trimming…", "Stop": "Stop", "Zoom": "Zoom",
        "Déposer ici": "Drop here",
        "Normalisation rapide en cours...": "Normalizing...",
        "Erreur normalisation": "Normalization error",
        "Lecture : Original": "Play: Original",
        "Lecture : Normalise (-14 LUFS)": "Play: Normalized (-14 LUFS)",
        "▶  Original": "▶  Original", "▶  Normalise": "▶  Normalized",
        "Clique sur Original ou Normalise pour ecouter": "Click Original or Normalized to listen",
        "Aperçu du renommage": "Rename preview",
        "Champs en lot": "Batch fields", "Renommer par lot": "Batch rename",
        "Fichier introuvable": "File not found",
        "Doublons possibles": "Possible duplicates",
        "Aller au prochain problème": "Go to next issue",
        "⏹  Stop": "⏹  Stop", "▶  Écouter la sélection": "▶  Play selection",
        "Résultats automatiques :": "Automatic results:",
        "Chargement des résultats...": "Loading results...",
        "Chargement de l'image...": "Loading image...",
        "Sélection trop courte": "Selection too short",
        "Statistiques de la bibliotheque": "Library statistics",
        "select_file": "Select a file",
        "Vue album": "Album view", "Vue liste": "List view",
        "Erreur": "Error",
        "Écraser le fichier": "Overwrite file",
        "Créer un nouveau fichier": "Create new file",
        "Comment sauvegarder les modifications ?": "How to save changes?",
        "Exporter les prêts": "Export ready files",
        "Exporter tout": "Export all",
        "Ignorer": "Ignore",
        "Quitter sans sauvegarder": "Quit without saving",
        "Sauvegarder et quitter": "Save and quit",
        "spotify_confirm": "Create Spotify-ready copies?",
        "spotify_save_tags": "Save tags before Spotify export?",
        "Statut Spotify": "Spotify Status",
        "img_url_placeholder": "Paste an image URL directly (https://...)",
        "ffmpeg_not_found": "ffmpeg not found — brew install ffmpeg",
        "Normaliser le volume": "Normalize volume",
        "Statistiques": "Statistics",
        "Doublons possibles": "Possible duplicates",
        "Avant / Apres normalisation": "Before / After normalization",
        "Champs en lot": "Batch fields",
        "Renommer par lot": "Batch rename",
        "Aperçu du renommage": "Rename preview",
        "Contrôle Spotify": "Spotify control",
        "Convertir le format": "Convert format",
        "Couper le morceau": "Trim audio",
        "Sauvegarder": "Save",
        "Raccourcis clavier": "Keyboard shortcuts",
        "Recadrer la pochette": "Crop cover art",
        "Recherche de pochette": "Search cover art",
        "Export Spotify Ready": "Export Spotify Ready",
        "Modifications non sauvegardées": "Unsaved changes",
        "dl_tooltip": "Download from URL (YouTube, SoundCloud…)",
        "img_astuce": "Tip: right-click an image in Chrome → Copy image address",
        "trim_hint": "Drag green handles to select · Move selection from center",
        "crop_hint": "Scroll to zoom · Drag to move · Square output 640x640",
        "mp3_info": "MP3 320 kbps. Original file is kept.",
        "Statut Spotify": "Spotify Status",
        "À vérifier Spotify : ": "Spotify issue: ",
        "Aucun problème Spotify restant": "No remaining Spotify issues",
        "Choisir le dossier Spotify Ready": "Choose Spotify Ready folder",
        "Normalisation a -14 LUFS (standard Spotify / Apple Music)": "Normalize to -14 LUFS (Spotify / Apple Music standard)",
        "n_unsaved": "{n} unsaved file(s).",
        "save_before_quit": "Save before quitting?",
        "export_note": "Export copies files as they are on disk.",
        "n_renames": "{n} rename(s) planned",
        "file_modified": "File modified: {name}",
        "Haute qualité": "High quality",
        "Bonne qualité": "Good quality",
        "Qualité standard": "Standard quality",
        "Basse qualité": "Low quality",
        "dl_file_not_found": "File not found after download",
        "dl_cancelled": "Download cancelled",
        "dl_timeout": "Timeout — download took too long",
        "MP3 320 kbps. Le fichier original est conserve.": "MP3 320 kbps. Original file is kept.",
        "Scroll pour zoomer · Glisser pour déplacer · Sortie carrée 640x640": "Scroll to zoom · Drag to move · Square output 640x640",
        "Redémarrez Tagr pour appliquer la langue.": "Restart Tagr to apply the language change.",
        "Coller une URL d'image directement (https://...)": "Paste an image URL directly (https://...)",
        "Astuce : clic droit sur une image dans Chrome → Copier l'adresse de l'image": "Tip: right-click an image in Chrome → Copy image address",
        "{n} fichier(s) non sauvegardé(s).": "{n} unsaved file(s).",
        "Créer les copies prêtes pour Spotify ?": "Create Spotify-ready copies?",
        "Tagr — Éditeur de tags audio": "Tagr — Audio Tag Editor",
        "Sauvegarder avant de quitter ?": "Save before quitting?",
        "Sauvegarder les tags avant l'export Spotify ?": "Save tags before Spotify export?",
        "L'export copie les fichiers tels qu'ils sont sur disque.": "Export copies files as they are on disk.",
        "ffmpeg introuvable — brew install ffmpeg": "ffmpeg not found — brew install ffmpeg",
        "Glisse les poignées vertes pour sélectionner · Déplace la sélection par le centre": "Drag green handles to select · Move selection from center",
        "Sélectionne un fichier": "Select a file",
        "Télécharger depuis URL (YouTube, SoundCloud…)": "Download from URL (YouTube, SoundCloud…)",
        "Fichier modifié : {name}": "File modified: {name}",
        "yt-dlp introuvable — brew install yt-dlp": "yt-dlp not found — brew install yt-dlp",
        "{n} renommage(s) prévu(s)": "{n} rename(s) planned",
        "YouTube · SoundCloud · Bandcamp · et + de 1000 sites": "YouTube · SoundCloud · Bandcamp · and 1000+ sites",
        "Glisse des fichiers audio\\\\nou un dossier entier ici\\\\n\\\\nMP3  FLAC  M4A  AAC  OGG": "Drop audio files\\\\nor a folder here\\\\n\\\\nMP3  FLAC  M4A  AAC  OGG",
        "dl_cancelled2": "Download cancelled",
        "duration_error": "Cannot read file duration",
        "Année": "Year",
        "num_tracks_hint": "Number tracks in list order",
        "yt_not_found2": "yt-dlp not found — install Tagr dependencies",
        "lang_toggle": "Français", "lang_name": "English",
        "lang_restart": "Restart Tagr to apply the language change.",
        "lang_title": "Langue / Language",
        "empty_title": "Select a file",
        "empty_hint": "↑ ↓ to navigate · Cmd+S to save · Enter to save",
        "unknown_artist": "Unknown artist",
        "cover_sources": "Sources: Deezer · iTunes · MusicBrainz · Artist first",
        "cover_no_results": "No automatic result found.\nPaste an image URL above.",
        "ffmpeg_preview_error": "ffmpeg preview error",
        "duration_label": "Duration: {duration}",
        "start_time": "Start (m:ss.s)",
        "end_time": "End (m:ss.s)",
        "file_label": "File: {name}",
        "target_format": "Target format:",
        "apply_from_selected": "Apply from selected track:",
        "rename_pattern": "Rename pattern:",
        "rename_variables": "Variables: {title}  {artist}  {album}  {track}  {year}",
        "apply_all_files": "Apply to all files in the list",
        "overwrite_original": "Overwrite original file",
        "stats_total_files": "Total files",
        "stats_no_cover": "No cover art",
        "stats_missing_tags": "Incomplete tags",
        "stats_formats": "Formats:",
        "stats_quality": "Quality:",
        "spotify_ready_review": "{ready} ready · {review} to review",
        "spotify_check": "Review",
        "missing_artist": "missing artist",
        "missing_title": "missing title",
        "missing_cover": "missing cover art",
        "not_mp3": "not MP3",
        "possible_duplicate": "possible duplicate",
        "file_previous_next": "Previous / next file",
        "remove_current_file": "Remove current file",
        "shortcuts_audio_tools": "Trim, Normalize, Convert, Rename",
        "shortcuts_spotify_export": "Export Spotify-ready copies",
        "preview_compare": "Compare listening: Original vs Normalized (-14 LUFS)",
    }
}

_LANG = "fr"

def T(key):
    lang = _TRANSLATIONS.get(_LANG, _TRANSLATIONS["fr"])
    return lang.get(key, _TRANSLATIONS["fr"].get(key, key))

def set_lang(lang):
    global _LANG
    _LANG = lang


PROJECT_ROOT = Path(__file__).resolve().parents[1]
AUDIO_BACKUP_DIR = PROJECT_ROOT / "backups" / "audio"

def load_config():
    try: return json.loads(CONFIG_PATH.read_text())
    except (json.JSONDecodeError, OSError, IOError, Exception): return {}

def _init_lang():
    cfg = load_config()
    if cfg.get("lang") in ("fr", "en"):
        set_lang(cfg["lang"])
_init_lang()

def save_config(d):
    try: CONFIG_PATH.write_text(json.dumps(d))
    except (OSError, IOError, Exception): pass

def backup_audio_file(path, reason="edit"):
    try:
        src = Path(path)
        if not src.is_file():
            return False, "Fichier introuvable"
        from datetime import datetime
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        reason = safe_fn(reason).replace(" ", "_").lower() or "edit"
        folder = AUDIO_BACKUP_DIR / datetime.now().strftime("%Y-%m-%d") / reason
        folder.mkdir(parents=True, exist_ok=True)
        dest = folder / f"{stamp}_{safe_fn(src.stem) or 'audio'}{src.suffix}"
        i = 1
        while dest.exists():
            dest = folder / f"{stamp}_{safe_fn(src.stem) or 'audio'}_{i}{src.suffix}"
            i += 1
        shutil.copy2(src, dest)
        return True, str(dest)
    except Exception as e:
        return False, str(e)

# ── Couleurs ──────────────────────────────────────────────────────────────────
# ── Palettes ─────────────────────────────────────────────
DARK_PALETTE = dict(
    BG="#0f0f0f", BG2="#161616", PANEL="#1e1e1e", PANEL2="#272727",
    BORDER="#303030", ACCENT="#1DB954", ACCENT2="#17a349",
    TEXT="#efefef", TEXTM="#aaaaaa", TEXTD="#606060",
    ERROR="#e05252", WARN="#e8a538", FIELDBG="#141414", SELBG="#192b1d"
)
LIGHT_PALETTE = dict(
    BG="#f5f5f5", BG2="#ebebeb", PANEL="#ffffff", PANEL2="#e0e0e0",
    BORDER="#cccccc", ACCENT="#1DB954", ACCENT2="#17a349",
    TEXT="#111111", TEXTM="#555555", TEXTD="#999999",
    ERROR="#d63031", WARN="#e17055", FIELDBG="#f9f9f9", SELBG="#d4f5e0"
)

def _apply_palette(p):
    global BG,BG2,PANEL,PANEL2,BORDER,ACCENT,ACCENT2,TEXT,TEXTM,TEXTD,ERROR,WARN,FIELDBG,SELBG
    BG=p["BG"]; BG2=p["BG2"]; PANEL=p["PANEL"]; PANEL2=p["PANEL2"]
    BORDER=p["BORDER"]; ACCENT=p["ACCENT"]; ACCENT2=p["ACCENT2"]
    TEXT=p["TEXT"]; TEXTM=p["TEXTM"]; TEXTD=p["TEXTD"]
    ERROR=p["ERROR"]; WARN=p["WARN"]; FIELDBG=p["FIELDBG"]; SELBG=p["SELBG"]

_apply_palette(DARK_PALETTE)

BG      = BG
BG2     = BG2
PANEL   = PANEL
PANEL2  = PANEL2
BORDER  = BORDER
ACCENT  = ACCENT
ACCENT2 = ACCENT2
TEXT    = TEXT
TEXTM   = TEXTM
TEXTD   = TEXTD
ERROR   = ERROR
WARN    = WARN
FIELDBG = FIELDBG
SELBG   = SELBG

def is_audio(p): return p.lower().endswith((".mp3",".flac",".m4a",".aac"))
def is_image(p): return p.lower().endswith((".jpg",".jpeg",".png",".webp",".bmp"))
def safe_fn(s):
    for c in r'/\:*?"<>|': s=s.replace(c,"")
    return s.strip()

def clean_text(s):
    return " ".join(str(s or "").split()).strip()

def unique_path(path):
    path = Path(path)
    if not path.exists():
        return path
    i = 1
    while True:
        candidate = path.with_name(f"{path.stem}_{i}{path.suffix}")
        if not candidate.exists():
            return candidate
        i += 1

def name_from_pattern(pattern, tags, path):
    base = os.path.splitext(os.path.basename(path))[0]
    values = {
        "{titre}": clean_text(tags.get("title")) or base,
        "{title}": clean_text(tags.get("title")) or base,
        "{artiste}": clean_text(tags.get("artist")) or "Inconnu",
        "{artist}": clean_text(tags.get("artist")) or "Unknown",
        "{album}": clean_text(tags.get("album")),
        "{piste}": clean_text(tags.get("track")),
        "{track}": clean_text(tags.get("track")),
        "{annee}": clean_text(tags.get("year")),
        "{year}": clean_text(tags.get("year")),
    }
    name = pattern
    for key, value in values.items():
        name = name.replace(key, value)
    return safe_fn(clean_text(name))

def spotify_filename(tags, path):
    title = clean_text(tags.get("title")) or os.path.splitext(os.path.basename(path))[0]
    artist = clean_text(tags.get("artist"))
    stem = f"{artist} - {title}" if artist else title
    return f"{safe_fn(stem) or 'audio'}{os.path.splitext(path)[1].lower()}"

def pil_to_qpixmap(img, size):
    img=img.copy(); img.thumbnail((size,size),PILImage.LANCZOS)
    bg=PILImage.new("RGB",(size,size),(30,30,30))
    bg.paste(img,((size-img.width)//2,(size-img.height)//2))
    data=bg.tobytes("raw","RGB")
    qi=QImage(data,size,size,size*3,QImage.Format.Format_RGB888)
    return QPixmap.fromImage(qi)

def pil_to_qpixmap_exact(img, w, h):
    img=img.copy().convert("RGB"); img=img.resize((w,h),PILImage.LANCZOS)
    data=img.tobytes("raw","RGB")
    qi=QImage(data,w,h,w*3,QImage.Format.Format_RGB888)
    return QPixmap.fromImage(qi)

# ── Tags I/O ──────────────────────────────────────────────────────────────────

def read_tags(path):
    info={"title":"","artist":"","album":"","year":"","genre":"","bpm":"","track":"","cover":None,"_read_error":None}
    # Vérification préliminaire : fichier lisible et non vide
    try:
        if not os.path.isfile(path) or os.path.getsize(path) == 0:
            info["_read_error"] = "Fichier vide ou introuvable"
            info["title"] = os.path.splitext(os.path.basename(path))[0]
            return info
    except OSError as e:
        info["_read_error"] = str(e)
        info["title"] = os.path.splitext(os.path.basename(path))[0]
        return info
    ext=path.lower().rsplit(".",1)[-1]
    try:
        if ext=="mp3":
            try: t=ID3(path)
            except ID3NoHeaderError: t=ID3()
            info["title"] =str(t.get("TIT2","")).strip()
            info["artist"]=str(t.get("TPE1","")).strip()
            info["album"] =str(t.get("TALB","")).strip()
            info["year"]  =str(t.get("TDRC","")).strip()
            info["genre"] =str(t.get("TCON","")).strip()
            info["bpm"]   =str(t.get("TBPM","")).strip()
            info["track"] =str(t.get("TRCK","")).strip()
            for k in t:
                if k.startswith("APIC"):
                    info["cover"]=PILImage.open(io.BytesIO(t[k].data)).convert("RGB"); break
        elif ext=="flac":
            a=FLAC(path)
            info["title"] =(a.get("title", [""])[0]).strip()
            info["artist"]=(a.get("artist",[""])[0]).strip()
            info["album"] =(a.get("album", [""])[0]).strip()
            info["year"]  =(a.get("date",  [""])[0]).strip()
            info["genre"] =(a.get("genre", [""])[0]).strip()
            info["bpm"]   =(a.get("bpm",   [""])[0]).strip()
            info["track"] =(a.get("tracknumber",[""])[0]).strip() if a.get("tracknumber") else ""
            if a.pictures: info["cover"]=PILImage.open(io.BytesIO(a.pictures[0].data)).convert("RGB")
        elif ext in("m4a","aac"):
            a=MP4(path)
            info["title"] =(a.get("\xa9nam",[""])[0]).strip()
            info["artist"]=(a.get("\xa9ART",[""])[0]).strip()
            info["album"] =(a.get("\xa9alb",[""])[0]).strip()
            info["year"]  =(a.get("\xa9day",[""])[0]).strip()
            info["genre"] =(a.get("\xa9gen",[""])[0]).strip()
            tmpo=a.get("tmpo"); info["bpm"]=str(tmpo[0]).strip() if tmpo else ""
            trkn=a.get("trkn"); info["track"]=f'{trkn[0][0]}/{trkn[0][1]}' if trkn and trkn[0][1] else (str(trkn[0][0]) if trkn else "")
            c=a.get("covr")
            if c: info["cover"]=PILImage.open(io.BytesIO(bytes(c[0]))).convert("RGB")
    except Exception as e:
        info["_read_error"] = str(e)
        print(f"read_tags: {e}")
    if not info["title"]: info["title"]=os.path.splitext(os.path.basename(path))[0]
    return info

def write_tags(path,title,artist,album,year,genre,bpm,track="",cover=None):
    ext=path.lower().rsplit(".",1)[-1]
    try:
        if ext=="mp3":
            try: t=ID3(path)
            except ID3NoHeaderError: t=ID3()
            t["TIT2"]=TIT2(encoding=3,text=title)
            t["TPE1"]=TPE1(encoding=3,text=artist)
            t["TALB"]=TALB(encoding=3,text=album)
            if year:  t["TDRC"]=TDRC(encoding=3,text=year)
            if genre: t["TCON"]=TCON(encoding=3,text=genre)
            if bpm:   t["TBPM"]=TBPM(encoding=3,text=bpm)
            if track:
                from mutagen.id3 import TRCK
                t["TRCK"]=TRCK(encoding=3,text=track)
            if cover:
                buf=io.BytesIO(); cover.save(buf,"JPEG",quality=90)
                t["APIC"]=APIC(encoding=3,mime="image/jpeg",type=3,desc="Cover",data=buf.getvalue())
            t.save(path)
        elif ext=="flac":
            a=FLAC(path)
            a["title"]=title; a["artist"]=artist; a["album"]=album
            if year:  a["date"]=year
            if genre: a["genre"]=genre
            if bpm:   a["bpm"]=bpm
            if track: a["tracknumber"]=track
            if cover:
                from mutagen.flac import Picture
                p=Picture(); buf=io.BytesIO(); cover.save(buf,"JPEG",quality=90)
                p.data=buf.getvalue(); p.type=3; p.mime="image/jpeg"
                p.width,p.height=cover.size; p.depth=24
                a.clear_pictures(); a.add_picture(p)
            a.save()
        elif ext in("m4a","aac"):
            a=MP4(path)
            a["\xa9nam"]=title; a["\xa9ART"]=artist; a["\xa9alb"]=album
            if year:  a["\xa9day"]=year
            if genre: a["\xa9gen"]=genre
            if bpm:
                try: a["tmpo"]=[int(bpm)]
                except Exception: pass
            if track:
                try:
                    parts=track.split("/")
                    tot=int(parts[1]) if len(parts)>1 else 0
                    a["trkn"]=[(int(parts[0]),tot)]
                except Exception: pass
            if cover:
                from mutagen.mp4 import MP4Cover
                buf=io.BytesIO(); cover.save(buf,"JPEG",quality=90)
                a["covr"]=[MP4Cover(buf.getvalue(),imageformat=MP4Cover.FORMAT_JPEG)]
            a.save()
        return True
    except Exception as e: return str(e)


# ── Qualité audio ─────────────────────────────────────────────────────────────

def read_audio_quality(path):
    """Retourne un dict avec les infos de qualité audio du fichier."""
    info = {"bitrate": None, "sample_rate": None, "bits": None,
            "channels": None, "duration": None, "size": None}
    try:
        info["size"] = os.path.getsize(path)
        ext = path.lower().rsplit(".", 1)[-1]
        if ext == "mp3":
            from mutagen.mp3 import MP3
            a = MP3(path)
            info["bitrate"]     = int(a.info.bitrate / 1000)
            info["sample_rate"] = a.info.sample_rate
            info["channels"]    = a.info.channels
            info["duration"]    = a.info.length
            info["bits"]        = None  # MP3 = lossy, pas de bit depth
        elif ext == "flac":
            a = FLAC(path)
            info["bitrate"]     = int(a.info.bits_per_sample * a.info.sample_rate * a.info.channels / 1000)
            info["sample_rate"] = a.info.sample_rate
            info["bits"]        = a.info.bits_per_sample
            info["channels"]    = a.info.channels
            info["duration"]    = a.info.length
        elif ext in ("m4a", "aac"):
            a = MP4(path)
            info["bitrate"]     = int(a.info.bitrate / 1000) if a.info.bitrate else None
            info["sample_rate"] = a.info.sample_rate
            info["channels"]    = a.info.channels
            info["duration"]    = a.info.length
            info["bits"]        = None
        elif ext == "ogg":
            from mutagen.oggvorbis import OggVorbis
            a = OggVorbis(path)
            info["bitrate"]     = int(a.info.bitrate / 1000) if a.info.bitrate else None
            info["sample_rate"] = a.info.sample_rate
            info["channels"]    = a.info.channels
            info["duration"]    = a.info.length
            info["bits"]        = None
    except Exception as e:
        print(f"read_audio_quality: {e}")
    return info

def quality_label(path, q):
    """Retourne (label, couleur) selon la qualité."""
    ext = path.lower().rsplit(".", 1)[-1]
    if ext == "flac":
        bits = q.get("bits") or 16
        sr   = q.get("sample_rate") or 44100
        if bits >= 24 or sr > 48000:
            return "Hi-Res Lossless", "#a78bfa"   # violet
        return "Lossless (CD)", "#1DB954"          # vert
    br = q.get("bitrate") or 0
    if br >= 256:  return T("Haute qualité"),    "#1DB954"   # vert
    if br >= 192:  return T("Bonne qualité"),    "#86efac"   # vert clair
    if br >= 128:  return T("Qualité standard"), "#e8a538"   # orange
    return T("Basse qualité"), "#e05252"                     # rouge

# ── Recherche ─────────────────────────────────────────────────────────────────

def fetch_image_url(url):
    try: return PILImage.open(io.BytesIO(urllib.request.urlopen(url,timeout=8).read())).convert("RGB")
    except (urllib.error.URLError, OSError, IOError, Exception): return None

def search_itunes(q, n=4):
    try:
        p = urllib.parse.urlencode({"term":q,"entity":"song","limit":n,"media":"music"})
        d = json.loads(urllib.request.urlopen(
            f"https://itunes.apple.com/search?{p}", timeout=5).read())
        return [{"title":   r.get("trackName",""),
                 "artist":  r.get("artistName",""),
                 "album":   r.get("collectionName",""),
                 "artwork": r.get("artworkUrl100","").replace("100x100","600x600"),
                 "source":  "iTunes"}
                for r in d.get("results",[]) if r.get("artworkUrl100")]
    except (urllib.error.URLError, json.JSONDecodeError, Exception): return []


def search_itunes_artist(q, n=4):
    """Cherche par NOM D'ARTISTE sur iTunes — retourne les images d'artiste."""
    try:
        p = urllib.parse.urlencode({"term":q,"entity":"musicArtist","limit":n})
        d = json.loads(urllib.request.urlopen(
            f"https://itunes.apple.com/search?{p}", timeout=5).read())
        results = []
        for r in d.get("results",[]):
            art = r.get("artworkUrl100","").replace("100x100","600x600")
            if art:
                results.append({
                    "title":   r.get("artistName",""),
                    "artist":  r.get("artistName",""),
                    "album":   "Image artiste",
                    "artwork": art,
                    "source":  "iTunes"
                })
        return results
    except (urllib.error.URLError, json.JSONDecodeError, Exception): return []

def search_deezer(q, n=4):
    try:
        p = urllib.parse.urlencode({"q":q,"limit":n})
        d = json.loads(urllib.request.urlopen(
            f"https://api.deezer.com/search?{p}", timeout=5).read())
        return [{"title":   r.get("title",""),
                 "artist":  r.get("artist",{}).get("name",""),
                 "album":   r.get("album",{}).get("title",""),
                 "artwork":  r.get("album",{}).get("cover_xl") or
                             r.get("album",{}).get("cover_big",""),
                 "source":  "Deezer"}
                for r in d.get("data",[])
                if r.get("album",{}).get("cover_xl") or r.get("album",{}).get("cover_big")]
    except (urllib.error.URLError, json.JSONDecodeError, Exception): return []


def search_deezer_artist(q, n=4):
    """Cherche par NOM D'ARTISTE sur Deezer — retourne les photos d'artiste."""
    try:
        p = urllib.parse.urlencode({"q":q,"limit":n})
        d = json.loads(urllib.request.urlopen(
            f"https://api.deezer.com/search/artist?{p}", timeout=5).read())
        results = []
        for r in d.get("data",[]):
            pic = r.get("picture_xl") or r.get("picture_big","")
            if pic and "default" not in pic:
                results.append({
                    "title":   r.get("name",""),
                    "artist":  r.get("name",""),
                    "album":   "Photo artiste",
                    "artwork": pic,
                    "source":  "Deezer"
                })
        return results
    except (urllib.error.URLError, json.JSONDecodeError, Exception): return []

def search_musicbrainz(q, n=4):
    try:
        headers = {"User-Agent": "Tagr/3.0 (audio-metadata-editor)"}
        p = urllib.parse.urlencode({"query": q, "limit": n, "fmt": "json"})
        req = urllib.request.Request(
            f"https://musicbrainz.org/ws/2/recording/?{p}", headers=headers)
        d = json.loads(urllib.request.urlopen(req, timeout=8).read())
        results = []
        for r in d.get("recordings", []):
            releases = r.get("releases", [])
            if not releases: continue
            rel = releases[0]
            rid = rel.get("id", "")
            artist = ""
            if r.get("artist-credit"):
                artist = r["artist-credit"][0].get("artist", {}).get("name", "")
            results.append({
                "title":   r.get("title", ""),
                "artist":  artist,
                "album":   rel.get("title", ""),
                "artwork": f"https://coverartarchive.org/release/{rid}/front-500" if rid else "",
                "source":  "MusicBrainz"
            })
        return [r for r in results if r["artwork"]]
    except (urllib.error.URLError, json.JSONDecodeError, Exception):
        return []


def multi_search(query, n=9):
    """Recherche avec priorité ARTISTE.
    Si un terme artiste est fourni, cherche d'abord par artiste
    puis complète avec les morceaux."""
    results = []
    threads = [
        threading.Thread(target=lambda: results.extend(search_deezer_artist(query, 4)), daemon=True),
        threading.Thread(target=lambda: results.extend(search_itunes_artist(query, 3)), daemon=True),
        threading.Thread(target=lambda: results.extend(search_deezer(query, 3)), daemon=True),
        threading.Thread(target=lambda: results.extend(search_musicbrainz(query, 3)), daemon=True),
    ]
    for t in threads: t.start()
    for t in threads: t.join(8)
    # Dédoublonnage par artwork URL (pas par titre — les images artiste ont des URLs uniques)
    seen_urls = set(); out = []
    for r in results:
        url = r.get("artwork","")
        if url and url not in seen_urls:
            seen_urls.add(url); out.append(r)
    return out[:n]

# ── Crop dialog ───────────────────────────────────────────────────────────────

class CropDialog(QDialog):
    cropped=pyqtSignal(object)
    OUTPUT_SIZE = 640

    def __init__(self, parent, img):
        super().__init__(parent)
        self.setWindowTitle(T("Recadrer la pochette"))
        self.setModal(True); self.setStyleSheet(f"background:{BG2};color:{TEXT};")
        self.orig=img; self._zoom=1.0; self._offset=[0,0]
        self._drag_start=None; self._preview_size=400
        self._build()
        self._render()

    def _build(self):
        v=QVBoxLayout(self); v.setContentsMargins(20,20,20,20); v.setSpacing(12)
        tk=QLabel(T("Recadrer la pochette")); tk.setStyleSheet(f"font-size:14px;font-weight:bold;")
        v.addWidget(tk)

        sub=QLabel(T("crop_hint"))
        sub.setStyleSheet(f"font-size:9px;color:{TEXTD};"); v.addWidget(sub)

        self.canvas=QLabel(); self.canvas.setFixedSize(self._preview_size,self._preview_size)
        self.canvas.setStyleSheet(f"background:#000;border-radius:6px;")
        self.canvas.setCursor(Qt.CursorShape.OpenHandCursor)
        v.addWidget(self.canvas,alignment=Qt.AlignmentFlag.AlignCenter)

        # Zoom slider
        zrow=QHBoxLayout()
        QLabel(T("Zoom")).setParent(None)
        zl=QLabel(T("Zoom")); zl.setStyleSheet(f"color:{TEXTD};font-size:9px;")
        self.zoom_slider=QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setRange(10,400); self.zoom_slider.setValue(100)
        self.zoom_slider.setStyleSheet(f"QSlider::groove:horizontal{{background:{BORDER};height:4px;border-radius:2px;}}"
                                        f"QSlider::handle:horizontal{{background:{ACCENT};width:14px;height:14px;border-radius:7px;margin:-5px 0;}}"
                                        f"QSlider::sub-page:horizontal{{background:{ACCENT};height:4px;border-radius:2px;}}")
        self.zoom_slider.valueChanged.connect(lambda v:(setattr(self,'_zoom',v/100),self._render()))
        zrow.addWidget(zl); zrow.addWidget(self.zoom_slider)
        v.addLayout(zrow)

        brow=QHBoxLayout(); brow.setSpacing(10)
        ok=QPushButton(T("Appliquer"))
        ok.setStyleSheet(f"background:{ACCENT};color:#000;font-weight:bold;border:none;padding:9px 20px;border-radius:4px;")
        ok.setCursor(Qt.CursorShape.PointingHandCursor); ok.clicked.connect(self._apply)
        cancel=QPushButton(T("Annuler"))
        cancel.setStyleSheet(f"background:{PANEL};color:{TEXTM};border:none;padding:9px 20px;border-radius:4px;")
        cancel.setCursor(Qt.CursorShape.PointingHandCursor); cancel.clicked.connect(self.reject)
        brow.addStretch(); brow.addWidget(ok); brow.addWidget(cancel)
        v.addLayout(brow)

    def _render(self):
        S=self._preview_size; img=self.orig.copy()
        z=self._zoom
        new_w=max(1,int(img.width*z)); new_h=max(1,int(img.height*z))
        img=img.resize((new_w,new_h),PILImage.LANCZOS)
        ox=int(self._offset[0]); oy=int(self._offset[1])
        # Centre dans canvas carré
        canvas=PILImage.new("RGB",(S,S),(0,0,0))
        px=S//2-new_w//2+ox; py=S//2-new_h//2+oy
        canvas.paste(img,(px,py))
        # Crop central
        self._current_canvas=canvas
        px2=pil_to_qpixmap_exact(canvas,S,S)
        # Overlay : la pochette Spotify est carree, on garde un cadre 1:1.
        painter=QPainter(px2)
        painter.setPen(QPen(QColor(255,255,255,80),1))
        painter.drawRect(0,0,S-1,S-1)
        painter.end()
        self.canvas.setPixmap(px2)

    def mousePressEvent(self,e):
        if e.button()==Qt.MouseButton.LeftButton:
            self._drag_start=e.globalPosition().toPoint()
            self.canvas.setCursor(Qt.CursorShape.ClosedHandCursor)

    def mouseMoveEvent(self,e):
        if self._drag_start:
            d=e.globalPosition().toPoint()-self._drag_start
            self._drag_start=e.globalPosition().toPoint()
            self._offset[0]+=d.x(); self._offset[1]+=d.y()
            self._render()

    def mouseReleaseEvent(self,e):
        self._drag_start=None
        self.canvas.setCursor(Qt.CursorShape.OpenHandCursor)

    def wheelEvent(self,e):
        delta=e.angleDelta().y()/120
        self._zoom=max(0.1,min(4.0,self._zoom+delta*0.1))
        self.zoom_slider.setValue(int(self._zoom*100))
        self._render()

    def _apply(self):
        S=self._preview_size
        result=self._current_canvas.crop((0,0,S,S))
        result=result.resize((self.OUTPUT_SIZE,self.OUTPUT_SIZE),PILImage.LANCZOS)
        self.cropped.emit(result); self.accept()

# ── Workers ───────────────────────────────────────────────────────────────────

class TagLoader(QThread):
    done=pyqtSignal(str,dict)
    def __init__(self,p): super().__init__(); self.p=p
    def run(self): self.done.emit(self.p,read_tags(self.p))

class Searcher(QThread):
    done=pyqtSignal(list)
    def __init__(self,q): super().__init__(); self.q=q
    def run(self): self.done.emit(multi_search(self.q))

class ImageFetcher(QThread):
    done=pyqtSignal(object,dict)
    def __init__(self,url,meta): super().__init__(); self.url=url; self.meta=meta
    def run(self):
        img=fetch_image_url(self.url)
        if img: self.done.emit(img,self.meta)

# ── Cover label (avec drag & drop image) ─────────────────────────────────────

class CoverLabel(QLabel):
    clicked=pyqtSignal()
    image_dropped=pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.setFixedSize(160,160)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setAcceptDrops(True)
        self._reset()

    def _reset(self):
        self.setPixmap(QPixmap())
        self.setScaledContents(False)
        self.setText(T("Ajouter\nune pochette"))
        self.setStyleSheet(f"background:{PANEL};border-radius:6px;color:{TEXTD};"
                           f"font-size:13px;border:2px dashed {BORDER};")

    def set_image(self,img):
        px=pil_to_qpixmap(img,160)
        self.setPixmap(px); self.setScaledContents(True); self.setText("")
        self.setStyleSheet(f"background:{PANEL};border-radius:6px;border:none;")

    def mousePressEvent(self,e): self.clicked.emit()

    def dragEnterEvent(self,e):
        if e.mimeData().hasUrls():
            urls=[u.toLocalFile() for u in e.mimeData().urls()]
            if any(is_image(u) for u in urls):
                e.acceptProposedAction()
                self.setStyleSheet(f"background:{SELBG};border-radius:6px;color:{ACCENT};"
                                   f"font-size:11px;border:2px solid {ACCENT};")
                self.setText(T("Déposer ici"))

    def dragLeaveEvent(self,e):
        if self.pixmap() and not self.pixmap().isNull():
            self.setStyleSheet(f"background:{PANEL};border-radius:6px;border:none;")
        else: self._reset()

    def dropEvent(self,e):
        for url in e.mimeData().urls():
            p=url.toLocalFile()
            if is_image(p):
                try:
                    img=PILImage.open(p).convert("RGB")
                    self.image_dropped.emit(img); break
                except (OSError, IOError, Exception): pass
        e.acceptProposedAction()

# ── FileRow ───────────────────────────────────────────────────────────────────

class FileRow(QFrame):
    selected_signal=pyqtSignal(object, object)
    delete_signal=pyqtSignal(object)

    def __init__(self,path):
        super().__init__()
        self.path=path; self._selected=False; self._dirty=False; self._hover=False
        self.setFixedHeight(60); self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._build(); self._style(False)

    def _build(self):
        lay=QHBoxLayout(self); lay.setContentsMargins(10,8,10,8); lay.setSpacing(10)
        self.thumb=QLabel(); self.thumb.setFixedSize(44,44)
        self.thumb.setStyleSheet(f"background:{PANEL2};border-radius:4px;")
        lay.addWidget(self.thumb)
        mid=QVBoxLayout(); mid.setSpacing(2)
        self.lbl_t=QLabel(os.path.basename(self.path))
        self.lbl_t.setStyleSheet(f"color:{TEXT};font-size:12px;font-weight:bold;background:transparent;")
        self.lbl_a=QLabel("—")
        self.lbl_a.setStyleSheet(f"color:{TEXTM};font-size:10px;background:transparent;")
        mid.addWidget(self.lbl_t); mid.addWidget(self.lbl_a); lay.addLayout(mid,1)
        right=QVBoxLayout(); right.setSpacing(4); right.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.dot=QLabel("●"); self.dot.setStyleSheet("color:transparent;font-size:7px;background:transparent;")
        self.dot.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ext=os.path.splitext(self.path)[1].lstrip(".").upper()
        badge=QLabel(ext)
        badge.setStyleSheet(f"color:{TEXTD};font-size:8px;font-family:'Courier New';"
                            f"background:transparent;padding:0;")
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setFixedWidth(32)
        right.addWidget(self.dot); right.addWidget(badge)
        right.setAlignment(self.dot, Qt.AlignmentFlag.AlignCenter)
        right.setAlignment(badge, Qt.AlignmentFlag.AlignCenter)
        lay.addLayout(right)

    def set_display(self,title,artist,cover=None):
        self.lbl_t.setText(title or os.path.basename(self.path))
        self.lbl_a.setText(artist or T("unknown_artist"))
        if cover:
            px=pil_to_qpixmap(cover,44); self.thumb.setPixmap(px); self.thumb.setScaledContents(True)

    def set_dirty(self,val):
        self._dirty=val
        self.dot.setStyleSheet("color:transparent;font-size:7px;background:transparent;")

    def set_selected(self,val):
        self._selected=val; self._style(val)

    def _style(self,sel):
        bg=SELBG if sel else (PANEL2 if self._hover else PANEL)
        bl=f"border-left:2px solid {ACCENT};" if sel else "border-left:2px solid transparent;"
        border=f"border-top:1px solid {BORDER};border-bottom:1px solid {BORDER};" if self._hover and not sel else ""
        self.setStyleSheet(f"FileRow{{background:{bg};{bl}{border}}}")

    def enterEvent(self,e):
        self._hover=True; self._style(self._selected); super().enterEvent(e)

    def leaveEvent(self,e):
        self._hover=False; self._style(self._selected); super().leaveEvent(e)

    def mousePressEvent(self,e):
        if e.button()==Qt.MouseButton.LeftButton: self.selected_signal.emit(self, e)
        elif e.button()==Qt.MouseButton.RightButton: self._ctx(e)

    def _ctx(self,e):
        from PyQt6.QtWidgets import QMenu
        m=QMenu(self)
        m.setStyleSheet(f"QMenu{{background:{PANEL2};color:{TEXT};border:1px solid {BORDER};padding:4px;}}"
                        f"QMenu::item{{padding:6px 16px;}}"
                        f"QMenu::item:selected{{background:{ERROR};color:{TEXT};}}")
        m.addAction(T("Retirer de la liste"),lambda:self.delete_signal.emit(self))
        m.exec(e.globalPosition().toPoint())

# ── Cover picker ──────────────────────────────────────────────────────────────

class CoverPicker(QDialog):
    chosen = pyqtSignal(object, dict)

    def __init__(self, parent, results):
        super().__init__(parent)
        self.setWindowTitle(T("Recherche de pochette"))
        self.setStyleSheet(f"background:{BG2};color:{TEXT};")
        self.setModal(True)
        self.setMinimumWidth(500)
        self.results = results
        self.fetchers = []
        self._count = 0
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setSpacing(10); lay.setContentsMargins(20, 18, 20, 18)

        # Titre
        title = QLabel(T("Recherche de pochette"))
        title.setStyleSheet(f"font-size:15px;font-weight:bold;color:{TEXT};")
        lay.addWidget(title)

        # Sources
        src_lbl = QLabel(T("cover_sources"))
        src_lbl.setStyleSheet(f"font-size:9px;color:{TEXTD};")
        lay.addWidget(src_lbl)

        # Champ URL directe
        url_row = QHBoxLayout(); url_row.setSpacing(8)
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText(T("img_url_placeholder"))
        self.url_input.setStyleSheet(
            f"background:{FIELDBG};color:{TEXT};border:1px solid {BORDER};"
            f"border-radius:4px;padding:7px 10px;font-size:11px;")
        url_btn = QPushButton(T("Utiliser"))
        url_btn.setStyleSheet(
            f"background:{ACCENT};color:#000;font-weight:bold;border:none;"
            f"padding:7px 14px;border-radius:4px;font-size:11px;")
        url_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        url_btn.clicked.connect(self._use_url)
        url_row.addWidget(self.url_input, 1)
        url_row.addWidget(url_btn)
        lay.addLayout(url_row)

        hint = QLabel(T("img_astuce"))
        hint.setStyleSheet(f"font-size:8px;color:{TEXTD};")
        lay.addWidget(hint)

        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color:{BORDER};"); lay.addWidget(sep)

        # Grille résultats
        results_lbl = QLabel(T("Résultats automatiques :"))
        results_lbl.setStyleSheet(f"font-size:10px;color:{TEXTM};")
        lay.addWidget(results_lbl)

        self.grid = QGridLayout(); self.grid.setSpacing(8)
        lay.addLayout(self.grid)

        self.no_results_lbl = QLabel(T("Chargement des résultats..."))
        self.no_results_lbl.setStyleSheet(f"color:{TEXTD};font-size:10px;")
        self.no_results_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.no_results_lbl)

        cancel = QPushButton(T("Fermer"))
        cancel.setStyleSheet(
            f"background:{PANEL};color:{TEXTM};border:none;"
            f"padding:8px 20px;font-size:11px;border-radius:4px;")
        cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel.clicked.connect(self.reject)
        lay.addWidget(cancel, alignment=Qt.AlignmentFlag.AlignCenter)

        # Charger les images
        if self.results:
            self.no_results_lbl.hide()
            for r in self.results[:9]:
                if r.get("artwork"):
                    f = ImageFetcher(r["artwork"], r)
                    f.done.connect(self._add)
                    f.start(); self.fetchers.append(f)
        else:
            self.no_results_lbl.setText(T("cover_no_results"))

    def _use_url(self):
        url = self.url_input.text().strip()
        if not url: return
        self.no_results_lbl.setText(T("Chargement de l'image..."))
        self.no_results_lbl.show()
        f = ImageFetcher(url, {"title": "", "artist": "", "album": "",
                                "source": "URL directe"})
        f.done.connect(lambda img, meta: (self.chosen.emit(img, meta), self.accept()))
        f.done.connect(lambda img, meta: None)
        f.start(); self.fetchers.append(f)

    def _add(self, img, meta):
        i = self._count; self._count += 1
        row, col = i // 3, i % 3

        fr = QFrame()
        fr.setStyleSheet(f"background:{PANEL};border-radius:6px;")
        fr.setCursor(Qt.CursorShape.PointingHandCursor)
        v = QVBoxLayout(fr); v.setContentsMargins(5, 5, 5, 5); v.setSpacing(2)

        px = pil_to_qpixmap(img, 120)
        lbl = QLabel(); lbl.setPixmap(px)
        lbl.setScaledContents(True); lbl.setFixedSize(120, 120)

        title_lbl = QLabel((meta.get("title") or "")[:20])
        title_lbl.setStyleSheet(
            f"color:{TEXT};font-size:8px;font-weight:bold;background:transparent;")

        artist_lbl = QLabel((meta.get("artist") or "")[:20])
        artist_lbl.setStyleSheet(f"color:{TEXTM};font-size:7px;background:transparent;")

        src = meta.get("source", "")
        src_colors = {"iTunes": ACCENT, "Deezer": "#0064ff",
                      "MusicBrainz": "#ba8f00"}
        src_lbl = QLabel(src)
        src_lbl.setStyleSheet(
            f"color:{src_colors.get(src, TEXTD)};font-size:7px;background:transparent;")

        for w in [lbl, title_lbl, artist_lbl, src_lbl]:
            v.addWidget(w, alignment=Qt.AlignmentFlag.AlignCenter)

        def click(checked=False, img=img, meta=meta):
            self.chosen.emit(img, meta); self.accept()
        fr.mousePressEvent = lambda e, fn=click: fn()
        lbl.mousePressEvent = lambda e, fn=click: fn()

        self.grid.addWidget(fr, row, col)

# ── Panel empilé ──────────────────────────────────────────────────────────────

class StackPanel(QWidget):
    def __init__(self):
        super().__init__(); self.setStyleSheet(f"background:{BG};")
        self._lay=QVBoxLayout(self); self._lay.setContentsMargins(0,0,0,0)
        self.empty=None; self.editor=None
    def addWidget(self,w): self._lay.addWidget(w)
    def show_empty(self):
        if self.empty: self.empty.show()
        if self.editor: self.editor.hide()
    def show_editor(self):
        if self.empty: self.empty.hide()
        if self.editor: self.editor.show()

# ── App principale ────────────────────────────────────────────────────────────

# ── Waveform loader ───────────────────────────────────────────────────────────

def load_waveform(path, n_bars=100):
    """Génère les données de forme d'onde. Retourne liste de 0.0-1.0."""
    import struct, wave as wavemod
    tmp = "/tmp/tagr_wave.wav"
    try:
        r = subprocess.run(
            ["afconvert","-f","WAVE","-d","LEI16@8000","-c","1", path, tmp],
            capture_output=True, timeout=15)
        if r.returncode != 0:
            raise Exception("afconvert failed")
        with wavemod.open(tmp,"rb") as wf:
            raw = wf.readframes(wf.getnframes())
        samples = struct.unpack(f"<{len(raw)//2}h", raw)
        chunk = max(1, len(samples) // n_bars)
        bars = []
        for i in range(n_bars):
            sl = samples[i*chunk:(i+1)*chunk]
            bars.append(max(abs(s) for s in sl)/32768.0 if sl else 0.0)
        return bars
    except Exception:
        # Fallback : barres simulées si afconvert échoue
        import math, random; random.seed(0)
        return [abs(math.sin(i/4))*0.6 + random.random()*0.4 for i in range(n_bars)]


class WaveformLoader(QThread):
    done = pyqtSignal(list)
    def __init__(self, path): super().__init__(); self.path = path
    def run(self): self.done.emit(load_waveform(self.path))


# ── iPhone-style timeline ─────────────────────────────────────────────────────

class IPhoneTimeline(QWidget):
    """Timeline de découpe style éditeur vidéo iPhone.
    Poignée gauche (start) et droite (end) sur fond waveform.
    Zone sélectionnée éclairée, zones hors sélection assombries.
    """
    range_changed = pyqtSignal(float, float)
    HANDLE_W = 18   # largeur des poignées
    MIN_SEL  = 0.02 # sélection minimum en ratio

    def __init__(self, duration):
        super().__init__()
        self.duration = duration
        self.setFixedHeight(72)
        self.setMinimumWidth(500)
        self._start   = 0.0
        self._end     = 1.0
        self._bars    = []
        self._drag    = None   # "start" | "end" | "body"
        self._drag_offset = 0.0
        self.setMouseTracking(True)

    def set_waveform(self, bars):
        self._bars = bars
        self.update()

    def set_range(self, s, e):
        self._start = max(0.0, min(1.0, s))
        self._end   = max(0.0, min(1.0, e))
        self.update()

    def _r2x(self, r):
        W = self.width()
        return int(self.HANDLE_W + r * (W - 2 * self.HANDLE_W))

    def _x2r(self, x):
        W = self.width()
        inner = W - 2 * self.HANDLE_W
        return max(0.0, min(1.0, (x - self.HANDLE_W) / inner))

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        W, H = self.width(), self.height()
        HW   = self.HANDLE_W
        inner_w = W - 2 * HW

        xs = self._r2x(self._start)
        xe = self._r2x(self._end)

        # ── Fond total ─────────────────────────────────────────────────
        p.fillRect(0, 0, W, H, QColor(20, 20, 20))

        # ── Waveform ───────────────────────────────────────────────────
        bars = self._bars
        n    = len(bars) if bars else 1
        bar_w = max(1.0, inner_w / n)
        mid_y = H // 2

        for i, v in enumerate(bars):
            bx = HW + int(i * inner_w / n)
            bh = max(2, int(v * (H - 10)))
            by = mid_y - bh // 2

            # Couleur : sélectionnée vs hors sélection
            ratio = i / n
            if self._start <= ratio <= self._end:
                c = QColor(ACCENT); c.setAlpha(220)
            else:
                c = QColor(70, 70, 70)
            p.fillRect(int(bx), by, max(1, int(bar_w) - 1), bh, c)

        # ── Overlay sombre hors sélection ──────────────────────────────
        shadow = QColor(0, 0, 0, 140)
        p.fillRect(HW, 0, max(0, xs - HW), H, shadow)
        p.fillRect(xe, 0, max(0, W - xe - HW), H, shadow)

        # ── Bordures de sélection (haut et bas) ────────────────────────
        p.setPen(QPen(QColor(ACCENT), 2))
        p.drawLine(xs, 0, xe, 0)
        p.drawLine(xs, H-1, xe, H-1)

        # ── Poignée GAUCHE ─────────────────────────────────────────────
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(ACCENT)))
        p.drawRoundedRect(0, 0, HW, H, 5, 5)
        # Ligne blanche centrale
        p.setPen(QPen(QColor(0, 0, 0, 200), 3, Qt.PenStyle.SolidLine,
                      Qt.PenCapStyle.RoundCap))
        cx = HW // 2
        p.drawLine(cx - 2, H//2 - 8, cx - 2, H//2 + 8)
        p.drawLine(cx + 2, H//2 - 8, cx + 2, H//2 + 8)

        # ── Poignée DROITE ─────────────────────────────────────────────
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(ACCENT)))
        p.drawRoundedRect(W - HW, 0, HW, H, 5, 5)
        p.setPen(QPen(QColor(0, 0, 0, 200), 3, Qt.PenStyle.SolidLine,
                      Qt.PenCapStyle.RoundCap))
        cx2 = W - HW // 2
        p.drawLine(cx2 - 2, H//2 - 8, cx2 - 2, H//2 + 8)
        p.drawLine(cx2 + 2, H//2 - 8, cx2 + 2, H//2 + 8)

        # ── Repositionner les poignées sur xs/xe ───────────────────────
        # Poignée start (colle au marqueur xs)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(ACCENT)))
        p.drawRoundedRect(xs - HW, 0, HW, H, 4, 4)
        p.setPen(QPen(QColor(0,0,0,180), 3, Qt.PenStyle.SolidLine,
                      Qt.PenCapStyle.RoundCap))
        lx = xs - HW//2
        p.drawLine(lx-2, H//2-8, lx-2, H//2+8)
        p.drawLine(lx+2, H//2-8, lx+2, H//2+8)

        # Poignée end
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(ACCENT)))
        p.drawRoundedRect(xe, 0, HW, H, 4, 4)
        p.setPen(QPen(QColor(0,0,0,180), 3, Qt.PenStyle.SolidLine,
                      Qt.PenCapStyle.RoundCap))
        rx = xe + HW//2
        p.drawLine(rx-2, H//2-8, rx-2, H//2+8)
        p.drawLine(rx+2, H//2-8, rx+2, H//2+8)

        p.end()

    def mousePressEvent(self, e):
        x  = e.position().x()
        xs = self._r2x(self._start)
        xe = self._r2x(self._end)
        HW = self.HANDLE_W

        if xs - HW <= x <= xs + 4:
            self._drag = "start"
        elif xe - 4 <= x <= xe + HW:
            self._drag = "end"
        elif xs < x < xe:
            self._drag = "body"
            self._drag_offset = self._x2r(x) - self._start
        self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def mouseMoveEvent(self, e):
        if not self._drag:
            # Cursor adaptatif
            x  = e.position().x()
            xs = self._r2x(self._start)
            xe = self._r2x(self._end)
            HW = self.HANDLE_W
            if xs - HW <= x <= xs + 4 or xe - 4 <= x <= xe + HW:
                self.setCursor(Qt.CursorShape.SizeHorCursor)
            elif xs < x < xe:
                self.setCursor(Qt.CursorShape.SizeAllCursor)
            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)
            return

        r = self._x2r(e.position().x())
        if self._drag == "start":
            self._start = max(0.0, min(r, self._end - self.MIN_SEL))
        elif self._drag == "end":
            self._end = min(1.0, max(r, self._start + self.MIN_SEL))
        elif self._drag == "body":
            w = self._end - self._start
            s = max(0.0, min(1.0 - w, r - self._drag_offset))
            self._start = s
            self._end   = s + w
        self.update()
        self.range_changed.emit(self._start, self._end)

    def mouseReleaseEvent(self, _):
        self._drag = None
        self.setCursor(Qt.CursorShape.ArrowCursor)


# ── TrimDialog ────────────────────────────────────────────────────────────────

class TrimDialog(QDialog):
    def __init__(self, parent, path, duration):
        super().__init__(parent)
        self.setWindowTitle(T("Couper le morceau"))
        self.setModal(True)
        self.setMinimumWidth(620)
        self.setStyleSheet(f"background:{BG2};color:{TEXT};")
        self.path     = path
        self.duration = duration
        self._play_proc   = None
        self._ffmpeg_proc = None
        self._preview_tmp = None
        self._build()
        # Charge la waveform en arrière-plan
        self._wf_loader = WaveformLoader(path)
        self._wf_loader.done.connect(self.timeline.set_waveform)
        self._wf_loader.start()

    def _build(self):
        v = QVBoxLayout(self)
        v.setContentsMargins(20, 18, 20, 18)
        v.setSpacing(10)

        # Titre + nom fichier
        tk = QLabel(T("Couper le morceau"))
        tk.setStyleSheet(f"font-size:15px;font-weight:bold;color:{TEXT};")
        fn = QLabel(os.path.basename(self.path))
        fn.setStyleSheet(f"font-size:10px;color:{TEXTD};")
        v.addWidget(tk); v.addWidget(fn)

        # ── Timeline iPhone-style ──────────────────────────────────────
        self.timeline = IPhoneTimeline(self.duration)
        self.timeline.range_changed.connect(self._on_range)
        v.addWidget(self.timeline)

        # ── Temps start / durée / end ──────────────────────────────────
        row = QHBoxLayout()
        self.lbl_s = QLabel("0:00.0")
        self.lbl_s.setStyleSheet(f"color:{ACCENT};font-size:12px;font-weight:bold;")
        self.lbl_d = QLabel(T("duration_label").replace("{duration}", self._fmt(self.duration)))
        self.lbl_d.setStyleSheet(f"color:{TEXTM};font-size:11px;")
        self.lbl_d.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_e = QLabel(self._fmt(self.duration))
        self.lbl_e.setStyleSheet(f"color:{ACCENT};font-size:12px;font-weight:bold;")
        self.lbl_e.setAlignment(Qt.AlignmentFlag.AlignRight)
        row.addWidget(self.lbl_s)
        row.addWidget(self.lbl_d, 1)
        row.addWidget(self.lbl_e)
        v.addLayout(row)

        # ── Champs saisie précise ──────────────────────────────────────
        pr = QHBoxLayout(); pr.setSpacing(16)

        def tfield(label, attr, placeholder):
            col = QVBoxLayout(); col.setSpacing(3)
            col.addWidget(QLabel(label, styleSheet=f"color:{TEXTD};font-size:9px;"))
            e = QLineEdit(); e.setPlaceholderText(placeholder)
            e.setMaximumWidth(100)
            e.setStyleSheet(
                f"background:{FIELDBG};color:{TEXT};border:1px solid {BORDER};"
                f"border-radius:4px;padding:6px 8px;font-size:12px;"
                f"font-family:'Courier New';")
            col.addWidget(e); pr.addLayout(col)
            setattr(self, attr, e); return e

        tfield(T("start_time"), "edit_s", "0:00.0").setText("0:00.0")
        tfield(T("end_time"),   "edit_e", self._fmt(self.duration)).setText(self._fmt(self.duration))
        self.edit_s.editingFinished.connect(self._from_text_s)
        self.edit_e.editingFinished.connect(self._from_text_e)

        pr.addStretch()
        reset = QPushButton(T("Tout sélectionner"))
        reset.setStyleSheet(
            f"background:{PANEL};color:{TEXTM};border:none;"
            f"padding:8px 12px;font-size:10px;border-radius:4px;")
        reset.setCursor(Qt.CursorShape.PointingHandCursor)
        reset.clicked.connect(self._reset)
        pr.addWidget(reset, alignment=Qt.AlignmentFlag.AlignBottom)
        v.addLayout(pr)

        hint = QLabel(T("trim_hint"))
        hint.setStyleSheet(f"color:{TEXTD};font-size:9px;")
        v.addWidget(hint)

        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color:{BORDER};"); v.addWidget(sep)

        # ── Boutons ────────────────────────────────────────────────────
        br = QHBoxLayout(); br.setSpacing(10)

        self.prev_btn = QPushButton(T("▶  Écouter la sélection"))
        self.prev_btn.setStyleSheet(
            f"background:{PANEL};color:{TEXT};border:none;"
            f"padding:10px 18px;font-size:11px;border-radius:5px;")
        self.prev_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.prev_btn.clicked.connect(self._toggle_preview)

        apply_btn = QPushButton(T("Appliquer le découpage"))
        apply_btn.setStyleSheet(
            f"background:{ACCENT};color:#000;font-weight:bold;border:none;"
            f"padding:10px 22px;font-size:12px;border-radius:5px;")
        apply_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        apply_btn.clicked.connect(self._apply)

        cancel_btn = QPushButton(T("Annuler"))
        cancel_btn.setStyleSheet(
            f"background:{PANEL};color:{TEXTM};border:none;"
            f"padding:10px 16px;font-size:11px;border-radius:5px;")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)

        br.addWidget(self.prev_btn); br.addStretch()
        br.addWidget(cancel_btn); br.addWidget(apply_btn)
        v.addLayout(br)

        self.status = QLabel("")
        self.status.setStyleSheet(f"color:{ACCENT};font-size:10px;")
        v.addWidget(self.status)

    # ── Helpers ───────────────────────────────────────────────────────

    def _fmt(self, s):
        m, sec = divmod(float(s), 60)
        return f"{int(m)}:{sec:04.1f}"

    def _parse(self, txt):
        try:
            txt = txt.strip()
            if ":" in txt:
                p = txt.split(":")
                return int(p[0]) * 60 + float(p[1])
            return float(txt)
        except Exception:
            return None

    def _get_times(self):
        return (self.timeline._start * self.duration,
                self.timeline._end   * self.duration)

    def _update_labels(self, ts, te):
        self.lbl_s.setText(self._fmt(ts))
        self.lbl_e.setText(self._fmt(te))
        self.lbl_d.setText(T("duration_label").replace("{duration}", self._fmt(te - ts)))
        self.edit_s.blockSignals(True); self.edit_e.blockSignals(True)
        self.edit_s.setText(self._fmt(ts))
        self.edit_e.setText(self._fmt(te))
        self.edit_s.blockSignals(False); self.edit_e.blockSignals(False)

    def _on_range(self, s, e):
        self._update_labels(s * self.duration, e * self.duration)

    def _from_text_s(self):
        t = self._parse(self.edit_s.text())
        if t is None: return
        t = max(0.0, min(t, self.duration - 0.5))
        te = self.timeline._end * self.duration
        t = min(t, te - 0.5)
        self.timeline.set_range(t / self.duration, self.timeline._end)
        self._update_labels(t, te)

    def _from_text_e(self):
        t = self._parse(self.edit_e.text())
        if t is None: return
        t = max(0.5, min(t, self.duration))
        ts = self.timeline._start * self.duration
        t = max(t, ts + 0.5)
        self.timeline.set_range(self.timeline._start, t / self.duration)
        self._update_labels(ts, t)

    def _reset(self):
        self.timeline.set_range(0.0, 1.0)
        self._update_labels(0.0, self.duration)

    def _find_ffmpeg(self):
        for c in ["/opt/homebrew/bin/ffmpeg","/usr/local/bin/ffmpeg",
                  "/usr/bin/ffmpeg","/opt/local/bin/ffmpeg"]:
            if os.path.isfile(c): return c
        r = subprocess.run(["which","ffmpeg"], capture_output=True)
        return r.stdout.decode().strip() if r.returncode == 0 else None

    # ── Preview ───────────────────────────────────────────────────────

    def _toggle_preview(self):
        # Si en cours → stop
        if self._play_proc and self._play_proc.poll() is None:
            self._play_proc.terminate()
            self._play_proc = None
            self.prev_btn.setText(T("▶  Écouter la sélection"))
            return

        ts, te = self._get_times()
        dur = te - ts
        if dur < 0.1: return

        ffmpeg = self._find_ffmpeg()
        if not ffmpeg:
            self.status.setStyleSheet(f"color:{ERROR};font-size:10px;")
            self.status.setText(T("ffmpeg_not_found"))
            return

        # Extraire la sélection dans un fichier tmp puis jouer avec afplay
        import tempfile
        tmp = tempfile.mktemp(suffix=os.path.splitext(self.path)[1])
        self._preview_tmp = tmp

        cmd = [ffmpeg, "-y", "-ss", str(ts), "-t", str(dur),
               "-i", self.path, "-c", "copy", tmp]
        try:
            r = subprocess.run(cmd, capture_output=True, timeout=30)
        except subprocess.TimeoutExpired:
            self.status.setStyleSheet(f"color:{ERROR};font-size:10px;")
            self.status.setText(T("ffmpeg_preview_error"))
            return
        if r.returncode != 0:
            self.status.setStyleSheet(f"color:{ERROR};font-size:10px;")
            self.status.setText(T("ffmpeg_preview_error"))
            return

        try:
            self._play_proc = subprocess.Popen(
                ["/usr/bin/afplay", tmp],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.prev_btn.setText(T("⏹  Stop"))
            def watch():
                self._play_proc.wait()
                try:
                    os.remove(tmp)
                except (OSError, IOError, Exception): pass
                QTimer.singleShot(0, lambda: self.prev_btn.setText(T("▶  Écouter la sélection")))
            threading.Thread(target=watch, daemon=True).start()
        except Exception as ex:
            self.status.setStyleSheet(f"color:{ERROR};font-size:10px;")
            self.status.setText(f"Erreur lecture : {ex}")

    # ── Apply ─────────────────────────────────────────────────────────

    def _apply(self):
        ts, te = self._get_times()
        if te - ts < 0.5:
            self.status.setStyleSheet(f"color:{ERROR};font-size:10px;")
            self.status.setText(T("Sélection trop courte")); return

        ffmpeg = self._find_ffmpeg()
        if not ffmpeg:
            self.status.setStyleSheet(f"color:{ERROR};font-size:10px;")
            self.status.setText(T("ffmpeg_not_found")); return

        base, ext = os.path.splitext(self.path)
        out = f"{base}_cut{ext}"
        i = 1
        while os.path.exists(out):
            out = f"{base}_cut{i}{ext}"; i += 1

        self.status.setStyleSheet(f"color:{ACCENT};font-size:10px;")
        self.status.setText(T("Découpage en cours…"))
        QApplication.processEvents()

        try:
            r = subprocess.run(
                [ffmpeg,"-y","-ss",str(ts),"-t",str(te-ts),
                 "-i",self.path,"-c","copy", out],
                capture_output=True, timeout=300)
        except subprocess.TimeoutExpired:
            self.status.setStyleSheet(f"color:{ERROR};font-size:10px;")
            self.status.setText(T("ffmpeg_preview_error"))
            return

        if r.returncode == 0:
            try:
                orig = read_tags(self.path)
                write_tags(out, orig["title"], orig["artist"], orig["album"],
                           orig.get("year",""), orig.get("genre",""),
                           orig.get("bpm",""), orig.get("track",""),
                           orig.get("cover"))
            except (OSError, IOError, Exception): pass
            try: subprocess.run(["mdimport", out], capture_output=True, timeout=10)
            except Exception: pass
            try: subprocess.run(["open", "-R", out], timeout=5)
            except Exception: pass
            self.status.setText(f"Créé : {os.path.basename(out)}")
        else:
            self.status.setStyleSheet(f"color:{ERROR};font-size:10px;")
            self.status.setText(f"Erreur ffmpeg : {r.stderr.decode()[-80:]}")

    def closeEvent(self, e):
        for proc in [self._play_proc, self._ffmpeg_proc]:
            if proc and proc.poll() is None:
                proc.terminate()
        if self._preview_tmp and os.path.exists(self._preview_tmp):
            try: os.remove(self._preview_tmp)
            except (OSError, IOError, Exception): pass
        e.accept()


class FfmpegWorker(QThread):
    progress = pyqtSignal(int)    # 0-100
    finished = pyqtSignal(bool, str)  # success, message

    def __init__(self, cmd, duration_ms=0):
        super().__init__()
        self.cmd = cmd
        self.duration_ms = duration_ms

    def run(self):
        import re as _re
        try:
            cmd = self.cmd + ["-progress", "pipe:2", "-nostats"]
            proc = subprocess.Popen(
                cmd, stderr=subprocess.PIPE, stdout=subprocess.DEVNULL,
                text=True, bufsize=1)
            for line in proc.stderr:
                line = line.strip()
                m = _re.search(r"out_time_ms=(-?\d+)", line)
                if m and self.duration_ms > 0:
                    t = max(0, int(m.group(1)))
                    pct = min(99, int(t / self.duration_ms * 100))
                    self.progress.emit(pct)
                elif "progress=end" in line:
                    self.progress.emit(100)
            proc.wait()
            if proc.returncode == 0:
                self.finished.emit(True, "")
            else:
                self.finished.emit(False, "Erreur ffmpeg")
        except Exception as e:
            self.finished.emit(False, str(e))


class DlWorker(QThread):
    """Worker de téléchargement audio via yt-dlp."""
    success = pyqtSignal(str)   # chemin du fichier téléchargé
    error   = pyqtSignal(str)   # message d'erreur

    AUDIO_EXTS = (".mp3", ".flac", ".m4a", ".aac", ".wav", ".opus", ".webm", ".ogg", ".oga")

    def __init__(self, cmd, dest, before, url=None, ytdlp_opts=None):
        super().__init__()
        self.cmd = cmd
        self.dest = dest
        self.before = before
        self.url = url
        self.ytdlp_opts = ytdlp_opts
        self._proc = None
        self._cancelled = False

    def cancel(self):
        self._cancelled = True
        if self._proc and self._proc.poll() is None:
            try:
                self._proc.terminate()
            except Exception:
                pass

    def _audio_files(self):
        return set(
            os.path.join(self.dest, f) for f in os.listdir(self.dest)
            if f.lower().endswith(self.AUDIO_EXTS)
        )

    def _emit_downloaded_file(self):
        after = self._audio_files()
        new_files = sorted(after - self.before, key=os.path.getmtime, reverse=True)
        if new_files:
            self.success.emit(new_files[0])
            return
        all_a = list(after)
        if all_a:
            self.success.emit(max(all_a, key=os.path.getmtime))
        else:
            self.error.emit(T("dl_file_not_found"))

    def _run_python_ytdlp(self):
        class DownloadCancelled(Exception):
            pass

        def hook(_info):
            if self._cancelled:
                raise DownloadCancelled()

        try:
            import yt_dlp
        except Exception:
            self.error.emit("yt-dlp introuvable")
            return

        opts = dict(self.ytdlp_opts or {})
        hooks = list(opts.get("progress_hooks", []))
        hooks.append(hook)
        opts["progress_hooks"] = hooks

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.extract_info(self.url, download=True)
            if self._cancelled:
                self.error.emit(T("dl_cancelled"))
            else:
                self._emit_downloaded_file()
        except DownloadCancelled:
            self.error.emit(T("dl_cancelled"))
        except Exception as ex:
            self.error.emit(str(ex))

    def run(self):
        if self.ytdlp_opts is not None:
            self._run_python_ytdlp()
            return
        try:
            self._proc = subprocess.Popen(
                self.cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            try:
                out, err = self._proc.communicate(timeout=300)
            except subprocess.TimeoutExpired:
                self.cancel()
                try:
                    self._proc.communicate(timeout=5)
                except Exception:
                    pass
                self.error.emit(T("dl_timeout"))
                return
            if self._cancelled:
                self.error.emit(T("dl_cancelled"))
                return
            if self._proc.returncode != 0:
                msg = err[-300:] if err else "Erreur inconnue"
                self.error.emit(msg)
                return
            self._emit_downloaded_file()
        except Exception as ex:
            self.error.emit(str(ex))


class Tagr(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(T("app_title")); self.resize(1060,720); self.setMinimumSize(820,560)
        # Titlebar macOS transparente — on dessine notre propre barre
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        try:
            # Masquer la titlebar native et étendre le contenu dans la zone de titre
            from PyQt6.QtCore import Qt as _Qt
            self.setWindowFlag(_Qt.WindowType.FramelessWindowHint, False)
            # Utiliser le style macOS sans titlebar visible
            self.setUnifiedTitleAndToolBarOnMac(True)
        except Exception: pass
        self.setStyleSheet(f"QMainWindow{{background:{BG};}}")
        self.setAcceptDrops(True)
        self.files=[]; self.rows=[]; self.current_index=-1
        self.selected_rows=set(); self._selection_anchor=None
        self.current_cover=None; self.tags_cache={}
        self._play_proc=None; self._workers=[]
        self._sort_key="name"; self._filter_text=""
        self._cfg=load_config()
        self._build_ui()
        QShortcut(QKeySequence("Ctrl+S"),self,self._save_current)
        QShortcut(QKeySequence("Meta+S"),self,self._save_current)
        QShortcut(QKeySequence(Qt.Key.Key_Delete),self,self._delete_selected)
        QShortcut(QKeySequence(Qt.Key.Key_Backspace),self,self._delete_selected)
        QShortcut(QKeySequence(Qt.Key.Key_Up),self,self._prev_file)
        QShortcut(QKeySequence(Qt.Key.Key_Down),self,self._next_file)
        # Espace géré via keyPressEvent pour respecter le focus des champs
        QShortcut(QKeySequence("Ctrl+I"),self,self._show_shortcuts)
        QShortcut(QKeySequence("Meta+I"),self,self._show_shortcuts)
        # Cleanup workers toutes les 30 secondes
        self._cleanup_timer = QTimer(self)
        self._cleanup_timer.timeout.connect(self._cleanup_workers)
        self._cleanup_timer.start(30000)
        # Restaurer theme
        self._is_dark = self._cfg.get("is_dark", True)
        if not self._is_dark:
            _apply_palette(LIGHT_PALETTE)
        QShortcut(QKeySequence("Ctrl+Z"),self,self._undo_current)
        QShortcut(QKeySequence("Meta+Z"),self,self._undo_current)
        QShortcut(QKeySequence("Ctrl+Shift+S"),self,self._save_all)
        QShortcut(QKeySequence("Meta+Shift+S"),self,self._save_all)
        # Restaure geometry
        geo = self._cfg.get("geometry")
        if geo:
            try:
                from PyQt6.QtCore import QByteArray
                self.restoreGeometry(QByteArray.fromHex(geo.encode()))
            except Exception: pass
        # Restaure les fichiers de la session précédente
        for p in self._cfg.get("recent_files", []):
            if os.path.isfile(p) and p not in self.files:
                self.files.append(p); self._add_row(p)
        if self.files: self._update_count()

    # ── Drag & drop (fenêtre entière) ─────────────────────────────────────────

    def dragEnterEvent(self,e):
        if e.mimeData().hasUrls():
            urls=[u.toLocalFile() for u in e.mimeData().urls()]
            if any(is_audio(u) or os.path.isdir(u) for u in urls):
                e.acceptProposedAction()
                self.list_widget.setStyleSheet(f"background:{SELBG};border-right:1px solid {BORDER};")

    def dragLeaveEvent(self,e):
        self.list_widget.setStyleSheet(f"background:{BG2};")

    def dropEvent(self,e):
        self.list_widget.setStyleSheet(f"background:{BG2};")
        for url in e.mimeData().urls():
            path=url.toLocalFile()
            if os.path.isdir(path): self._add_folder(path)
            elif is_audio(path) and path not in self.files:
                self.files.append(path); self._add_row(path)
        self._update_count(); e.acceptProposedAction()

    def contextMenuEvent(self, e):
        # Clic droit sur la colonne gauche → ajouter
        if self.list_widget.geometry().contains(e.pos()):
            from PyQt6.QtWidgets import QMenu
            m = QMenu(self)
            m.setStyleSheet(
                f"QMenu{{background:{PANEL2};color:{TEXT};border:1px solid {BORDER};padding:4px;}}"
                f"QMenu::item{{padding:8px 18px;font-size:11px;}}"
                f"QMenu::item:selected{{background:{PANEL};color:{TEXT};}}")
            m.addAction(T("Ajouter des fichiers…"), self._browse_files)
            m.addAction(T("Ajouter un dossier…"), self._browse_folder)
            m.exec(e.globalPos())
        else:
            super().contextMenuEvent(e)

    def _browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Choisir un dossier audio")
        if folder: self._add_folder(folder)

    def _add_folder(self,folder):
        for root,_,fnames in os.walk(folder):
            for f in sorted(fnames):
                p=os.path.join(root,f)
                if is_audio(p) and p not in self.files:
                    self.files.append(p); self._add_row(p)

    # ── Navigation clavier ────────────────────────────────────────────────────

    def _prev_file(self):
        if self.current_index>0 and self._check_dirty_before_nav():
            self._on_row_select(self.rows[self.current_index-1])

    def _next_file(self):
        if 0<=self.current_index<len(self.rows)-1 and self._check_dirty_before_nav():
            self._on_row_select(self.rows[self.current_index+1])

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        root=QWidget(); self.setCentralWidget(root)
        main=QVBoxLayout(root); main.setContentsMargins(0,0,0,0); main.setSpacing(0)

        # Barre titre
        bar=QFrame(); bar.setFixedHeight(52)
        bar.setStyleSheet(f"background:{BG};border-bottom:1px solid {BORDER};")
        bl=QHBoxLayout(bar); bl.setContentsMargins(16,0,16,0)
        # Layout barre : [lang_btn] [stretch] [logo] [stretch]
        # stretch gauche = stretch droit pour centrer le logo
        self._lang_combo = None  # sera créé dans la colonne gauche
        logo=QLabel("Tagr")
        logo.setStyleSheet(f"color:{TEXT};font-size:22px;font-weight:bold;letter-spacing:1px;")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        bl.addStretch(1)
        bl.addWidget(logo)
        bl.addStretch(1)

        self.album_btn = None
        main.addWidget(bar)

        body=QHBoxLayout(); body.setSpacing(0); body.setContentsMargins(0,0,0,0)
        main.addLayout(body,1)

        # ── Colonne gauche ──
        self.list_widget=QFrame()
        self.list_widget.setFixedWidth(290)
        self.list_widget.setStyleSheet(f"background:{BG2};")
        lv=QVBoxLayout(self.list_widget); lv.setContentsMargins(0,0,0,0); lv.setSpacing(0)

        # Header : filtre dropdown + bouton + rond
        hdr=QFrame(); hdr.setFixedHeight(44)
        hdr.setStyleSheet(f"background:{BG2};")
        hl=QHBoxLayout(hdr); hl.setContentsMargins(10,4,10,4); hl.setSpacing(8)

        # Dropdown TRI : A→Z / Artiste / Album / Titre
        self.filter_field=QComboBox()
        self.filter_field.addItems([T("A → Z"),T("Artiste"),T("Album"),T("Titre")])
        self.filter_field.setStyleSheet(
            f"QComboBox{{background:{FIELDBG};color:{TEXTM};border:1px solid {BORDER};"
            f"border-radius:6px;padding:4px 8px;font-size:10px;}}"
            f"QComboBox QAbstractItemView{{background:{PANEL2};color:{TEXT};border:1px solid {BORDER};}}"
            f"QComboBox::drop-down{{border:none;width:16px;}}")
        self.filter_field.currentIndexChanged.connect(self._apply_sort)

        # Champ filtre texte (caché — conservé pour _apply_filter)
        self.filter_input=QLineEdit()
        self.filter_input.hide()
        self.filter_input.textChanged.connect(self._apply_filter)

        # Sort combo caché conservé pour compatibilité
        self.sort_combo=QComboBox()
        self.sort_combo.hide()

        # count_lbl caché conservé pour la logique
        self.count_lbl=QLabel(""); self.count_lbl.hide()

        # Bouton + rond (style bouton i)
        add_round=QPushButton("+")
        add_round.setFixedSize(28,28)
        add_round.setStyleSheet(
            f"QPushButton{{background:{PANEL};color:{TEXTM};border:1px solid {BORDER};"
            f"border-radius:14px;font-size:16px;font-weight:bold;padding:0;}}"
            f"QPushButton:hover{{background:{ACCENT};color:#000;border-color:{ACCENT};}}")
        add_round.setCursor(Qt.CursorShape.PointingHandCursor)
        add_round.clicked.connect(self._browse_files)

        dl_round = QPushButton("↓")
        dl_round.setFixedSize(28, 28)
        dl_round.setToolTip(T("dl_tooltip"))
        dl_round.setStyleSheet(
            f"QPushButton{{background:{PANEL};color:{TEXTM};border:1px solid {BORDER};"
            f"border-radius:14px;font-size:14px;font-weight:bold;padding:0;}}"
            f"QPushButton:hover{{background:{ACCENT};color:#000;border-color:{ACCENT};}}")
        dl_round.setCursor(Qt.CursorShape.PointingHandCursor)
        dl_round.clicked.connect(self._download_from_url)

        hl.addWidget(self.filter_field, 1)
        hl.addWidget(dl_round)
        hl.addWidget(add_round)
        lv.addWidget(hdr)

        # Liste
        scroll=QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"QScrollArea{{background:{BG2};border:none;}}"
                             f"QScrollBar:vertical{{background:{BG2};width:4px;}}"
                             f"QScrollBar::handle:vertical{{background:{BORDER};border-radius:2px;}}"
                             f"QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{{height:0;}}")
        self.list_container=QWidget(); self.list_container.setStyleSheet(f"background:{BG2};")
        self.list_layout=QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(0,0,0,0); self.list_layout.setSpacing(1)
        self.list_layout.addStretch()
        scroll.setWidget(self.list_container); lv.addWidget(scroll,1)
        self._scroll_area = scroll
        # Clic sur zone vide → désélectionner
        self.list_container.mouseDoubleClickEvent = lambda e: self._browse_files()
        def _list_click(e):
            # Si clic sur fond (pas sur une row), désélectionner
            child = self.list_container.childAt(e.pos())
            if child is None or child == self.list_container:
                self._deselect_all()
        self.list_container.mousePressEvent = _list_click

        self.hint=QLabel(T("hint_drop"))
        self.hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hint.setStyleSheet(f"color:{TEXTD};font-size:11px;padding:40px 16px;background:{BG2};")
        self.hint.mouseDoubleClickEvent = lambda e: self._browse_files()
        self.list_layout.insertWidget(0,self.hint)
        # Double-clic sur la zone scrollable pour ajouter
        self.list_container.mouseDoubleClickEvent = lambda e: self._browse_files()

        # Barre langue en bas de colonne gauche
        lang_bar = QFrame(); lang_bar.setFixedHeight(40)
        lang_bar.setStyleSheet(f"background:{BG2};border-top:1px solid {BORDER};")
        lb = QHBoxLayout(lang_bar); lb.setContentsMargins(12,0,12,0); lb.setSpacing(8)
        globe = QLabel("🌐︎")
        globe.setStyleSheet(f"color:{ACCENT};font-size:14px;background:transparent;")
        from PyQt6.QtWidgets import QComboBox as _LC
        lang_combo = _LC()
        lang_combo.addItems(["Français", "English"])
        lang_combo.setCurrentIndex(0 if _LANG == "fr" else 1)
        lang_combo.setFixedHeight(24)
        lang_combo.setStyleSheet(
            f"QComboBox{{background:transparent;color:{TEXTM};border:none;"
            f"font-size:10px;padding:0 4px;}}"
            f"QComboBox::drop-down{{border:none;width:12px;}}"
            f"QComboBox QAbstractItemView{{background:{PANEL2};color:{TEXT};border:1px solid {BORDER};}}")
        lang_combo.currentIndexChanged.connect(self._switch_lang)
        self._lang_combo = lang_combo
        lb.addWidget(globe); lb.addWidget(lang_combo); lb.addStretch()
        lv.addWidget(lang_bar)
        body.addWidget(self.list_widget)

        # ── Colonne droite ──
        self.right=StackPanel(); body.addWidget(self.right,1)
        self._build_empty(); self._build_editor()
        self.right.show_empty()  # afficher l'état vide à l'ouverture

    def _build_empty(self):
        w=QWidget(); w.setStyleSheet(f"background:{BG};")
        v=QVBoxLayout(w); v.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_title = QLabel(T("empty_title"), styleSheet=f"color:{TEXTD};font-size:14px;")
        self._empty_hint = QLabel(T("empty_hint"), styleSheet=f"color:{TEXTD};font-size:10px;")
        v.addWidget(self._empty_title, alignment=Qt.AlignmentFlag.AlignCenter)
        v.addWidget(self._empty_hint, alignment=Qt.AlignmentFlag.AlignCenter)
        self.right.empty=w; self.right.addWidget(w)

    def _build_editor(self):
        scroll=QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"QScrollArea{{background:{BG};border:none;}}"
                             f"QScrollBar:vertical{{background:{BG};width:4px;}}"
                             f"QScrollBar::handle:vertical{{background:{BORDER};border-radius:2px;}}"
                             f"QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{{height:0;}}")
        w=QWidget(); w.setStyleSheet(f"background:{BG};")
        v=QVBoxLayout(w); v.setContentsMargins(32,28,32,24); v.setSpacing(0)
        scroll.setWidget(w)

        # Pochette + boutons
        top=QHBoxLayout(); top.setSpacing(20); top.setAlignment(Qt.AlignmentFlag.AlignTop)
        cc=QVBoxLayout(); cc.setSpacing(6); cc.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.cover_lbl=CoverLabel()
        self.cover_lbl.clicked.connect(self._browse_cover)
        self.cover_lbl.image_dropped.connect(self._on_image_dropped)
        sub=QLabel(T("Cliquer ou glisser une image")); self._cover_hint=sub
        sub.setStyleSheet(f"color:{TEXTD};font-size:9px;"); sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cover_info=QLabel("")
        self.cover_info.setStyleSheet(f"color:{TEXTD};font-size:8px;"); self.cover_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Bouton recadrer
        crop_btn=QPushButton(T("Recadrer")); self._crop_btn=crop_btn
        crop_btn.setStyleSheet(
            f"QPushButton{{background:{PANEL};color:{TEXTM};border:1px solid {BORDER};"
            f"border-radius:4px;font-size:9px;padding:4px 10px;}}"
            f"QPushButton:hover{{background:{PANEL2};color:{TEXT};}}")
        crop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        crop_btn.clicked.connect(self._crop_current_cover)
        cc.addWidget(self.cover_lbl); cc.addWidget(sub); cc.addWidget(self.cover_info)
        cc.addWidget(crop_btn)
        top.addLayout(cc)

        bc=QVBoxLayout(); bc.setSpacing(6); bc.setAlignment(Qt.AlignmentFlag.AlignTop)

        def section(txt):
            lbl=QLabel(txt)
            lbl.setStyleSheet(f"color:{TEXTD};font-size:8px;font-weight:bold;margin-top:7px;background:transparent;")
            bc.addWidget(lbl)
            return lbl

        def abtn(txt, fn, role="secondary"):
            b=QPushButton(txt)
            if role=="primary":
                b.setStyleSheet(f"QPushButton{{background:{ACCENT};color:#000;border:none;padding:10px 14px;"
                                f"font-size:11px;font-weight:bold;text-align:left;border-radius:4px;}}"
                                f"QPushButton:hover{{background:{ACCENT2};}}")
            else:
                b.setStyleSheet(f"QPushButton{{background:{PANEL};color:{TEXTM};border:1px solid transparent;"
                                f"padding:9px 14px;font-size:11px;text-align:left;border-radius:4px;}}"
                                f"QPushButton:hover{{background:{PANEL2};color:{TEXT};border:1px solid {BORDER};}}")
            b.setCursor(Qt.CursorShape.PointingHandCursor); b.clicked.connect(fn); bc.addWidget(b); return b

        self._lbl_section_pochette = section(T("POCHETTE"))
        self._btn_search_cover = abtn(T("Recherche de pochette"), self._search_cover_smart)
        self._btn_export_cover = abtn(T("Exporter la pochette"), self._export_cover)

        self._lbl_section_lecture = section(T("LECTURE"))
        self.play_btn=abtn(T("Ecouter"), self._toggle_play)
        self._btn_listen = self.play_btn

        self._lbl_section_outils = section(T("OUTILS AUDIO"))
        # Menu déroulant pour les outils audio
        self._audio_tools_btn=QPushButton(T("Outils audio…"))
        self._btn_audio_tools = self._audio_tools_btn
        self._audio_tools_btn.setStyleSheet(
            f"QPushButton{{background:{PANEL};color:{TEXTM};border:1px solid transparent;"
            f"padding:9px 14px;font-size:11px;text-align:left;border-radius:4px;}}"
            f"QPushButton:hover{{background:{PANEL2};color:{TEXT};border:1px solid {BORDER};}}")
        self._audio_tools_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._audio_tools_btn.clicked.connect(self._show_audio_tools_menu)
        bc.addWidget(self._audio_tools_btn)



        top.addLayout(bc,1)
        v.addLayout(top)

        # Qualité audio
        v.addSpacing(16)
        self.quality_frame = QFrame()
        self.quality_frame.setStyleSheet(f"background:{PANEL};border-radius:6px;")
        ql = QHBoxLayout(self.quality_frame)
        ql.setContentsMargins(14,10,14,10); ql.setSpacing(20)

        self.qlbl_badge  = QLabel(); self.qlbl_badge.setStyleSheet(f"color:{TEXT};font-size:11px;font-weight:bold;background:transparent;")
        self.qlbl_detail = QLabel(); self.qlbl_detail.setStyleSheet(f"color:{TEXTM};font-size:10px;background:transparent;")
        self.qlbl_grade  = QLabel(); self.qlbl_grade.setStyleSheet(f"font-size:10px;font-weight:bold;background:transparent;")
        self.qlbl_size   = QLabel(); self.qlbl_size.setStyleSheet(f"color:{TEXTD};font-size:9px;background:transparent;")

        ql.addWidget(self.qlbl_badge)
        ql.addWidget(self.qlbl_detail, 1)
        ql.addWidget(self.qlbl_grade)
        ql.addWidget(self.qlbl_size)
        v.addWidget(self.quality_frame)

        self.spotify_status_lbl = QLabel(T("Statut Spotify"))
        self.spotify_status_lbl.setStyleSheet(f"background:{PANEL};color:{TEXTD};border:1px solid {BORDER};"
                                              f"border-radius:5px;padding:8px 12px;font-size:10px;margin-top:8px;")
        v.addWidget(self.spotify_status_lbl)

        # Champs
        def field(label_key, attr, label_attr):
            lbl=QLabel(T(label_key)); lbl.setStyleSheet(f"color:{TEXTD};font-size:9px;margin-top:12px;")
            e=QLineEdit()
            e.setStyleSheet(f"background:{FIELDBG};color:{TEXT};border:1px solid {BORDER};"
                            f"border-radius:4px;padding:9px 10px;font-size:13px;"
                            f"selection-background-color:{ACCENT};selection-color:#000;")
            e.textChanged.connect(self._mark_dirty); setattr(self,attr,e)
            setattr(self,label_attr,lbl)
            v.addWidget(lbl); v.addWidget(e)

        v.addSpacing(8)
        field("TITRE",   "field_title",  "_lbl_titre")
        field("ARTISTE", "field_artist", "_lbl_artiste")
        field("ALBUM",   "field_album",  "_lbl_album")

        # Champs cachés pour compatibilité (non affichés mais utilisés en lecture/écriture)
        for attr in ["field_track","field_year","field_genre","field_bpm"]:
            e = QLineEdit(); e.hide()
            e.textChanged.connect(self._mark_dirty); setattr(self, attr, e)

        # Bouton sauvegarder pleine largeur
        bot_wrap=QVBoxLayout(); bot_wrap.setContentsMargins(0,20,0,0)
        save=QPushButton(T("Sauvegarder")); self._save_btn=save
        save.setStyleSheet(f"QPushButton{{background:{ACCENT};color:#000;font-weight:bold;font-size:12px;"
                           f"border:none;padding:12px;border-radius:5px;}}"
                           f"QPushButton:hover{{background:{ACCENT2};}}")
        save.setCursor(Qt.CursorShape.PointingHandCursor)
        save.clicked.connect(self._save_current)
        bot_wrap.addWidget(save)
        v.addLayout(bot_wrap)

        self.status_lbl=QLabel("")
        self.status_lbl.setStyleSheet(f"color:{ACCENT};font-size:10px;margin-top:6px;")
        v.addWidget(self.status_lbl); v.addStretch()

        self.right.editor=scroll; self.right.addWidget(scroll)

    # ── Fichiers ──────────────────────────────────────────────────────────────

    def _browse_files(self):
        last=self._cfg.get("last_folder","")
        paths,_=QFileDialog.getOpenFileNames(self,"Choisir des fichiers audio",last,
            "Audio (*.mp3 *.flac *.m4a *.aac);;Tous (*)")
        if paths:
            self._cfg["last_folder"]=os.path.dirname(paths[0]); save_config(self._cfg)
        for p in paths:
            if p not in self.files: self.files.append(p); self._add_row(p)
        self._update_count()

    def _add_row(self,path):
        self.hint.hide()
        row=FileRow(path)
        row.selected_signal.connect(self._on_row_select)
        row.delete_signal.connect(self._on_delete_row)
        self.list_layout.insertWidget(self.list_layout.count()-1,row)
        self.rows.append(row)
        self._apply_filter()
        self._cfg["recent_files"]=[r.path for r in self.rows]; save_config(self._cfg)
        w=TagLoader(path); w.done.connect(self._on_tags_loaded); w.start(); self._workers.append(w)

    def _on_tags_loaded(self,path,tags):
        self.tags_cache[path]=tags
        if tags.get("_read_error"):
            self._flash(f"⚠️ Fichier illisible : {os.path.basename(path)}", err=True)
        for row in self.rows:
            if row.path==path: row.set_display(tags["title"],tags["artist"],tags["cover"]); break

    def _update_count(self):
        n=len(self.files)
        self.count_lbl.setText(f"{n} fichier{'s' if n>1 else ''}" if n else "Aucun fichier")

    # ── Filtre & tri ──────────────────────────────────────────────────────────


    def _apply_filter(self):
        txt = self.filter_input.text().lower().strip()
        field_idx = self.filter_field.currentIndex() if hasattr(self, "filter_field") else 0
        for row in self.rows:
            if not txt:
                row.setVisible(True); continue
            tags = self.tags_cache.get(row.path, {})
            if field_idx == 1:   # Artiste
                match = txt in tags.get("artist","").lower()
            elif field_idx == 2: # Album
                match = txt in tags.get("album","").lower()
            elif field_idx == 3: # Titre
                match = txt in tags.get("title","").lower()
            else:                # Tout
                match = (txt in os.path.basename(row.path).lower() or
                         txt in tags.get("title","").lower() or
                         txt in tags.get("artist","").lower() or
                         txt in tags.get("album","").lower())
            row.setVisible(match)

    def _apply_sort(self, _=None):
        idx = self.filter_field.currentIndex() if hasattr(self, "filter_field") else 0
        if idx == 1:   # Artiste
            key = lambda r: self.tags_cache.get(r.path,{}).get("artist","").lower()
        elif idx == 2: # Album
            key = lambda r: self.tags_cache.get(r.path,{}).get("album","").lower()
        elif idx == 3: # Titre
            key = lambda r: self.tags_cache.get(r.path,{}).get("title","").lower()
        else:          # A→Z (nom de fichier)
            key = lambda r: os.path.basename(r.path).lower()
        sorted_rows = sorted(self.rows, key=key)
        for r in sorted_rows:
            self.list_layout.removeWidget(r)
            self.list_layout.insertWidget(self.list_layout.count()-1, r)

    # ── Sélection ─────────────────────────────────────────────────────────────

    def _clear_row_selection(self):
        for r in list(self.selected_rows):
            try:
                r.set_selected(False)
            except Exception:
                pass
        self.selected_rows.clear()

    def _set_selected_rows(self, rows):
        rows = {r for r in rows if r in self.rows}
        for r in self.rows:
            r.set_selected(r in rows)
        self.selected_rows = rows

    def _focus_row_editor(self, row):
        self._stop_play()
        idx=self.rows.index(row); self.current_index=idx
        # Auto-scroll vers le fichier sélectionné
        # Scroll vertical uniquement — ensureWidgetVisible peut décaler horizontalement
        def _scroll_to_row():
            try:
                sb = self._scroll_area.verticalScrollBar()
                row_y = row.mapTo(self._scroll_area.widget(), row.rect().topLeft()).y()
                visible_h = self._scroll_area.viewport().height()
                cur = sb.value()
                if row_y < cur:
                    sb.setValue(max(0, row_y - 8))
                elif row_y + row.height() > cur + visible_h:
                    sb.setValue(row_y + row.height() - visible_h + 8)
            except Exception: pass
        QTimer.singleShot(50, _scroll_to_row)
        path=self.files[idx]
        tags=self.tags_cache.get(path) or read_tags(path)
        self.tags_cache[path]=tags
        for f,k in[(self.field_title,"title"),(self.field_artist,"artist"),
                   (self.field_album,"album"),(self.field_year,"year"),
                   (self.field_genre,"genre"),(self.field_bpm,"bpm"),(self.field_track,"track")]:
            f.blockSignals(True); f.setText(tags.get(k,"")); f.blockSignals(False)
        self.current_cover=tags["cover"]
        if tags["cover"]:
            self.cover_lbl.set_image(tags["cover"])
            self._update_cover_info(tags["cover"])
        else:
            self.cover_lbl._reset()
            try: self.cover_info.setText("")
            except Exception: pass
        self.right.show_editor(); self.status_lbl.setText("")
        self.play_btn.setText(T("Ecouter"))
        # Qualité audio
        self._update_quality(path)
        self._update_spotify_status()

    def _on_row_select(self,row,event=None):
        modifiers = event.modifiers() if event is not None else Qt.KeyboardModifier.NoModifier
        idx = self.rows.index(row)
        focus_row = row
        multi_key = bool(modifiers & (Qt.KeyboardModifier.MetaModifier | Qt.KeyboardModifier.ControlModifier))
        range_key = bool(modifiers & Qt.KeyboardModifier.ShiftModifier)

        if range_key and self.rows:
            anchor = self._selection_anchor
            if anchor not in self.rows:
                anchor = self.rows[self.current_index] if self.current_index >= 0 else row
            a = self.rows.index(anchor)
            lo, hi = sorted((a, idx))
            self._set_selected_rows(self.rows[lo:hi + 1])
        elif multi_key:
            rows = set(self.selected_rows)
            if row in rows and len(rows) > 1:
                rows.remove(row)
                focus_row = sorted(rows, key=lambda r: self.rows.index(r))[0]
            else:
                rows.add(row)
            self._set_selected_rows(rows)
            self._selection_anchor = row
        else:
            self._set_selected_rows([row])
            self._selection_anchor = row

        self._focus_row_editor(focus_row)

    def _update_quality(self, path):
        q = read_audio_quality(path)
        ext = path.lower().rsplit(".", 1)[-1].upper()
        sr  = q.get("sample_rate")
        br  = q.get("bitrate")
        bits= q.get("bits")
        dur = q.get("duration")
        sz  = q.get("size")

        # Badge format
        self.qlbl_badge.setText(ext)

        # Détail technique
        parts = []
        if br:   parts.append(f"{br} kbps")
        if sr:   parts.append(f"{sr/1000:.1f} kHz")
        if bits: parts.append(f"{bits}-bit")
        if dur:  m,s=divmod(int(dur),60); parts.append(f"{m}:{s:02d}")
        self.qlbl_detail.setText("  ·  ".join(parts))

        # Grade
        label, color = quality_label(path, q)
        self.qlbl_grade.setText(label)
        self.qlbl_grade.setStyleSheet(f"font-size:10px;font-weight:bold;color:{color};background:transparent;")

        # Taille fichier
        if sz:
            if sz > 1_000_000: self.qlbl_size.setText(f"{sz/1_000_000:.1f} Mo")
            else: self.qlbl_size.setText(f"{sz/1000:.0f} Ko")

    def _current_editor_tags(self):
        return {
            "title": self.field_title.text().strip(),
            "artist": self.field_artist.text().strip(),
            "album": self.field_album.text().strip(),
            "year": self.field_year.text().strip(),
            "genre": self.field_genre.text().strip(),
            "bpm": self.field_bpm.text().strip(),
            "track": self.field_track.text().strip(),
            "cover": self.current_cover,
        }

    def _update_spotify_status(self):
        if self.current_index < 0 or not hasattr(self, "spotify_status_lbl"):
            return
        path = self.files[self.current_index]
        issues = self._spotify_issues(self._current_editor_tags(), path)
        if issues:
            self.spotify_status_lbl.setText(T("À vérifier Spotify : ") + ", ".join(issues))
            self.spotify_status_lbl.setStyleSheet(f"background:{PANEL};color:{WARN};border:1px solid {BORDER};"
                                                  f"border-radius:5px;padding:8px 12px;font-size:10px;margin-top:8px;")
        else:
            self.spotify_status_lbl.setText(T("Prêt Spotify"))
            self.spotify_status_lbl.setStyleSheet(f"background:{SELBG};color:{ACCENT};border:1px solid {ACCENT};"
                                                  f"border-radius:5px;padding:8px 12px;font-size:10px;font-weight:bold;margin-top:8px;")

    def _mark_dirty(self):
        if self.current_index>=0:
            self.rows[self.current_index].set_dirty(True)
            self._update_spotify_status()

    # ── Supprimer ─────────────────────────────────────────────────────────────

    def _on_delete_row(self,row):
        rows = list(self.selected_rows) if row in self.selected_rows and len(self.selected_rows) > 1 else [row]
        self._delete_rows(rows)

    def _delete_rows(self, rows):
        rows = [r for r in dict.fromkeys(rows) if r in self.rows]
        if not rows:
            return
        idxs = sorted(self.rows.index(r) for r in rows)
        first_idx = idxs[0]
        current_path = self.files[self.current_index] if self.current_index >= 0 else None
        deleted_current = current_path in {r.path for r in rows}

        for idx in reversed(idxs):
            row = self.rows.pop(idx)
            self.files.pop(idx)
            self.list_layout.removeWidget(row)
            row.deleteLater()

        self.selected_rows.clear()
        self.current_index = -1

        if self.rows:
            if current_path and not deleted_current:
                for row in self.rows:
                    if row.path == current_path:
                        QTimer.singleShot(0, lambda r=row: self._on_row_select(r))
                        break
            else:
                next_idx = min(first_idx, len(self.rows) - 1)
                QTimer.singleShot(0, lambda r=self.rows[next_idx]: self._on_row_select(r))
        else:
            self.right.show_empty()
        if not self.files:
            self.hint.show()
        self._cfg["recent_files"]=[r.path for r in self.rows]; save_config(self._cfg)
        self._update_count()

    def _delete_selected(self):
        rows = list(self.selected_rows)
        if not rows and self.current_index>=0:
            rows = [self.rows[self.current_index]]
        self._delete_rows(rows)

    # ── Pochette ──────────────────────────────────────────────────────────────

    def _browse_cover(self):
        path,_=QFileDialog.getOpenFileName(self,"Choisir une image",
            filter="Images (*.jpg *.jpeg *.png *.webp *.bmp);;Tous (*)")
        if path:
            try:
                img=PILImage.open(path).convert("RGB")
                self._open_crop(img)
            except Exception as e: self._flash(f"Erreur : {e}",err=True)

    def _on_image_dropped(self,img):
        self._open_crop(img)

    def _open_crop(self,img):
        d=CropDialog(self,img); d.cropped.connect(self._apply_cover); d.exec()

    def _apply_cover(self,img):
        self.current_cover=img; self.cover_lbl.set_image(img)
        self._mark_dirty(); self._flash("Pochette appliquée")

    def _export_cover(self):
        if not self.current_cover:
            self._flash("Aucune pochette à exporter",err=True); return
        path,_=QFileDialog.getSaveFileName(self,"Exporter la pochette",
            os.path.expanduser("~/Desktop/pochette.jpg"),
            "JPEG (*.jpg);;PNG (*.png)")
        if path:
            try:
                self.current_cover.save(path,quality=95)
                self._flash("Pochette exportée")
            except Exception as e: self._flash(f"Erreur : {e}",err=True)

    def _search_cover(self):
        q=f"{self.field_artist.text()} {self.field_title.text()}".strip()
        if not q: self._flash("Renseigne titre ou artiste d'abord",err=True); return
        self._flash("Recherche en cours…")
        w=Searcher(q); w.done.connect(self._on_search_done); w.start(); self._workers.append(w)

    def _on_search_done(self,results):
        if not results: self._flash("Aucun résultat",err=True); return
        d=CoverPicker(self,results); d.chosen.connect(self._on_cover_chosen); d.exec()

    def _on_cover_chosen(self,img,meta):
        self._open_crop(img)

    def _auto_identify(self):
        if self.current_index<0: return
        t=self.field_title.text().strip(); a=self.field_artist.text().strip()
        q=(f"{a} {t}".strip() or
           os.path.splitext(os.path.basename(self.files[self.current_index]))[0])
        self._flash("Identification en cours…")
        w=Searcher(q); w.done.connect(self._on_identify_done); w.start(); self._workers.append(w)

    def _on_identify_done(self,results):
        if not results: self._flash("Aucun résultat",err=True); return
        r=results[0]
        for f,k in[(self.field_title,"title"),(self.field_artist,"artist"),(self.field_album,"album")]:
            f.blockSignals(True); f.setText(r.get(k,"")); f.blockSignals(False)
        self._mark_dirty(); self._flash(f"{r['artist']} — {r['title']}")
        if r.get("artwork"):
            f=ImageFetcher(r["artwork"],r)
            f.done.connect(lambda img,m:(setattr(self,'current_cover',img),self.cover_lbl.set_image(img)))
            f.start(); self._workers.append(f)

    # ── Lecture ───────────────────────────────────────────────────────────────

    def _toggle_play(self):
        if self._play_proc and self._play_proc.poll() is None: self._stop_play()
        else: self._start_play()

    def _start_play(self):
        if self.current_index<0: return
        self._play_proc=subprocess.Popen(["afplay",self.files[self.current_index]])
        self.play_btn.setText(T("Stop"))
        def watch():
            self._play_proc.wait()
            QTimer.singleShot(0,lambda:self.play_btn.setText(T("Ecouter")))
        threading.Thread(target=watch,daemon=True).start()

    def _stop_play(self):
        if self._play_proc and self._play_proc.poll() is None: self._play_proc.terminate()
        self._play_proc=None
        try: self.play_btn.setText(T("Ecouter"))
        except Exception: pass

    # ── Sauvegarder ───────────────────────────────────────────────────────────

    def _save_current(self):
        if self.current_index < 0: return True
        path  = self.files[self.current_index]
        title = self.field_title.text().strip()
        artist= self.field_artist.text().strip()
        album = self.field_album.text().strip()
        year  = self.field_year.text().strip()
        genre = self.field_genre.text().strip()
        bpm   = self.field_bpm.text().strip()
        track = self.field_track.text().strip()

        # Dialog : écraser ou créer nouveau fichier
        from PyQt6.QtWidgets import QMessageBox
        msg = QMessageBox(self)
        msg.setWindowTitle(T("Sauvegarder"))
        msg.setText(T("Comment sauvegarder les modifications ?"))
        msg.setInformativeText(os.path.basename(path))
        msg.setStyleSheet(f"background:{BG2};color:{TEXT};")
        overwrite_btn = msg.addButton(T("Écraser le fichier"), QMessageBox.ButtonRole.AcceptRole)
        new_btn       = msg.addButton(T("Créer un nouveau fichier"), QMessageBox.ButtonRole.ActionRole)
        cancel_btn    = msg.addButton(T("Annuler"), QMessageBox.ButtonRole.RejectRole)
        msg.exec()
        clicked = msg.clickedButton()
        if clicked == cancel_btn: return False

        ext = os.path.splitext(path)[1]
        folder = os.path.dirname(path)

        if clicked == new_btn:
            # Nom basé sur Artiste - Titre
            new_name = safe_fn(f"{artist} - {title}" if artist and title
                               else (title or artist or os.path.splitext(os.path.basename(path))[0]))
            out = os.path.join(folder, new_name + ext)
            # Éviter les conflits de nom
            i = 1
            while os.path.exists(out) and out != path:
                out = os.path.join(folder, f"{new_name}_{i}{ext}"); i += 1
            try:
                import shutil
                shutil.copy2(path, out)
                target = out
            except Exception as e:
                self._flash(f"Erreur copie : {e}", err=True); return False
        else:
            # Écraser : renommer aussi le fichier en Artiste - Titre si les tags changent
            if artist or title:
                new_name = safe_fn(f"{artist} - {title}" if artist and title
                                   else (title or artist or os.path.splitext(os.path.basename(path))[0]))
                new_path = os.path.join(folder, new_name + ext)
                if new_path != path and not os.path.exists(new_path):
                    try:
                        os.rename(path, new_path)
                        self.files[self.current_index] = new_path
                        self.rows[self.current_index].path = new_path
                        self.tags_cache.pop(path, None)
                        path = new_path
                    except Exception: pass
            target = path

        res = write_tags(target, title, artist, album, year, genre, bpm, track, self.current_cover)
        if res is True:
            self.tags_cache[target] = {"title":title,"artist":artist,"album":album,
                                       "year":year,"genre":genre,"bpm":bpm,"track":track,
                                       "cover":self.current_cover}
            self.rows[self.current_index].set_display(title, artist, self.current_cover)
            self.rows[self.current_index].set_dirty(False)
            # Mettre à jour le Finder
            try: subprocess.run(["mdimport", target], capture_output=True, timeout=10)
            except Exception: pass
            if clicked == new_btn:
                self._flash(f"Créé : {os.path.basename(target)}")
            else:
                self._flash(f"Sauvegardé : {os.path.basename(target)}")
            return True
        else:
            self._flash(f"Erreur : {res}", err=True)
            return False

    def _save_and_next(self):
        if self.current_index < 0:
            return
        if not self._save_current():
            return
        if self.current_index < len(self.rows) - 1:
            self._on_row_select(self.rows[self.current_index + 1])
        else:
            self._flash("Dernier fichier sauvegardé")

    # ── Renommer ──────────────────────────────────────────────────────────────

    def _rename_file(self):
        if self.current_index<0: return
        path=self.files[self.current_index]
        title=self.field_title.text().strip(); artist=self.field_artist.text().strip()
        if not title: self._flash("Renseigne un titre d'abord",err=True); return
        ext=os.path.splitext(path)[1]
        new_name=safe_fn(f"{artist} - {title}" if artist else title)+ext
        new_path=os.path.join(os.path.dirname(path),new_name)
        if new_path==path: self._flash("Déjà ce nom"); return
        if os.path.exists(new_path): self._flash("Ce nom existe déjà",err=True); return
        try:
            ok, backup = backup_audio_file(path, "rename")
            if not ok:
                self._flash(f"Sauvegarde impossible : {backup}", err=True); return
            os.rename(path,new_path)
            self.files[self.current_index]=new_path
            self.tags_cache[new_path]=self.tags_cache.pop(path,{})
            self.rows[self.current_index].path=new_path
            try: subprocess.run(["mdimport", new_path], capture_output=True, timeout=10)
            except Exception: pass
            self._flash(f"Renommé : {new_name}")
        except Exception as e: self._flash(f"Erreur : {e}",err=True)


    def _open_trim(self):
        if self.current_index < 0: return
        path = self.files[self.current_index]
        duration = None
        try:
            ext = path.lower().rsplit(".", 1)[-1]
            if ext == "mp3":
                from mutagen.mp3 import MP3; duration = MP3(path).info.length
            elif ext == "flac":
                duration = FLAC(path).info.length
            elif ext in ("m4a","aac"):
                duration = MP4(path).info.length
        except: pass
        if not duration:
            self._flash(T("duration_error"), err=True); return
        TrimDialog(self, path, duration).exec()

    def keyPressEvent(self, event):
        from PyQt6.QtWidgets import QLineEdit
        focused = QApplication.focusWidget()
        if event.key() == Qt.Key.Key_Space and not isinstance(focused, QLineEdit):
            self._toggle_play()
            event.accept()
        elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if not isinstance(focused, QLineEdit):
                self._save_current()
                event.accept()
            else:
                super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        if self._play_proc and self._play_proc.poll() is None:
            self._play_proc.terminate()
        self._cfg["recent_files"] = [r.path for r in self.rows]
        self._cfg["geometry"] = self.saveGeometry().toHex().data().decode()
        self._cfg["is_dark"] = getattr(self, "_is_dark", True)
        save_config(self._cfg)
        dirty = [r for r in self.rows if r._dirty]
        if dirty:
            from PyQt6.QtWidgets import QMessageBox
            msg = QMessageBox(self)
            msg.setWindowTitle(T("Modifications non sauvegardées"))
            msg.setText(T("n_unsaved").replace("{n}", str(len(dirty))))
            msg.setInformativeText(T("save_before_quit"))
            msg.setStyleSheet(f"background:{BG2};color:{TEXT};")
            save_btn   = msg.addButton(T("Sauvegarder et quitter"), QMessageBox.ButtonRole.AcceptRole)
            nosave_btn = msg.addButton(T("Quitter sans sauvegarder"), QMessageBox.ButtonRole.DestructiveRole)
            cancel_btn = msg.addButton(T("Annuler"), QMessageBox.ButtonRole.RejectRole)
            msg.exec()
            clicked = msg.clickedButton()
            if clicked == cancel_btn:
                event.ignore(); return
            elif clicked == save_btn:
                if not self._save_all():
                    event.ignore(); return
        event.accept()

    def _reveal_finder(self):
        if self.current_index>=0:
            try: subprocess.run(["open", "-R", self.files[self.current_index]], timeout=5)
            except Exception: pass


    def _undo_current(self):
        if self.current_index < 0: return
        path = self.files[self.current_index]
        tags = read_tags(path)
        self.tags_cache[path] = tags
        for f, k in [(self.field_title,"title"),(self.field_artist,"artist"),
                     (self.field_album,"album"),(self.field_year,"year"),
                     (self.field_genre,"genre"),(self.field_bpm,"bpm"),(self.field_track,"track")]:
            f.blockSignals(True); f.setText(tags.get(k,"")); f.blockSignals(False)
        self.current_cover = tags["cover"]
        if tags["cover"]: self.cover_lbl.set_image(tags["cover"])
        else: self.cover_lbl._reset()
        self.rows[self.current_index].set_dirty(False)
        self._flash("Modifications annulées")

    def _save_all(self):
        if self.current_index >= 0 and not self._save_current():
            return False
        saved = 0
        for i, row in enumerate(self.rows):
            if row._dirty and i != self.current_index:
                path = self.files[i]
                tags = self.tags_cache.get(path, {})
                ok, backup = backup_audio_file(path, "tags")
                if not ok:
                    self._flash(f"Sauvegarde impossible : {backup}", err=True); return False
                res = write_tags(path,
                    tags.get("title",""), tags.get("artist",""),
                    tags.get("album",""), tags.get("year",""),
                    tags.get("genre",""), tags.get("bpm",""),
                    tags.get("track",""), tags.get("cover"))
                if res is True:
                    row.set_dirty(False)
                    subprocess.run(["mdimport", path], capture_output=True)
                    saved += 1
                else:
                    self._flash(f"Erreur : {res}", err=True); return False
        self._flash(f"Tout sauvegardé ({saved} fichier(s))")
        return True

    def _row_tags(self, row):
        tags = self.tags_cache.get(row.path) or read_tags(row.path)
        self.tags_cache[row.path] = tags
        return tags

    def _spotify_issues(self, tags, path):
        issues = []
        ext = os.path.splitext(path)[1].lower()
        if ext != ".mp3":
            issues.append(T("not_mp3"))
        if not clean_text(tags.get("title")):
            issues.append(T("missing_title"))
        if not clean_text(tags.get("artist")):
            issues.append(T("missing_artist"))
        if not tags.get("cover"):
            issues.append(T("missing_cover"))
        return issues

    def _spotify_audit(self):
        ready = []
        review = []
        duplicates = {}
        for row in self.rows:
            tags = self._row_tags(row)
            key = (clean_text(tags.get("title")).lower(),
                   clean_text(tags.get("artist")).lower())
            if key[0] and key[1]:
                duplicates.setdefault(key, []).append(row.path)
            issues = self._spotify_issues(tags, row.path)
            if issues:
                review.append((row, tags, issues))
            else:
                ready.append((row, tags))
        duplicate_paths = {p for paths in duplicates.values() if len(paths) > 1 for p in paths}
        for row, tags in ready[:]:
            if row.path in duplicate_paths:
                ready.remove((row, tags))
                review.append((row, tags, [T("possible_duplicate")]))
        for i, (row, tags, issues) in enumerate(review):
            if row.path in duplicate_paths and T("possible_duplicate") not in issues:
                review[i] = (row, tags, issues + [T("possible_duplicate")])
        return ready, review

    def _select_path(self, path):
        for row in self.rows:
            if row.path == path:
                self._on_row_select(row)
                return

    def _next_spotify_issue(self):
        if not self.rows:
            return None
        start = self.current_index + 1 if self.current_index >= 0 else 0
        ordered = self.rows[start:] + self.rows[:start]
        for row in ordered:
            if self._spotify_issues(self._row_tags(row), row.path):
                return row
        return None

    def _save_and_next_issue(self):
        if self.current_index >= 0 and not self._save_current():
            return
        row = self._next_spotify_issue()
        if row:
            self._on_row_select(row)
        else:
            self._flash(T("Aucun problème Spotify restant"))

    def _show_spotify_control(self):
        if not self.rows:
            self._flash("Aucun fichier dans la liste", err=True); return
        from PyQt6.QtWidgets import QDialog
        ready, review = self._spotify_audit()
        d = QDialog(self)
        d.setWindowTitle(T("Contrôle Spotify"))
        d.setStyleSheet(f"background:{BG2};color:{TEXT};")
        d.setMinimumSize(620, 460)
        v = QVBoxLayout(d); v.setContentsMargins(20,18,20,18); v.setSpacing(10)
        title = QLabel(T("spotify_ready_review").replace("{ready}", str(len(ready))).replace("{review}", str(len(review))))
        title.setStyleSheet(f"color:{TEXT};font-size:15px;font-weight:bold;")
        v.addWidget(title)
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"QScrollArea{{background:{BG2};border:1px solid {BORDER};}}")
        cont = QWidget(); cont.setStyleSheet(f"background:{BG2};")
        rows = QVBoxLayout(cont); rows.setContentsMargins(0,0,0,0); rows.setSpacing(1)
        entries = [(row, "OK", spotify_filename(tags, row.path), ACCENT)
                   for row, tags in ready]
        entries += [(row, T("spotify_check"), f"{os.path.basename(row.path)} · {', '.join(issues)}", WARN)
                    for row, tags, issues in review]
        for row, status, detail, color in entries:
            btn = QPushButton(f"{status}  {detail}")
            btn.setStyleSheet(f"background:{PANEL};color:{color};border:none;"
                              f"text-align:left;padding:8px 10px;font-size:10px;")
            btn.clicked.connect(lambda _, p=row.path, dia=d: (dia.accept(), self._select_path(p)))
            rows.addWidget(btn)
        rows.addStretch()
        scroll.setWidget(cont); v.addWidget(scroll, 1)
        brow = QHBoxLayout()
        next_btn = QPushButton(T("Aller au prochain problème"))
        next_btn.setStyleSheet(f"background:{ACCENT};color:#000;font-weight:bold;border:none;padding:8px 14px;border-radius:4px;")
        next_btn.clicked.connect(lambda: (d.accept(), self._select_path(self._next_spotify_issue().path) if self._next_spotify_issue() else self._flash(T("Aucun problème Spotify restant"))))
        close = QPushButton(T("Fermer"))
        close.setStyleSheet(f"background:{PANEL};color:{TEXTM};border:none;padding:8px 14px;border-radius:4px;")
        close.clicked.connect(d.accept)
        brow.addStretch(); brow.addWidget(next_btn); brow.addWidget(close)
        v.addLayout(brow)
        d.exec()

    def _batch_apply_fields(self):
        if self.current_index < 0:
            self._flash("Sélectionne un fichier modèle", err=True); return
        from PyQt6.QtWidgets import QDialog, QCheckBox
        source = {
            "artist": self.field_artist.text().strip(),
            "album": self.field_album.text().strip(),
            "genre": self.field_genre.text().strip(),
            "year": self.field_year.text().strip(),
        }
        d = QDialog(self)
        d.setWindowTitle(T("Champs en lot"))
        d.setStyleSheet(f"background:{BG2};color:{TEXT};")
        d.setMinimumWidth(360)
        v = QVBoxLayout(d); v.setContentsMargins(20,18,20,18); v.setSpacing(10)
        v.addWidget(QLabel(T("apply_from_selected"), styleSheet=f"color:{TEXT};font-size:12px;"))
        checks = []
        for key, label in [("artist","Artiste"),("album","Album"),("genre","Genre"),("year",T("Année"))]:
            chk = QCheckBox(f"{label} : {source[key] or '(vide)'}")
            chk.setEnabled(bool(source[key]))
            chk.setStyleSheet(f"color:{TEXTM};font-size:10px;")
            v.addWidget(chk); checks.append((key, chk))
        number_chk = QCheckBox(T("num_tracks_hint"))
        number_chk.setStyleSheet(f"color:{TEXTM};font-size:10px;")
        v.addWidget(number_chk)
        brow = QHBoxLayout()
        ok = QPushButton(T("Appliquer"))
        ok.setStyleSheet(f"background:{ACCENT};color:#000;font-weight:bold;border:none;padding:8px 16px;border-radius:4px;")
        cancel = QPushButton(T("Annuler"))
        cancel.setStyleSheet(f"background:{PANEL};color:{TEXTM};border:none;padding:8px 14px;border-radius:4px;")
        ok.clicked.connect(d.accept); cancel.clicked.connect(d.reject)
        brow.addStretch(); brow.addWidget(cancel); brow.addWidget(ok)
        v.addLayout(brow)
        if d.exec() != QDialog.DialogCode.Accepted:
            return
        changed = 0
        total = len(self.rows)
        for idx, row in enumerate(self.rows, start=1):
            tags = self._row_tags(row).copy()
            touched = False
            for key, chk in checks:
                if chk.isChecked():
                    tags[key] = source[key]
                    touched = True
            if number_chk.isChecked():
                tags["track"] = f"{idx}/{total}"
                touched = True
            if not touched:
                continue
            ok, backup = backup_audio_file(row.path, "batch_fields")
            if not ok:
                continue
            res = write_tags(row.path, tags.get("title",""), tags.get("artist",""),
                             tags.get("album",""), tags.get("year",""),
                             tags.get("genre",""), tags.get("bpm",""),
                             tags.get("track",""), tags.get("cover"))
            if res is True:
                self.tags_cache[row.path] = tags
                row.set_display(tags.get("title",""), tags.get("artist",""), tags.get("cover"))
                row.set_dirty(False)
                subprocess.run(["mdimport", row.path], capture_output=True)
                changed += 1
        if self.current_index >= 0:
            self._on_row_select(self.rows[self.current_index])
        self._flash(f"Champs appliqués à {changed} fichier(s)")

    def _prepare_spotify_folder(self):
        if not self.rows:
            self._flash("Aucun fichier à exporter", err=True); return
        if any(r._dirty for r in self.rows):
            from PyQt6.QtWidgets import QMessageBox
            msg = QMessageBox(self)
            msg.setWindowTitle(T("Modifications non sauvegardées"))
            msg.setText(T("spotify_save_tags"))
            msg.setInformativeText(T("export_note"))
            msg.setStyleSheet(f"background:{BG2};color:{TEXT};")
            save_btn = msg.addButton(T("Sauvegarder"), QMessageBox.ButtonRole.AcceptRole)
            cancel_btn = msg.addButton(T("Annuler"), QMessageBox.ButtonRole.RejectRole)
            msg.exec()
            if msg.clickedButton() == cancel_btn:
                return
            if msg.clickedButton() == save_btn and not self._save_all():
                return

        default_dir = self._cfg.get(
            "spotify_export_folder",
            str(Path.home() / "Music" / "Tagr Spotify Ready"))
        out_dir = QFileDialog.getExistingDirectory(
            self, T("Choisir le dossier Spotify Ready"), default_dir)
        if not out_dir:
            return
        self._cfg["spotify_export_folder"] = out_dir
        save_config(self._cfg)

        ready_rows, review_rows = self._spotify_audit()
        ready = [(row.path, tags) for row, tags in ready_rows]
        review = [(row.path, tags, issues) for row, tags, issues in review_rows]

        lines = [
            f"{len(ready)} fichier(s) prêts",
            f"{len(review)} fichier(s) à vérifier",
            "",
        ]
        for path, tags in ready[:8]:
            lines.append(f"OK  {spotify_filename(tags, path)}")
        if len(ready) > 8:
            lines.append(f"... +{len(ready)-8} autres prêts")
        for path, tags, issues in review[:8]:
            lines.append(f"À vérifier  {os.path.basename(path)} : {', '.join(issues)}")
        if len(review) > 8:
            lines.append(f"... +{len(review)-8} autres à vérifier")

        from PyQt6.QtWidgets import QMessageBox
        msg = QMessageBox(self)
        msg.setWindowTitle(T("Export Spotify Ready"))
        msg.setText(T("spotify_confirm"))
        msg.setInformativeText("\n".join(lines))
        msg.setStyleSheet(f"background:{BG2};color:{TEXT};")
        export_btn = msg.addButton(T("Exporter les prêts"), QMessageBox.ButtonRole.AcceptRole)
        all_btn = msg.addButton(T("Exporter tout"), QMessageBox.ButtonRole.ActionRole)
        cancel_btn = msg.addButton(T("Annuler"), QMessageBox.ButtonRole.RejectRole)
        msg.exec()
        clicked = msg.clickedButton()
        if clicked == cancel_btn:
            return
        targets = ready if clicked == export_btn else [(p, t) for p, t in ready] + [(p, t) for p, t, _ in review]

        copied = 0
        failed = 0
        copied_names = []
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        for path, tags in targets:
            try:
                dest = unique_path(Path(out_dir) / spotify_filename(tags, path))
                shutil.copy2(path, dest)
                copied_names.append(dest.name)
                copied += 1
            except Exception:
                failed += 1
        try:
            report = Path(out_dir) / "rapport_spotify.txt"
            with open(report, "w", encoding="utf-8") as f:
                from datetime import datetime
                f.write(f"Export Tagr Spotify Ready - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write(f"Exportés : {copied}\n")
                f.write(f"Echecs : {failed}\n")
                f.write(f"A vérifier : {len(review)}\n\n")
                f.write("Fichiers exportés\n")
                for name in copied_names:
                    f.write(f"- {name}\n")
                if review:
                    f.write("\nFichiers à vérifier\n")
                    for path, tags, issues in review:
                        f.write(f"- {os.path.basename(path)} : {', '.join(issues)}\n")
        except Exception:
            pass
        subprocess.run(["open", out_dir], capture_output=True)
        msg = f"Spotify Ready : {copied} fichier(s) exporté(s)"
        if failed:
            msg += f" · {failed} échec(s)"
        if review and clicked == export_btn:
            msg += f" · {len(review)} à vérifier"
        self._flash(msg, err=failed > 0)

    def _check_dirty_before_nav(self):
        if self.current_index < 0: return True
        row = self.rows[self.current_index]
        if not row._dirty: return True
        from PyQt6.QtWidgets import QMessageBox
        msg = QMessageBox(self)
        msg.setWindowTitle(T("Modifications non sauvegardées"))
        msg.setText(T("file_modified").replace("{name}", os.path.basename(self.files[self.current_index])))
        msg.setStyleSheet(f"background:{BG2};color:{TEXT};")
        save_btn   = msg.addButton(T("Sauvegarder"), QMessageBox.ButtonRole.AcceptRole)
        skip_btn   = msg.addButton(T("Ignorer"),     QMessageBox.ButtonRole.DestructiveRole)
        cancel_btn = msg.addButton(T("Annuler"),     QMessageBox.ButtonRole.RejectRole)
        msg.exec()
        clicked = msg.clickedButton()
        if clicked == cancel_btn: return False
        if clicked == save_btn: return self._save_current()
        return True


    def _update_cover_info(self, img):
        try:
            w, h = img.size
            # Taille approximative réelle (pixels * 3 canaux / compression ~10:1)
            kb_approx = max(1, (w * h * 3) // (1024 * 8))
            # Évaluation qualité
            if w >= 1000 and h >= 1000:
                quality = "Bonne qualité"
                qcolor = ACCENT
            elif w >= 640 and h >= 640 and w == h:
                quality = "Carrée Spotify"
                qcolor = ACCENT
            elif w >= 500 and h >= 500:
                quality = "Qualité correcte"
                qcolor = WARN
            else:
                quality = "Trop petite"
                qcolor = ERROR
            self.cover_info.setText(f"{w}x{h} px  •  {quality}")
            self.cover_info.setStyleSheet(f"color:{qcolor};font-size:8px;")
        except (OSError, IOError, Exception):
            pass

    def _find_ffmpeg(self):
        for c in ["/opt/homebrew/bin/ffmpeg", "/usr/local/bin/ffmpeg",
                  "/usr/bin/ffmpeg", "/opt/local/bin/ffmpeg"]:
            if os.path.isfile(c): return c
        r = subprocess.run(["which", "ffmpeg"], capture_output=True)
        return r.stdout.decode().strip() if r.returncode == 0 else None

    def _normalize_volume(self):
        if self.current_index < 0: return
        path = self.files[self.current_index]
        ff = self._find_ffmpeg()
        if not ff: self._flash("ffmpeg introuvable", err=True); return

        from PyQt6.QtWidgets import QDialog, QCheckBox, QProgressDialog
        d = QDialog(self); d.setWindowTitle(T("Normaliser le volume"))
        d.setStyleSheet(f"background:{BG2};color:{TEXT};"); d.setMinimumWidth(360)
        v = QVBoxLayout(d); v.setContentsMargins(20,20,20,20); v.setSpacing(10)
        v.addWidget(QLabel(T("file_label").replace("{name}", os.path.basename(path)),
                           styleSheet=f"color:{TEXTD};font-size:10px;"))
        v.addWidget(QLabel(T("Normalisation a -14 LUFS (standard Spotify / Apple Music)"),
                           styleSheet=f"color:{TEXT};font-size:11px;"))
        overwrite_chk = QCheckBox(T("overwrite_original"))
        overwrite_chk.setStyleSheet(f"color:{TEXTM};font-size:10px;")
        v.addWidget(overwrite_chk)
        brow = QHBoxLayout()
        ok = QPushButton(T("Normaliser"))
        ok.setStyleSheet(f"background:{ACCENT};color:#000;font-weight:bold;border:none;padding:9px 20px;border-radius:4px;")
        ok.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel = QPushButton(T("Annuler"))
        cancel.setStyleSheet(f"background:{PANEL};color:{TEXTM};border:none;padding:9px 16px;border-radius:4px;")
        cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        ok.clicked.connect(d.accept); cancel.clicked.connect(d.reject)
        brow.addStretch(); brow.addWidget(cancel); brow.addWidget(ok)
        v.addLayout(brow)
        if d.exec() != QDialog.DialogCode.Accepted: return

        if overwrite_chk.isChecked():
            ok, backup = backup_audio_file(path, "normalize")
            if not ok:
                self._flash(f"Sauvegarde impossible : {backup}", err=True); return
            import tempfile
            tmp_out = tempfile.mktemp(suffix=os.path.splitext(path)[1])
        else:
            base, ext = os.path.splitext(path)
            tmp_out = f"{base}_norm{ext}"
            i = 1
            while os.path.exists(tmp_out): tmp_out = f"{base}_norm{i}{ext}"; i += 1

        # Obtenir durée
        duration_ms = 0
        try:
            import mutagen
            af = mutagen.File(path)
            if af: duration_ms = int(af.info.length * 1000)
        except (OSError, IOError, Exception): pass

        prog = QProgressDialog("Normalisation en cours...", "Annuler", 0, 100, self)
        prog.setWindowTitle("Tagr"); prog.setMinimumWidth(300)
        prog.setStyleSheet(f"background:{BG2};color:{TEXT};")
        prog.setWindowModality(Qt.WindowModality.WindowModal)
        prog.setValue(0); prog.show()

        cmd = [ff, "-y", "-i", path, "-af", "loudnorm=I=-14:TP=-1:LRA=11",
               "-ar", "44100", tmp_out]
        worker = FfmpegWorker(cmd, duration_ms)
        worker.progress.connect(prog.setValue)

        def on_done(ok_flag, msg):
            prog.close()
            if ok_flag:
                try:
                    orig = read_tags(path)
                    write_tags(tmp_out, orig["title"], orig["artist"], orig["album"],
                               orig.get("year",""), orig.get("genre",""),
                               orig.get("bpm",""), orig.get("track",""), orig.get("cover"))
                except (OSError, IOError, Exception): pass
                if overwrite_chk.isChecked():
                    try:
                        import shutil
                        shutil.move(tmp_out, path)
                        subprocess.run(["mdimport", path], capture_output=True)
                        self._flash("Normalise (-14 LUFS) — fichier original remplace")
                    except Exception as e:
                        self._flash(f"Erreur remplacement : {e}", err=True)
                else:
                    subprocess.run(["mdimport", tmp_out], capture_output=True)
                    self._flash(f"Normalise : {os.path.basename(tmp_out)}")
            else:
                self._flash("Erreur normalisation", err=True)

        worker.finished.connect(on_done)
        prog.canceled.connect(worker.terminate)
        worker.start()
        self._workers.append(worker)

    def _convert_format(self):
        if self.current_index < 0: return
        from PyQt6.QtWidgets import QDialog, QComboBox
        path = self.files[self.current_index]
        ext_cur = os.path.splitext(path)[1].lstrip(".").upper()
        fmts = [f for f in ["MP3", "FLAC", "M4A", "AAC", "WAV"] if f != ext_cur]
        d = QDialog(self)
        d.setWindowTitle(T("Convertir le format"))
        d.setStyleSheet(f"background:{BG2};color:{TEXT};")
        v = QVBoxLayout(d); v.setContentsMargins(20,20,20,20); v.setSpacing(12)
        lbl_f = QLabel(T("file_label").replace("{name}", os.path.basename(path)))
        lbl_f.setStyleSheet(f"color:{TEXTD};font-size:10px;")
        v.addWidget(lbl_f)
        v.addWidget(QLabel(T("target_format"), styleSheet=f"color:{TEXT};font-size:11px;"))
        combo = QComboBox(); combo.addItems(fmts)
        combo.setStyleSheet(f"background:{FIELDBG};color:{TEXT};border:1px solid {BORDER};"
                            f"border-radius:4px;padding:6px;font-size:12px;")
        v.addWidget(combo)
        lbl_note = QLabel(T("mp3_info"))
        lbl_note.setStyleSheet(f"color:{TEXTD};font-size:9px;")
        v.addWidget(lbl_note)
        brow = QHBoxLayout()
        ok = QPushButton(T("Convertir"))
        ok.setStyleSheet(f"background:{ACCENT};color:#000;font-weight:bold;border:none;"
                         f"padding:9px 20px;border-radius:4px;")
        ok.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel = QPushButton(T("Annuler"))
        cancel.setStyleSheet(f"background:{PANEL};color:{TEXTM};border:none;"
                             f"padding:9px 16px;border-radius:4px;")
        cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        ok.clicked.connect(d.accept); cancel.clicked.connect(d.reject)
        brow.addStretch(); brow.addWidget(cancel); brow.addWidget(ok)
        v.addLayout(brow)
        if d.exec() != QDialog.DialogCode.Accepted: return
        fmt = combo.currentText().lower()
        ext_map = {"mp3":".mp3","flac":".flac","m4a":".m4a","aac":".aac","wav":".wav"}
        base = os.path.splitext(path)[0]
        out = base + ext_map[fmt]
        if os.path.exists(out): out = base + f"_conv{ext_map[fmt]}"
        ff = self._find_ffmpeg()
        if not ff: self._flash("ffmpeg introuvable", err=True); return
        self._flash("Conversion en cours...")
        QApplication.processEvents()
        codecs = {"mp3":["-codec:a","libmp3lame","-b:a","320k"],
                  "flac":["-codec:a","flac"],
                  "m4a":["-codec:a","aac","-b:a","256k"],
                  "aac":["-codec:a","aac","-b:a","256k"],
                  "wav":["-codec:a","pcm_s16le"]}
        cmd = [ff, "-y", "-i", path] + codecs.get(fmt, []) + [out]
        duration_ms = 0
        try:
            import mutagen as _m
            af = _m.File(path)
            if af: duration_ms = int(af.info.length * 1000)
        except (OSError, IOError, Exception): pass

        prog = QProgressDialog(f"Conversion en cours...", "Annuler", 0, 100, self)
        prog.setWindowTitle("Tagr"); prog.setMinimumWidth(300)
        prog.setStyleSheet(f"background:{BG2};color:{TEXT};")
        prog.setWindowModality(Qt.WindowModality.WindowModal)
        prog.setValue(0); prog.show()

        worker = FfmpegWorker(cmd, duration_ms)
        worker.progress.connect(prog.setValue)

        def on_conv_done(ok_flag, msg, out=out, path=path):
            prog.close()
            if ok_flag:
                try:
                    orig = read_tags(path)
                    write_tags(out, orig["title"], orig["artist"], orig["album"],
                               orig.get("year",""), orig.get("genre",""),
                               orig.get("bpm",""), orig.get("track",""), orig.get("cover"))
                except (OSError, IOError, Exception): pass
                subprocess.run(["mdimport", out], capture_output=True)
                self._flash(f"Converti : {os.path.basename(out)}")
            else:
                self._flash("Erreur conversion", err=True)

        worker.finished.connect(on_conv_done)
        prog.canceled.connect(worker.terminate)
        worker.start()
        self._workers.append(worker)

    def _batch_rename(self):
        from PyQt6.QtWidgets import QDialog, QLineEdit, QCheckBox
        d = QDialog(self)
        d.setWindowTitle(T("Renommer par lot"))
        d.setStyleSheet(f"background:{BG2};color:{TEXT};")
        v = QVBoxLayout(d); v.setContentsMargins(20,20,20,20); v.setSpacing(10)
        v.addWidget(QLabel(T("rename_pattern"), styleSheet=f"color:{TEXT};font-size:11px;"))
        pattern_edit = QLineEdit("{artist} - {title}" if _LANG == "en" else "{artiste} - {titre}")
        pattern_edit.setStyleSheet(f"background:{FIELDBG};color:{TEXT};border:1px solid {BORDER};"
                                   f"border-radius:4px;padding:8px;font-size:12px;")
        v.addWidget(pattern_edit)
        hint = QLabel(T("rename_variables"))
        hint.setStyleSheet(f"color:{TEXTD};font-size:9px;")
        v.addWidget(hint)
        all_chk = QCheckBox(T("apply_all_files"))
        all_chk.setChecked(True)
        all_chk.setStyleSheet(f"color:{TEXTM};font-size:10px;")
        v.addWidget(all_chk)
        brow = QHBoxLayout()
        ok = QPushButton(T("Renommer"))
        ok.setStyleSheet(f"background:{ACCENT};color:#000;font-weight:bold;border:none;"
                         f"padding:9px 20px;border-radius:4px;")
        ok.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel = QPushButton(T("Annuler"))
        cancel.setStyleSheet(f"background:{PANEL};color:{TEXTM};border:none;"
                             f"padding:9px 16px;border-radius:4px;")
        cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        ok.clicked.connect(d.accept); cancel.clicked.connect(d.reject)
        brow.addStretch(); brow.addWidget(cancel); brow.addWidget(ok)
        v.addLayout(brow)
        self.status_lbl2 = QLabel("")
        self.status_lbl2.setStyleSheet(f"color:{TEXTD};font-size:9px;")
        v.addWidget(self.status_lbl2)
        if d.exec() != QDialog.DialogCode.Accepted: return
        pattern = pattern_edit.text().strip()
        if not pattern: return
        targets = self.rows if all_chk.isChecked() else (
            [self.rows[self.current_index]] if self.current_index >= 0 else [])
        preview = []
        conflicts = 0
        seen_targets = set()
        for row in targets:
            tags = self._row_tags(row)
            name = name_from_pattern(pattern, tags, row.path)
            if not name:
                continue
            new_path = os.path.join(os.path.dirname(row.path), name + os.path.splitext(row.path)[1])
            if new_path == row.path:
                continue
            issue = ""
            if os.path.exists(new_path) or new_path in seen_targets:
                issue = "conflit"
                conflicts += 1
            seen_targets.add(new_path)
            preview.append((row.path, new_path, issue))
        if not preview:
            self._flash("Aucun renommage à appliquer"); return
        from PyQt6.QtWidgets import QMessageBox
        lines = []
        for old, new, issue in preview[:12]:
            suffix = f" ({issue})" if issue else ""
            lines.append(f"{os.path.basename(old)} -> {os.path.basename(new)}{suffix}")
        if len(preview) > 12:
            lines.append(f"... +{len(preview)-12} autres")
        msg = QMessageBox(self)
        msg.setWindowTitle(T("Aperçu du renommage"))
        msg.setText(T("n_renames").replace("{n}", str(len(preview))))
        msg.setInformativeText("\n".join(lines))
        msg.setStyleSheet(f"background:{BG2};color:{TEXT};")
        apply_btn = msg.addButton(T("Appliquer"), QMessageBox.ButtonRole.AcceptRole)
        cancel_btn = msg.addButton(T("Annuler"), QMessageBox.ButtonRole.RejectRole)
        msg.exec()
        if msg.clickedButton() == cancel_btn:
            return
        renamed = 0
        skipped = conflicts
        rows_by_path = {row.path: row for row in targets}
        for path, new_path, issue in preview:
            if issue:
                continue
            row = rows_by_path.get(path)
            if not row:
                skipped += 1; continue
            tags = self._row_tags(row)
            try:
                ok, backup = backup_audio_file(path, "batch_rename")
                if not ok:
                    skipped += 1
                    continue
                os.rename(path, new_path)
                idx = self.rows.index(row)
                self.files[idx] = new_path
                row.path = new_path
                self.tags_cache[new_path] = self.tags_cache.pop(path, {})
                row.update_display(tags.get("title",""), tags.get("artist",""),
                                   tags.get("cover"))
                subprocess.run(["mdimport", new_path], capture_output=True)
                renamed += 1
            except (OSError, IOError, Exception):
                skipped += 1
        msg = f"{renamed} fichier(s) renomme(s)"
        if skipped:
            msg += f" · {skipped} ignore(s)"
        self._flash(msg)

    def _show_shortcuts(self):
        from PyQt6.QtWidgets import QDialog
        d = QDialog(self)
        d.setWindowTitle(T("Raccourcis clavier"))
        d.setStyleSheet(f"background:{BG2};color:{TEXT};")
        d.setMinimumWidth(380)
        v = QVBoxLayout(d); v.setContentsMargins(24,20,24,20); v.setSpacing(4)
        title = QLabel(T("Raccourcis clavier"))
        title.setStyleSheet(f"font-size:15px;font-weight:bold;color:{TEXT};")
        v.addWidget(title)
        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color:{BORDER};margin:8px 0;"); v.addWidget(sep)
        shortcuts = [
            ("Cmd+S",           T("Sauvegarder")),
            ("Cmd+Shift+S",     T("Tout sauvegarder")),
            ("Cmd+Z",           "Annuler les modifications"),
            (T("Outils audio…"), T("shortcuts_audio_tools")),
            ("Spotify",         T("shortcuts_spotify_export")),
            ("Entree",          T("Sauvegarder")),
            ("Espace",          "Lecture / Pause"),
            ("Haut / Bas",      T("file_previous_next")),
            ("Suppr / Retour",  T("remove_current_file")),
        ]
        for keys, desc in shortcuts:
            row = QHBoxLayout(); row.setSpacing(12)
            k = QLabel(keys)
            k.setStyleSheet(f"background:{PANEL};color:{ACCENT};font-family:'Courier New';"
                            f"font-size:10px;padding:3px 8px;border-radius:3px;")
            k.setFixedWidth(160)
            d_lbl = QLabel(desc)
            d_lbl.setStyleSheet(f"color:{TEXT};font-size:11px;")
            row.addWidget(k); row.addWidget(d_lbl); row.addStretch()
            w = QWidget(); w.setLayout(row); v.addWidget(w)
        v.addSpacing(8)
        close = QPushButton(T("Fermer"))
        close.setStyleSheet(f"background:{PANEL};color:{TEXTM};border:none;"
                            f"padding:8px 20px;border-radius:4px;")
        close.setCursor(Qt.CursorShape.PointingHandCursor)
        close.clicked.connect(d.accept)
        v.addWidget(close, alignment=Qt.AlignmentFlag.AlignCenter)
        d.exec()

    def _detect_duplicates(self):
        # Anciennement, Tagr colorait les doublons en orange dans la colonne gauche.
        # On garde uniquement le reset visuel : la détection reste disponible ailleurs.
        for row in self.rows:
            try:
                row.lbl_t.setStyleSheet(
                    f"color:{TEXT};font-size:12px;font-weight:bold;background:transparent;")
            except Exception: pass

    def _duplicate_groups(self):
        groups = {}
        for row in self.rows:
            tags = self._row_tags(row)
            t = clean_text(tags.get("title")).lower()
            a = clean_text(tags.get("artist")).lower()
            if t and a:
                groups.setdefault((t, a), []).append(row)
        return [rows for rows in groups.values() if len(rows) > 1]

    def _show_duplicates(self):
        groups = self._duplicate_groups()
        if not groups:
            self._flash("Aucun doublon titre/artiste détecté"); return
        from PyQt6.QtWidgets import QDialog
        d = QDialog(self)
        d.setWindowTitle(T("Doublons possibles"))
        d.setStyleSheet(f"background:{BG2};color:{TEXT};")
        d.setMinimumSize(560, 380)
        v = QVBoxLayout(d); v.setContentsMargins(20,18,20,18); v.setSpacing(10)
        title = QLabel(f"{len(groups)} groupe(s) de doublons possibles")
        title.setStyleSheet(f"color:{TEXT};font-size:15px;font-weight:bold;")
        v.addWidget(title)
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        cont = QWidget(); cont.setStyleSheet(f"background:{BG2};")
        rows_l = QVBoxLayout(cont); rows_l.setContentsMargins(0,0,0,0); rows_l.setSpacing(1)
        for group in groups:
            tags = self._row_tags(group[0])
            header = QLabel(f"{tags.get('artist','')} - {tags.get('title','')}")
            header.setStyleSheet(f"color:{WARN};font-size:11px;font-weight:bold;padding:8px;background:{BG2};")
            rows_l.addWidget(header)
            for row in group:
                btn = QPushButton(os.path.basename(row.path))
                btn.setStyleSheet(f"background:{PANEL};color:{TEXTM};border:none;text-align:left;padding:7px 10px;font-size:10px;")
                btn.clicked.connect(lambda _, p=row.path, dia=d: (dia.accept(), self._select_path(p)))
                rows_l.addWidget(btn)
        rows_l.addStretch(); scroll.setWidget(cont); v.addWidget(scroll, 1)
        close = QPushButton(T("Fermer"))
        close.setStyleSheet(f"background:{PANEL};color:{TEXTM};border:none;padding:8px 14px;border-radius:4px;")
        close.clicked.connect(d.accept)
        v.addWidget(close, alignment=Qt.AlignmentFlag.AlignRight)
        d.exec()


    def _export_csv(self):
        if not self.files:
            self._flash("Aucun fichier dans la liste", err=True); return
        path, _ = QFileDialog.getSaveFileName(
            self, "Exporter en CSV", os.path.expanduser("~/Desktop/tagr_export.csv"),
            "CSV (*.csv)")
        if not path: return
        import csv
        fields = ["fichier","titre","artiste","album","piste","annee","genre","bpm","qualite"]
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=fields)
                w.writeheader()
                for row in self.rows:
                    tags = self.tags_cache.get(row.path, {})
                    q = read_audio_quality(row.path)
                    label, _ = quality_label(row.path, q)
                    w.writerow({
                        "fichier": os.path.basename(row.path),
                        "titre":   tags.get("title",""),
                        "artiste": tags.get("artist",""),
                        "album":   tags.get("album",""),
                        "piste":   tags.get("track",""),
                        "annee":   tags.get("year",""),
                        "genre":   tags.get("genre",""),
                        "bpm":     tags.get("bpm",""),
                        "qualite": label,
                    })
            self._flash(f"CSV exporte : {os.path.basename(path)}")
            subprocess.run(["open", "-R", path])
        except Exception as e:
            self._flash(f"Erreur export : {e}", err=True)

    def _suggest_with_ai(self):
        if self.current_index < 0: return
        api_key = self._cfg.get("anthropic_key", "").strip()
        if not api_key:
            self._ask_api_key(); return
        path = self.files[self.current_index]
        filename = os.path.splitext(os.path.basename(path))[0]
        t = self.field_title.text().strip()
        a = self.field_artist.text().strip()
        self._flash("Analyse IA en cours...")

        def do():
            try:
                import urllib.request, json
                prompt = (f"Fichier audio : \"{filename}\"\n"
                          f"Titre actuel : \"{t}\"\n"
                          f"Artiste actuel : \"{a}\"\n\n"
                          f"Analyse le nom du fichier et suggere les metadonnees les plus probables.\n"
                          f"Reponds UNIQUEMENT en JSON avec ces cles exactes (sans markdown) :\n"
                          f"{{\"title\":\"...\",\"artist\":\"...\",\"album\":\"...\","
                          f"\"year\":\"...\",\"genre\":\"...\",\"confidence\":\"high|medium|low\"}}")
                body = json.dumps({
                    "model": "claude-sonnet-4-6",
                    "max_tokens": 300,
                    "messages": [{"role": "user", "content": prompt}]
                }).encode()
                req = urllib.request.Request(
                    "https://api.anthropic.com/v1/messages",
                    data=body,
                    headers={
                        "Content-Type": "application/json",
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01"
                    })
                resp = urllib.request.urlopen(req, timeout=15)
                data = json.loads(resp.read())
                text = data["content"][0]["text"].strip()
                # Nettoyer si besoin
                if text.startswith("```"): text = text.split("```")[1].lstrip("json").strip()
                suggestion = json.loads(text)
                QTimer.singleShot(0, lambda: self._apply_ai_suggestion(suggestion))
            except Exception as e:
                QTimer.singleShot(0, lambda: self._flash(f"Erreur IA : {e}", err=True))

        import threading
        threading.Thread(target=do, daemon=True).start()

    def _apply_ai_suggestion(self, s):
        conf = s.get("confidence","")
        for f, k in [(self.field_title,"title"),(self.field_artist,"artist"),
                     (self.field_album,"album"),(self.field_year,"year"),
                     (self.field_genre,"genre")]:
            val = s.get(k,"").strip()
            if val and not f.text().strip():
                f.blockSignals(True); f.setText(val); f.blockSignals(False)
        self._mark_dirty()
        label = {"high":"(confiance elevee)","medium":"(confiance moyenne)","low":"(confiance basse)"}.get(conf,"")
        self._flash(f"Suggestion IA appliquee {label}")

    def _ask_api_key(self):
        from PyQt6.QtWidgets import QInputDialog
        key, ok = QInputDialog.getText(
            self, "Cle API Anthropic",
            "Entre ta cle API Anthropic :\n(https://console.anthropic.com)",
            QLineEdit.EchoMode.Password)
        if ok and key.strip():
            self._cfg["anthropic_key"] = key.strip()
            save_config(self._cfg)
            self._flash("Cle API enregistree")
            self._suggest_with_ai()

    def _search_cover_smart(self):
        if self.current_index < 0: return
        a = self.field_artist.text().strip()
        t = self.field_title.text().strip()
        # Priorité à l'artiste — si vide, fallback sur le titre ou le nom de fichier
        q = a or t or os.path.splitext(
            os.path.basename(self.files[self.current_index]))[0]
        if not q: return
        label = ("Recherche artiste: " + q + "...") if a else ("Recherche: " + q + "...")
        self._flash(label)
        w = Searcher(q); w.done.connect(self._on_search_done)
        w.start(); self._workers.append(w)


    # ── Worker cleanup ────────────────────────────────────────────
    def _cleanup_workers(self):
        self._workers = [w for w in self._workers if w.isRunning()]

    # ── Theme toggle ──────────────────────────────────────────────
    def _toggle_theme(self):
        self._is_dark = not getattr(self, "_is_dark", True)
        p = DARK_PALETTE if self._is_dark else LIGHT_PALETTE
        _apply_palette(p)
        self._rebuild_stylesheet()

    def _rebuild_stylesheet(self):
        self.setStyleSheet(f"QMainWindow{{background:{BG};}}"
        )  # fond unifié
        # Rebuild barre titre
        for w in self.findChildren(QFrame):
            try:
                if w.height() == 54:
                    w.setStyleSheet(f"background:{BG};border-bottom:1px solid {BORDER};")
            except Exception: pass
        # Rebuild liste
        if hasattr(self, 'list_widget'):
            self.list_widget.setStyleSheet(
                f"background:{BG2};border-right:1px solid {BORDER};")
        self._flash("Theme " + ("sombre" if self._is_dark else "clair"))

    # ── BPM auto-detect ───────────────────────────────────────────
    def _detect_bpm(self):
        if self.current_index < 0: return
        path = self.files[self.current_index]
        ff = self._find_ffmpeg()
        if not ff: self._flash("ffmpeg introuvable", err=True); return
        self._flash("Detection BPM en cours...")
        def do():
            try:
                import struct, wave as wavemod, math
                tmp = "/tmp/tagr_bpm.wav"
                r = subprocess.run(
                    [ff, "-y", "-i", path, "-ar", "22050", "-ac", "1",
                     "-t", "60", "-f", "wav", tmp],
                    capture_output=True, timeout=20)
                if r.returncode != 0: raise Exception("Conversion echouee")
                with wavemod.open(tmp, "rb") as wf:
                    sr = wf.getframerate()
                    raw = wf.readframes(wf.getnframes())
                samples = [s/32768.0 for s in struct.unpack(f"<{len(raw)//2}h", raw)]
                # Energie par fenetre de 512 samples
                win = 512
                energies = []
                for i in range(0, len(samples)-win, win//2):
                    chunk = samples[i:i+win]
                    e = sum(x*x for x in chunk)/win
                    energies.append(e)
                if len(energies) < 4:
                    raise Exception("Fichier trop court")
                # Detection de pics d'energie (beats)
                avg_e = sum(energies)/len(energies)
                beats = []
                hop_sec = (win//2) / sr
                for i in range(1, len(energies)-1):
                    if (energies[i] > avg_e * 1.3 and
                        energies[i] > energies[i-1] and
                        energies[i] > energies[i+1]):
                        t = i * hop_sec
                        if not beats or t - beats[-1] > 0.2:
                            beats.append(t)
                if len(beats) > 4:
                    intervals = [beats[i+1]-beats[i] for i in range(len(beats)-1)]
                    median = sorted(intervals)[len(intervals)//2]
                    bpm = round(60.0 / median)
                    # Ajustement si hors plage raisonnable
                    while bpm < 60: bpm *= 2
                    while bpm > 200: bpm //= 2
                    QTimer.singleShot(0, lambda b=bpm: self._apply_bpm(b))
                else:
                    QTimer.singleShot(0, lambda: self._flash("BPM non detectable", err=True))
            except Exception as e:
                QTimer.singleShot(0, lambda: self._flash(f"Erreur BPM: {e}", err=True))
        import threading
        threading.Thread(target=do, daemon=True).start()

    def _apply_bpm(self, bpm):
        self.field_bpm.blockSignals(True)
        self.field_bpm.setText(str(bpm))
        self.field_bpm.blockSignals(False)
        self._mark_dirty()
        self._flash(f"BPM detecte : {bpm}")

    # ── Stats bibliotheque ────────────────────────────────────────
    def _show_stats(self):
        if not self.files:
            self._flash("Aucun fichier dans la liste", err=True); return
        from PyQt6.QtWidgets import QDialog
        d = QDialog(self); d.setWindowTitle(T("Statistiques"))
        d.setStyleSheet(f"background:{BG2};color:{TEXT};")
        d.setMinimumWidth(340)
        v = QVBoxLayout(d); v.setContentsMargins(24,20,24,20); v.setSpacing(6)

        title = QLabel(T("Statistiques de la bibliotheque"))
        title.setStyleSheet(f"font-size:14px;font-weight:bold;color:{TEXT};")
        v.addWidget(title)

        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color:{BORDER};"); v.addWidget(sep)

        # Calcul stats
        formats = {}; qualities = {}; artists = set(); albums = set()
        total_dur = 0; missing_cover = 0; missing_tags = 0

        for row in self.rows:
            ext = os.path.splitext(row.path)[1].lstrip(".").upper()
            formats[ext] = formats.get(ext, 0) + 1
            tags = self.tags_cache.get(row.path, {})
            if tags.get("artist"): artists.add(tags["artist"])
            if tags.get("album"):  albums.add(tags["album"])
            if not tags.get("cover"): missing_cover += 1
            if not tags.get("title") or not tags.get("artist"): missing_tags += 1
            try:
                q = read_audio_quality(row.path)
                lbl, _ = quality_label(row.path, q)
                qualities[lbl] = qualities.get(lbl, 0) + 1
                if q.get("duration"): total_dur += q["duration"]
            except (OSError, IOError, Exception): pass

        def stat_row(label, value, color=None):
            row_w = QWidget(); row_l = QHBoxLayout(row_w)
            row_l.setContentsMargins(0,2,0,2)
            lbl = QLabel(label); lbl.setStyleSheet(f"color:{TEXTM};font-size:10px;")
            val = QLabel(str(value))
            val.setStyleSheet(f"color:{color or ACCENT};font-size:10px;font-weight:bold;")
            val.setAlignment(Qt.AlignmentFlag.AlignRight)
            row_l.addWidget(lbl); row_l.addStretch(); row_l.addWidget(val)
            v.addWidget(row_w)

        stat_row(T("stats_total_files"), len(self.files))
        h, m = divmod(int(total_dur), 3600)
        m, s = divmod(m, 60)
        stat_row("Duree totale", f"{h}h {m}m {s}s")
        stat_row("Artistes uniques", len(artists))
        stat_row("Albums uniques", len(albums))
        stat_row(T("stats_no_cover"), missing_cover, ERROR if missing_cover else ACCENT)
        stat_row(T("stats_missing_tags"), missing_tags, WARN if missing_tags else ACCENT)

        sep2 = QFrame(); sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet(f"color:{BORDER};"); v.addWidget(sep2)
        v.addWidget(QLabel(T("stats_formats"), styleSheet=f"color:{TEXTD};font-size:9px;"))
        for fmt, count in sorted(formats.items()):
            stat_row(f"  {fmt}", count, TEXT)
        v.addWidget(QLabel(T("stats_quality"), styleSheet=f"color:{TEXTD};font-size:9px;"))
        for ql, count in sorted(qualities.items()):
            stat_row(f"  {ql}", count, TEXT)

        close = QPushButton(T("Fermer"))
        close.setStyleSheet(f"background:{PANEL};color:{TEXTM};border:none;"
                            f"padding:8px 20px;border-radius:4px;")
        close.setCursor(Qt.CursorShape.PointingHandCursor)
        close.clicked.connect(d.accept)
        v.addWidget(close, alignment=Qt.AlignmentFlag.AlignCenter)
        d.exec()

    # ── Vue album ─────────────────────────────────────────────────
    def _toggle_album_view(self):
        self._album_view = not getattr(self, "_album_view", False)
        if self._album_view:
            self._build_album_view()
            if self.album_btn: self.album_btn.setText(T("Vue liste"))
        else:
            self._clear_album_groups()
            if self.album_btn: self.album_btn.setText(T("Vue album"))

    def _build_album_view(self):
        self._clear_album_groups()
        # Grouper par album
        groups = {}
        for i, row in enumerate(self.rows):
            tags = self.tags_cache.get(row.path, {})
            album = tags.get("album","") or "Sans album"
            if album not in groups: groups[album] = []
            groups[album].append((i, row))
        # Re-organiser la liste avec headers
        self._album_headers = []
        pos = 0
        for album, items in sorted(groups.items()):
            hdr = QFrame()
            hdr.setStyleSheet(f"background:{PANEL2};border-radius:4px;")
            hdr.setFixedHeight(28)
            hl = QHBoxLayout(hdr); hl.setContentsMargins(10,0,10,0)
            lbl = QLabel(album); lbl.setStyleSheet(
                f"color:{ACCENT};font-size:10px;font-weight:bold;")
            count = QLabel(f"{len(items)} titre(s)")
            count.setStyleSheet(f"color:{TEXTD};font-size:9px;")
            hl.addWidget(lbl); hl.addStretch(); hl.addWidget(count)
            self.list_layout.insertWidget(pos, hdr)
            self._album_headers.append(hdr)
            pos += 1
            for _, row in items:
                self.list_layout.removeWidget(row)
                self.list_layout.insertWidget(pos, row)
                pos += 1

    def _clear_album_groups(self):
        for hdr in getattr(self, "_album_headers", []):
            self.list_layout.removeWidget(hdr)
            hdr.deleteLater()
        self._album_headers = []
        # Remettre les rows dans l'ordre original
        for row in self.rows:
            self.list_layout.removeWidget(row)
            self.list_layout.insertWidget(self.list_layout.count()-1, row)

    # ── Before/After normalisation ────────────────────────────────
    def _preview_before_after(self):
        if self.current_index < 0: return
        path = self.files[self.current_index]
        ff = self._find_ffmpeg()
        if not ff: self._flash("ffmpeg introuvable", err=True); return

        from PyQt6.QtWidgets import QDialog
        d = QDialog(self); d.setWindowTitle(T("Avant / Apres normalisation"))
        d.setStyleSheet(f"background:{BG2};color:{TEXT};")
        d.setMinimumWidth(360)
        v = QVBoxLayout(d); v.setContentsMargins(20,18,20,18); v.setSpacing(10)

        v.addWidget(QLabel(T("preview_compare"),
                           styleSheet=f"font-size:13px;font-weight:bold;color:{TEXT};"))
        v.addWidget(QLabel(os.path.basename(path),
                           styleSheet=f"font-size:9px;color:{TEXTD};"))

        self._ba_proc = None
        self._ba_tmp = None

        def play_original():
            _stop()
            self._ba_proc = subprocess.Popen(
                ["/usr/bin/afplay", path],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            status.setText(T("Lecture : Original"))

        def play_norm():
            _stop()
            import tempfile
            tmp = tempfile.mktemp(suffix=".mp3")
            self._ba_tmp = tmp
            status.setText(T("Normalisation rapide en cours..."))
            QApplication.processEvents()
            r = subprocess.run(
                [ff, "-y", "-i", path, "-af", "loudnorm=I=-14:TP=-1:LRA=11",
                 "-ar", "44100", "-t", "30", tmp], capture_output=True)
            if r.returncode == 0:
                self._ba_proc = subprocess.Popen(
                    ["/usr/bin/afplay", tmp],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                status.setText(T("Lecture : Normalise (-14 LUFS)"))
            else:
                status.setText(T("Erreur normalisation"))

        def _stop():
            if self._ba_proc and self._ba_proc.poll() is None:
                self._ba_proc.terminate()
            self._ba_proc = None

        brow = QHBoxLayout(); brow.setSpacing(10)
        btn_orig = QPushButton(T("▶  Original"))
        btn_orig.setStyleSheet(f"background:{PANEL};color:{TEXT};border:none;"
                               f"padding:10px 18px;font-size:11px;border-radius:5px;")
        btn_orig.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_orig.clicked.connect(play_original)

        btn_norm = QPushButton(T("▶  Normalise"))
        btn_norm.setStyleSheet(f"background:{ACCENT};color:#000;font-weight:bold;border:none;"
                               f"padding:10px 18px;font-size:11px;border-radius:5px;")
        btn_norm.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_norm.clicked.connect(play_norm)

        btn_stop = QPushButton(T("⏹  Stop"))
        btn_stop.setStyleSheet(f"background:{PANEL};color:{TEXTM};border:none;"
                               f"padding:10px 14px;font-size:11px;border-radius:5px;")
        btn_stop.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_stop.clicked.connect(_stop)

        status = QLabel(T("Clique sur Original ou Normalise pour ecouter"))
        status.setStyleSheet(f"color:{TEXTD};font-size:9px;")

        brow.addWidget(btn_orig); brow.addWidget(btn_norm); brow.addWidget(btn_stop)
        v.addLayout(brow); v.addWidget(status)

        def _on_close():
            _stop()
            if self._ba_tmp and os.path.exists(self._ba_tmp):
                try: os.remove(self._ba_tmp)
                except (OSError, IOError, Exception): pass
        d.rejected.connect(_on_close)
        d.accepted.connect(_on_close)

        close = QPushButton(T("Fermer"))
        close.setStyleSheet(f"background:{PANEL};color:{TEXTM};border:none;"
                            f"padding:8px 20px;border-radius:4px;")
        close.setCursor(Qt.CursorShape.PointingHandCursor)
        close.clicked.connect(d.accept)
        v.addWidget(close, alignment=Qt.AlignmentFlag.AlignCenter)
        d.exec()


    def _show_audio_tools_menu(self):
        from PyQt6.QtWidgets import QMenu
        menu = QMenu(self)
        menu.setStyleSheet(
            f"QMenu{{background:{PANEL2};color:{TEXT};border:1px solid {BORDER};padding:4px;}}"
            f"QMenu::item{{padding:8px 20px;font-size:11px;}}"
            f"QMenu::item:selected{{background:{PANEL};color:{TEXT};}}"
            f"QMenu::separator{{height:1px;background:{BORDER};margin:4px 0;}}")
        menu.addAction(T("Couper le morceau"), self._open_trim)
        menu.addSeparator()
        menu.addAction(T("Normaliser le volume (-14 LUFS)"), self._normalize_volume)
        menu.addAction(T("Avant / Apres normalisation"), self._preview_before_after)
        menu.addSeparator()
        menu.addAction(T("Convertir le format"), self._convert_format)
        btn = self._audio_tools_btn
        pos = btn.mapToGlobal(btn.rect().bottomLeft())
        menu.exec(pos)

    def _show_save_menu(self):
        from PyQt6.QtWidgets import QMenu
        menu = QMenu(self)
        menu.setStyleSheet(
            f"QMenu{{background:{PANEL2};color:{TEXT};border:1px solid {BORDER};padding:4px;}}"
            f"QMenu::item{{padding:8px 20px;font-size:11px;}}"
            f"QMenu::item:selected{{background:{PANEL};color:{TEXT};}}"
            f"QMenu::separator{{height:1px;background:{BORDER};margin:4px 0;}}")
        menu.addAction(T("Sauvegarder + fichier suivant"), self._save_and_next)
        menu.addAction(T("Sauvegarder + problème suivant"), self._save_and_next_issue)
        menu.addSeparator()
        menu.addAction(T("Tout sauvegarder"), self._save_all)
        menu.exec(self.cursor().pos())



    def _switch_lang(self, idx):
        new_lang = "fr" if idx == 0 else "en"
        set_lang(new_lang)
        cfg = load_config()
        cfg["lang"] = new_lang
        save_config(cfg)
        self._apply_translations()

    def _apply_translations(self):
        """Met à jour tous les textes de l'UI sans redémarrer."""
        # Combo langue (sans emoji, le globe est à côté)
        if hasattr(self, "_lang_combo") and self._lang_combo is not None:
            self._lang_combo.blockSignals(True)
            self._lang_combo.setItemText(0, "Français")
            self._lang_combo.setItemText(1, "English")
            self._lang_combo.setCurrentIndex(0 if _LANG == "fr" else 1)
            self._lang_combo.blockSignals(False)
        # Fenêtre titre
        self.setWindowTitle(T("app_title"))
        # Bouton sauvegarder
        if hasattr(self, "_save_btn"):
            self._save_btn.setText(T("Sauvegarder"))
        # Labels champs
        if hasattr(self, "_lbl_titre"):
            self._lbl_titre.setText(T("TITRE"))
        if hasattr(self, "_lbl_artiste"):
            self._lbl_artiste.setText(T("ARTISTE"))
        if hasattr(self, "_lbl_album"):
            self._lbl_album.setText(T("ALBUM"))
        # Sections POCHETTE / LECTURE / OUTILS AUDIO
        if hasattr(self, "_lbl_section_pochette"):
            self._lbl_section_pochette.setText(T("POCHETTE"))
        if hasattr(self, "_lbl_section_lecture"):
            self._lbl_section_lecture.setText(T("LECTURE"))
        if hasattr(self, "_lbl_section_outils"):
            self._lbl_section_outils.setText(T("OUTILS AUDIO"))
        # Hint zone vide
        if hasattr(self, "hint") and self.hint is not None:
            self.hint.setText(T("hint_drop"))
        if hasattr(self, "_empty_title"):
            self._empty_title.setText(T("empty_title"))
        if hasattr(self, "_empty_hint"):
            self._empty_hint.setText(T("empty_hint"))
        # Hint pochette
        if hasattr(self, "_cover_hint") and self._cover_hint is not None:
            self._cover_hint.setText(T("Cliquer ou glisser une image"))
        if hasattr(self, "cover_lbl") and self.cover_lbl.pixmap().isNull():
            self.cover_lbl._reset()
        # Bouton recadrer
        if hasattr(self, "_crop_btn"):
            self._crop_btn.setText(T("Recadrer"))
        # Dropdown filtre
        if hasattr(self, "filter_field"):
            self.filter_field.blockSignals(True)
            for i, key in enumerate(["A → Z", "Artiste", "Album", "Titre"]):
                self.filter_field.setItemText(i, T(key))
            self.filter_field.blockSignals(False)
        # Boutons actions droite
        if hasattr(self, "_btn_search_cover"):
            self._btn_search_cover.setText(T("Recherche de pochette"))
        if hasattr(self, "_btn_export_cover"):
            self._btn_export_cover.setText(T("Exporter la pochette"))
        if hasattr(self, "_btn_listen"):
            self._btn_listen.setText(T("Ecouter"))
        if hasattr(self, "_btn_audio_tools"):
            self._btn_audio_tools.setText(T("Outils audio…"))
        if hasattr(self, "spotify_status_lbl") and self.current_index < 0:
            self.spotify_status_lbl.setText(T("Statut Spotify"))
        # Re-render le fichier sélectionné pour mettre à jour qualité + Spotify issue
        if hasattr(self, "current_index") and self.current_index is not None and 0 <= self.current_index < len(self.files):
            try:
                self._on_row_select(self.rows[self.current_index])
            except Exception:
                pass

    def _deselect_all(self):
        self._clear_row_selection()
        self.current_index = -1
        self._selection_anchor = None
        self._stop_play()
        self.right.show_empty()


    def _crop_current_cover(self):
        if not self.current_cover:
            self._flash("Aucune pochette à recadrer", err=True); return
        d = CropDialog(self, self.current_cover)
        d.cropped.connect(self._apply_cover)
        d.exec()


    def _find_ytdlp(self):
        for c in ["/opt/homebrew/bin/yt-dlp", "/usr/local/bin/yt-dlp", "/usr/bin/yt-dlp"]:
            if os.path.isfile(c): return c
        r = subprocess.run(["which", "yt-dlp"], capture_output=True)
        return r.stdout.decode().strip() if r.returncode == 0 else None

    def _has_ytdlp_module(self):
        try:
            import yt_dlp
            return True
        except Exception:
            return False

    def _download_from_url(self):
        ytdlp = self._find_ytdlp()
        has_ytdlp_module = self._has_ytdlp_module()
        if not ytdlp and not has_ytdlp_module:
            self._flash(T("yt_not_found2"), err=True)
            return

        from PyQt6.QtWidgets import QDialog, QComboBox
        d = QDialog(self)
        d.setWindowTitle(T("Télécharger depuis URL"))
        d.setStyleSheet(f"background:{BG2};color:{TEXT};")
        d.setMinimumWidth(480)
        v = QVBoxLayout(d); v.setContentsMargins(20,20,20,20); v.setSpacing(12)

        title_lbl = QLabel(T("Télécharger un fichier audio"))
        title_lbl.setStyleSheet(f"font-size:14px;font-weight:bold;color:{TEXT};")
        v.addWidget(title_lbl)

        src_lbl = QLabel(T("sc_bandcamp"))
        src_lbl.setStyleSheet(f"font-size:9px;color:{TEXTD};")
        v.addWidget(src_lbl)

        v.addWidget(QLabel(T("URL :"), styleSheet=f"color:{TEXTM};font-size:10px;"))
        url_input = QLineEdit()
        url_input.setPlaceholderText(T("placeholder_url"))
        url_input.setStyleSheet(
            f"background:{FIELDBG};color:{TEXT};border:1px solid {BORDER};"
            f"border-radius:5px;padding:8px 10px;font-size:12px;")
        v.addWidget(url_input)

        fmt_row = QHBoxLayout(); fmt_row.setSpacing(10)
        fmt_row.addWidget(QLabel(T("Format :"), styleSheet=f"color:{TEXTM};font-size:10px;"))
        fmt_combo = QComboBox()
        fmt_combo.addItems([T("MP3 320k"), T("Meilleure qualité (natif)")])
        fmt_combo.setStyleSheet(
            f"QComboBox{{background:{FIELDBG};color:{TEXT};border:1px solid {BORDER};"
            f"border-radius:5px;padding:6px 8px;font-size:11px;}}"
            f"QComboBox::drop-down{{border:none;width:16px;}}"
            f"QComboBox QAbstractItemView{{background:{PANEL2};color:{TEXT};border:1px solid {BORDER};}}")
        fmt_row.addWidget(fmt_combo); fmt_row.addStretch()
        v.addLayout(fmt_row)

        dest_row = QHBoxLayout(); dest_row.setSpacing(8)
        dest_row.addWidget(QLabel(T("Dossier :"), styleSheet=f"color:{TEXTM};font-size:10px;"))
        dl_dest = [os.path.expanduser("~/Downloads")]
        dest_lbl = QLabel(dl_dest[0])
        dest_lbl.setStyleSheet(f"color:{TEXTD};font-size:9px;")
        dest_btn = QPushButton(T("Changer"))
        dest_btn.setStyleSheet(
            f"QPushButton{{background:{PANEL};color:{TEXTM};border:1px solid {BORDER};"
            f"border-radius:4px;font-size:9px;padding:4px 8px;}}"
            f"QPushButton:hover{{background:{PANEL2};color:{TEXT};}}")
        dest_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        def choose_dest():
            folder = QFileDialog.getExistingDirectory(d, "Choisir le dossier")
            if folder:
                dl_dest[0] = folder
                dest_lbl.setText(folder)
        dest_btn.clicked.connect(choose_dest)
        dest_row.addWidget(dest_lbl, 1); dest_row.addWidget(dest_btn)
        v.addLayout(dest_row)

        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color:{BORDER};"); v.addWidget(sep)

        dl_btn = QPushButton(T("Télécharger"))
        dl_btn.setStyleSheet(
            f"QPushButton{{background:{ACCENT};color:#000;font-weight:bold;border:none;"
            f"padding:11px;font-size:12px;border-radius:5px;}}"
            f"QPushButton:hover{{background:{ACCENT2};}}"
            f"QPushButton:disabled{{background:{PANEL};color:{TEXTD};}}")
        dl_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_dl_btn = QPushButton(T("Annuler"))
        cancel_dl_btn.setStyleSheet(
            f"QPushButton{{background:{PANEL};color:{TEXTM};border:1px solid {BORDER};"
            f"padding:11px;font-size:12px;border-radius:5px;}}"
            f"QPushButton:hover{{background:{PANEL2};color:{TEXT};}}"
            f"QPushButton:disabled{{color:{TEXTD};}}")
        cancel_dl_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_dl_btn.setEnabled(False)
        dl_row = QHBoxLayout()
        dl_row.setSpacing(8)
        dl_row.addWidget(cancel_dl_btn)
        dl_row.addWidget(dl_btn, 1)
        v.addLayout(dl_row)

        status_lbl = QLabel("")
        status_lbl.setStyleSheet(f"color:{TEXTD};font-size:9px;")
        v.addWidget(status_lbl)

        # Etat du worker en cours
        self._dl_worker_ref = [None]

        # Détecter ffmpeg une seule fois, en dehors du slot
        import sys as _sys_dl
        _exe_dir = os.path.dirname(_sys_dl.executable)
        _ffmpeg_candidates = [
            os.path.join(_exe_dir, "ffmpeg"),
            os.path.join(os.path.dirname(_exe_dir), "MacOS", "ffmpeg"),
            os.path.join(os.path.dirname(_exe_dir), "Resources", "ffmpeg"),
            "/opt/homebrew/bin/ffmpeg",
            "/usr/local/bin/ffmpeg",
            "/usr/bin/ffmpeg",
        ]
        _found_ffmpeg = next((p for p in _ffmpeg_candidates if os.path.isfile(p)), None)
        _ffmpeg_dir = os.path.dirname(_found_ffmpeg) if _found_ffmpeg else "/opt/homebrew/bin"

        def do_download():
          try:
            url = url_input.text().strip()
            if not url:
                status_lbl.setStyleSheet(f"color:{ERROR};font-size:9px;")
                status_lbl.setText(T("Entre une URL valide"))
                return

            dest = dl_dest[0]
            fmt_idx = fmt_combo.currentIndex()
            tpl = os.path.join(dest, "%(artist)s - %(title)s.%(ext)s")
            worker_opts = None

            if has_ytdlp_module:
                worker_opts = {
                    "outtmpl": tpl,
                    "noplaylist": True,
                    "quiet": True,
                    "no_warnings": True,
                }
                _ffmpeg_loc2 = _ffmpeg_dir
                _sc_cookies = "safari" if "soundcloud.com" in url else None
                if fmt_idx == 0:
                    worker_opts.update({
                        "format": "bestaudio/best",
                        "ffmpeg_location": _ffmpeg_loc2,
                        "writethumbnail": True,
                        "cookiesfrombrowser": (_sc_cookies, None, None, None) if _sc_cookies else None,
                        "postprocessors": [
                            {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "0"},
                            {"key": "EmbedThumbnail"},
                            {"key": "FFmpegMetadata"},
                        ],
                    })
                else:
                    worker_opts.update({
                        "format": "bestaudio/best",
                        "ffmpeg_location": _ffmpeg_loc2,
                        "cookiesfrombrowser": (_sc_cookies, None, None, None) if _sc_cookies else None,
                        "postprocessors": [{"key": "FFmpegMetadata"}],
                    })
                # Retirer les None
                worker_opts = {k: v for k, v in worker_opts.items() if v is not None}
                cmd = None
            else:
                _ffmpeg_loc = _ffmpeg_dir
                # SoundCloud nécessite les cookies du navigateur
                _sc_extra = ["--cookies-from-browser", "safari"] if "soundcloud.com" in url else []
                if fmt_idx == 0:
                    cmd = [ytdlp, "-x", "--audio-format", "mp3", "--audio-quality", "0",
                           "--ffmpeg-location", _ffmpeg_loc,
                           "-o", tpl, "--no-playlist", "--embed-thumbnail", "--add-metadata",
                           *_sc_extra, url]
                else:
                    cmd = [ytdlp, "-f", "bestaudio",
                           "--ffmpeg-location", _ffmpeg_loc,
                           "-o", tpl, "--no-playlist", "--add-metadata",
                           *_sc_extra, url]

            before_set = set(
                os.path.join(dest, f) for f in os.listdir(dest)
                if f.lower().endswith((".mp3", ".flac", ".m4a", ".aac", ".wav", ".opus", ".webm", ".ogg", ".oga"))
            ) if os.path.isdir(dest) else set()

            dl_btn.setEnabled(False)
            dl_btn.setText(T("Téléchargement..."))
            cancel_dl_btn.setEnabled(True)
            status_lbl.setStyleSheet(f"color:{ACCENT};font-size:9px;")
            status_lbl.setText(T("Téléchargement en cours..."))

            worker = DlWorker(cmd, dest, before_set, url=url, ytdlp_opts=worker_opts)
            self._dl_worker_ref[0] = worker

            def on_success(path):
                status_lbl.setStyleSheet(f"color:{ACCENT};font-size:9px;")
                status_lbl.setText(f"✓ {os.path.basename(path)}")
                dl_btn.setText(T("Télécharger"))
                dl_btn.setEnabled(True)
                cancel_dl_btn.setEnabled(False)
                if path not in self.files:
                    self.files.append(path)
                    self._add_row(path)
                    self._update_count()
                subprocess.run(["mdimport", path], capture_output=True)
                self._flash(f"Téléchargé : {os.path.basename(path)}")
                QTimer.singleShot(200, lambda: self._on_row_select(self.rows[-1]))

            def on_error(msg):
                if "ERROR" in msg:
                    msg = msg[msg.rfind("ERROR"):][:150]
                status_lbl.setStyleSheet(f"color:{ERROR};font-size:9px;")
                status_lbl.setText(f"Erreur : {msg}")
                dl_btn.setText(T("Réessayer"))
                dl_btn.setEnabled(True)
                cancel_dl_btn.setEnabled(False)

            worker.success.connect(on_success)
            worker.error.connect(on_error)
            self._workers.append(worker)
            worker.start()
          except Exception as _e:
            status_lbl.setStyleSheet(f"color:{ERROR};font-size:9px;")
            status_lbl.setText(f"Erreur : {str(_e)[:120]}")
            dl_btn.setText(T("Réessayer"))
            dl_btn.setEnabled(True)

        dl_btn.clicked.connect(do_download)
        def cancel_download():
            worker = self._dl_worker_ref[0]
            if worker:
                cancel_dl_btn.setEnabled(False)
                status_lbl.setStyleSheet(f"color:{TEXTD};font-size:9px;")
                status_lbl.setText(T("Annulation en cours..."))
                worker.cancel()
        cancel_dl_btn.clicked.connect(cancel_download)
        url_input.returnPressed.connect(
            lambda: do_download() if dl_btn.isEnabled() else None)

        # Echap ferme, Entrée lance DL, on bloque la propagation vers la fenêtre principale
        orig_key = d.keyPressEvent
        def dlg_key(event):
            if event.key() == Qt.Key.Key_Escape:
                d.reject()
            elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                if dl_btn.isEnabled():
                    do_download()
            else:
                orig_key(event)
        d.keyPressEvent = dlg_key

        # Changer format remet le bouton
        def on_fmt_change(_):
            if dl_btn.isEnabled():
                status_lbl.setText("")
        fmt_combo.currentIndexChanged.connect(on_fmt_change)

        url_input.setFocus()
        d.exec()

    def _on_dl_error(self, err, btn):
        pass  # géré dans le worker

    def _flash(self,msg,err=False):
        self.status_lbl.setStyleSheet(f"color:{ERROR if err else ACCENT};font-size:10px;margin-top:6px;")
        self.status_lbl.setText(msg)
        QTimer.singleShot(4000,lambda:self.status_lbl.setText(""))



# ── Entrypoint ────────────────────────────────────────────────────────────────

APP_VERSION = "3.1"

def _handle_cli_args(argv):
    args = set(argv[1:])
    if not args:
        return False
    if args & {"-h", "--help"}:
        print("Tagr - Audio Metadata Editor")
        print("Usage: tagr.py [--version] [--health-check]")
        return True
    if "--version" in args:
        print(f"Tagr {APP_VERSION}")
        return True
    if "--health-check" in args:
        print("Tagr health check OK")
        return True
    return False


if __name__=="__main__":
    if _handle_cli_args(sys.argv):
        sys.exit(0)
    app=QApplication(sys.argv); app.setStyle("Fusion")
    win=Tagr(); win.show(); sys.exit(app.exec())
