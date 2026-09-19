#!/usr/bin/env bash
set -euo pipefail

REPO="BrunoCunha1983-creator/ha_apps"
BRANCH="${PORTUGAL_FOOTBALL_BRANCH:-main}"
CONFIG_DIR="${HA_CONFIG_DIR:-/config}"
TMP_DIR="$(mktemp -d)"
ZIP_FILE="$TMP_DIR/repo.zip"

cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

echo "== Portugal Football installer =="
echo "Repository: $REPO ($BRANCH)"
echo "Home Assistant config: $CONFIG_DIR"

if command -v curl >/dev/null 2>&1; then
  curl -fsSL "https://github.com/$REPO/archive/refs/heads/$BRANCH.zip" -o "$ZIP_FILE"
elif command -v wget >/dev/null 2>&1; then
  wget -q "https://github.com/$REPO/archive/refs/heads/$BRANCH.zip" -O "$ZIP_FILE"
else
  echo "ERRO: é necessário curl ou wget."
  exit 1
fi

if ! command -v unzip >/dev/null 2>&1; then
  echo "ERRO: é necessário unzip."
  exit 1
fi

unzip -q "$ZIP_FILE" -d "$TMP_DIR"
SRC_ROOT="$TMP_DIR/ha_apps-$BRANCH"

if [ ! -d "$SRC_ROOT" ]; then
  SRC_ROOT="$(find "$TMP_DIR" -maxdepth 1 -type d -name 'ha_apps-*' | head -n1)"
fi

INTEGRATION_SRC="$SRC_ROOT/integrations/portugal_football/custom_components/portugal_football"
CARD_SRC="$SRC_ROOT/cards/portugal_football/portugal-football-card.js"

if [ ! -d "$INTEGRATION_SRC" ] || [ ! -f "$CARD_SRC" ]; then
  echo "ERRO: ficheiros Portugal Football não encontrados no ramo $BRANCH."
  exit 1
fi

mkdir -p "$CONFIG_DIR/custom_components"
rm -rf "$CONFIG_DIR/custom_components/portugal_football"
cp -R "$INTEGRATION_SRC" "$CONFIG_DIR/custom_components/portugal_football"

mkdir -p "$CONFIG_DIR/www/community/portugal_football"
cp "$CARD_SRC" "$CONFIG_DIR/www/community/portugal_football/portugal-football-card.js"

echo
echo "INSTALAÇÃO CONCLUÍDA."
echo
echo "1) Reinicia o Home Assistant."
echo "2) Definições -> Dispositivos e Serviços -> Adicionar integração -> Portugal Football"
echo "3) Introduz a API Key do football-data.org."
echo "4) Em Definições -> Dashboards -> Recursos adiciona:"
echo "   /local/community/portugal_football/portugal-football-card.js"
echo "   Tipo: JavaScript Module"
echo
echo "Exemplo de card:"
echo "type: custom:portugal-football-card"
echo "view: table"
