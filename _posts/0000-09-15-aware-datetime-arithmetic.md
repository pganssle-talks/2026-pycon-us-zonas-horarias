# Semántica de aritmética con datetimes conscientes

Un problema análogo a la semántica de comparación es que sumar tiempo tras una transición de DST no está bien definida:

```python
>>> NYC = ZoneInfo("America/New_York")
>>> dt1 = datetime(2020, 3, 7, 13, tzinfo=NYC)
>>> dt2 = d1 + timedelta(days=1)
```

<br/>
<br/>

Dado que hay una transición entre `dt1` y `dt2`, hay dos opciones:

```python
>>> print(sumar_reloj(dt1, timedelta(days=1)))  # Siguiente día del calendario a la misma hora
2020-03-08 13:00-04:00

>>> print(sumar_absoluto(dt1, timedelta(days=1)))  # 24 horas transcurridas después de dt1
2020-03-08 12:00-04:00
```

Notes:

And there is an analogous problem with arithmetic, right? Because when you're going over a daylight saving time transition, you can either have wall time semantics, where you say, "Just give me the same time tomorrow" (if you're adding 24 hours), or you could say, "Give me what time it is after 24 hours have elapsed" like in absolute time in UTC. And these may be two different values.

--

# Semántica de aritmética con datetimes conscientes en Python

`datetime` siempre usa semántica de hora de reloj cuando interactúa con un `timedelta`:


```python
>>> print(sumar_reloj(dt1, timedelta(days=1)))
2020-03-08 13:00-04:00

>>> print(sumar_absoluto(dt1, timedelta(days=1)))
2020-03-08 12:00-04:00

>>> print(dt1 + timedelta(days=1))
2020-03-08 13:00-04:00
```

Cuando se restan dos `datetime`s, el comportamiento es diferente entre los casos de «misma zona» y «zona diferente»:

```
>>> dt2 = datetime(2020, 3, 8, 13, tzinfo=NYC)
>>> dt1_misma = datetime(2020, 3, 7, 13, tzinfo=NYC)
>>> dt1_diferente = dt1_misma.astimezone(timezone.utc)  # dt1_misma == dt1_diferente!

>>> print(dt2 - dt1_misma)
1 day, 0:00:00

>>> print(dt2 - dt1_misma)
23:00:00
```

*Consultad mi artículo de blog (en inglés) ["Semantics of timezone-aware datetime arithmetic"](https://blog.ganssle.io/articles/2018/02/aware-datetime-arithmetic.html) para un análisis más exhaustivo.*

Notes:

And there's a sort of similar dichotomy here, where `datetime` really likes to use wall time semantics. So when you're adding a `timedelta`, it says, "Oh, that's a same-zone operation, so we'll use wall times." And if you're subtracting two datetimes, if they're in the same zone, we'll use wall time semantics.

And if they're in different zones, again, it doesn't make sense to use wall time semantics, so we'll switch to absolute time. And I have a blog post that goes into detail about why this isn't as crazy as it sounds, but unfortunately, most people really, really, really don't think that should be the case — they are constantly reporting it as a bug.

--

# Cómo usar `zoneinfo`: Semántica del tiempo absoluto

La semántica de hora de reloj de Python puede sorprender a muchos usuarios; para utilizar deliberadamente la semántica del tiempo absoluto, primero hay que convertir a UTC:

```python
def sumar_absoluto(dt: datetime, td: timedelta) -> datetime:
    dt_utc = dt.astimezone(timezone.utc)
    rv_utc = dt_utc + td
    return rv_utc.astimezone(dt.tzinfo)

def restar_absoluto(dt1: datetime, dt2: datetime) -> timedelta:
    dt1_utc = dt1.astimezone(timezone.utc)
    dt2_utc = dt2.astimezone(timezone.utc)

    return dt1 - dt2
```

Notes:

So what I recommend is that you define some little helper functions like this that just take your operands and convert them to UTC before doing any operations on it, and then you can get absolute time semantics regardless of whether they're same zone or different zone or whatever.
