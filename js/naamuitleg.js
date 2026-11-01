/* Zet de betekenis van een naam tussen haakjes achter de naam, één keer per
   hoofdstuk: de aanroeper geeft daarvoor per hoofdstuk één Set mee.
   De gegevens staan in js/naamsbetekenissen.js; Open Gods Woord is de bron.
   scripts/build_leespaginas.py doet hetzelfde voor de vooraf gebouwde pagina's.

   Geen lookbehind: die breekt de hele lezer op iPadOS 15. */
(function (global) {
    const NIET_NA = /[.!?:;…‘’“”"'(]\s*$/;
    let patroon = null;

    function maakPatroon(namen) {
        const vormen = Object.keys(namen).sort((a, b) => b.length - a.length)
            .map(naam => naam.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
        return vormen.length ? new RegExp(`(^|[^\\p{L}\\p{N}-])(${vormen.join('|')})(?![\\p{L}\\p{N}-])`, 'gu') : null;
    }

    /* Woorden als Dan en Er zijn aan het begin van een zin gewoon Nederlands. */
    function zinsbegin(tekst, positie) {
        const ervoor = tekst.slice(0, positie);
        return !ervoor.trim() || NIET_NA.test(ervoor);
    }

    /* Abrahams is dezelfde persoon als Abraham. */
    function persoon(naam, namen) {
        const stam = naam.endsWith('s') ? naam.slice(0, -1) : naam;
        return namen[stam] ? stam : naam;
    }

    /* Haran de stad is niet Haran de broer van Abram: sommige namen tellen alleen
       in de verzen waar de persoon bedoeld is. */
    function persoonBedoeld(naam, gegevens, plek) {
        if (!plek) return true;
        const wie = persoon(naam, gegevens.namen);
        const alleen = gegevens.alleenInVerzen && gegevens.alleenInVerzen[wie];
        if (alleen && !alleen.includes(plek)) return false;
        const niet = gegevens.nietInVerzen && gegevens.nietInVerzen[wie];
        return !(niet && niet.includes(plek));
    }

    function inTekst(tekst, gegevens, gezien, plek) {
        patroon.lastIndex = 0;
        return tekst.replace(patroon, (geheel, voor, naam, positie) => {
            const start = positie + voor.length;
            if (gegevens.alleenMiddenInZin.includes(naam) && zinsbegin(tekst, start)) return geheel;
            if (!persoonBedoeld(naam, gegevens, plek)) return geheel;
            if (gezien) {
                const wie = persoon(naam, gegevens.namen);
                if (gezien.has(wie)) return geheel;
                gezien.add(wie);
            }
            return `${voor}${naam} (${gegevens.namen[naam]})`;
        });
    }

    function voegToe(html, gegevens = global.NAAMSBETEKENISSEN, gezien = null, plek = null) {
        if (!html || !gegevens) return html;
        if (!patroon) patroon = maakPatroon(gegevens.namen);
        if (!patroon) return html;
        return html.split(/(<[^>]+>)/).map((deel, index) => index % 2 ? deel : inTekst(deel, gegevens, gezien, plek)).join('');
    }

    global.NaamUitleg = { voegToe };
})(typeof window !== 'undefined' ? window : globalThis);
