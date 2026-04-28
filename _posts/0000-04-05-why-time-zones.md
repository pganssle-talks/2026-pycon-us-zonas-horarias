# ¿Por qué narices necesitamos zonas horarias?

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
<pre style="margin-top: 0.5em">

2023-03-08 17:00:00-05:00
2023-03-09 17:00:00-05:00
2023-03-10 17:00:00<b>-05:00</b>
2023-03-13 17:00:00<b>-04:00</b>
2023-03-14 17:00:00-04:00

</pre>

```python
# Obtener fin de jornada en UTC
for dt in horas_de_cerrar:
    print(dt.replace(tzinfo=NYC).astimezone(timezone.utc))
```

<pre style="margin-top: 0.5em">

2023-03-08 22:00:00+00:00
2023-03-09 22:00:00+00:00
2023-03-10 <b>22:00:00</b>+00:00
2023-03-13 <b>21:00:00</b>+00:00
2023-03-14 21:00:00+00:00

</pre>

Notes:

Vale, así que ya os he dado un poco de miedo, y quizás te preguntes: ¿por qué tenemos que trabajar con zonas horarias en absoluto? ¿No podemos usar UTC para todo?

Y la respuesta es que no, no puedes, porque el UTC no es una abstracción natural para la mayor parte del mundo. Porque la gente organiza sus vidas según las horas en que el sol está en lo más alto, y en muchas ubicaciones les gusta el horario de verano.

Entonces, en el mundo real, si quieres hacer algo como generar varios `datetime`s que representen el fin de jornada en Nueva York, es jarto conveniente poder decir: "Oye, aquí tienes una regla que representa cada día del lunes al viernes a las cinco de la tarde", y entonces le adjuntas una zona horaria para Nueva York y ya está. Y puedes ver que el desplazamiento de UTC cambia entre menos cinco y menos cuatro sin problemas en algún punto de tu secuencia.

Si quisieras hacerlo en UTC, tendrías que hacer algo como: "Sí, vale, pues el fin de jornada a veces es a las diez UTC pero a veces a las nueve". ¿Y cuándo ocurre esta pequeña transición? No lo sé, puede ser que haga falta un conjunto de normas para cuando eso ocurra... pero eso describe una zona horaria, ¿cierto?

--

<div style="font-size: 3rem;">
Cuando guardas objetos datetime y lo que importa es la <em>hora de pared</em>, hay que almacenar el tiempo local, porque el mapeo entre UTC y el tiempo local <em>no es estable</em>.
</div>

Notes:

Y puedes pensar: "Pues sí, seguro que tenemos que manejar zonas horarias cuando estamos lidiando con humanos, pero ¿al menos podemos almacenarlo todo en UTC para no tener que pensar en ello?".

Y siento ser otra vez el portador de malas noticias, pero tampoco puedes hacer eso, porque no funciona cuando lo que te importa es la hora de reloj. Imagínate que tienes una reunión en el Líbano a las dos, y todo está programado en torno a las dos, porque el almuerzo es a las doce y todo eso. Si metes esta reunión en tu base de datos como UTC y —como ha pasado en realidad— cambian la fecha de la transición de DST con solo tres días de antelación, de repente no puedes traducir el UTC de vuelta a la hora local; el valor que has almacenado ya no corresponde con las dos, ahora corresponde con la una o las tres, porque el mapeo entre el UTC y la hora local no es estable.

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
