# El modelo de zonas horarias de Python: `tzinfo`

* Las zonas horarias se definen mediante subclases de `tzinfo`.

* La información se proporciona en función del objeto `datetime`:
    * `tzname`: El nombre (normalmente abreviado) de la zona horaria para el `datetime` indicado.
    * `utcoffset`: El desplazamiento respecto a UTC para ese `datetime`.
    * <span class="fragment disappearing-fragment nospace-fragment fade-out" data-fragment-index="1">`dst`: La magnitud del desplazamiento del `datetime` que se atribuye al horario de verano (normalmente 0 o 1 hora).</span><span class="fragment nospace-fragment" data-fragment-index="1" style="color: #b70000"><strike>`dst`: La magnitud del desplazamiento del `datetime` que se atribuye al horario de verano (normalmente 0 o 1 hora).</strike></span>

<!-- TODO: Use an emphasis transition here rather than two fragments -->

Notes:

So now that we've established that you actually need to *ugh* understand the abstractions you are working with, let's get into some of the details of how it works in Python.

Python's time zone model is based around an abstract base class `tzinfo`. The idea is that each time zone object provides three functions that take the `datetime` as an argument. There's `tzname`, which gives the name of the zone at the given datetime, `utcoffset`, which does most of the heavy lifting here, this gives the offset that applies at the relevant datetime, and then `dst`, which gives you the difference between the current offset and standard time. I think basically every time I've seen someone use the `dst` method it was something that I would consider a mistake, so basically never use that last one.
