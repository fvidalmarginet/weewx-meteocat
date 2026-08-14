# Script de desplegament per al giny meteorològic Meteocat a WeeWX (Windows)
#
# Ús:
#   .\deploy-weewx.ps1 -SSHTarget "vidalmarginet@mcvm" -WeewxPath "/var/www/html/weewx/meteocat" -SkinPath "/etc/weewx/skins/Seasons_extended" -ApiKey "your-key"
#
# Exemples:
#   $env:METEOCAT_API_KEY = "OOk3ltNTYf3s892NwNi6kaGw6ablvVoZ5EPiJU9K"
#   .\deploy-weewx.ps1 -SSHTarget "vidalmarginet@mcvm"
#

param(
    [string]$SSHTarget = "vidalmarginet@mcvm",
    [string]$WeewxPath = "/var/www/html/weewx/meteocat",
    [string]$SkinPath = "/etc/weewx/skins/Seasons_extended",
    [string]$ApiKey = $env:METEOCAT_API_KEY,
    [string]$Municipi = "080193",
    [string]$MunicipiNom = "Barcelona"
)

# Colors
$GREEN = "`e[32m"
$YELLOW = "`e[33m"
$RED = "`e[31m"
$RESET = "`e[0m"

function Write-Status {
    param([string]$Message)
    Write-Host "$YELLOW$Message$RESET"
}

function Write-Success {
    param([string]$Message)
    Write-Host "$GREEN✓ $Message$RESET"
}

function Write-Error {
    param([string]$Message)
    Write-Host "$RED✗ ERROR: $Message$RESET"
}

Write-Host "$GREEN╔════════════════════════════════════════════════════════════════╗$RESET"
Write-Host "$GREEN║          Desplegament del giny Meteocat a WeeWX               ║$RESET"
Write-Host "$GREEN╚════════════════════════════════════════════════════════════════╝$RESET"
Write-Host ""

# Verificar paràmetres
if ([string]::IsNullOrEmpty($ApiKey)) {
    Write-Host "$RED⚠️  AVÍS: No s'ha definit METEOCAT_API_KEY$RESET"
    Write-Host "Defineix la variable d'entorn:"
    Write-Host "`$env:METEOCAT_API_KEY = 'OOk3ltNTYf3s892NwNi6kaGw6ablvVoZ5EPiJU9K'"
    Write-Host "I torna a executar el script."
    exit 1
}

Write-Host "📍 Destinació: $SSHTarget"
Write-Host "🌐 Ruta web: $WeewxPath"
Write-Host "🎨 Skin de WeeWX: $SkinPath"
Write-Host "🗺️  Municipi: $MunicipiNom ($Municipi)"
Write-Host ""

try {
    # 1. Copiar fitxers del giny
    Write-Status "1️⃣  Copiant fitxers al servidor..."
    ssh $SSHTarget "mkdir -p '$WeewxPath'"
    scp -r ./prototype/* "${SSHTarget}:${WeewxPath}/"
    Write-Success "Fitxers copiats"

    # 2. Copiar fitxer d'inclusió al skin
    Write-Status "2️⃣  Copiant meteocat-custom.inc al skin..."
    scp ./meteocat-custom.inc "${SSHTarget}:${SkinPath}/"
    Write-Success "Fitxer d'inclusió copiat"

    # 3. Configurar permisos
    Write-Status "3️⃣  Configurant permisos..."
    ssh $SSHTarget @"
        chmod 755 '$WeewxPath'
        chmod 644 '$WeewxPath'/*.html '$WeewxPath'/*.css '$WeewxPath'/*.json 2>/dev/null || true
        chmod 755 '$WeewxPath'/weather-icons/font/* 2>/dev/null || true
"@
    Write-Success "Permisos configurats"

    # 4. Configurar cron
    Write-Status "4️⃣  Configurant tasca cron (9:00 cada dia)..."
    $cronCmd = "00 9 * * * export METEOCAT_API_KEY='$ApiKey' && /usr/bin/python3 $WeewxPath/fetch_meteocat.py --municipi '$Municipi' --nom '$MunicipiNom' --output $WeewxPath/forecast.json > /dev/null 2>&1"
    
    ssh $SSHTarget @"
        (crontab -l 2>/dev/null || true) | grep -v 'fetch_meteocat.py' | crontab - 2>/dev/null || true
        (crontab -l 2>/dev/null || true; echo '$cronCmd') | crontab -
"@
    Write-Success "Tasca cron configurada"

    # 5. Primer test
    Write-Status "5️⃣  Executant primer test de fetch_meteocat.py..."
    ssh $SSHTarget "export METEOCAT_API_KEY='$ApiKey' && /usr/bin/python3 $WeewxPath/fetch_meteocat.py --municipi '$Municipi' --nom '$MunicipiNom' --output $WeewxPath/forecast.json"
    Write-Success "Test completat"

    # 6. Verificar forecast.json
    Write-Status "6️⃣  Verificant fitxer de dades..."
    $forecastTest = ssh $SSHTarget "test -f '$WeewxPath/forecast.json' && echo 'OK'"
    
    if ($forecastTest -like "*OK*") {
        Write-Success "forecast.json creat correctament"
        Write-Host ""
        Write-Host "$YELLOW Mostra de les primeres línies:$RESET"
        ssh $SSHTarget "head -n 10 '$WeewxPath/forecast.json'"
    } else {
        Write-Error "No s'ha creat forecast.json"
        exit 1
    }

    # Resum final
    Write-Host ""
    Write-Host "$GREEN╔════════════════════════════════════════════════════════════════╗$RESET"
    Write-Host "$GREEN║                ✅ DESPLEGAMENT COMPLETAT!                      ║$RESET"
    Write-Host "$GREEN╚════════════════════════════════════════════════════════════════╝$RESET"
    Write-Host ""
    Write-Host "📍 URL del giny:     http://$SSHTarget/meteocat/"
    Write-Host "📄 Fitxer de dades:  $WeewxPath/forecast.json"
    Write-Host "🔄 Actualitzacions:  Cada dia a les 09:00"
    Write-Host ""
    Write-Host "➕ Per integrar-ho a la teva pàgina, afegeix aquest codi:"
    Write-Host ""
    Write-Host "    #include `$Extras.meteocat_custom_inc"
    Write-Host ""

} catch {
    Write-Error $_.Exception.Message
    exit 1
}
