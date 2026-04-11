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

All right, so okay I've scared you, and you might be asking yourself, why do we need to work with time zones at all? Can't we just use UTC for everything?

And the answer is that no, you can't, because UTC is not a natural abstraction for most of the world. It's not a great time zone for most of the world, and also the world actually does have daylight saving time in it and people run their schedules based on when the sun is overhead. 

So in the real world, if you want to do something like generate a bunch of datetimes that represent close of business in New York, it's *very convenient* to be able to say, "Hey, here's this RRule, and I want it to be every day Monday through Friday at five o'clock", and then I'll just attach this New York time zone to it. And you'll see that seamlessly your UTC offset changes from -5 to -4 at some point in your sequence. 

If you wanted to do this in UTC, you'd be like, "Oh okay, well close of business is sometimes 10 o'clock UTC, but sometimes it's nine o'clock UTC." And when does this little transition happen? I don't know, maybe I need a set of rules for when that would happen, and that's a time zone, right?

--

<div style="font-size: 3rem;">
Cuando guardas objetos datetime y lo que importa es la <em>hora de pared</em>, hay que almacenar el tiempo local, porque el mapeo entre UTC y el tiempo local <em>no es estable</em>.
</div>

Notes:

And you might think, "Okay, well we may have to work with time zones when we're dealing with humans, but can we at least just store everything in UTC so we don't have to think about it?"

And again, I'm sorry to be the bearer of bad news, but you can't do that either, because when what you care about is the wall time; like, if I'm going to have a meeting in Lebanon at two o'clock and everyone's scheduled around two o'clock because lunch is at 12 and all these things — if you take that meeting at two o'clock and you store it in your databases UTC, and then — as really happened — they change when daylight saving time is on like three days' notice, all of a sudden, when you try and look up what's the local time for whatever UTC you stored, it's now a different value. It's not two o'clock; it's one o'clock or three o'clock or something like that, because the mapping between UTC and local time is not stable.

So what you need to care about is the abstraction that most closely matches what you're trying to represent.


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
