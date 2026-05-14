<div class="bullet-container medium-code code-indented smaller-margins">

# ¿Por qué usar `zoneinfo`?

¡Es muy **rápida**! (cifras de los benchmarks de `backports.zoneinfo`):

```
Ejecutando el constructor en la zona America/New_York
c_zoneinfo: mean: 214.65 ns ± 43.48 ns; min: 190.88 ns (k=5, N=1000000)
pytz: mean: 1.21 µs ± 78.31 ns; min: 1.10 µs (k=5, N=200000)
dateutil: mean: 1.33 µs ± 117.35 ns; min: 1.23 µs (k=5, N=200000)

Ejecutando from_utc en la zona America/New_York
c_zoneinfo: mean: 658.55 ns ± 28.92 ns; min: 617.08 ns (k=5, N=500000)
pytz: mean: 5.12 µs ± 515.26 ns; min: 4.70 µs (k=5, N=50000)
dateutil: mean: 10.64 µs ± 746.99 ns; min: 10.20 µs (k=5, N=20000)

Ejecutando to_utc en la zona America/New_York
c_zoneinfo: mean: 616.13 ns ± 16.14 ns; min: 604.76 ns (k=5, N=500000)
pytz: mean: 848.44 ns ± 28.10 ns; min: 806.72 ns (k=5, N=500000)
dateutil: mean: 8.03 µs ± 509.75 ns; min: 7.55 µs (k=5, N=50000)

Ejecutando utcoffset en la zona America/New_York
c_zoneinfo: mean: 373.89 ns ± 5.76 ns; min: 368.24 ns (k=5, N=1000000)
pytz: mean: 564.55 ns ± 13.65 ns; min: 552.88 ns (k=5, N=500000)
dateutil: mean: 7.95 µs ± 642.62 ns; min: 7.44 µs (k=5, N=50000)
```

Gracias a su implementación en C, `zoneinfo` es más rápida que `pytz` y `dateutil` en todas las métricas de rendimiento.

</div>

Notes:

Vale, pues no quiero dar por sentado que, por el mero hecho de estar en la biblioteca estándar, vayáis a querer liaros con todo este jaleo que acabo de explicar. Y creo que, además de ser la librería más armónica con el diseño de `datetime`, aun hay al menos dos buenos motivos más para usarla.

Uno es que es muy rápida, ya que está escrita en C. Pero no quiero jactarme del rendimiento, así que no vamos a pasar mucho tiempo en esta diapositiva.

[30s; T: 28m 00s]

--

<style>
div.bullet-container.smaller-margins {
    ul {
        margin-bottom: 0;
    }

    pre.code-wrapper {
        margin-top: 0;
        margin-bottom: 0;
    }
}
</style>
<div class="bullet-container medium-code code-indented smaller-margins">

# ¿Por qué usar `zoneinfo`?

<div class="small-spacer"></div>

Es la única librería de zonas horarias con soporte para fechas posteriores a 2038 (el «epochalypse») y para el formato "slim" de `tzdata`.

```python
>>> for i in range(5):
...     dt = datetime(2037, 6, 1) + timedelta(days=183) * i
...
...     print_comparison(
...         pytz.timezone("America/Los_Angeles").localize(dt),
...         dt.replace(tzinfo=ZoneInfo("America/Los_Angeles"))
...     )
...     print()
```

<pre>
<tt>

pytz:          2037-06-01     PDT  -07:00
zoneinfo:      2037-06-01     PDT  -07:00

pytz:          2037-12-01     PST  -08:00
zoneinfo:      2037-12-01     PST  -08:00

<span class="fragment custom highlight-current-fragment" data-fragment-index="1">pytz:          2038-06-02     PST  -08:00</span>
<span class="fragment custom highlight-current-fragment" data-fragment-index="1">zoneinfo:      2038-06-02     PDT  -07:00</span>

pytz:          2038-12-02     PST  -08:00
zoneinfo:      2038-12-02     PST  -08:00

<span class="fragment custom highlight-current-fragment" data-fragment-index="1">pytz:          2039-06-03     PST  -08:00</span>
<span class="fragment custom highlight-current-fragment" data-fragment-index="1">zoneinfo:      2039-06-03     PDT  -07:00</span>
</tt>
</pre>

</div>

</div>

Notes:

El motivo más importante es que ni `pytz` ni `dateutil` soporta el nuevo formato de los datos de IANA, y el formato antiguo no admite timestamps de más de treinta y dos bits. Así que para fechas posteriores a dos mil treinta y ocho, deja de funcionar; ⏭️ las transiciones simplemente se detienen, y el "epochalypse" se acerca cada día más.

<!-- Skip this for now: probably doesn't apply.

Pero algo más urgente es que algunas distros ya usan el formato "slim", que aprovecha una nueva capacidad en el nuevo formato de usar reglas en lugar de listas de transiciones. Como `pytz` tampoco lo soporta, en muchos sitios, como en los Estados Unidos, si usas los datos del sistema, `pytz` ya falla hoy mismo.

-->

[30s; T: 28m 30s]

