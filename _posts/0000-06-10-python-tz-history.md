<div class="bullet-container">

<div class="bullets-with-header">

# Historia de las zonas horarias en Python

Cuando `datetime` se estrenó en [Python 2.3](https://docs.python.org/3/whatsnew/2.3.html#date-time-type), no había zonas horarias concretas en la biblioteca estándar.
</div>

<div class="small-spacer"></div>

<div class="medium-code">

```python
from dateutil import relativedelta as rd  # Trampita...

class ET(tzinfo):
    def utcoffset(self, dt):
        if self.isdaylight(dt):
            return timedelta(hours=-4)
        else:
            return timedelta(hours=-5)

    def dst(self, dt):
        if self.isdaylight(dt):
            return timedelta(hours=1)
        else:
            return timedelta(hours=0)

    def tzname(self, dt):
        return "EDT" if self.isdaylight(dt) else "EST"

    def isdaylight(self, dt):
        dst_start = datetime(dt.year, 1, 1) + rd.relativedelta(month=3, weekday=rd.SU(+2),
                                                               hour=2)
        dst_end = datetime(dt.year, 1, 1) + rd.relativedelta(month=11, weekday=rd.SU,
                                                             hour=2)

        return dst_start <= dt.replace(tzinfo=None) < dst_end
```
</div>

<div class="small-spacer"></div>

</div>

Notes:

Bueno, e históricamente, eso fue todo lo que tenías en Python. En Python dos punto tres, dijeron: "Aquí tienes una interfaz, pero no queremos encargarnos de implementar las reglas por ti". Se suponía que debías averiguar por tu cuenta, según tu lógica de negocio, cuál sería el mejor método para representar tus zonas horarias, y quizá se esperaba que hicieras algo así: una clase con las reglas que representen la hora del Este.

[30s; T: 11m45s]

--

<div class="bullet-container">

<div class="bullets-with-header">

# Historia de las zonas horarias en Python: Zonas concretas

- UTC / Desplazamientos fijos <span class="fragment" style="color: green" data-fragment-index="1">✔ Añadidos en 3.2</span>
- Hora local
- Zonas horarias de IANA

</div>

<p style="text-align: center">
<img src="images/nuevo_en_3.2.png" alt="What's new in Python 3.2 excerpt"
     class="fragment" data-fragment-index="1" />
</p>

<div class="small-spacer"></div>

</div>

Notes:

Pero si lo pensáis un poco, la verdad es que solo hay tres tipos de zona horaria que la inmensa mayoría de la gente quiere.

Uno es el UTC o desplazamientos fijos respecto a este; otro es la hora local, o sea, la hora de tu sistema; y el tercero es una zona de la base de datos de IANA, por ejemplo America/Chicago o America/New_York, ese tipo de cosas.

Y el primero es muy fácil, porque solo necesitas un `timedelta` fijo, así que eso lo añadieron pronto, en tres punto dos. Pero los otros dos resultan ser un poco más complejos.

[30s; T:12m15s]

--

<!-- .slide: data-visibility="hidden" -->

# Historia de las zonas horarias en Python: Horas ambiguas

```python
EASTERN = ET()

print(datetime(2017, 11, 4, 12, 0, tzinfo=EASTERN))
print(datetime(2017, 11, 5, 12, 0, tzinfo=EASTERN))
```

```
2017-11-04 12:00:00-04:00
2017-11-05 12:00:00-05:00
```

```python
dt_before_utc = datetime(2017, 11, 5, 0, 30, tzinfo=EASTERN).astimezone(datetime.UTC)
dt_during = (dt_before_utc + timedelta(hours=1)).astimezone(EASTERN)  # 1:30 EDT
dt_after = (dt_before_utc + timedelta(hours=2)).astimezone(EASTERN)   # 1:30 EST

print(dt_during)   # ¡Pinta bien!
print(dt_after)    # ¡Ay no!
```

```
2017-11-05 01:30:00-04:00
2017-11-05 02:30:00-05:00
```

--

<div class="bullet-container">

<div class="bullets-with-header">

# Horas ambiguas

Las horas ambiguas son aquellas en las que la misma "hora de reloj" se repite, como durante una transición de horario de verano (DST) a estándar (STD).

</div>

<div class="medium-code">

```python
from dateutil import tz

dt1 = datetime(2004, 10, 31, 4, 30, tzinfo=timezone.utc)
for i in range(4):
    dt = (dt1 + timedelta(hours=i)).astimezone(NYC)
    print('{} | {} |  {}'.format(dt, dt.tzname(), 
                                   "Ambigua" if tz.datetime_ambiguous(dt)
                                   else "No ambigua"))
```

<pre>
<tt>
2004-10-31 00:30:00-04:00 | EDT |  No ambigua
<span class="fragment highlight-current-fragment" data-fragment-index="1">2004-10-31 01:30:00-04:00 | EDT |  Ambigua</span>
<span class="fragment highlight-current-fragment" data-fragment-index="1">2004-10-31 01:30:00-05:00 | EST |  Ambigua</span>
2004-10-31 02:30:00-05:00 | EST |  No ambigua
</tt>
</pre>

</div>

¡Pueden existir datetimes en una zona que se diferencian solo por su desplazamiento!

</div>

Notes:

Y para explicaros por qué, tengo que irme un poco por las ramas para hablar sobre las horas ambiguas.

Las horas ambiguas son momentos en los que la misma hora se marca dos veces; por ejemplo, cuando toca atrasar el reloj. Si se retrasa la hora a las dos, cada minuto entre la una y las dos pasa dos veces.

Fijaos en que en esta lista que tengo aquí la "una y media" aparece dos veces, y la diferencia principal es el desplazamiento. Pero si os acordáis, el modelo de `datetime` es que el desplazamiento es la *salida* del método `utcoffset`, no puede formar parte de la entrada, así que en realidad es imposible distinguir entre estas dos situaciones.

Y esto es un problema fundamental, un defecto que tenía la interfaz de `tzinfo` en aquella época.

[1m15s; T: 13m30s]

--

<div class="bullet-container">

<div class="small-spacer"></div>
<div class="bullets-with-header">

# Horas imaginarias

El complemento de las horas ambiguas son las horas imaginarias: horas de reloj que no existen en una zona determinada, como sucede durante una transición de horario estándar (STD) a verano (DST).

</div>

<div class="medium-code">

```python
dt1 = datetime(2004, 4, 4, 6, 30, tzinfo=timezone.utc)
for i in range(3):
    dt = (dt1 + timedelta(hours=i)).astimezone(NYC)
    print(f'{dt} | {dt.tzname()} ')
```

<pre>
<tt>
2004-04-04 01:30:00-05:00 | EST
2004-04-04 03:30:00-04:00 | EDT
2004-04-04 04:30:00-04:00 | EDT
</tt>
</pre>

</div>

¡Fijaos en que falta la hora `2004-04-04 02:30:00`!

<div class="small-spacer"></div>

</div>

Notes:

Y además hay otro problema, el complemento de las horas ambiguas, que llamamos horas imaginarias. Estas son básicamente horas que no existen en una zona horaria; por ejemplo, cuando toca adelantar el reloj: cualquier hora en ese hueco no corresponderá a un momento real.

Lidiar con esto es más fácil porque estos tiempos simplemente no existen, pero aun así, como detalle de implementación, es importante saber qué desplazamiento deben devolver tus funciones de `tzinfo`.

[15s; 13m45s]
