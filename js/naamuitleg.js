/* Zet de betekenis van een naam tussen haakjes achter de naam.
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

    function inTekst(tekst, gegevens) {
        patroon.lastIndex = 0;
        return tekst.replace(patroon, (geheel, voor, naam, positie) => {
            const start = positie + voor.length;
            if (gegevens.alleenMiddenInZin.includes(naam) && zinsbegin(tekst, start)) return geheel;
            return `${voor}${naam} (${gegevens.namen[naam]})`;
        });
    }

    function voegToe(html, gegevens = global.NAAMSBETEKENISSEN) {
        if (!html || !gegevens) return html;
        if (!patroon) patroon = maakPatroon(gegevens.namen);
        if (!patroon) return html;
        return html.split(/(<[^>]+>)/).map((deel, index) => index % 2 ? deel : inTekst(deel, gegevens)).join('');
    }

    global.NaamUitleg = { voegToe };
})(typeof window !== 'undefined' ? window : globalThis);
