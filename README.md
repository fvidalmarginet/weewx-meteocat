# weewx-meteocat

Predicció meteorològica del **Meteocat** dissenyada específicament com un giny (widget) ultra ràpid per integrar fàcilment a les plantilles de **WeeWX**.

## Característiques

*   **Rendiment instantani (Ultra ràpid)**: El giny no fa crides a APIs externes des del navegador del client. Simplement carrega de forma asíncrona un fitxer estàtic local `forecast.json` de menys d'1 KB que es troba al mateix servidor.
*   **Icones professionals**: Utilitza la llibreria [Weather Icons](https://github.com/erikflowers/weather-icons) descarregada completament de forma local (al teu propi servidor) per evitar dependències o CDNs externs.
*   **Disseny modern i adaptatiu (Responsive)**: S'ajusta automàticament a pantalles de mòbils, tauletes o ordinadors.
*   **Completament en català**: Noms de dies, mesos i descripcions meteorològiques adaptades de forma nativa.

---

## Estructura real del desplegament

```text
Servidor Linux / GCP
├── /opt/weewx-meteocat/fetch_meteocat.py    # Script de descàrrega de Meteocat
├── /var/www/html/weewx/meteocat/            # Directori públic del widget
│   ├── index.html                           # Pàgina del widget
│   ├── meteocat.css                         # Estils del widget
│   ├── forecast.json                        # JSON generat per l'script
│   └── weather-icons/                       # Llibreria Weather Icons local
│       ├── css/
│       └── font/
├── /etc/weewx/skins/Seasons_extended/       # Skin de WeeWX
│   └── meteocat-custom.inc                  # Include que carrega /meteocat/
└── README.md                                # Documentació del projecte
```

---

## Com funciona l'arquitectura real

La implementació real no posa el script dins la skin ni dins el directori del tema. La part útil es separa en tres capes:

```mermaid
graph TD
    Cron[Cron cada dia a les 09:00] -->|Executa| PyScript[/opt/weewx-meteocat/fetch_meteocat.py]
    PyScript -->|Crida API| MeteocatAPI[API Oficial del Meteocat]
    MeteocatAPI -->|Retorna predicció| PyScript
    PyScript -->|Genera i desa| JSON[/var/www/html/weewx/meteocat/forecast.json]

    Browser[Navegador del client] -->|Carrega /meteocat/| Web[/var/www/html/weewx/meteocat/index.html]
    Web -->|Llegeix JSON local| JSON
    WeeWXSkin[/etc/weewx/skins/Seasons_extended/meteocat-custom.inc] -->|Inclou iframe| Browser
```

Aquesta separació és important perquè la skin de WeeWX no executa Python, i la web pública del servidor només serveix el widget estàtic i el JSON ja generat.

---

## Guia d'Instal·lació i Integració

### 1. Posar el script fora de la skin

La part de Python no va dins `Seasons_extended`. El lloc correcte és un directori de serveis, per exemple:

```bash
sudo mkdir -p /opt/weewx-meteocat
sudo cp /home/vidalmarginet/fetch_meteocat.py /opt/weewx-meteocat/fetch_meteocat.py
sudo chmod 755 /opt/weewx-meteocat/fetch_meteocat.py
```

Això evita barrejar lògica de descàrrega amb els fitxers de la skin.

### 2. Preparar el directori públic del widget

Copia el contingut de `prototype/` al directori web públic:

```bash
sudo mkdir -p /var/www/html/weewx/meteocat
sudo cp -r /home/vidalmarginet/weewx-meteocat/prototype/* /var/www/html/weewx/meteocat/
```

La ruta final ha de quedar així:

```text
/var/www/html/weewx/meteocat/
├── index.html
├── meteocat.css
├── forecast.json
├── weather-icons/
```

### 3. Generar el JSON real de Meteocat

Executa el script sobre la clau real:

```bash
export METEOCAT_API_KEY="OOk3ltNTYf3s892NwNi6kaGw6ablvVoZ5EPiJU9K"
python3 /opt/weewx-meteocat/fetch_meteocat.py \
  --municipi "080193" \
  --nom "Barcelona" \
  --output /var/www/html/weewx/meteocat/forecast.json
```

Verifica-ho:

```bash
cat /var/www/html/weewx/meteocat/forecast.json | head
```

### 4. Configurar cron a les 9:00

```bash
crontab -e
```

Afegeix:

```text
00 9 * * * export METEOCAT_API_KEY="OOk3ltNTYf3s892NwNi6kaGw6ablvVoZ5EPiJU9K" && /usr/bin/python3 /opt/weewx-meteocat/fetch_meteocat.py --municipi "080193" --nom "Barcelona" --output /var/www/html/weewx/meteocat/forecast.json > /dev/null 2>&1
```

---

## Integració del giny a la skin de WeeWX

### Fitxer include
Crea aquest fitxer dins la skin:

```bash
sudo nano /etc/weewx/skins/Seasons_extended/meteocat-custom.inc
```

Contingut:

```html
<!-- Giny meteorològic propi -->
<div class="meteocat-custom-widget">
    <iframe
        src="/meteocat/"
        title="Predicció meteorològica"
        width="100%"
        height="360"
        frameborder="0"
        loading="lazy"
        style="border:0; display:block;">
    </iframe>
</div>
```

### Incloure-ho a la plantilla
A la teva plantilla WeeWX, on vulguis mostrar-ho:

```html
#include $Extras.meteocat-custom.inc
```

O bé:

```html
#include ./meteocat-custom.inc
```

### Reinici
```bash
sudo systemctl restart weewx
```

---

## Notes de desplegament reals

- El script de Meteocat no va dins la skin de WeeWX.
- El widget es serveix com a pàgina HTML estàtica a `/var/www/html/weewx/meteocat/`.
- La skin només l’inclou mitjançant un `<iframe>`.
- El JSON es genera un cop al dia i la web de la pàgina es carrega ràpidament i sense crides externes des del navegador.

---

## Integració del Giny a la teva plantilla WeeWX

Pots incrustar aquest giny a qualsevol lloc de la teva pàgina web existent de dues maneres molt senzilles:

### Opció A: Mitjançant un `<iframe>` (Recomanat per la simplicitat)
Incrusta la predicció directament en qualsevol pàgina de WeeWX:
```html
<iframe src="index.html" style="width: 100%; height: 280px; border: none; overflow: hidden;" scrolling="no"></iframe>
```

### Opció B: Integració directa en HTML (Inline)
1. Afegeix les fulles d'estil a la capçalera (`<head>`) de la teva plantilla:
   ```html
   <link rel="stylesheet" href="weather-icons/css/weather-icons.min.css">
   <link rel="stylesheet" href="meteocat.css">
   ```
2. Copia l'estructura de contenidors en qualsevol part del cos (`<body>`):
   ```html
   <div class="weather-widget">
       <div class="widget-header">
           <div>
               <div class="widget-title">Predicció meteorològica</div>
               <div class="widget-location" id="widget-location">Cargant...</div>
           </div>
           <div class="widget-source">Meteocat</div>
       </div>
       <div class="forecast" id="forecast-container"></div>
       <div class="widget-footer">
           <span>Predicció per als propers 8 dies</span>
           <span id="updated-at">...</span>
       </div>
   </div>
   ```
3. Afegeix el script asíncron JavaScript al final de la pàgina per carregar les dades des del teu `forecast.json` local.
