<div class="bullet-container big-code">


# El modelo de zonas horarias de Python: `tzinfo`

<div class="bullets-with-header">

* Las zonas horarias se definen mediante subclases de `tzinfo`.

* La información se proporciona en función del objeto `datetime`:
    * <span class="fragment highlight-current-fragment" data-fragment-index="0">`utcoffset`</span>: El desplazamiento respecto a UTC para ese `datetime`.
    * <span class="fragment highlight-current-fragment" data-fragment-index="1">`tzname`</span>: El nombre (normalmente abreviado) del horario para el `datetime` indicado.
    * <span class="fragment strike highlight-red" data-fragment-index="3"><span class="fragment highlight-current-fragment" data-fragment-index="2">`dst`</span>: La magnitud del desplazamiento del `datetime` que se atribuye al horario de verano (normalmente 0 o 1 hora)</span>

</div>

<div style="min-height: 11.5em;">
<div class="fragment disappearing-fragment fade-in-then-out" data-fragment-index="0">

```pycon
>>> LOS = zoneinfo.ZoneInfo("America/Los_Angeles")
>>> dt_mayo = datetime(2026, 5, 13, 14, tzinfo=LOS)
>>> dt_noviembre = datetime(2026, 11, 14, tzinfo=LOS)

>>> dt_mayo.utcoffset() / timedelta(hours=1)
-7.0

>>> dt_noviembre.utcoffset() / timedelta(hours=1)
-8.0
```
</div>

<div class="fragment disappearing-fragment nospace-fragment fade-in-then-out" data-fragment-index="1">

```pycon
>>> LOS = zoneinfo.ZoneInfo("America/Los_Angeles")          # tzinfo
>>> dt_mayo = datetime(2026, 5, 13, 14, tzinfo=LOS)
>>> dt_noviembre = datetime(2026, 11, 14, tzinfo=LOS)

>>> dt_mayo.tzname()  # En Windows podría dar "Pacific Daylight Time"
'PDT'

>>> dt_noviembre.tzname()
'PST'
```
</div>

<div class="fragment disappearing-fragment nospace-fragment fade-in-then-out" data-fragment-index="2">

```pycon
>>> LOS = zoneinfo.ZoneInfo("America/Los_Angeles")
>>> dt_mayo = datetime(2026, 5, 13, 14, tzinfo=LOS)
>>> dt_noviembre = datetime(2026, 11, 14, tzinfo=LOS)

>>> dt_mayo.dst() / timedelta(hours=1)
1.0

>>> dt_noviembre.dst()
0.0
```

</div>

<div class="fragment disappearing-fragment nospace-fragment fade-in-then-out"
     data-fragment-index="3"
     style="width: 100%; display: flex; justify-content: center"
     >

<img src="external-images/bob-rakes.gif"
     style="height: 10em; border: 1px solid;"
     />

</div>
<div class="fragment disappearing-fragment nospace-fragment fade-in"
     data-fragment-index="4"
     style="width: 100%; display: flex; justify-content: center"
     >

<img src="images/figures/tz_map_standard.png"
     style="height: 10em; border: 1px solid;"
     />

</div>
</div>
<div class="small-spacer"></div>
</div>


Notes:

Ok, ya que hemos establecido que en realidad hace falta *ugh* entender las abstracciones con las que trabajamos, vamos a bucear más en los detalles de cómo funciona en Python.

El modelo de zonas horarias de Python se centra en una clase base abstracta que se llama `tzinfo`. La idea es que cada objeto que representa una zona horaria proporciona tres funciones que toman como argumento un `datetime`.

➡️La más importante y la que de verdad tira del carro es `utcoffset`, que da el desplazamiento que aplica a la fecha y hora indicada.

➡️A continuación hay `tzname`, que da el nombre que aplica a ese desplazamiento — normalmente estos serían nuestras nefastas abreviaturas de tres letras.

➡️Y finalmente tenemos a la oveja negra de la familia, `dst`, que da la diferencia entre el desplazamiento actual y el horario estándar. ➡️La verdad es que creo que casi cada vez que he visto a alguien usar este método ha sido un error de algún tipo. No lo uséis, amigos.

Aunque hace poco, por primera vez en mi vida entera, he dado con un uso legítimo para este método... ➡️ haciendo este mapa de "horas estándares" para esta misma charla. Como si quisiera socavar mi propio argumento...

[1m 30s; T: 12m 30s]
