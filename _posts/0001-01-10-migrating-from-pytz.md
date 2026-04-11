# Migrating from `pytz`

If you have any public-facing interface that returns `pytz` timezones (or `datetimes` localized with `pytz`), it will be a **breaking change** to move away from `pytz`:

```python
def pre_migration():
    return pytz.timezone("America/New_York").localize(datetime(2020, 1, 1))

def post_migration():
    return datetime(2020, 1, 1, tzinfo=ZoneInfo("America/New_York"))

def sixty_days_later(dt: datetime) -> datetime:
    non_normalized_dt = dt + timedelta(days=60)
    return dt.tzinfo.normalize(non_normalized_dt)
```

<br/>


```python
>>> sixty_days_later(pre_migration())
datetime.datetime(2020, 3, 1, 0, 0, tzinfo=&lt;DstTzInfo 'America/New_York' EST-1 day, 19:00:00 STD>)

>>> sixty_days_later(post_migration())
---------------------------------------------------------------------------
AttributeError                            Traceback (most recent call last)
&lt;ipython-input-7-b71365e0022f> in &lt;module>
----> 1 sixty_days_later(post_migration())

&lt;ipython-input-5-f165abf34e2a> in sixty_days_later(dt)
      7 def sixty_days_later(dt: datetime) -> datetime:
      8     non_normalized_dt = dt + timedelta(days=60)
----> 9     return dt.tzinfo.normalize(non_normalized_dt)

AttributeError: 'zoneinfo.ZoneInfo' object has no attribute 'normalize'
```

Notes:

If you're going to migrate from `pytz`, you should be aware that it can be a breaking change if you have any public-facing interfaces that return `pytz` time zone objects. Your users may be expecting to use `pytz`-specific methods like `.localize()` or `.normalize()` on those objects, and those don't exist in `ZoneInfo`.

--

# `pytz-deprecation-shim`

[`pytz-deprecation-shim`](https://pytz-deprecation-shim.readthedocs.io/en/latest/) is a mostly backwards-compatible implementation of `pytz`'s interface that is *also* a thin wrapper around `zoneinfo`. It can be used exactly as a `zoneinfo.ZoneInfo` object would be:

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

But also exposes `pytz`'s interface, raising a `DeprecationWarning` when `pytz`-specific features are used:

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

**Caution:** There are some changes in arithmetic semantics, see [the migration guide](https://pytz-deprecation-shim.readthedocs.io/en/latest/migration.html).

Notes:

To help with this, I've created a third-party library called `pytz-deprecation-shim`. It provides a mostly backwards-compatible implementation of the `pytz` interface, but it's actually just a thin wrapper around `ZoneInfo`.

--

<!-- .slide: data-visibility="hidden" -->

# `pytz-deprecation-shim`: Helper functions

- `pytz_deprecation_shim.wrap_zone(tz, key=...)`: Wrap an existing `zoneinfo` object in a shim object.
    <br/>
- `pytz_deprecation_shim.is_pytz_zone(tz)`: Detect whether you have a `pytz` zone or not, without needing to be able to import `pytz`.
    <br/>
- `pytz_deprecation_shim.upgrade_tzinfo(tz)`:

    -  "Unwraps" a shim zone into the underlying `zoneinfo` or `dateutil.tz` (Python 2.7) implementation.
    - Turns a `pytz` zone into its `zoneinfo` / `dateutil.tz` equivalent (raises an exception if no equivalent exists)

Notes:

Because it's a wrapper around `ZoneInfo`, it works perfectly fine with standard `datetime` methods. However, if anyone calls a `pytz`-specific method, the shim will raise a `DeprecationWarning`. This can be very useful for large codebases: you can swap out your `pytz` zones for the shim and then slowly find and fix all the `pytz`-specific calls until you're ready to switch to pure `ZoneInfo`.

--

<!-- .slide: data-visibility="hidden" -->

# `pytz-deprecation-shim`: Difference in arithmetic semantics

It is not possible to make a shim time zone with the same arithmetic semantics as both `pytz` and `zoneinfo` `datetimes`:

```python
def one_day_later(dt: datetime) -> datetime:
    next_day_non_normalized = dt + timedelta(days=1)
    return dt.tzinfo.normalize(next_day_non_normalized)
```
<br/>

```python
>>> dt_pytz = pytz.timezone("America/New_York").localize(datetime(2020, 10, 31, 12))
>>> print(one_day_later(dt_pytz))
2020-11-01 11:00:00-05:00

>>> dt_shim = pds.timezone("America/New_York").localize(datetime(2020, 10, 31, 12))
>>> print(one_day_later(dt_shim))
2020-11-01 12:00:00-05:00
```

Other than the deprecation warning, this will be a silent behavior change!

Notes:

The only major warning here is that there are some subtle changes in arithmetic semantics when moving from `pytz` to `ZoneInfo` (or the shim). I recommend looking at the migration guide I've written — even if you don't use the shim — because it goes into detail about these exact differences. It's actually a pretty good general-purpose guide for the transition.

