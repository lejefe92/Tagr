#!/bin/bash
set -e

# ── Config ────────────────────────────────────────────────────────────────────
APP_NAME="Tagr"
SRC="$HOME/Documents/Tagr/src/tagr.py"
SPEC="$HOME/Documents/Tagr/Tagr.spec"
DIST="$HOME/Documents/Tagr/dist"
ICON="$HOME/Documents/Tagr/assets/Tagr.icns"
ENV="$HOME/tagdrop-env312"

echo "▶ Activation de l'environnement virtuel..."
source "$ENV/bin/activate"

echo "▶ Installation / mise à jour de PyInstaller..."
pip install pyinstaller --quiet --quiet
pip install -r "$HOME/Documents/Tagr/requirements.txt" --quiet --quiet

echo "▶ Nettoyage des builds précédents..."
rm -rf "$HOME/Documents/Tagr/build" "$DIST"

echo "▶ Build de $APP_NAME.app..."
pyinstaller "$SPEC" \
    --distpath "$DIST" \
    --workpath "$HOME/Documents/Tagr/build" \
    --noconfirm

echo "▶ Vérification..."
if [ -d "$DIST/$APP_NAME.app" ]; then
    echo "✅ Build réussi : $DIST/$APP_NAME.app"
    echo "▶ Copie sur le Bureau..."
    rm -rf "$HOME/Desktop/$APP_NAME.app"
    cp -r "$DIST/$APP_NAME.app" "$HOME/Desktop/$APP_NAME.app"
    echo "✅ Tagr.app disponible sur le Bureau"
else
    echo "❌ Build échoué — vérifie les erreurs ci-dessus"
    exit 1
fi
