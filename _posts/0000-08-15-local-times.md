# Zonas horarias concretas: hora local

- UTC / Desplazamientos fijos <span class="fragment" style="color: green" data-fragment-index="1">✔ Añadidos en 3.2</span>
- Hora local
- Zonas horarias de IANA <span class="fragment" style="color: red" data-fragment-index="1">✘ (en Python 3.8)</span>

A partir de Python 3.2, los `datetime`s naífs ya se consideran hora local del sistema, y puedes adjuntarles un desplazamiento fijo para conseguir información sobre la zona horaria:

```python
>>> print(datetime(2023, 11, 4, 12).astimezone())
2023-11-04 12:00:00-04:00
```

```python
>>> print(datetime(2023, 11, 5, 12).astimezone())
2023-11-05 12:00:00-05:00
```

<br/>

Configurar el atributo `fold` en un `datetime` naíf funciona:

```python
>>> print(datetime(2023, 11, 5, 1, fold=0).astimezone())
2023-11-05 01:00:00-04:00
>>> print(datetime(2023, 11, 5, 1, fold=1).astimezone())
2023-11-05 01:00:00-05:00
```

Para más información, mirad mis posts de blog (en inglés): [Why naïve times are local times](https://blog.ganssle.io/articles/2022/04/naive-local-datetimes.html) y [Stop using utcnow and utcfromtimestamp](https://blog.ganssle.io/articles/2019/11/utcnow.html)

Notes:

Okay, so this allows you to start implementing those other two time zones I've talked about: local time and IANA zones. And it turns out a lot of people don't know this, but we've already had local time support in `datetime` for quite a while, basically since 3.6. The `fold` attribute just works.

But the thing is, it was done sort of sneakily, where naive datetimes (which is to say, something without a time zone) now represent local time in any situation where they need to be converted to UTC. So you can call `timestamp` on them, you can call `astimezone` on them, and it'll work — it'll just assume that your naive time is in the system local time zone.

And I have a blog post called "Why naive times are local times" which explains the convoluted reasoning why this is actually probably the best way you can do this, instead of having some `tzinfo` object that represents local time.

But one thing I'd like to call attention to here is that there's also this sort of `pytz`-like interface here; if you want to know not just some calculation that happens on local time, but you want to specifically know what the offset is, you can call `astimezone` with no argument (or with `None` as an argument), and it will attach a fixed time zone to the result so that you can query `tzname` and UTC offset.

The one caveat is that you're not supposed to do math on that kind of thing; you're supposed to do math on the naive time and then call `astimezone` as necessary.

So this gives us 2 out of our 3 types of time zones, but as of Python 3.8 we still didn't have IANA zones.
