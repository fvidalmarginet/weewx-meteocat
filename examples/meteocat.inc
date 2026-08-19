<div id="meteocat_widget" class="widget">
  <div class="widget_title">
    Predicció meteorològica
    <a class="widget_control" onclick="toggle_widget('meteocat')">&diams;</a>
  </div>
  <div class="widget_contents">
    <section class="meteocat-widget" aria-label="Predicció meteorològica">
      <header class="meteocat-header">
        <div class="meteocat-source">METEOCAT</div>
        <h3>Predicció municipal</h3>
      </header>
  <div class="meteocat-forecast">
    #for $day in $meteocat.forecast
    #set $day_class = "meteocat-day"
    #if $day.day_name == "AVUI"
      #set $day_class = "meteocat-day meteocat-day-today"
    #end if
    <article class="$day_class">
      <div class="meteocat-day-name">$day.day_name</div>
      <div class="meteocat-date">$day.date</div>
      <img src="weather-icons/$day.icon_class" alt="$day.sky_code" width="56" height="48" />
      <div class="meteocat-temperatures"><strong>$day.max_temp&#176;</strong><span>$day.min_temp&#176;</span></div>
      <div class="meteocat-description">$day.description</div>
      <div class="meteocat-rain">Pluja $day.rain_percent%</div>
    </article>
    #end for
  </div>
      <footer class="meteocat-footer">Actualitzat: $meteocat.updatedAt</footer>
    </section>
  </div>
</div>