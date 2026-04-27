# Semántica de aritmética con datetimes conscientes

Un problema análogo a la semántica de comparación es que sumar tiempo tras una transición de DST no está bien definida:

```python
>>> NYC = ZoneInfo("America/New_York")
>>> dt1 = datetime(2020, 3, 7, 13, tzinfo=NYC)
>>> dt2 = d1 + timedelta(days=1)
```

<br/>
<br/>

Dado que hay una transición entre `dt1` y `dt2`, hay dos opciones:

```python
>>> print(sumar_reloj(dt1, timedelta(days=1)))  # Siguiente día del calendario a la misma hora
2020-03-08 13:00-04:00

>>> print(sumar_absoluto(dt1, timedelta(days=1)))  # 24 horas transcurridas después de dt1
2020-03-08 12:00-04:00
```

Notes:

Y además de la comparación, hay un problema análogo con la aritmética. Porque imagínate que quieres añadir veinticuatro horas a un `datetime` justo antes de una transición de horario de verano. Puedes optar por la semántica de la hora de reloj, en la que dices en plan: "Solo dame la misma hora, pero de mañana", lo que serían, por ejemplo, veintitrés horas de tiempo real. O puedes decir: "Dame la hora que será cuando hayan pasado veinticuatro horas", lo que supone una hora de diferencia respecto al caso anterior.

--

# Semántica de aritmética con datetimes conscientes en Python

`datetime` siempre usa semántica de hora de reloj cuando interactúa con un `timedelta`:


```python
>>> print(sumar_reloj(dt1, timedelta(days=1)))
2020-03-08 13:00-04:00

>>> print(sumar_absoluto(dt1, timedelta(days=1)))
2020-03-08 12:00-04:00

>>> print(dt1 + timedelta(days=1))
2020-03-08 13:00-04:00
```

Cuando se restan dos `datetime`s, el comportamiento es diferente entre los casos de «misma zona» y «zona diferente»:

```
>>> dt2 = datetime(2020, 3, 8, 13, tzinfo=NYC)
>>> dt1_misma = datetime(2020, 3, 7, 13, tzinfo=NYC)
>>> dt1_diferente = dt1_misma.astimezone(timezone.utc)  # dt1_misma == dt1_diferente!

>>> print(dt2 - dt1_misma)
1 day, 0:00:00

>>> print(dt2 - dt1_misma)
23:00:00
```

*Consultad mi artículo de blog (en inglés) ["Semantics of timezone-aware datetime arithmetic"](https://blog.ganssle.io/articles/2018/02/aware-datetime-arithmetic.html) para un análisis más exhaustivo.*

Notes:

Y la dicotomía es la misma que con la comparación, ya que a `datetime` le gusta mucho la semántica de la hora de reloj. Así que, si añades un `timedelta`, Python dice: "Vale, esta es una operación dentro de la misma zona, así que usemos horas de reloj". Y si estás restando `datetime`s y están en la misma zona, también usa la semántica de la hora de reloj.

Pero si están en zonas diferentes, de nuevo no tiene sentido usar la semántica de hora de reloj, así que se usa tiempo absoluto. Tengo un artículo en mi blog que profundiza en por qué esto no es tan descabellado como parece; pero, aunque sea razonable, la gente no cree en absoluto que debería ser así y no paran de enviar «bug reports» diciendo que los cálculos están mal.

--

# Cómo usar `zoneinfo`: Semántica del tiempo absoluto

La semántica de hora de reloj de Python puede sorprender a muchos usuarios; para utilizar deliberadamente la semántica del tiempo absoluto, primero hay que convertir a UTC:

```python
def sumar_absoluto(dt: datetime, td: timedelta) -> datetime:
    dt_utc = dt.astimezone(timezone.utc)
    rv_utc = dt_utc + td
    return rv_utc.astimezone(dt.tzinfo)

def restar_absoluto(dt1: datetime, dt2: datetime) -> timedelta:
    dt1_utc = dt1.astimezone(timezone.utc)
    dt2_utc = dt2.astimezone(timezone.utc)

    return dt1 - dt2
```

Notes:

Por desgracia, a estas alturas ya no es algo que podamos cambiar, así que lo que os recomiendo es que definas algunas funciones auxiliares como las que tengo aquí, que tomen tus operandos y los conviertan a UTC antes de hacer las operaciones, para que así no importe si están en la misma zona o no.
