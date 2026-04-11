# Benefits of `zoneinfo`?

- Only major time zone library with year 2038 and slim tzdata support

- It's *fast* (numbers from `backports.zoneinfo`'s benchmark suite):

```
Running constructor in zone America/New_York
c_zoneinfo: mean: 214.65 ns ± 43.48 ns; min: 190.88 ns (k=5, N=1000000)
pytz: mean: 1.21 µs ± 78.31 ns; min: 1.10 µs (k=5, N=200000)
dateutil: mean: 1.33 µs ± 117.35 ns; min: 1.23 µs (k=5, N=200000)

Running from_utc in zone America/New_York
c_zoneinfo: mean: 658.55 ns ± 28.92 ns; min: 617.08 ns (k=5, N=500000)
pytz: mean: 5.12 µs ± 515.26 ns; min: 4.70 µs (k=5, N=50000)
dateutil: mean: 10.64 µs ± 746.99 ns; min: 10.20 µs (k=5, N=20000)

Running to_utc in zone America/New_York
c_zoneinfo: mean: 616.13 ns ± 16.14 ns; min: 604.76 ns (k=5, N=500000)
pytz: mean: 848.44 ns ± 28.10 ns; min: 806.72 ns (k=5, N=500000)
dateutil: mean: 8.03 µs ± 509.75 ns; min: 7.55 µs (k=5, N=50000)

Running utcoffset in zone America/New_York
c_zoneinfo: mean: 373.89 ns ± 5.76 ns; min: 368.24 ns (k=5, N=1000000)
pytz: mean: 564.55 ns ± 13.65 ns; min: 552.88 ns (k=5, N=500000)
dateutil: mean: 7.95 µs ± 642.62 ns; min: 7.44 µs (k=5, N=50000)
```

Because of the C backend, `zoneinfo` is faster than `pytz` and `dateutil` on every metric.

Notes:

I don't want to presume that just because `ZoneInfo` is in the standard library, you'll immediately want to switch, especially since it might be a significant migration. So, here are a few key benefits of using `ZoneInfo`.

First, there's a really big issue coming up (and already here in some ways) with `tzdata` formats. The newer formats allow for transitions beyond the 32-bit limit, which is important for the "year 2038" problem. Anything not updated to support these newer formats will simply stop having DST transitions after 2038. `pytz` is currently in that boat.

Even more immediately, there's a new "slim" format for `tzdata` that many operating systems are adopting. If you are using slim `tzdata` and you're *not* using `ZoneInfo`, you might find that you get no DST transitions at all, even for current dates in the US. `ZoneInfo` is currently the only major time zone library with full support for both year 2038 and slim `tzdata`.

Finally, `ZoneInfo` is incredibly fast. Because it has a C backend, it's significantly faster than `pytz` or `dateutil` on pretty much every benchmark. So, you don't have to give up any performance to get these benefits.

