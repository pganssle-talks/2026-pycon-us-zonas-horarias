# Why do we need to work with time zones at all?
<br/>

```python
from dateutil import rrule as rr
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

# Close of business in New York on weekdays
closing_times = rr.rrule(freq=rr.DAILY, byweekday=(rr.MO, rr.TU, rr.WE, rr.TH, rr.FR),
                         byhour=17, dtstart=datetime(2023, 3, 8, 17), count=5)

NYC = ZoneInfo("America/New_York")
for dt in closing_times:
    print(dt.replace(tzinfo=NYC))
```
<pre style="margin-top: 0.5em">
2023-03-08 17:00:00-05:00
2023-03-09 17:00:00-05:00
2023-03-10 17:00:00<b>-05:00</b>
2023-03-13 17:00:00<b>-04:00</b>
2023-03-14 17:00:00-04:00
</pre>
<br/>

```python
# Get close of business in UTC
for dt in closing_times:
    print(dt.replace(tzinfo=NYC).astimezone(timezone.utc))
```
<pre style="margin-top: 0.5em">
2023-03-08 22:00:00+00:00
2023-03-09 22:00:00+00:00
2023-03-10 <b>22:00:00</b>+00:00
2023-03-13 <b>21:00:00</b>+00:00
2023-03-14 21:00:00+00:00
<pre>

Notes:

Alright, so I've scared you, and you might be asking yourself: why do we need to work with time zones at all? Can't we just use UTC for everything?

The answer is no, because UTC is not a natural abstraction for most of the world. The world actually does have daylight saving time, and people run their schedules based on when the sun is overhead.

In the real world, if you want to do something like generate a bunch of datetimes representing close of business in New York, it's very convenient to be able to say, "I want this to be every day Monday through Friday at five o'clock", and then just attach the New York time zone to it. You'll see that seamlessly your UTC offset changes from -5 to -4 at some point in your sequence. 

If you wanted to do this in UTC, you'd have to say, "Okay, well close of business is sometimes 10 o'clock UTC, but sometimes it's nine o'clock UTC." When does this transition happen? You'd need a set of rules for that, and that's a time zone!


--

<div style="font-size: 3rem;">
When storing datetimes where the <em>wall time</em> matters (e.g. meetings), you must store local time, because the mapping between UTC and local time is <em>not stable</em>.</div>

Notes:

And you might think, "Okay, well we may have to work with time zones when dealing with humans, but can we at least just store everything in UTC so we don't have to think about it?"

Again, I'm sorry to be the bearer of bad news, but you can't do that either. When what you care about is the wall time — like if I'm going to have a meeting in Lebanon at two o'clock — and everyone's scheduled around two o'clock because lunch is at 12 and all these things... if you take that meeting at two o'clock and store it in your database as UTC, and then (as really happened) they change when daylight saving time is on three days' notice... all of a sudden, when you try and look up what the local time is for whatever UTC you stored, it's now a different value. It's not two o'clock; it's one o'clock or three o'clock.

Because the mapping between UTC and local time is not stable. You need to care about the abstraction that most closely matches what you're trying to represent.

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

Notes:


