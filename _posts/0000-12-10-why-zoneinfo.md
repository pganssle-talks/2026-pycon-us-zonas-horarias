# ¿Por qué usar `zoneinfo`?

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

Notes:

Okay, so I don't want to presume that just because it's in the standard library you're going to want to use `ZoneInfo`, and also maybe it's going to be quite a big migration.

So I thought I would give you a couple benefits of why you should use `ZoneInfo`. For one thing, there's kind of a really big bug that's coming up and is already here in some senses because `pytz` only supports an older time zone data forma, and the older format cannot represent timestamps beyond 32 bits.

So after the year 2038, anything that's not updated to the newer format will just not have transitions anymore. But also this is becoming more of an issue because more distros are also distributing a "slim" version of the `tzdata` package where that cut-off point comes much sooner, because the newer format can represent recurring transitions and so to save space they don't list every transition anymore, they just list all the historical transitions up until the rule becomes regular, and then they give the rule, so if you are trying to work with that type of data you may have problems *today* in places like the US where time zones have been relatively stable for some time.

Also, `ZoneInfo` is incredibly fast, because it was written in C and these other things are written in Python. On pretty much every benchmark I ran, `ZoneInfo` was much faster, than the other two, so you don't have to give up any speed to adopt it.
