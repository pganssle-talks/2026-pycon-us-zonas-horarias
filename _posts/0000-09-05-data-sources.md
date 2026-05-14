<div class="bullet-container">

<div class="bullets-with-header">

# Fuente de datos: Zonas horarias de IANA

- Proporciona información sobre zonas horarias históricas.
- Fuente estándar y abierta (dominio público) para información de zonas horarias.
- Muchos sistemas operativos la incluyen.
- Fuente de datos para `dateutil` y `pytz`.
- 2-21 versiones al año (9 de promedio).

</div>

<div class="centered-container">
<img src="images/all_zones.png" alt="Mapa de zonas horarias de IANA"/>
</div>
</div>

Notes:

Así que ya he mencionado las zonas horarias de IANA algunas veces, y esto se refiere a la fuente de los datos. Es básicamente la base de datos canónica sobre zonas horarias que todo el mundo usa; bastantes sistemas operativos la incluyen, pero no todos.

Y la idea era incluirla con Python como fuente de las reglas, pero el problema es que sacan versiones nuevas demasiado frecuentemente, con mucha más frecuencia que la cadencia anual de Python, y a menudo es importante que la gente reciba los datos actualizados cuanto antes.

[1m 15s; T: 20m 45s]

--

<div class="bullet-container">

# PEP 615: Soporte para la base de datos de zonas horarias de IANA en la biblioteca estándar

<div class="small-spacer"></div>

<div class="centered-container" style="height: unset; padding-bottom: unset;">

<img 
    src="images/zoneinfo-documentation.png"
    class="screenshot"
    style="max-height: 40dvh"
    alt="Captura de pantalla de la documentación de zoneinfo en Python 3.9."/>
</div>

- Se usa cuando el sistema tiene disponible la base de datos.
- Por defecto, Python busca en ubicaciones de despliegue "bien conocidas".
- Se puede configurar en el programa con `zoneinfo.reset_tzpath`.
- Se puede configurar con la variable de entorno `PYTHONTZPATH`.
- El valor por defecto se puede configurar en tu compilador.

- También proporcionamos el paquete `tzdata` en PyPI: un paquete "first party" de solo datos como fallback.

</div>

Notes:

Decidimos resolver este dilema convirtiéndolo en una situación de "traer sus propios datos". En vez de incluir una base de datos directamente en Python, `zoneinfo` la busca en ubicaciones bien conocidas, y puedes configurar la ruta de búsqueda de varias formas. También proporcionamos un paquete de PyPI que puedes usar como fallback para plataformas que no traen los datos de forma accesible, como Windows.

[1m; T: 21m 45s]

--

<div class="bullet-container medium-code">

# Cómo usar `zoneinfo`

<div class="bullets-with-header">

## Backport (3.6+)

```python
try:
    from backports import zoneinfo
except ImportError:
    import zoneinfo
```

</div>

<div class="bullets-with-header">

## Construir datetimes conscientes (aware)

```pycon
>>> dt = datetime(2020, 11, 12, 19, tzinfo=ZoneInfo("America/Chicago"))
>>> print(dt)
2020-11-12 19:00:00-06:00

>>> print(datetime.now(ZoneInfo("America/Chicago")))
2020-11-12 19:46:21.211438-06:00
```

</div>

<div class="bullets-with-header">

## Convertir entre zonas

```pycon
>>> print(dt.astimezone(ZoneInfo("Europe/Paris")))
2020-11-13 02:00:00+01:00
```

</div>
<div class="small-spacer"></div>
</div>

Notes:

Hoy en día si usas cualquier versión con soporte de Python, y incluso muchas versiones sin soporte, puedes usar el módulo `zoneinfo` para tus zonas IANA.

Y no tengo que explicaros cómo usarlo porque lo haces como os imaginaréis. Pasas un objeto `ZoneInfo` al constructor o `.replace` o `.now` o `.astimezone` y funciona bien.

Aunque lo importante a notar aquí es que en este mundo post-`pytz`, es mucho más probable que te enfrentes a las semánticas poco intuitivas inherentes al modelo de `datetimes` que tiene Python.

[1m; T: 22m 45s]
