# Introducción

## UTC

- Zona horaria de referencia
- Cambia a casi un segundo por segundo (¿qué son unos segundos intercalares entre amigos?)
<br/>
<br/>

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

Notes:

Empecemos por lo fácil, aclarando qué es el UTC. El UTC es la zona horaria de referencia; es el cero respecto al cual se miden los desplazamientos.

Debería ser un reloj que avance de manera monótona y lineal, pero parece que los comités de estándares nos odian, así que existen los segundos intercalares — o mejor dicho, existían, porque se ha hablado de que van a dejar de añadirlos al UTC, lo cual es lo correcto, porque los segundos intercalares no tienen cabida alguna en el tiempo civil.

Otro concepto importante es conocer la diferencia entre zonas horarias y desplazamientos. "UTC menos seis" es un desplazamiento (u *offset*). Significa que, para obtener la hora local, hay que restar seis horas al UTC.

"America/Chicago" es una zona horaria (también llamada huso horario). Es un conjunto de reglas que determinan cómo varían los desplazamientos en función del tiempo, normalmente asociados a una región del mundo. En este caso, la zona se llama "America/Chicago" porque Chicago es la ciudad más grande que sigue este conjunto de reglas.

Y quizás hayáis visto algo como "CST". "CST" es una abreviatura que depende totalmente del contexto en el que se encuentre. En Chicago significa *Central Standard Time*, que es UTC-6. Pero si estás en Cuba, significa UTC-5, y en China significa *China Standard Time*, que es UTC+8.

Un consejo: nunca confiéis en estas abreviaturas de tres letras. No intentéis parsearlas para obtener una zona horaria específica si podéis evitarlo. No deis por hecho que tengan un significado único y ni siquiera asumáis que todas las zonas tienen una abreviatura asociada.

[1m 15s; T: 1m 45s]
