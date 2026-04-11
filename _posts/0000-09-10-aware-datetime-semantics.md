# Un caso curioso...

```python
>>> LON = ZoneInfo("Europe/London")

>>> x = datetime(2007, 3, 25, 1, 0, tzinfo=LON)
>>> ts = x.timestamp()
>>> y = datetime.fromtimestamp(ts, LON)
>>> z = datetime.fromtimestamp(ts, ZoneInfo.no_cache("Europe/London"))
```
<br/>

```python
>>> x == y
False
```
<fragment/>
<br/>


```python
>>> x == z
True
```
<fragment/>
<br/>

```python
>>> y == z
True
```
<fragment/>

Notes:

And to illustrate that, I thought I would bring up this bug report that came into `dateutil` years and years ago, which was very fun to debug. Someone said, "Okay, this date March 25th at 1:00 AM in London — if I create this object and I convert it to a timestamp and I convert it back, basically putting it in UTC and back, the datetimes don't compare equal." That seems weird, right?

And even weirder, if I create a new instance of the London time zone and I compare those, it *does* compare equal. And even weirder than that, those two things that compared equal to X, they compare equal to each other. So they have this non-transitive relationship, which is very strange, right?

--

# Pista

¡`2007-03-25 01:00:00` en Londres es imaginario!

```python
>>> print(x)                                # x (LON)
2007-03-25 01:00:00+01:00

>>> print(x.astimezone(timezone.utc))       # x (LON → UTC)
2007-03-25 00:00:00+00:00

>>> print(x.astimezone(timezone.utc).
...        .astimezone(LON))                # x (LON → UTC → LON)
2007-03-25 00:00:00+00:00
```

Notes:

And the first hint that I got as to how to debug this was when I realized that this is actually an imaginary time; it didn't exist in London.

So Y and Z, they can't represent the original datetime that we passed in, right? It can't be 1:00 AM, because you can't go from UTC to an imaginary datetime.

So what's happening is that X gets converted to some real time in UTC, and then back to whatever the actual existing time is in London.

--

# ¿Qué significa la igualdad?

<div style="display:flex; flex-flow: row nowrap; justify-content: space-between; align-items: flex-start; padding: 1rem;">

<div style="flex-grow: 2">
<ol>
    <li>Semántica de hora de reloj: solo comparar la parte naíf<br/>
    <table style="margin-top: 0.5em">
        <tr>
            <td><tt>x == y</tt></td>
            <td><tt>False</tt></td>
        </tr>
        <tr>
            <td><tt>x == z</tt></td>
            <td><tt>False</tt></td>
        </tr>
        <tr>
            <td><tt>y == z</tt></td>
            <td><tt>True</tt></td>
        </tr>
    </table>
    <br/>
    </li>
    <li>Semántica de tiempo absoluto: convertir a UTC<br/>
    <table style="margin-top: 0.5em">
        <tr>
            <td><tt>x == y</tt></td>
            <td><tt>True</tt></td>
        </tr>
        <tr>
            <td><tt>x == z</tt></td>
            <td><tt>True</tt></td>
        </tr>
        <tr>
            <td><tt>y == z</tt></td>
            <td><tt>True</tt></td>
        </tr>
    </table>
    </li>
</ol>
</div>

<div style="border: 1px solid; padding-left: 5px; padding-right: 5px; background: #fff; align-items: flex-start">
<div class="fragment disappearing-fragment nospace-fragment fade-out" data-fragment-index="1">
<u>Horas de reloj:</u><br/>
<tt>
    x: <b>2007-03-25 01:00:00</b>+01:00<br/><br/>
    y: <b>2007-03-25 00:00:00</b>+00:00<br/><br/>
    z: <b>2007-03-25 00:00:00</b>+00:00<br/><br/>
</tt>
</div>
<div class = "fragment nospace-fragment fade-in " data-fragment-index="1">
<u>UTC:</u><br/>
<tt>
    x: 2007-03-25 <b>00:00:00+00:00</b><br/><br/>
    y: 2007-03-25 <b>00:00:00+00:00</b><br/><br/>
    z: 2007-03-25 <b>00:00:00+00:00</b><br/><br/>
</tt>
</div>
</div>
</div>

## Otra pista <!-- .element: class="fragment" data-fragment-index="2" -->

```python
>>> x.tzinfo is y.tzinfo
True
```
<!-- .element: class="fragment" data-fragment-index="2" -->

```python
>>> x.tzinfo is z.tzinfo
False
```
<!-- .element: class="fragment" data-fragment-index="2" -->

Notes:

And then this brings up the question of: what does it mean for two datetimes to be equal to each other? Because there are actually two very good candidates. One is wall time semantics, where you only compare the part of the datetime that is the clock and the calendar — the naïve portion of the datetime. In that situation, X should not equal Y or Z, and Y and Z should equal each other, right?

The other option is absolute time semantics, where you convert everything to UTC before you do the comparison. And in that case, all three of these are equal.

But neither of these patterns is what we see in the actual result, right?

So the other hint that we need to see to explain why this is happening is that X and Y use the exact same object as their time zone, and X and Z have different objects as a time zone.

--

# Semántica de comparación de datetimes conscientes

1. Cuando dos `datetime`s están en la *misma zona*, solo se compara la parte naíf (semántica de hora de reloj).

2. Cuando están en *zonas diferentes*, ambos se convierten a UTC primero y después se comparan (semántica absoluta).

3. Dos `datetime`s solo se consideran en la "misma zona" si `dt1.tzinfo is dt2.tzinfo`.

<br/>
<br/>

## Misterio resuelto: <!-- .element: class="fragment" data-fragment-index="1" -->

<div class="fragment" data-fragment-index="1" style="text-align:center">
<table>
<tr>
    <td></td>
    <td>Pared</td>
    <td>Absoluto</td>
    <td><tt>datetime</tt></td>
</tr>
<tr>
    <td><tt>x == y</tt></td>
    <td><b>False</b></td>
    <td>True</td>
    <td>False</td>
</tr>
<tr>
    <td><tt>x == z</tt></td>
    <td>False</td>
    <td><b>True</b></td>
    <td>True</td>
</tr>
<tr>
    <td><tt>y == z</tt></td>
    <td><b>True</b></td>
    <td>True</td>
    <td>True</td>
</tr>
</table>

</div>

Notes:

So the actual semantics of aware datetime comparison are that when two datetimes are in the same zone, you use wall time semantics. But when they're in different zones, it makes no sense to compare their wall times, right?

So you have to convert them to UTC first. And the key here is that you only consider two datetimes to be in the same zone if they have the same `tzinfo` object — it's the exact same object. So this solves the mystery, right?

Because we have wall time semantics for `x == y`, we have absolute time semantics for `x == z`, and then we have wall time semantics again for `y == z`, but it wouldn't matter either way.

--

# `zoneinfo`: Comportamiento de la caché

Las llamadas al constructor por defecto con argumentos idénticos tienen garantizado devolver objetos idénticos; específicamente, lo siguiente siempre debe ser válido:

   ```python
   a = ZoneInfo(key)
   b = ZoneInfo(key)
   assert a is b
   ```

   Esto es porque `datetime` asume que las zonas horarias son singletons, lo que daría resultados confusos si usáramos una implementación más simple:

   ```python
   >>> from datetime import *
   >>> from simple_zoneinfo import SimpleZoneInfo
   >>> dt0 = datetime(2020, 3, 8, tzinfo=SimpleZoneInfo("America/New_York"))
   >>> dt1 = dt0 + timedelta(1)
   >>> dt2 = dt1.replace(tzinfo=SimpleZoneInfo("America/New_York"))
   >>> dt2 == dt1
   True
   >>> print(dt2 - dt1)
   0:00:00
   >>> print(dt2 - dt0)
   23:00:00
   >>> print(dt1 - dt0)
   1 day, 0:00:00
   ```

Consultad el [PEP 615](https://www.python.org/dev/peps/pep-0615/) y [la documentación](https://docs.python.org/3/library/zoneinfo.html) para más información de la que jamás querríais saber sobre cómo trabajar con esta caché.

Notes:

Incidentally, this really informed how `ZoneInfo` was designed, because we didn't really want this confusing situation where sometimes you get wall time semantics and sometimes you get absolute time semantics.

So `ZoneInfo` is guaranteed to give you the same object every single time if you pass it the same key. So if you pass it "America/New_York" to a new constructor, or you just pass around an "America/New_York" object, it's going to be the same object, so you'll always get wall time semantics.
