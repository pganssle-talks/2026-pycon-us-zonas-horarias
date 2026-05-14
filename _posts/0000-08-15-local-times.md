<div class="bullet-container medium-code">

# Zonas horarias concretas: hora local

- UTC / Desplazamientos fijos <span class="fragment" style="color: green" data-fragment-index="2">✔ Añadidos en 3.2</span>
- Hora local
- Zonas horarias de IANA <span class="fragment" style="color: red" data-fragment-index="2">✘ (en Python 3.8)</span>

A partir de Python 3.2, los `datetime`s naífs ya se consideran hora local del sistema, y puedes adjuntarles un desplazamiento fijo para conseguir información sobre la zona horaria:

<div class="small-spacer"></div>

```pycon
>>> print(datetime(2023, 11, 4, 12).astimezone())
2023-11-04 12:00:00-04:00
```

```pycon
>>> print(datetime(2023, 11, 5, 12).astimezone())
2023-11-05 12:00:00-05:00
```

<div class="small-spacer"></div>

<div
    class="fragment highlight-current-dashed"
    data-fragment-index="1"
>

Configurar el atributo `fold` en un `datetime` naíf funciona:

```pycon
>>> print(datetime(2023, 11, 5, 1, fold=0).astimezone())
2023-11-05 01:00:00-04:00
>>> print(datetime(2023, 11, 5, 1, fold=1).astimezone())
2023-11-05 01:00:00-05:00
```

</div>

<div class="small-spacer"></div>

<div class="footnote">

Para más información, mirad mis posts de blog (en inglés): [Why naïve times are local times](https://blog.ganssle.io/articles/2022/04/naive-local-datetimes.html) y [Stop using utcnow and utcfromtimestamp](https://blog.ganssle.io/articles/2019/11/utcnow.html)
</p>

</div>

Notes:

Vale, entonces esto te permite implementar las otras dos formas de zona horaria que comenté antes: hora local y zonas de IANA. Y resulta que muy poca gente lo sabe, pero llevamos ya bastante tiempo con soporte para horas locales en `datetime`, básicamente desde la versión tres punto seis (3.6).

Pero se hizo un poco a escondidas — los `datetime`s naíf, que antes eran horas flotantes sin zona horaria, ahora representan la hora local siempre que Python necesite convertirlos a UTC. Así que puedes llamar a `timestamp` o `astimezone` y ya está.

Tengo un post de blog en inglés que explica el tortuoso razonamiento detrás de esta decisión, pero ahora basta con decir que ya estoy convencido de que era la decisión correcta.

⏭️ Y algo aquí que quiero destacar es que si quieres saber el desplazamiento o el nombre local, tienen una interfaz tipo `pytz`: si llamas a `.astimezone` sin argumentos, te dará  un `datetime` consciente con el `tzinfo` fijo que aplica a tu sistema.

Pero no debes hacer aritmética con eso — haz los cálculos primero y luego llama a `astimezone`.

Así que esto nos da dos de nuestros tres tipos de zonas horarias, pero en Python tres punto ocho (3.8), ⏭️ todavía no teníamos zonas de IANA, y el motivo eran los datos.

[1m 30s; T: 20m 30s]
