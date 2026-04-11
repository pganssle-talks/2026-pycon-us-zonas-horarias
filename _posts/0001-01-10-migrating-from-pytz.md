# Migrar de `pytz`

Si tienes una interfaz pública que devuelve zonas de `pytz` (o `datetime`s con zonas de `pytz` adjuntadas), migrar fuera de `pytz` implicará un **cambio disruptivo (*breaking change*)**:

```python
def pre_migration():
    return pytz.timezone("America/New_York").localize(datetime(2020, 1, 1))

def post_migration():
    return datetime(2020, 1, 1, tzinfo=ZoneInfo("America/New_York"))

def sesenta_dias_despuesdt: datetime) -> datetime:
    non_normalized_dt = dt + timedelta(days=60)
    return dt.tzinfo.normalize(non_normalized_dt)
```

<br/>


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

Notes:

So if you're going to migrate from `pytz`, if you have any public-facing interface that returns `pytz` zones, you should be aware that it is a breaking change to switch to `ZoneInfo`, because your users may be expecting you to have a time zone exposed that has `localize` and `normalize` methods and whatever `pytz`-specific interfaces.

So this may be a little bit of a problem for you.

--

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

**Cuidado:** Hay algunos cambios en la semántica de aritmética; consultad la [guía de migración](https://pytz-deprecation-shim.readthedocs.io/en/latest/migration.html).

Notes:

To help with that, I've created this third-party library, `pytz-deprecation-shim`. And the way this works is that it's a mostly backwards-compatible implementation of `pytz`'s interface, but it's also just a thin wrapper around `ZoneInfo`.

So it works just fine like a `ZoneInfo` zone. But if it also exposes `pytz`'s interface, and if anyone uses any of the `pytz`-specific stuff, it raises a `DeprecationWarning`.

So the only warning here is that there are some changes in the way arithmetic semantics work here. So I would recommend looking at this migration guide, whether or not you use it, because it's actually — I've been told — it's a quite good migration guide in general for the exact details. But you know, this might be very useful, especially if you have like a big codebase, if you just swap out all your `pytz` zones for something like this, and then start raising errors whenever you see this deprecation warning, and then you can start pulling out all the `pytz`-specific stuff.

