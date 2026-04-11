# Introducción

## UTC

- Zona horaria de referencia
- Cambia a casi un segundo por segundo (¿qué son unos segundos intercalares entre amigos?)
<br/>
<br/>

## Zonas horarias vs. desplazamientos <!-- .element: class="fragment" data-fragment-index="1" -->

<ul class="fragment" data-fragment-index="1">
    <li><tt>UTC-6</tt> es un desplazamiento</li>
    <li><tt>America/Chicago</tt>  es una zona horaria / un huso horario</tt></li>
    <li><tt>CST</tt> es una abreviatura poco fiable que depende mucho en su contexto
        <ul>
            <li>Central Standard Time (<tt>UTC-6</tt>)</li>
            <li>Cuba Standard Time (<tt>UTC-5</tt>)</li>
            <li>China Standard Time (<tt>UTC+8</tt>)</li>
        </ul>
    </li>
<ul>

Notes:

We can start out easy, with UTC. UTC is the reference time zone, it's the 0 against which offsets are measured. It is mostly monotonic — which is to say that it doesn't have daylight saving time. It still has leap seconds, which is infuriating, since leap seconds don't belong in civil time *at all*, much less in the reference time zone, but there has recently been talk of ending the practice of leap seconds, so hopefully, going forward, UTC will actually record 1 second per second of elapsed time.

Another concept that is important to know is the difference between time zones and offsets.

UTC-6 is an offset. It means that you should add 6 hours to the local time to get a time in UTC.

`America/Chicago` is a time zone - it's the set of rules for what offsets and abbreviations apply in a given region as a function of time. In this case, Chicago is the largest city in the region that observes these rules, which is why the zone is called that.

`CST` is a highly context-dependent abbreviation referring to an offset. In Chicago, it means Central Standard Time, which is UTC-6, but if you're in Cuba, it means UTC-5, and if you're in China, it means UTC+8.

Word of advice: never rely on these 3-letter abbreviations. Don't try to parse them into a specific time zone if you can avoid it, don't rely on them meaning a specific thing, and don't even rely on every zone having an associated 3-letter abbreviation.

[1m 15s; T: 1m 45s]
