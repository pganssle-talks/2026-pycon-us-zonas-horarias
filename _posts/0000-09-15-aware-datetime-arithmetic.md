# Semantics of aware datetime arithmetic

An analogous problem for comparison semantics is that addition across a DST boundary is not well-defined:

```python
>>> NYC = ZoneInfo("America/New_York")
>>> dt1 = datetime(2020, 3, 7, 13, tzinfo=NYC)
>>> dt2 = d1 + timedelta(days=1)
```

<br/>
<br/>

Given that there is a DST transition between `dt1` and `dt2`, there are two options:

```python
>>> print(wall_add(dt1, timedelta(days=1)))  # Next calendar day at the same time
2020-03-08 13:00-04:00

>>> print(absolute_add(dt1, timedelta(days=1)))  # 24 elapsed hours after dt1
2020-03-08 12:00-04:00
```

Notes:

And there is an analogous problem with arithmetic, right? Because when you're going over a daylight saving time transition, you can either have wall time semantics, where you say, "Just give me the same time tomorrow" (if you're adding 24 hours), or you could say, "Give me what time it is after 24 hours have elapsed" like in absolute time in UTC. And these may be two different values.

--

# Semantics of aware datetime arithmetic


Datetime always uses wall-time semantics when interacting with a `timedelta`:


```python
>>> print(wall_add(dt1, timedelta(days=1)))
2020-03-08 13:00-04:00

>>> print(absolute_add(dt1, timedelta(days=1)))
2020-03-08 12:00-04:00

>>> print(dt1 + timedelta(days=1))
2020-03-08 13:00-04:00
```

When two `datetime`s are subtracted, the behavior is different for same-zone and different-zone subtractions:

```
>>> dt2 = datetime(2020, 3, 8, 13, tzinfo=NYC)
>>> dt1_same = datetime(2020, 3, 7, 13, tzinfo=NYC)
>>> dt1_different = dt1_same.astimezone(timezone.utc)  # dt1_same == dt1_different!

>>> print(dt2 - dt1_same)
1 day, 0:00:00

>>> print(dt2 - dt1_different)
23:00:00
```

*See my blog post "Semantics of timezone-aware datetime arithmetic" (https://blog.ganssle.io/articles/2018/02/aware-datetime-arithmetic.html) for a more thorough analysis.*

Notes:

And there's a sort of similar dichotomy here, where `datetime` really likes to use wall time semantics. So when you're adding a `timedelta`, it says, "Oh, that's a same-zone operation, so we'll use wall times." And if you're subtracting two datetimes, if they're in the same zone, we'll use wall time semantics.

And if they're in different zones, again, it doesn't make sense to use wall time semantics, so we'll switch to absolute time. And I have a blog post that goes into detail about why this isn't as crazy as it sounds, but unfortunately, most people really, really, really don't think that should be the case — they are constantly reporting it as a bug.

--

# Using `zoneinfo`: Absolute time semantics

Many `pytz` users will be surprised by the "wall time" semantics of `datetime`. To deliberately use absolute time semantics, convert to UTC first:

```python
def absolute_add(dt: datetime, td: timedelta) -> datetime:
    dt_utc = dt.astimezone(timezone.utc)
    rv_utc = dt_utc + td
    return rv_utc.astimezone(dt.tzinfo)

def absolute_diff(dt1: datetime, dt2: datetime) -> timedelta:
    dt1_utc = dt1.astimezone(timezone.utc)
    dt2_utc = dt2.astimezone(timezone.utc)

    return dt1 - dt2
```

Notes:

So what I recommend is that you define some little helper functions like this that just take your operands and convert them to UTC before doing any operations on it, and then you can get absolute time semantics regardless of whether they're same zone or different zone or whatever.
