# Concrete Time Zones: Local time

- UTC / Fixed Offsets <span style="color: green">Added in 3.2</span>
- Local time <span style="color: orange"><strong>○</strong> Basically supported in 3.6+</span>
- IANA Time Zones <span class="fragment" style="color: red" data-fragment-index="1">✘ (as of Python 3.8)</span>

<br/>
<br/>

Naïve datetimes are now considered system local times, and you can attach a fixed offset zone to them to probe time zone information:

```python
>>> print(datetime(2023, 11, 4, 12).astimezone())
2023-11-04 12:00:00-04:00
```

```python
>>> print(datetime(2023, 11, 5, 12).astimezone())
2023-11-05 12:00:00-05:00
```

<br/>

Setting `fold` on a naïve datetime works:

```python
>>> print(datetime(2023, 11, 5, 1, fold=0).astimezone())
2023-11-05 01:00:00-04:00
>>> print(datetime(2023, 11, 5, 1, fold=1).astimezone())
2023-11-05 01:00:00-05:00
```

<br/>

See my blog posts: [Why naïve times are local times](https://blog.ganssle.io/articles/2022/04/naive-local-datetimes.html) and [Stop using utcnow and utcfromtimestamp](https://blog.ganssle.io/articles/2019/11/utcnow.html)

Notes:

We've actually had support for system local time in `datetime` for quite a while now — basically since Python 3.6. It was done somewhat sneakily: naive datetimes (those without an attached `tzinfo`) now represent local time in any situation where they need to be converted to UTC. For example, you can call `.timestamp()` or `.astimezone()` on a naive datetime and it will just work, assuming that the naive time represents the local system time.

I have a blog post called "Why naive times are local times" that explains the somewhat convoluted reasoning for why this is actually the best way to handle this, rather than having a specific `tzinfo` object that represents "local time". 

The key takeaway is that there's now a `pytz`-like interface for local time. If you want to know the specific offset for a naive datetime, you can call `.astimezone()` with no arguments (or with `None`). This will return a new aware datetime with a fixed offset zone attached, allowing you to query `tzname()` and `utcoffset()`. However, you're not supposed to do arithmetic on that result; instead, you should perform your math on the naive datetime and only call `.astimezone()` when you need to probe the specific offset.

But even with this, as of Python 3.8, we still didn't have a way to access the IANA time zone database directly from the standard library.

