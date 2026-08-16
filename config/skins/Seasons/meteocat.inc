<div class="meteocat-forecast">
  <h3>Predicció Municipal (Meteocat)</h3>
  <p><small>Actualitzat: $meteocat.updatedAt</small></p>
  <div class="forecast-days" style="display: flex; gap: 15px;">
    #for $day in $meteocat.forecast
    <div class="forecast-day" style="text-align: center; border: 1px solid #ccc; padding: 10px; border-radius: 5px;">
      <h4>$day.date</h4>
      <i class="wi $day.icon_class" style="font-size: 2em;"></i>
      <p><strong>Max:</strong> $day.max_tempºC</p>
      <p><strong>Min:</strong> $day.min_tempºC</p>
      <p><strong>Pluja:</strong> $day.rain_percent%</p>
    </div>
    #end for
  </div>
</div>