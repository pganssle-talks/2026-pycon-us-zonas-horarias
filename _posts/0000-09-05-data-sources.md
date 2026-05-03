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

Así que ya mencioné zonas horarias de IANA algunas veces, y esto refiere a la fuente de los datos. Esto a veces se llama el base de datos de Olson o tzdb. Es basicamente el base de datos canonico sobre zonas horarias que todo el mundo usa. Tiene información historica remontandose hasta al menos mil novecientos setenta, y en la mayoría de lugares mucho más allá.

Es de software libre y bastantes sistemas operativos lo incluyen, pero el problema es que hacen releases entre dos y ventiuno veces al año, a veces con muy poca antelación. Por promedio, eso sucedio mas frequentemente que occuren meses con treinta días, lo que no funciona bien con la cadencia annual del release de Python, y mucho menos con el ritmo con que se actualiza la mayoría de deploys reales, así que no podemos atar los datos directamente al release de Python.

(IANA = Internet Assigned Numbers Authority)

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

Decidimos resolver este dilema covertiendolo en una situación de "traer sus propios datos". En vez de incluir un base de datos directamente en Python, `zoneinfo` buscalo en ubicaciones bien conocidas, y puedes configurar la ruta de busqueda de varias formas. Tambien proporcionamos un paquete (?) de PyPI que puedes usar como fallback para plataformas que no traen los datos en forma acesible, como Windows.

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

```python
>>> dt = datetime(2020, 11, 12, 19, tzinfo=ZoneInfo("America/Chicago"))
>>> print(dt)
2020-11-12 19:00:00-06:00

>>> print(datetime.now(ZoneInfo("America/Chicago")))
2020-11-12 19:46:21.211438-06:00
```

</div>

<div class="bullets-with-header">

## Convertir entre zonas

```python
>>> print(dt.astimezone(ZoneInfo("Europe/Paris")))
2020-11-13 02:00:00+01:00
```

</div>
<div class="small-spacer"></div>
</div>

Notes:

Hoy en dia si usas cualquier version apoyada de Python, puedes usar el modulo `zoneinfo` para tus zonas IANA. En versiones anteriores que 3.9, hay un backport que pudieras usar, pero sin importar como obtienes tus objetos `ZoneInfo`, ahora puedes usar los idioms estandares de Python para construir datetimes conscientes, como muestran en la documentación: pasando tu `tzinfo` al constructor, al `.replace` o `.now` o `.astimezone`.

Aunque lo importante a notar aquí es que en este mundo post-`pytz`, es mucho más probable que te enfrentes a las semánticas poco intuitivas inherentes al modelo de `datetimes` que tiene Python.
