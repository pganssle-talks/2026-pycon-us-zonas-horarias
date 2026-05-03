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

Vale, así que ya os he dado un poco de miedo, y quizás os preguntéis: ¿por qué tenemos que trabajar con zonas horarias en absoluto? ¿No podemos usar UTC para todo?

Y la respuesta es que no, no puedes, porque el UTC no es una abstracción natural para la mayor parte del mundo. Porque la gente organiza sus vidas según las horas en que el sol está en lo más alto, y en muchas ubicaciones les gusta el horario de verano.

Entonces, en el mundo real, si quieres representar las horas que se marcan en el reloj de pared, hay que utilizar una abstracción que capture el tiempo como se observa.

Si quieres representar el fin de jornada en Nueva York, es jarto conveniente hacerlo con una regla que gira en torno al hora de reloj, con un mapeo entre la hora local y UTC, para capturar fácilmente cosas como la transición de horario de verano.

--

<div class="centered-container splash">
<p style="font-size: 2em;">
Cuando guardas objetos datetime y lo que importa es la <em>hora de pared</em>, hay que almacenar el tiempo local, porque el mapeo entre UTC y el tiempo local <em>no es estable</em>.
</p>
</div>

Notes:

Y podéis pensar: "Pues sí, seguro que tenemos que manejar zonas horarias cuando estamos lidiando con humanos, pero ¿al menos podemos almacenar los `datetimes` en UTC para no tener que pensar en ello?".

Y siento ser otra vez el portador de malas noticias, pero tampoco puedes hacer eso, porque no funciona cuando lo que te importa es la hora de reloj.

El problema es que el mapeo entre la hora local y UTC no es estable, entonces para fechas en el futuro, si alacenas el `datetime` en UTC y el mapeo cambia (como ocurre muy frecuentemente, y a menudo con muy poca antelación), habrás perdido información sobre lo que te importaba: la hora *local*.

Si tienes una reunión a la una en algún lugar, no te importa la hora en UTC, y si tu desplazamiento para la fecha indicada cambia, seguro que quieres mantener la hora original, así que si lo que te importa es la hora en una zona indicada, tienes que almacenar *esa hora*.

Lo que eso quiere decir es que lo que tenéis que buscar es la abstracción que más se parezca al concepto que queréis representar.

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
