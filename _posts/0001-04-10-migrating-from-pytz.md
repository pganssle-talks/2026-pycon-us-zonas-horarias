<!-- .slide: data-visibility="uncounted" -->

<div class="bullet-container medium-code">

# Migrar de `pytz`

Si tienes una interfaz pública que devuelve zonas de `pytz` (o `datetime`s con zonas de `pytz` adjuntadas), migrar fuera de `pytz` implicará un **cambio disruptivo (*breaking change*)**:

```python
def pre_migration():
    return pytz.timezone("America/New_York").localize(datetime(2020, 1, 1))

def post_migration():
    return datetime(2020, 1, 1, tzinfo=ZoneInfo("America/New_York"))

def sesenta_dias_despues(dt: datetime) -> datetime:
    non_normalized_dt = dt + timedelta(days=60)
    return dt.tzinfo.normalize(non_normalized_dt)
```


```python
>>> sesenta_dias_despues(pre_migration())
datetime.datetime(2020, 3, 1, 0, 0, tzinfo=&lt;DstTzInfo 'America/New_York' EST-1 day, 19:00:00 STD>)

>>> sesenta_dias_despues(post_migration())
---------------------------------------------------------------------------
AttributeError                            Traceback (most recent call last)
&lt;ipython-input-7-b71365e0022f> in &lt;module>
----> 1 sesenta_dias_despues(post_migration())

&lt;ipython-input-5-f165abf34e2a> in sixty_days_later(dt)
      7 def sesenta_dias_despues(dt: datetime) -> datetime:
      8     non_normalized_dt = dt + timedelta(days=60)
----> 9     return dt.tzinfo.normalize(non_normalized_dt)

AttributeError: 'zoneinfo.ZoneInfo' object has no attribute 'normalize'
```

</div>

Notes:

Si vas a migrar de `pytz`, y tienes alguna interfaz orientada al público que devuelva sus zonas horarias, hay que ser consciente de que cambiar a `ZoneInfo` supondrá un *breaking change* (un cambio disruptivo). Básicamente, porque tus usuarios pueden esperar que los objetos que devuelves tengan los métodos `localize` y `normalize` u otras interfaces exclusivas de `pytz`, lo cual podría daros algún que otro problema.

--

<!-- .slide: data-visibility="uncounted" -->

<div class="bullet-container">

# `pytz-deprecation-shim`

[`pytz-deprecation-shim`](https://pytz-deprecation-shim.readthedocs.io) es una implementación mayormente compatible de la interfaz de `pytz` que **también** es una capa fina (wrapper) sobre `zoneinfo`. Se puede usar igual que un objeto de `zoneinfo.ZoneInfo`:

```python
>>> import pytz_deprecation_shim as pds
>>> from datetime import datetime, timedelta
>>> LA = pds.timezone("America/Los_Angeles")

>>> dt = datetime(2020, 10, 31, 12, tzinfo=LA)
>>> print(dt)
2020-10-31 12:00:00-07:00

>>> dt.tzname()
'PDT'
```

Pero también expone la interfaz de `pytz`, lanzando un `DeprecationWarning` cuando se usan funcionalidades específicas de `pytz`:

```python
>>> dt = LA.localize(datetime(2020, 10, 31, 12))
&lt;stdin>:1: PytzUsageWarning: The localize method is no longer necessary, as
this time zone supports the fold attribute (PEP 495). For more details on
migrating to a PEP 495-compliant implementation, see
https://pytz-deprecation-shim.readthedocs.io/en/latest/migration.html

 >>> print(dt)
2020-10-31 12:00:00-07:00
>>> dt.tzname()
'PDT'
```

<div class="footnote warning centered-container" style="font-size: 0.9em; height: unset;">

⚠️ **Cuidado:** Hay algunos cambios en la semántica de aritmética; consultad la [guía de migración](https://pytz-deprecation-shim.readthedocs.io/en/latest/migration.html). ⚠️

</div>

</div>

Notes:

Para ayudar con eso, he creado esta librería de terceros que se llama `pytz-deprecation-shim`. Funciona así: aunque es imposible ser cien por cien compatible con la interfaz de `pytz`, es "mayormente" compatible porque es un  «thin wrapper» sobre `ZoneInfo`. Expone las interfaces de `pytz`, pero lanza un `DeprecationWarning` cuando se usa algo exclusivo de `pytz` para avisar a tus usuarios de que deberían dejar de usar esos métodos.

Mi única advertencia es que hay algunos cambios sutiles en la semántica de la aritmética, así que, en ciertas circunstancias, el comportamiento de las zonas cambiará para tus usuarios sin aviso previo. Para entender mejor qué cambios son, os recomiendo que le echéis un ojo a la guía de migración. E incluso si no tenéis pensado usar la librería, os sugiero leerla igual, porque me dicen que explica muy bien los problemas típicos al migrar desde `pytz`.

De hecho, espero que no tengáis que usar la librería para migrar, pero si tienes una base de código grande, te puede venir bien para detectar dónde se están llamando a los métodos de `pytz` más allá de los usos directos.
