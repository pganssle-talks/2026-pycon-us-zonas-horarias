<div class="bullet-container big-code">
<div class=bullets-with-header">

# ¿Por qué narices necesitamos zonas horarias?


```python
from dateutil import rrule as rr
from datetime import datetime, UTC
from zoneinfo import ZoneInfo

# Fin de jornada en Nueva York
horas_de_cerrar = rr.rrule(freq=rr.DAILY, byweekday=(rr.MO, rr.TU, rr.WE, rr.TH, rr.FR),
                           byhour=17, dtstart=datetime(2023, 3, 8, 17), count=5)

NYC = ZoneInfo("America/New_York")
```

<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1em; align-items: start;">

<div>

```python
for dt in horas_de_cerrar:
    print(dt.replace(tzinfo=NYC))
```

<pre><tt>2023-03-08 17:00:00-05:00
2023-03-09 17:00:00-05:00
2023-03-10 17:00:00<b>-05:00</b>
2023-03-13 17:00:00<b>-04:00</b>
2023-03-14 17:00:00-04:00</tt></pre>

</div>

<div>

```python
# Obtener fin de jornada en UTC
for dt in horas_de_cerrar:
    print(dt.replace(tzinfo=NYC).astimezone(UTC))
```

<pre><tt>2023-03-08 22:00:00+00:00
2023-03-09 22:00:00+00:00
2023-03-10 <b>22:00:00</b>+00:00
2023-03-13 <b>21:00:00</b>+00:00
2023-03-14 21:00:00+00:00</tt></pre>

</div>

</div>
</div>

</div>

Notes:

Vale, ya os he metido un poco de miedo, y quizás os preguntéis: "Ostras, menudo follón, ¿no podemos usar UTC para todo?"

Y la respuesta es que no, no podéis, porque el UTC no es una abstracción natural para la mayor parte del mundo. La gente organiza su vida según la posición del sol.

Así que, en el mundo real, si quieres representar la hora que marca el reloj de pared, hay que utilizar una abstracción que capture el tiempo tal y como se observa.

Si quieres representar el fin de jornada en Nueva York, es jarto conveniente hacerlo con una regla que diga "de lunes a viernes a las cinco", en lugar de algo que gire en torno al UTC, donde a veces son las veintidós y otras las veintiuno.

[1m 15s; T: 10m 15s]

--

<style>
.egypt-panel {
  display: grid;
  grid-template-columns: 1fr 1.5fr 1fr;
  gap: 0.5em 1.5em;
  width: 95%;
  margin: 0 auto;
}
.egypt-panel .egypt-date {
  text-align: center;
  font-size: 0.9em;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #333;
  padding-bottom: 0.5em;
  border-bottom: 1px solid #666;
}
.egypt-panel .egypt-cell {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0.5em 0.25em;
}
.egypt-panel .dt-convert {
  font-family: monospace;
  font-size: 0.72em;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.3em;
}
.egypt-panel .tz-arrow-wrap {
  position: relative;
  width: 100%;
  min-height: 1.1em;
  display: flex;
  justify-content: center;
  align-items: center;
}
.egypt-panel .tz-arrow-wrap::before {
  content: '';
  position: absolute;
  left: 50%;
  top: 0;
  transform: translateX(-50%);
  width: 3px;
  height: calc(100% - 15px);
  background: rgba(0, 0, 0, 0.6);
}
.egypt-panel .tz-arrow-wrap::after {
  content: '';
  position: absolute;
  left: 50%;
  bottom: 0;
  transform: translateX(-50%);
  width: 0;
  height: 0;
  border-left: 10px solid transparent;
  border-right: 10px solid transparent;
  border-top: 15px solid rgba(0, 0, 0, 0.6);
}
.egypt-panel .tz-label {
  position: relative;
  z-index: 1;
  background: var(--r-background-color, #fff);
  border: 1px solid #999;
  border-radius: 0.25em;
  margin-bottom: 1.25em;
  margin-top: 0.5em;
  padding: 0.05em 0.5em;
  font-size: 0.85em;
  white-space: nowrap;
}

.egypt-panel .tz-arrow-wrap.up {
    .tz-label {
        margin-bottom: 0.5em;
        margin-top: 1.25em;
    }
}

.egypt-panel .tz-arrow-wrap.up::before {
  top: 15px;
  height: calc(100% - 15px);
}
.egypt-panel .tz-arrow-wrap.up::after {
  top: 0;
  bottom: auto;
  border-left: 7px solid transparent;
  border-right: 7px solid transparent;
  border-bottom: 15px solid rgba(0, 0, 0, 0.6);
  border-top: none;
}
.egypt-panel .db-icon {
  position: relative;
  width: 3.5em;
  height: 2.2em;
  margin: 0.1em auto;
}
.egypt-panel .db-icon::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 0.65em;
  background: #b4cce0;
  border: 2px solid #5a7a9a;
  border-radius: 50%;
  z-index: 1;
}
.egypt-panel .db-icon::after {
  content: '';
  position: absolute;
  top: 0.32em;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(to right, #8aaccc 0%, #b4cce0 50%, #8aaccc 100%);
  border: 2px solid #5a7a9a;
  border-top: none;
  border-bottom-left-radius: 50% 35%;
  border-bottom-right-radius: 50% 35%;
}
.egypt-panel .egypt-cell img {
  max-width: 100%;
  object-fit: contain;
  padding: 0.5em;
}
</style>

<div class="bullet-container">
<div class="bullets-with-header">
<div class="egypt-panel">
  <div class="egypt-date">01 Julio 2016</div>
  <div class="egypt-date">04 Julio 2016</div>
  <div class="egypt-date">09 Julio 2016</div>
  <div class="egypt-cell">
    <div class="dt-convert">
      <span>2016-07-09 <span class="fragment highlight-current-fragment" data-fragment-index="1">13:00:00 EEST</span></span>
      <div class="tz-arrow-wrap"><span class="tz-label">Africa/Cairo</span></div>
      <span>2016-07-09 10:00:00 UTC</span>
      <div class="tz-arrow-wrap"></div>
      <div class="db-icon"></div>
    </div>
  </div>
  <div class="egypt-cell">
    <img
        src="images/egipto_noticias.png"
        alt="Egipto canceló el horario de verano tres días antes de su entrada en vigor"/>
  </div>
  <div class="egypt-cell">
    <div class="dt-convert">
      <span>2016-07-09 <span class="fragment highlight-current-fragment" data-fragment-index="1">14:00:00 EET</span></span>
      <div class="tz-arrow-wrap up"><span class="tz-label">Africa/Cairo</span></div>
      <span>2016-07-09 10:00:00 UTC</span>
      <div class="tz-arrow-wrap up"></div>
      <div class="db-icon"></div>
    </div>
  </div>
</div>
<div class="small-spacer"></div>
<p style="font-size: 1.25em; text-align: center; margin-top: 0.75em;">
Cuando guardas objetos datetime y lo que importa es la <em>hora de reloj</em>, hay que guardar el tiempo local, porque el mapeo entre UTC y el tiempo local <em>no es estable</em>.
</p>
</div>

</div>

Notes:

Y podéis pensar: "Bueno, seguro que tenemos que manejar zonas horarias al tratar con *humanos*, pero ¿podemos al menos *guardar* los datetimes en UTC, y evitar todo el tinglado?".

Y siento ser otra vez el pájaro de mal agüero, pero tampoco podéis, porque eso no funciona cuando lo que importa es la hora local.

Si programas una reunión a la una en el futuro y, antes de la cita, el desplazamiento cambia (lo cual pasa todo el rato, y muchas veces sin mucho aviso), seguro que quieres mantener la reunión a la una, pero si has guardado el `datetime` en UTC antes del cambio, ➡️ cuando lo saques después, lo que sale no será correcto. El mapeo entre la hora local y UTC no es estable, así que has perdido la información que te importaba.

Dicho de otro modo: tienes que usar la abstracción que mejor represente tu situación; si lo que importa es la hora local, guarda la hora local.

[1m; T: 11m 15s]

--

<!-- .slide: data-visibility="hidden" -->

<p style="text-align: center">
<img src="images/lebanon_news.png" alt="Lebanon wakes up in two time zones because of daylight savings spat — a news article from reuters about Lebanon changing their time zone at the last minute."
/>

</p>

<p style="text-align: center">
<img src="images/timing_of_timezone_changes.png" alt="A screenshot of the opening paragraph of Matt Johnson-Pint's 'On the Timing of Time Zone Changes'"
/>
</p>

<span><em>Further Reading:</em> 
<a href="https://codeofmatt.com/on-the-timing-of-time-zone-changes/">On the Timing of Time Zone Changes</a>, <a href="https://codeofmatt.com/time-zone-chaos-inevitable-in-egypt/">Time Zone Chaos Inevitable in Egypt</a></span>
