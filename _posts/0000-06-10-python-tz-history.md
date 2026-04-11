# History of Python's Time Zones

When `datetime` was introduced in [Python 2.3](https://docs.python.org/3/whatsnew/2.3.html#date-time-type), there were *no* concrete time zones in the standard library.
<div class="small-spacer"></div>

```python
from dateutil import relativedelta as rd  # Cheating...

class ET(tzinfo):
    def utcoffset(self, dt):
        if self.isdaylight(dt):
            return timedelta(hours=-4)
        else:
            return timedelta(hours=-5)

    def dst(self, dt):
        if self.isdaylight(dt):
            return timedelta(hours=1)
        else:
            return timedelta(hours=0)

    def tzname(self, dt):
        return "EDT" if self.isdaylight(dt) else "EST"

    def isdaylight(self, dt):
        dst_start = datetime(dt.year, 1, 1) + rd.relativedelta(month=3, weekday=rd.SU(+2),
                                                               hour=2)
        dst_end = datetime(dt.year, 1, 1) + rd.relativedelta(month=11, weekday=rd.SU,
                                                             hour=2)

        return dst_start <= dt.replace(tzinfo=None) < dst_end
```

Notes:

All right, so historically, that was pretty much what you got in Python. In Python 2.3 they said, "Here is an interface, but we don't want to deal with implementing rules for you." You're supposed to figure out according to your business logic what's the best way to represent time zones, and you're maybe supposed to do something like this, where you have a class that represents Eastern Time and it has its set of rules.

--

# History of Python's Time Zones: Concrete Time Zones

- UTC / Fixed Offsets <span class="fragment" style="color: green" data-fragment-index="1">✔ Added in 3.2</span>
- Local time
- IANA Time Zones

<p style="text-align: center">
<img src="images/whatsnew3.2.png" alt="What's new in Python 3.2 excerpt"
     class="fragment" data-fragment-index="1" />
</p>

Notes:

But if you think about it, there's really only three kinds of time zones that the vast majority of people want to look at.

One is UTC or fixed offsets thereof, the other is local time, which is like whatever time it is on your laptop or something, and the third one is the IANA time zone database, which is basically that America/Chicago, America/New_York kind of thing.

And the first one is actually like super easy, because that just returns a fixed `timedelta`. So that was added early on in 3.2. But these other two, it turns out to be a little bit trickier.

--

<!-- .slide: data-visibility="hidden" -->

# History of Python's Time Zones: Ambiguous time problem

```python
EASTERN = ET()

print(datetime(2017, 11, 4, 12, 0, tzinfo=EASTERN))
print(datetime(2017, 11, 5, 12, 0, tzinfo=EASTERN))
```

```
2017-11-04 12:00:00-04:00
2017-11-05 12:00:00-05:00
```

<br/><br/>

```python
dt_before_utc = datetime(2017, 11, 5, 0, 30, tzinfo=EASTERN).astimezone(datetime.UTC)
dt_during = (dt_before_utc + timedelta(hours=1)).astimezone(EASTERN)  # 1:30 EDT
dt_after = (dt_before_utc + timedelta(hours=2)).astimezone(EASTERN)   # 1:30 EST

print(dt_during)   # Lookin good!
print(dt_after)    # OH NO!
```

```
2017-11-05 01:30:00-04:00
2017-11-05 02:30:00-05:00
```

--

# Ambiguous times

Ambiguous times are times where the same "wall time" occurs twice, such as during a DST to STD transition.
<br/>

```python
from dateutil import tz

dt1 = datetime(2004, 10, 31, 4, 30, tzinfo=timezone.utc)
for i in range(4):
    dt = (dt1 + timedelta(hours=i)).astimezone(NYC)
    print('{} | {} |  {}'.format(dt, dt.tzname(), 
                                   'Ambiguous' if tz.datetime_ambiguous(dt)
                                   else 'Unambiguous'))
```

<br/>
<pre>
2004-10-31 00:30:00-04:00 | EDT |  Unambiguous
2004-10-31 01:30:00-04:00 | EDT |  Ambiguous
2004-10-31 01:30:00-05:00 | EST |  Ambiguous
2004-10-31 02:30:00-05:00 | EST |  Unambiguous
</pre>

<br/>

There can be multiple times in a time zone differentiated by their offset!

Notes:

And to explain why, I have to have a little digression and talk about ambiguous times.

Ambiguous times are times where the same wall time occurs twice, so like when you set your clock back one hour, right? It'll be 1:59, and then one minute later you go back one hour and then it's 1:59 again about an hour later, right?

And you'll notice that in this list here I have two 1:30s, and their main difference is the offset. That's what differentiates those two times on the timeline. But if you recall, `datetime`'s model is that the `tzinfo` time zone object just takes as its argument the naïve portion of the `datetime`, so it's actually impossible to disambiguate these two things because they are differentiated only by the *output* of those functions.

And this is a fundamental problem, a flaw that existed in the `tzinfo` interface at the time.

--

# Imaginary times

The complement of ambiguous times is imaginary times — wall times that don't exist in a given time zone, such as during an STD to DST transition.


```python
dt1 = datetime(2004, 4, 4, 6, 30, tzinfo=timezone.utc)
for i in range(3):
    dt = (dt1 + timedelta(hours=i)).astimezone(NYC)
    print(f'{dt} | {dt.tzname()} ')
```

<br/>
<pre>
2004-04-04 01:30:00-05:00 | EST
2004-04-04 03:30:00-04:00 | EDT
2004-04-04 04:30:00-04:00 | EDT
</pre>

Notice the lack of a `2004-04-04 02:30:00`!

Notes:

And then there's the complement of this, which is a lot easier to solve, which is called imaginary times. And these are basically times that don't exist in a given time zone, like when you jump forward an hour, any time in that gap doesn't correspond to a real time.

This one's easier to deal with because these times just don't exist rather than being unrepresentable, but also in that case what offset are you supposed to use for the offset? It's undefined.
