<div class="bullet-container">

<div class="bullets-with-header">

# El modelo de zonas horarias de Python: `tzinfo`

* Las zonas horarias se definen mediante subclases de `tzinfo`.

* La información se proporciona en función del objeto `datetime`:
    * `tzname`: El nombre (normalmente abreviado) de la zona horaria para el `datetime` indicado.
    * `utcoffset`: El desplazamiento respecto a UTC para ese `datetime`.
    * <span class="fragment strike highlight-red" data-fragment-index="1">`dst`: La magnitud del desplazamiento del `datetime` que se atribuye al horario de verano (normalmente 0 o 1 hora)</span>

</div>
</div>

Notes:

Ya que hemos establecido que en realidad hace falta *ugh* entender las abstracciones con las que trabajamos, vamos a bucear más en los detalles de cómo funciona en Python.

El modelo de zonas horarias de Python se centra en una clase base abstracta que se llama `tzinfo`. La idea es que cada objeto que representa una zona horaria proporciona tres funciones que toman como argumento un `datetime`.

Tienes `tzname`, que da el nombre de la zona para el `datetime` indicado, y `utcoffset`, que es la que de verdad tira del carro; esa función da el desplazamiento respecto al UTC que se aplica al `datetime`.

Y finalmente tenemos a la oveja negra de la familia, `dst`, que da la diferencia entre el desplazamiento actual y el horario estándar. La verdad es que creo que cada vez que he visto a alguien usar este método ha sido un error de algún tipo.

[1m; T: 11m15s]
