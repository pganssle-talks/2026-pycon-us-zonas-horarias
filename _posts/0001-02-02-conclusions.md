<!-- .slide: data-state="hide-right-arrow" -->
<!-- .slide: data-visibility="hidden" -->

<div class="bullet-container code-indented">

# Resumen

<div style="text-align: center; font-size: 1.2em; font-style: italic">No hay atajos: ¡tienes que entender tus abstracciones!</div>

<div>

- ¿Qué quieres representar?
  - Tiempo absoluto (UTC, *timestamps*)
  - Hora de reloj (zona IANA, hora local)

- ¿Cuál zona aplica?

</div>

<div>

- ¿Cuál semántica aplica a tu cálculo?
  - Tiempo absoluto: ¿cuánto tiempo ha pasado o pasará?
  - Tiempo de reloj: ¿cuántas horas *nominales* han pasado o pasarán?

</div>

<!--

<div class="bullet-with-headers">


### Bonus

Nunca tienes que usar `total_seconds()`:

```python
>>> timedelta(days=3, minutes=4).total_seconds() / 60   # ❌
>>> timedelta(days=3, minutes=4) / timedelta(minutes=1) # ✅
4324.0

>>> timedelta(days=3, minutes=4) / timedelta(minutes=4)
1081.0

>>> timedelta(weeks=1) / timedelta(hours=1)
168.0
```

</div>
-->

</div>

Notes:

Sé que normalmente la gente prefiere cuando rematas con un resumen con unos «top tips» simples que sinteticen la charla, pero pensándolo bien, me he dado cuenta de que, en realidad, el tema de esta charla es que aquí no hay atajos: no hay reglas simples como "usa siempre UTC", porque todo depende mucho del contexto.
Así que en vez de reglas simples, os presento unas preguntas que os podéis hacer. Podéis preguntaros, "¿Qué quiero representar?". Si es un evento en el pasado como un log, o algo en el futuro que no depende del reloj humano como la llegada de un asteroide o algo así, probablemente puedes usar UTC o timestamps. En otros casos, tienes que usar la hora local de alguna zona.

Y para cálculos, otra vez preguntaos cuál semántica será mejor: ¿te importa la cantidad del tiempo, o te importan los cálculos en un calendario? Si quieres "la misma hora en siete días", usas tiempo del reloj. Si quieres saber "cuántos segundos han pasado entre estos `datetime`s", usas tiempo absoluto.

<!--
Y finalmente, tengo un bonus, que no tiene que ver mucho con zonas horarias pero es un «tip» que no se descubre fácilmente y es muy útil. Si quieres saber cuántas veces cabe una unidad en un periodo de tiempo, en vez de usar `total_seconds` e intentar dividir por el número de segundos de la unidad, puedes dividir directamente por un `timedelta` que represente la unidad. Es por eso que no hay un `total_minutes` ni `total_hours` u otros métodos en `timedelta`: incluso `total_seconds` fue un error, porque el Core Dev que lo añadió no sabía este tip.

-->

--

<!-- .slide: data-state="hide-right-arrow" -->

<div class="centered-container">

# ¡Gracias! <!-- .element: style="margin-top: 0.5em" -->

<div style="display: flex; flex-direction: row;">

<div>
<img
    src="external-images/with_time.png"
    class="splash"
    style="max-width: 40dvw"
    alt="Un híbrido entre un globo terráqueo y un reloj"
/>
</div>
<div class="left-container"
style="font-size: 1.5em; display: flex; flex-direction: column; justify-content: center; margin-left: 2em; ">
    <p><b>Página web:</b> <a href="https://ganssle.io">https://ganssle.io</a></p>
    <p><b>Blog:</b> <a href="https://blog.ganssle.io">https://blog.ganssle.io</a></p>
    <p><b>Mastodon:</b> <a href="https://qoto.org/@pganssle">@pganssle@qoto.org</a></p>
    <p><b>Github:</b> <a href="https://github.com/pganssle">@pganssle</a></p>
    <p><b>Gitlab:</b> <a href="https://gitlab.com/pganssle">@pganssle</a></p>
</div>
</div>

</div>

Notes:

Okay, y hasta aquí mi charla. Espero que hayáis aprendido un poco sobre zonas horarias.

No creo que nos quede tiempo para preguntas, pero aquí tenéis mi información, y estaré en los pasillos después de la charla y luego deambulando por la conferencia; o sea, si no habré muerto de vergüenza pensando en los errores que haya cometido 😅

No, es broma, habéis sido una audiencia genial. Hace casi tres años, empecé a aprender español, y el año pasado, mejorar lo suficiente para dar una charla ha sido algo entre meta y reto para mí, así que, ya cumplido, os agradezco que hayáis venido y participado en este pequeño hito personal. Nos vemos por los pasillos.

[45s; T: 29m 30s]
