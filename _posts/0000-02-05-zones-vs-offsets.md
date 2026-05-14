<div class="bullet-container">

# Introducción

<div class="bullets-with-header">

## UTC

- Zona horaria de referencia
- Avanza a casi un segundo por segundo (¿qué son unos segundos intercalares entre amigos?)

</div>
<div class="bullets-with-header">

## Zonas horarias vs. desplazamientos <!-- .element: class="fragment" data-fragment-index="1" -->

<ul class="fragment" data-fragment-index="1">
    <li><tt>UTC-6</tt> es un desplazamiento</li>
    <li><tt>America/Chicago</tt> es una zona horaria / un huso horario</li>
    <li><tt>CST</tt> es una abreviatura poco fiable que depende mucho de su contexto:
        <ul>
            <li>Central Standard Time (<tt>UTC-6</tt>)</li>
            <li>Cuba Standard Time (<tt>UTC-5</tt>)</li>
            <li>China Standard Time (<tt>UTC+8</tt>)</li>
        </ul>
    </li>
</ul>

</div>

<div class="small-spacer"></div>
</div>

Notes:

Empecemos por lo fácil, aclarando qué es el UTC, que mencionaré muchas veces en esta charla. El UTC es la zona de referencia; es el cero respecto al cual se miden los desplazamientos.

Debería ser un reloj que avance de manera monótona y lineal, pero los comités de estándares parecen odiarnos, así que han puesto segundos intercalares. Entonces, aunque es mejor que una zona con cambios de horario, el UTC tampoco está libre de complicaciones.

➡️ Otro concepto importante es la diferencia entre zonas horarias y desplazamientos. "UTC menos seis" es un desplazamiento (u *offset*). Significa que, para obtener la hora local, hay que restar seis horas al UTC.

"America/Chicago" es una zona horaria, un conjunto de reglas que nos dicen cómo varían los desplazamientos en función del tiempo, y normalmente están asociadas a una región del mundo.

Y quizás hayáis visto algo como "CST". "CST" es una abreviatura que depende totalmente del contexto. En Chicago significa *Central Standard Time*, que es UTC-6. Pero si estás en Cuba, es UTC-5, y en China es *China Standard Time*, que es UTC+8.

Un consejo: nunca confiéis en estas abreviaturas. No intentéis obtener una zona horaria específica de ellas; no deis por hecho que tengan un significado único y ni siquiera podéis asumir que todas las zonas tengan una abreviatura asociada.

[1m 45s; T: 2m 30s]
