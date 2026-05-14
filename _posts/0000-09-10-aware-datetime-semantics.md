<div class="bullet-container medium-code">

<div class="bullets-with-header">

# Un caso curioso...

```python
>>> LON = ZoneInfo("Europe/London")

>>> x = datetime(2007, 3, 25, 1, 0, tzinfo=LON)
```


<div class="small-spacer" style="height: 0.5em"></div>


```python
>>> y = datetime.fromtimestamp(x.timestamp(), LON)
>>> x == y
False
```

<div class="small-spacer"></div>


```python
>>> z = datetime.fromtimestamp(x.timestamp(), ZoneInfo.no_cache("Europe/London"))
>>> x == z
True
```
<fragment/>

<div class="small-spacer"></div>

```python
>>> y == z          # 🤯
True
```
<fragment/>

</div>
</div>
<div class="small-spacer"></div>
</div>

Notes:

Para ilustrar eso, os cuento un «bug report» que llegó a `dateutil` hace años y años y fue muy divertido de debuggear. Alguien dijo: "Esta fecha, el veinticinco de marzo a la una de la madrugada en Londres — si la paso a timestamp y de vuelta — los `datetime`s no evalúan como iguales". Un poco chungo, ¿no?

Y más raro aún: si creo una nueva instancia del objeto de la zona horaria de Londres para hacer mi `datetime`, *sí* que evalúan como iguales. E incluso más raro: ¡esas dos también son iguales entre sí! Así que la relación no es transitiva, ¿cierto?

[45s; T: 23m 30s]

--

<div class="bullet-container big-code">

# Pista

<div class="centered-container" style="height: unset; padding-bottom:unset; font-size: 1.5em; font-style: italic">

¡`2007-03-25 01:00:00` en Londres es imaginario!

</div>

```pycon
>>> print(x)                                # x (LON)

2007-03-25 01:00:00+01:00


>>> print(x.astimezone(UTC))                # x (LON ➜ UTC)

2007-03-25 00:00:00+00:00


>>> print(x.astimezone(UTC).
...        .astimezone(LON))                # x (LON ➜ UTC ➜ LON)

2007-03-25 00:00:00+00:00
```


<div class="small-spacer"></div>
</div>

Notes:

Mi primera pista fue darme cuenta de que esta hora no existía — era imaginaria.

Así que Y y Z no podían representar el `datetime` original; no puedes llegar a una hora imaginaria desde UTC.

Y lo que pasa aquí es que X va a UTC — que sí existe — y de ahí al equivalente en Londres.

[30s; T: 24m 00s]

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

<style>
div#hours-compare {
    border: 1px solid;
    background: #fff;
    align-items: center;
    margin-left: 1em;

    div {
        display: flex;
        flex-direction: column;
        align-items: center;
        margin-top: 0.5em;
        margin-bottom: 0.5em;

        tt {
            /* Container query units */
            font-size: 1.8cqi;
            white-space: nowrap;
            margin-left: 0.5em;
            margin-right: 0.5em;
        }

    }

}
</style>
<div id="hours-compare">
<div class="fragment disappearing-fragment nospace-fragment fade-out"
     data-fragment-index="1">
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

Eso nos lleva al tema de la igualdad: ¿qué significa que dos `datetime`s sean iguales? Porque de hecho hay dos candidatos buenos.

Uno es la semántica de hora de reloj: solo comparas la parte naif, ignorando el desplazamiento. En esa situación, X no debería ser igual a Y o Z, e Y y Z deberían ser iguales entre sí.

La otra es la semántica de tiempo absoluto: pasas todo a UTC antes de compararlos, y en este caso, los tres son iguales.

Pero no vemos ninguno de esos patrones, ¿cierto? ¿Qué pasa?

La última pista que nos falta es que X e Y usan el mismo objeto `tzinfo`, pero Z tiene uno diferente, aunque sea igual a los otros.

[45s; T: 24m 45s]

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

Y resulta que la semántica que se usa de verdad es que cuando dos `datetime`s están en la misma zona, se usa la hora de reloj, pero cuando están en zonas diferentes, no tiene sentido comparar las partes naif, ¿cierto? Así que primero hay que ponerlos en la misma zona: UTC.

Y la clave final de nuestro misterio es que solo se considera que dos `datetime`s están en la misma zona si tienen el mismo objeto `tzinfo` — el mismísimo objeto, no basta con que tengan el mismo valor.

Entonces el misterio está resuelto, ¿lo veis? Porque para `x == y` se aplica la hora de reloj, para `x == z` tenemos tiempo absoluto, y para `y == z`, otra vez tenemos la hora de reloj, aunque para la última las dos dan el mismo resultado.

[45s; T: 25m 30s]

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

Dicho sea de paso, este problema influyó bastante en cómo se diseñó `ZoneInfo`, porque no queríamos esta situación tan confusa en la que a veces se aplica la semántica de la hora de reloj y otras la de tiempo absoluto.

Así que `ZoneInfo` garantiza que siempre vas a recibir el mismo objeto si usas la misma clave.

[15s; T: 25m 45s]
