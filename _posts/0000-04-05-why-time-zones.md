# ¿Por qué narices necesitamos zonas horarias?

<div class="left-container">
<div class="bullet-container medium-code">

```python
from dateutil import rrule as rr
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

# Fin de jornada en Nueva York
horas_de_cerrar = rr.rrule(freq=rr.DAILY, byweekday=(rr.MO, rr.TU, rr.WE, rr.TH, rr.FR),
                           byhour=17, dtstart=datetime(2023, 3, 8, 17), count=5)

NYC = ZoneInfo("America/New_York")
for dt in horas_de_cerrar:
    print(dt.replace(tzinfo=NYC))
```

<pre><tt>2023-03-08 17:00:00-05:00
2023-03-09 17:00:00-05:00
2023-03-10 17:00:00<b>-05:00</b>
2023-03-13 17:00:00<b>-04:00</b>
2023-03-14 17:00:00-04:00</tt></pre>

<div class="small-spacer"></div>

```python
# Obtener fin de jornada en UTC
for dt in horas_de_cerrar:
    print(dt.replace(tzinfo=NYC).astimezone(timezone.utc))
```

<pre><tt>2023-03-08 22:00:00+00:00
2023-03-09 22:00:00+00:00
2023-03-10 <b>22:00:00</b>+00:00
2023-03-13 <b>21:00:00</b>+00:00
2023-03-14 21:00:00+00:00</tt></pre>

</div>
</div>

Notes:

Vale, ya os he metido un poco de miedo, y quizás os preguntéis: ¿por qué tenemos que pelearnos con las zonas horarias? ¿No podemos usar UTC para todo?

Y la respuesta es que no, no podéis, porque el UTC no es una abstracción natural para la mayor parte del mundo. La gente organiza su vida según la posición del sol y a muchos les gusta el horario de verano.

Así que, en el mundo real, si quieres representar la hora que marca el reloj de pared, hay que utilizar una abstracción que capture el tiempo tal y como se observa.

Si quieres representar el fin de jornada en Nueva York, es jarto conveniente hacerlo con una regla que diga "de lunes a viernes a las cinco", en lugar de algo que gire en torno al UTC, donde tienes que andar comprobando cuándo cambia la hora entre las veintidós y las veintiuno.

[1m15s; T:9m15s]

--

<div class="centered-container splash">
<img src="images/egipto_noticias.png"/>
<p style="font-size: 1.25em;">
Cuando guardas objetos datetime y lo que importa es la <em>hora de pared</em>, hay que almacenar el tiempo local, porque el mapeo entre UTC y el tiempo local <em>no es estable</em>.
</p>
</div>

Notes:

Y podéis pensar: "Bueno, seguro que tenemos que manejar zonas horarias al tratar con humanos, pero ¿podemos al menos *guardar* los datetimes en UTC para evitar todo el tinglado?".

Y siento ser otra vez el pájaro de mal agüero, pero tampoco podéis, porque no funciona cuando lo que importa es la hora de reloj.

El problema es que el mapeo entre la hora local y el UTC no es estable; por eso, para fechas futuras, si guardas el datetime en UTC y el mapeo cambia (lo cual pasa a menudo y con poco aviso), habrás perdido la información que te importaba: la hora local.

Si tienes una reunión a la una, no te importa la hora en UTC; y si el desplazamiento para ese día cambia, seguro que quieres mantener la hora original. Por eso, si lo que te importa es la hora en una zona concreta, tienes que guardar esa hora.

En resumen: lo que tenéis que buscar es la abstracción que mejor represente el concepto que queréis capturar.

[1m; T: 10m15s]

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
