#!/bin/bash
#
# Script de desplegament per al giny meteorològic Meteocat a WeeWX
# 
# Ús:
#   bash deploy-weewx.sh [usuari@servidor] [ruta_weewx] [ruta_skin]
#
# Exemples:
#   bash deploy-weewx.sh vidalmarginet@mcvm /var/www/html/weewx/meteocat /etc/weewx/skins/Seasons_extended
#   bash deploy-weewx.sh root@192.168.1.100 /home/weewx/public_html/meteocat /etc/weewx/skins/Seasons_extended
#

set -e

# Paràmetres
SSH_TARGET="${1:-vidalmarginet@mcvm}"
WEEWX_WEB_ROOT="${2:-/var/www/html/weewx/meteocat}"
WEEWX_SKIN_DIR="${3:-/etc/weewx/skins/Seasons_extended}"
API_KEY="${METEOCAT_API_KEY:-}"
MUNICIPI="${METEOCAT_MUNICIPI:-080193}"
MUNICIPI_NOM="${METEOCAT_NOM:-Barcelona}"

# Colors per a la sortida
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║          Desplegament del giny Meteocat a WeeWX               ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Verificar paràmetres
if [ -z "$API_KEY" ]; then
    echo -e "${YELLOW}⚠️  Avís: No s'ha definit METEOCAT_API_KEY${NC}"
    echo "Defineix la variable d'entorn:"
    echo "  export METEOCAT_API_KEY='OOk3ltNTYf3s892NwNi6kaGw6ablvVoZ5EPiJU9K'"
    exit 1
fi

echo "📍 Destinació: $SSH_TARGET"
echo "🌐 Ruta web: $WEEWX_WEB_ROOT"
echo "🎨 Skin de WeeWX: $WEEWX_SKIN_DIR"
echo "🗺️  Municipi: $MUNICIPI_NOM ($MUNICIPI)"
echo ""

# 1. Copiar fitxers del giny
echo -e "${YELLOW}1️⃣  Copiant fitxers al servidor...${NC}"
ssh "$SSH_TARGET" "mkdir -p '$WEEWX_WEB_ROOT'"
scp -r ./prototype/* "$SSH_TARGET:$WEEWX_WEB_ROOT/"
echo -e "${GREEN}✓ Fitxers copiats${NC}"

# 2. Copiar fitxer d'inclusió al skin
echo -e "${YELLOW}2️⃣  Copiant meteocat-custom.inc al skin...${NC}"
scp ./meteocat-custom.inc "$SSH_TARGET:$WEEWX_SKIN_DIR/"
echo -e "${GREEN}✓ Fitxer d'inclusió copiat${NC}"

# 3. Configurar permisos
echo -e "${YELLOW}3️⃣  Configurant permisos...${NC}"
ssh "$SSH_TARGET" "chmod 755 '$WEEWX_WEB_ROOT' && chmod 644 '$WEEWX_WEB_ROOT'/*.{html,css,json} && chmod 755 '$WEEWX_WEB_ROOT'/weather-icons/font/*"
echo -e "${GREEN}✓ Permisos configurats${NC}"

# 4. Configurar cron per a actualització diària
echo -e "${YELLOW}4️⃣  Configurant tasca cron (9:00 cada dia)...${NC}"
CRON_CMD="00 9 * * * export METEOCAT_API_KEY='$API_KEY' && /usr/bin/python3 $WEEWX_WEB_ROOT/fetch_meteocat.py --municipi '$MUNICIPI' --nom '$MUNICIPI_NOM' --output $WEEWX_WEB_ROOT/forecast.json > /dev/null 2>&1"

ssh "$SSH_TARGET" "
    (crontab -l 2>/dev/null || true) | grep -v 'fetch_meteocat.py' | crontab -
    (crontab -l 2>/dev/null || true; echo '$CRON_CMD') | crontab -
"
echo -e "${GREEN}✓ Tasca cron configurada${NC}"

# 5. Primer test de l'script
echo -e "${YELLOW}5️⃣  Executant primer test de fetch_meteocat.py...${NC}"
ssh "$SSH_TARGET" "export METEOCAT_API_KEY='$API_KEY' && /usr/bin/python3 $WEEWX_WEB_ROOT/fetch_meteocat.py --municipi '$MUNICIPI' --nom '$MUNICIPI_NOM' --output $WEEWX_WEB_ROOT/forecast.json"
echo -e "${GREEN}✓ Test completat${NC}"

# 6. Verificar que forecast.json existeix
echo -e "${YELLOW}6️⃣  Verificant fitxer de dades...${NC}"
if ssh "$SSH_TARGET" "test -f '$WEEWX_WEB_ROOT/forecast.json'"; then
    echo -e "${GREEN}✓ forecast.json creat correctament${NC}"
    echo ""
    echo -e "${YELLOW}Mostra de les primeres línies:${NC}"
    ssh "$SSH_TARGET" "head -n 10 '$WEEWX_WEB_ROOT/forecast.json'"
else
    echo -e "${RED}✗ ERROR: No s'ha creat forecast.json${NC}"
    exit 1
fi

# Resum final
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                ✅ DESPLEGAMENT COMPLETAT!                      ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "📍 URL del giny:     http://$(ssh "$SSH_TARGET" "hostname -f")/meteocat/"
echo "📄 Fitxer de dades:  $WEEWX_WEB_ROOT/forecast.json"
echo "🔄 Actualitzacions:  Cada dia a les 09:00"
echo ""
echo "➕ Per integrar-ho a la teva pàgina, afegeix aquest codi a la teva plantilla:"
echo ""
echo "    #include \$Extras.meteocat_custom_inc"
echo ""
echo "O si la teva plantilla ja importa personalizacions:"
echo ""
echo "    #include ./meteocat-custom.inc"
echo ""
