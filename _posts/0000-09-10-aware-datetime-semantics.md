<div class="bullet-container medium-code">

<div class="bullets-with-header">

# Un caso curioso...

```python
>>> LON = ZoneInfo("Europe/London")

>>> x = datetime(2007, 3, 25, 1, 0, tzinfo=LON)
>>> ts = x.timestamp()
>>> y = datetime.fromtimestamp(ts, LON)
>>> z = datetime.fromtimestamp(ts, ZoneInfo.no_cache("Europe/London"))
```


<div class="small-spacer" style="height: 0.5em"></div>


```python
>>> x == y
False
```
<fragment/>

<div class="small-spacer"></div>


```python
>>> x == z
True
```
<fragment/>

<div class="small-spacer"></div>

```python
>>> y == z
True
```
<fragment/>

</div>
</div>
<div class="small-spacer"></div>
</div>

Notes:

Y para ilustrar eso, pensaba hablaros de este «bug report» que llegó a `dateutil` hace años y años, y que fue muy divertido de debuggear. Alguien dijo: "Vale, esta fecha, el veinticinco de marzo a la una de la madrugada en Londres — si creo este objeto, lo convierto en un timestamp y luego lo vuelvo a convertir en `datetime` —básicamente pasándolo a UTC y viceversa— los `datetime`s no evalúan como iguales". Un poco chungo, ¿no?

Y más raro aún, si creo una nueva instancia del objeto que representa la zona horaria de Londres y lo uso para crear mi `datetime`, *sí* que evalúan como iguales. E incluso más raro: ¡esas dos cosas que evaluaban como iguales a X, evalúan como iguales entre sí! Así que tienen una relación no transitiva, lo cual es rarísimo, ¿cierto?

--

<div class="bullet-container big-code">

# Pista

<div class="centered-container" style="height: unset; padding-bottom:unset; font-size: 1.5em; font-style: italic">

¡`2007-03-25 01:00:00` en Londres es imaginario!

</div>

```python
>>> print(x)                                # x (LON)
2007-03-25 01:00:00+01:00

>>> print(x.astimezone(timezone.utc))       # x (LON → UTC)
2007-03-25 00:00:00+00:00

>>> print(x.astimezone(timezone.utc).
...        .astimezone(LON))                # x (LON → UTC → LON)
2007-03-25 00:00:00+00:00
```


<div class="small-spacer"></div>
</div>

Notes:

Y mi primera pista de cómo debuggearlo fue cuando me di cuenta de que esta hora en realidad no existía, era una hora imaginaria.

Así que Y y Z no pueden representar el `datetime` original que teníamos; no puede ser la una porque no puedes ir de UTC a una hora imaginaria.

Y lo que pasa aquí es que X se convierte a una hora real en UTC, y luego de vuelta a la hora equivalente en Londres.

--

<div class="bullets-container">

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

<div style="border: 1px solid; background: #fff; align-items: flex-start; margin-left: 1em;">
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

<div class="bullets-with-header fragment big-code" data-fragment-index="2">

## Otra pista

```python
>>> x.tzinfo is y.tzinfo
True
```

```python
>>> x.tzinfo is z.tzinfo
False
```

</div>
</div>

Notes:

Entonces esto saca el tema de la igualdad: ¿qué significa que dos `datetime`s sean iguales? Porque de hecho hay dos candidatos muy buenos. Uno es la semántica de la hora de reloj, en la que solo comparas la parte del `datetime` que representa el reloj y el calendario — la parte naíf. En esa situación, X no debería ser igual a Y o Z, e Y y Z deberían ser iguales entre sí.

La otra opción es la semántica del tiempo absoluto, en la que conviertes todo a UTC antes de hacer la comparación, y en ese caso, los tres son iguales.

Pero no vemos ninguno de estos patrones en el resultado real, ¿cierto? ¿Qué pasa?

Y la otra pista que necesitamos para explicar por qué ocurre esto es que X e Y usan exactamente el mismo objeto como zona horaria, pero Z tiene un objeto *diferente* a los otros dos.

--

<div class="bullet-container">

# Semántica de comparación de datetimes conscientes

1. Cuando dos `datetime`s están en la *misma zona*, solo se compara la parte naíf (semántica de hora de reloj).

2. Cuando están en *zonas diferentes*, ambos se convierten a UTC primero y después se comparan (semántica absoluta).

3. Dos `datetime`s solo se consideran en la "misma zona" si `dt1.tzinfo is dt2.tzinfo`.

<div class="small-spacer"></div>

<div class="centered-container" style="height: unset">

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

</div>
</div>

Notes:

La semántica real de comparación de `datetime` es que cuando dos `datetime`s están en la misma zona, usará la semántica de la hora de reloj, pero cuando están en zonas diferentes, no tiene sentido comparar sus horas de reloj, ¿cierto? ¿A quién le importa una comparación entre las partes naíf de zonas diferentes?

Así que primero tienes que convertirlos a UTC. La clave final de nuestro misterio es que solo se considera que dos `datetime`s están en la misma zona si tienen el mismo objeto `tzinfo` —tiene que ser el mismo objeto, no basta con que tengan el mismo valor.

Entonces el misterio está resuelto, ¿lo veis? Porque para `x == y` se aplica la semántica de hora de reloj, para `x == z` tenemos la semántica de tiempo absoluto, y para `y == z`, otra vez tenemos la semántica de hora de reloj, aunque para la última no hace ninguna diferencia porque ambas dan el mismo resultado.

--

<div class="bullet-container medium-code">

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

<div class="footnote">

Consultad el [PEP 615](https://www.python.org/dev/peps/pep-0615/) y [la documentación](https://docs.python.org/3/library/zoneinfo.html) para más información de la que jamás querríais saber sobre cómo trabajar con esta caché.

</div>

</div>

Notes:

Dicho sea de paso, este issue influyó bastante en cómo se diseñó `ZoneInfo`, porque no queríamos esta situación confusa en la que a veces aplica la semántica de la hora de reloj y a veces aplica la de tiempo absoluto.

Así que `ZoneInfo` garantiza que vas a recibir el mismo objeto siempre si le pasas la misma clave. Entonces, si le pasas "America/New_York" a un nuevo constructor, o vas pasando por ahí un único objeto de "America/New_York", será el mismo objeto, y siempre se aplicará la semántica de la hora de reloj.
