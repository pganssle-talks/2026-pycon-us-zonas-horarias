# Zonas horarias concretas: hora local

- UTC / Desplazamientos fijos <span class="fragment" style="color: green" data-fragment-index="1">✔ Añadidos en 3.2</span>
- Hora local
- Zonas horarias de IANA <span class="fragment" style="color: red" data-fragment-index="1">✘ (en Python 3.8)</span>

A partir de Python 3.2, los `datetime`s naífs ya se consideran hora local del sistema, y puedes adjuntarles un desplazamiento fijo para conseguir información sobre la zona horaria:

```python
>>> print(datetime(2023, 11, 4, 12).astimezone())
2023-11-04 12:00:00-04:00
```

```python
>>> print(datetime(2023, 11, 5, 12).astimezone())
2023-11-05 12:00:00-05:00
```

<br/>

Configurar el atributo `fold` en un `datetime` naíf funciona:

```python
>>> print(datetime(2023, 11, 5, 1, fold=0).astimezone())
2023-11-05 01:00:00-04:00
>>> print(datetime(2023, 11, 5, 1, fold=1).astimezone())
2023-11-05 01:00:00-05:00
```

Para más información, mirad mis posts de blog (en inglés): [Why naïve times are local times](https://blog.ganssle.io/articles/2022/04/naive-local-datetimes.html) y [Stop using utcnow and utcfromtimestamp](https://blog.ganssle.io/articles/2019/11/utcnow.html)

Notes:

Vale, entonces esto te permite empezar a implementar las otras dos formas de zona horaria que comenté antes: hora local y zonas de IANA. Y resulta que muy poca gente lo sabe, pero llevamos ya un buen rato con soporte para horas locales en `datetime`, básicamente desde la versión tres punto seis (3.6). El atributo `fold` simplemente funciona.

Pero la cosa es que se hizo un poco a escondidas, porque lo que hicieron fue cambiar el sentido de los `datetime`s naíf; antes representaban una fecha y hora abstractas, desancladas de la realidad humana, pero después se convirtieron en algo más concreto, y ahora representan una fecha y hora en la hora local de tu sistema. Así que hoy en día puedes llamar a `timestamp` o `astimezone` y ya está, Python asume que la zona horaria será la hora local de tu sistema.

Y tengo un post de blog en inglés, "Por qué las horas naíf son horas locales", que explica el tortuoso razonamiento de por qué esta es probablemente la mejor manera de hacerlo, en lugar de tener un objeto `tzinfo` que represente la hora local.

Pero algo sobre lo que quiero llamar la atención es que, en este caso, hay una interfaz parecida a la de `pytz`; si quieres saber el desplazamiento que se aplica a alguna hora local, puedes llamar a `.astimezone` sin argumentos, y le adjunta un `tzinfo` fijo al resultado para que puedas consultar `tzname` y el `utcoffset`.

Pero al igual que con `pytz`, no puedes hacer aritmética con ese tipo de cosas, se supone que tienes que hacer los cálculos antes de llamar a `astimezone`.

Así que esto nos da dos de nuestros tres tipos de zonas horarias, pero en Python tres punto ocho (3.8), todavía no teníamos zonas de IANA.
