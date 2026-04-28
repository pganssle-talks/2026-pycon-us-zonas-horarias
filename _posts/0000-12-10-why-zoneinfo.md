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

- Es la única librería de zonas horarias con soporte para fechas posteriores a 2038 y para el formato "slim" de `tzdata`.

- ¡Es muy **rápida**! (cifras de los benchmarks de `backports.zoneinfo`):

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

Vale, ya os he asustado un poco con la complejidad de migrar a `ZoneInfo`, y no quiero dar por sentado que, simplemente por el hecho de estar en la biblioteca estándar, vais a querer usarlo. Por eso, quiero daros otros motivos de peso.

El primero es que cada zona de IANA contiene su información en dos formatos: la versión uno y la versión tres (o superior), por temas de compatibilidad. `pytz` no soporta la versión tres, lo cual normalmente no es un problema, pero la versión antigua no puede representar **timestamps** de más de treinta y dos bits. Así que `pytz` va a fallar para fechas más allá de dos mil treinta y ocho; las transiciones, simplemente, se detienen.

Pero algo incluso más urgente es que la versión tres introdujo la capacidad de representar zonas no solo como una lista de transiciones, sino como una lista más una regla para cuando la zona ya es estable. Existe una versión "slim" de `tzdata` que algunas distribuciones de Linux ya incluyen, en la que las listas de transiciones terminan en el pasado. Si intentáis usar los archivos del sistema con `pytz`, las transiciones van a estar mal hoy mismo en muchas zonas de lugares como los Estados Unidos.

Y además de ser más preciso, `ZoneInfo` es increíblemente rápido porque está escrito en C, mientras que `pytz` y `dateutil` están hechos en Python. En prácticamente todos los **benchmarks** que he pasado, `ZoneInfo` ha sido mucho más rápido que las otras dos, así que no tenéis que sacrificar rendimiento para empezar a usarlo.
