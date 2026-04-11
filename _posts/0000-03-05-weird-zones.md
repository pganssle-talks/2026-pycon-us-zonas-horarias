# Zonas horarias complejas

## Desplazamientos no enteros

- `Australia/Adelaide` (+09:30)
- `Asia/Kathmandu` (+05:45)
- `Africa/Monrovia` (+00:44:30) (Antes de 1979)

--

## Cambio de desplazamiento sin cambio de estatus DST

TODO: Add examples of base offset change

## Cambio de estatus DST sin cambio de desplazamiento

<ul>
    <li>
    Portugal, 1992
    <ul>
        <li><tt>WET (+0 STD) → WEST (+1 DST) 1992-03-29</tt></li>
        <li><tt>WEST (+1 DST) → CET (+1 STD) 1992-09-27</tt><br/></li>
    </ul>
    </li>
    <li>
    Colombia Británica, 2026?
    <ul>
        <li><tt>PST  (-8 STD) -> PDT (-7 DST)  2026-03-08</tt></li>
        <li><tt>PDT (-7 DST) -> "-07"  (-7 STD)  2026-11-01</tt></li>
    </ul>
    </li>
    <li>
    Portugal, 1996
    <ul>
        <li><tt>CET  (+1 STD) -> WEST (+1 DST)  1996-03-31</tt></li>
        <li><tt>WEST (+1 DST) -> WET  (+0 STD)  1996-10-27</tt></li>
    </ul>
    </li>
</ul>

Notes:

Now that we've got the basics down, let's move into the mandatory part of any time zone talk where the presenter tells you about all the weird and scandalous stuff people get up to with their local timekeeping.

You may have a friend — it's OK, I know you are asking for a friend — who thinks that there are only 24 time zones, and that they are all 1-hour increments away from UTC, but if you go to Australia or India, you'll find time zones that are at half-hour offsets, and if you go to Nepal, you'll find they even have one with a 15-minute offset. And if you look at historical data, like in Liberia before 1979, there are offsets that aren't even a whole number of *minutes* away from UTC.

Your friend may also think that the only time that the only time UTC offsets will change is during a daylight saving time change and vice versa — that the offset always changes when DST status changes, but in Portugal in 1992, they decided they didn't want to be on Western European Time anymore, but they wanted to join the UTC+1 time zone, Central European Time, so they decided they wanted to shift their base offset by 1 hour, and they decided to do this when Daylight Saving Time was schedule to end *anyway*, so that basically DST ended, but the clocks didn't change. This is very convenient for humans, but it also breaks anyone whose code relies on Daylight Saving Time transitions always corresponding to a change in offset.

As an aside, in 1996 they decided that having the sun set after midnight in the summer was not a good idea, so they did

OK, so now we know that base offsets can change, but you may think that a zone either has DST or it doesn't, and if it does it will just have two transitions per year, one going forward and one going back, right?

[2m 15s; T: 4:00]

--

## Más de un cambio de DST al año

<ul>
    <li>
    Marruecos, 2012
    <ul>
        <li><tt>WET  (+0 STD) -> WEST (+1 DST)  2012-04-29</tt></li>
        <li><tt>WEST (+1 DST) -> WET  (+0 STD)  2012-07-20</tt></li>
        <li><tt>WET  (+0 STD) -> WEST (+1 DST)  2012-08-20</tt></li>
        <li><tt>WEST (+1 DST) -> WET  (+0 STD)  2012-09-30</tt></li>
    </ul>
    </li>
</ul>
<br/>
<br/>

<span >... y en Marruecos durante 2013-2018, en Egipto en 2010 y 2014, y en Palestina en 2011.</span>


Notes:

Not so fast — In Morocco in most years since 2012, there have been *two* daylight saving time transitions. For example here in 2012 they went on to summer time in April, then in July they went back to standard time for 1 month, then back onto summer time. Seems like a kind of weird thing to do until you realize that Morocco is a majority Muslim country, and in 2012 this month was the month of Ramadan, when Muslims aren't supposed to eat anything before sundown. All of a sudden that extra hour before sunset isn't looking too good, so they just go back to standard time.

OK, so we know there can be all kinds of weird stuff around daylight saving time transitions, but at least we can feel confident that these things always happen at like 2 in the morning, we're never going to see some discontinuity in the middle of the day, right?

[1m; T: 5m]

--

## Días perdidos

* Isla de Navidad (Kiritimati), 31 de diciembre de 1994 (`UTC-10 → UTC+14`)


```python
>>> dt_antes = datetime(1994, 12, 30, 23, 59, tzinfo=ZoneInfo("Pacific/Kiritimati"))
>>> dt_despues = sumar_absoluto(dt_antes, timedelta(minutes=2))

>>> print(dt_antes)
1994-12-30 23:59:00-10:00

>>> print(dt_despues)
1995-01-01 00:01:00+14:00
```

<br/>

Tambien Samoa en 29 Enero 2011

Notes:

Alas, even this is not true — in 1994, Kiribati (prounounced kee-ree-bahs), which is an island nation in the South Pacific, decided that they wanted to be on the other side of the international dateline. Presumably this was something to do with aligning their timekeeping more closely with one of their trading partners or something, but the upshot of it was that they decided that they were going to just not have a December 31st in 1994. They would just go December 30th 11:159 then one minute later Happy New Year!

And you may so, "Oh well that's just something that happens in the far past, it was the 90s, we were inventing programming languages and watching Seinfeld, that couldn't happen *today*, could it? But just a bit over a decade ago, the same thing happened in Samoa in 2011.

[1m 15s; T: 6m15s]


--

## Días dobles

<br/>

* Atolón de Kwajalein, 1969


```python
>>> dt_antes = datetime(1969, 9, 30, 11, 59, tzinfo=ZoneInfo("Pacific/Kwajalein"))
>>> dt_despues = sumar_absoluto(dt_antes, timedelta(minutes=2))

>>> print(dt_antes)
1969-09-30 11:59:00+11:00

>>> print(dt_despues)
1969-09-30 12:01:00+11:00
```

<br/>
<br/>

Notes: 

And historically, some places have gone the other way as well. In Kwajalein Atoll in 1969, there were two September 30ths!

OK so maybe you say, "Ok, daylight saving time transitions can happen at any time, and there can be millions of them, and any sort of chaos can happen about offset changes, but at least I can count on one thing — if I know someone's location, I know what time zone they're in." But I think you can see where this is going...


[15s; T: 6m30s]

--

<!-- .slide: data-transition="slide-in none" -->

<h2 style="margin-top: 0.5em; font-family: monospace">Asia/Shanghai</h2>

![Asia/Shanghai time zone map](images/china_shanghai.png) <!-- .element: id="splash-noborder" -->


Notes:

In China, they decided it would be a great idea for there to be one time zone for the entire country. This is normally a country that would span 3 or 4 time zones, but administratively I guess it's easier to use UTC+8 everywhere, which I guess is great in Beijing, but in Xinjiang (pronounced: shin-jee-ang) which is far to the West, the sun rises at around 4:30AM, which is not great, so while the trains and the post offices and government offices all use UTC+8, the locals effectively observe UTC+6. And according to Wikipedia, the main difference of who chooses which time zone is whether you are part of the Uyghyur (pronounced: wee-gurr) minority or Han majority, so in a sense this is actually a racial time zone, so I suppose if you know someone's location and their ethnicity then you can know their time zone....

[1m15s; 7m45s]

--

<!-- .slide: data-transition="none slide-out" -->

<h2 style="margin-top: 0.5em; font-family: monospace">Asia/Urumqi</h2>

![Asia/Shanghai time zone map](images/china_overlay.png) <!-- .element: id="splash-noborder" -->

Notes:

In China, they decided it would be a great idea for there to be one time zone for the entire country. This is normally a country that would span 3 or 4 time zones, but administratively I guess it's easier to use UTC+8 everywhere, which I guess is great in Beijing, but in Xinjiang (pronounced: shin-jee-ang) which is far to the West, the sun rises at around 4:30AM, which is not great, so while the trains and the post offices and government offices all use UTC+8, the locals effectively observe UTC+6. And according to Wikipedia, the main difference of who chooses which time zone is whether you are part of the Uyghyur (pronounced: wee-gurr) minority or Han majority, so in a sense this is actually a racial time zone, so I suppose if you know someone's location and their ethnicity then you can know their time zone....

[1m15s; 7m45s]
