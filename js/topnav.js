/* Open Parafrase Weergave — gedeelde bovenbalk (shared nav).
 * Gebruik: laad /js/auth-bootstrap.js als module in de head; plaats
 * <nav id="topnav"></nav> in de body en laad dit script er direct na.
 * Injecteert de canonieke balk (merk, links, zoekbalk, thema-knop, auth-slot, hamburger)
 * en zet de actieve link op basis van de huidige pagina. Zo blijft de nav overal gelijk. */
(function () {
    /* Adressen van de zustersites (OGW voor wiki en achtergrond). Pagina's
       die ze al bij het laden nodig hebben, laden sites.js zelf vooraan. */
    if (!window.KASites && !document.querySelector('script[src$="sites.js"]')) {
        var sitesScript = document.createElement('script');
        sitesScript.src = 'js/sites.js';
        document.head.appendChild(sitesScript);
    }

    var nav = document.getElementById('topnav');
    if (!nav) return;
    nav.classList.remove('opw-sitekop');

    /* === Zustersites: gelijk in de drie sites (OV, OGW, OPV) ===============
       Eén strook boven de navigatie, met de drie sites in dezelfde volgorde en
       de eigen site goud onderstreept. Dit blok staat letterlijk gelijk in
       js/topnav.js van de Open Vertaling, Open Gods Woord en de Open Parafrase
       Weergave, met zijn eigen opmaak en lettertype; pas het in alle drie tegelijk
       aan. Lokaal vult sites.js (KASites.vulLinks) de adressen met de poorten. */
    var ZUSTERSITES = [
        ['ov', 'https://openvertaling.nl/', 'data-ov-href', 'Open Vertaling'],
        ['ogw', 'https://opengodsword.com/', 'data-ogw-href', 'Open Gods Woord'],
        ['opv', 'https://open-parafrase-weergave.nl/', 'data-opv-href', 'Open Parafrase Weergave']
    ];
    var ZUSTERSTIJL = [
        '.ka-fam { display: flex; align-items: center; justify-content: space-between; gap: 6px 14px;',
        '    padding: 5px 30px; min-height: 28px; background: var(--navy-deep, #0d2131); color: #c9d3db;',
        '    font: 400 12px/1.4 system-ui, -apple-system, "Segoe UI", Roboto, Arial, sans-serif;',
        '    letter-spacing: .02em; position: relative; z-index: 301; }',
        '.ka-fam-label { opacity: .78; }',
        '.ka-fam-links { display: flex; flex-wrap: wrap; align-items: center; gap: 2px 4px; }',
        '.ka-fam-links a { color: #c9d3db; text-decoration: none; padding: 2px 6px; border-radius: 4px; border: 0; }',
        '.ka-fam-links a:hover { color: #fff; background: rgba(255,255,255,.07); }',
        '.ka-fam-links a[aria-current] { color: #fff; font-weight: 600;',
        '    box-shadow: inset 0 -2px 0 var(--gold, #cba449); border-radius: 0; }',
        ':root[data-theme="donker"] .ka-fam-links a { color: #c9d3db !important; }',
        ':root[data-theme="donker"] .ka-fam-links a[aria-current] { color: #fff !important; }',
        '.ka-fam-sep { opacity: .45; }',
        '.ov-ingebed .ka-fam { display: none; }',
        ':root[lang="ar"] .ka-fam { letter-spacing: 0; text-transform: none; }',
        ':root[dir="rtl"] .ka-fam-links { direction: ltr; }',
        '@media (max-width: 768px) {',
        '    .ka-fam { padding: 3px 8px; justify-content: center; font-size: 11px; letter-spacing: 0; }',
        '    .ka-fam-links { flex-wrap: nowrap; white-space: nowrap; gap: 0 2px; }',
        '    .ka-fam-links a { padding: 2px 3px; }',
        '    .ka-fam-label { display: none; }',
        '    .ogw-lezer .ka-fam { display: none; }',
        '}'
    ].join('\n');

    function familiestrook(huidig) {
        if (!document.getElementById('ka-fam-stijl')) {
            var stijl = document.createElement('style');
            stijl.id = 'ka-fam-stijl';
            stijl.textContent = ZUSTERSTIJL;
            document.head.appendChild(stijl);
        }
        var strook = document.createElement('div');
        strook.className = 'ka-fam';
        strook.id = 'ka-fam';
        strook.setAttribute('role', 'navigation');
        strook.setAttribute('aria-label', 'Zustersites van de kleine ark');
        strook.innerHTML =
            '<span class="ka-fam-label">Familie van de kleine ark</span>' +
            '<span class="ka-fam-links" translate="no" dir="ltr">' +
            ZUSTERSITES.map(function (site) {
                return site[0] === huidig
                    ? '<a href="index.html" aria-current="page">' + site[3] + '</a>'
                    : '<a href="' + site[1] + '" ' + site[2] + '="">' + site[3] + '</a>';
            }).join('<span class="ka-fam-sep" aria-hidden="true">·</span>') +
            '</span>';
        if (window.KASites) window.KASites.vulLinks(strook);
        return strook;
    }
    /* === einde zustersites ================================================= */

    if (!document.querySelector('script[src$="global-options-host.js"]')) {
        var hostScript = document.createElement('script');
        hostScript.src = 'js/global-options-host.js';
        document.head.appendChild(hostScript);
    }

    /* Ingebed in de wiki? Die laadt pagina's in een iframe, en dan verschijnt
       de hele site nóg een keer binnen zichzelf: een tweede bovenbalk, en bij
       acht pagina's ook een tweede documentatie-zijbalk. Binnen een iframe
       renderen we daarom geen navigatie en laden we de zweefknoppen niet. De
       markering op <html> laat de CSS de eigen zijbalk van de pagina en de
       lege balk verbergen. */
    var ingebed;
    try { ingebed = window.self !== window.top; }
    catch (e) { ingebed = true; }   // andere herkomst: dan zitten we zeker ingebed
    if (ingebed) {
        document.documentElement.classList.add('ov-ingebed');
        return;
    }

    /* Logo: een opkomende zon boven de horizon, in navy, goud en zand. */
    var ZON = '<svg class="opv-zon" width="40" height="40" viewBox="0 0 40 40" aria-hidden="true" focusable="false">' +
        '<rect class="opv-zon-vlak" width="40" height="40" rx="12" fill="#142e42"/>' +
        '<path d="M9 26a11 11 0 0 1 22 0z" fill="#cba449"/>' +
        '<rect x="7" y="27.5" width="26" height="2.4" rx="1.2" fill="#f3ebdc"/>' +
        '<path d="M20 8.5v4M11.5 12.5l2.4 2.6M28.5 12.5l-2.4 2.6" stroke="#cba449" stroke-width="2" stroke-linecap="round"/></svg>';
    var PIJL = '<span class="opv-ext" aria-hidden="true">&#8599;</span>';
    var lezer = document.body.classList.contains('opv-lezerpagina');

    nav.insertAdjacentElement('beforebegin', familiestrook('opv'));
    nav.setAttribute('aria-label', 'Hoofdmenu');
    nav.innerHTML =
        '<div class="opv-balk">' +
            '<a class="topnav-brand-link opv-merk" href="index.html" aria-label="Open Parafrase Weergave, naar de startpagina">' + ZON +
                '<span class="opv-merk-naam">Open Parafrase Weergave<small>Gods Woord in begrijpelijke taal</small></span>' +
            '</a>' +
            (lezer ? '<button type="button" class="opv-hfst" id="opv-hfst" aria-label="Kies boek en hoofdstuk" aria-haspopup="dialog">' +
                '<span class="mp-label">Kies een boek</span>' +
                '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 9l6 6 6-6"/></svg>' +
            '</button>' : '') +
            '<div class="opv-rechts">' +
                '<div class="opv-links" id="topnav-links">' +
                    '<a href="/bijbel/">Alle boeken</a>' +
                    '<a href="/woordenboek.html">Woordenboek</a>' +
                    '<a href="over-opv.html">Over OPW</a>' +
                    '<a href="https://opengodsword.com/wiki.html" data-ogw-href="wiki.html" title="Wiki, Bijbelachtergrond en broninformatie op Open Gods Woord">Achtergrond ' + PIJL + '</a>' +
                '</div>' +
                '<button type="button" class="opv-icoon" id="topnav-zoek" aria-label="Zoeken" title="Zoeken (Ctrl+K)">' +
                    '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="11" cy="11" r="6.5"/><path d="M20 20l-4.2-4.2"/></svg>' +
                '</button>' +
                '<button type="button" class="opv-icoon opv-aa" id="topnav-weergave" aria-label="Leesinstellingen" aria-controls="sidebar-right" aria-expanded="false" title="Leesinstellingen">Aa</button>' +
                '<button type="button" class="opv-icoon topnav-theme" id="topnav-theme-toggle" title="Licht of nacht" aria-label="Wissel tussen licht en nacht">' +
                    '<svg class="theme-icon-sun" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41"/></svg>' +
                    '<svg class="theme-icon-moon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>' +
                '</button>' +
                '<div id="auth-slot" class="topnav-auth" hidden></div>' +
                '<button type="button" class="opv-icoon opv-menu" id="topnav-hamburger" aria-label="Menu" aria-controls="topnav-links" aria-expanded="false">' +
                    '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h16"/></svg>' +
                '</button>' +
            '</div>' +
        '</div>' +
        (lezer ? '<div class="opv-voortgang" id="opv-voortgang" aria-hidden="true"><i></i></div>' : '');

    var menuKnop = document.getElementById('topnav-hamburger');
    var navLinks = document.getElementById('topnav-links');
    menuKnop.addEventListener('click', function () {
        var open = !navLinks.classList.contains('open');
        navLinks.classList.toggle('open', open);
        menuKnop.classList.toggle('open', open);
        menuKnop.setAttribute('aria-expanded', open ? 'true' : 'false');
    });

    document.getElementById('topnav-zoek').addEventListener('click', function () {
        if (window.Search && window.Search.open) window.Search.open();
        else location.href = 'index.html?q=';
    });

    var optiesKnoppen = [
        document.getElementById('topnav-weergave')
    ].filter(Boolean);
    function openWeergave(trigger) {
            if (lezer && document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', function () {
                    openWeergave(trigger);
                }, { once: true });
                return;
            }
            if (window.OptionsPanel && document.getElementById('sidebar-right')) {
                // De hoofdlezer heeft het paneel al in het document; daar
                // hoeft de host niet eerst asynchroon te worden geladen.
                window.OptionsPanel.init();
                window.OptionsPanel.open(trigger);
            } else if (window.GlobalOptionsHost) {
                window.GlobalOptionsHost.ensure().then(function () {
                    window.OptionsPanel.open(trigger);
                });
            } else {
                window.addEventListener('ov:options-host-loaded', function () {
                    openWeergave(trigger);
                }, { once: true });
            }
    }
    optiesKnoppen.forEach(function (optiesKnop) {
        optiesKnop.dataset.globalOptionsBound = 'true';
        optiesKnop.addEventListener('click', function () { openWeergave(optiesKnop); });
    });

    document.getElementById('topnav-theme-toggle').addEventListener('click', function () {
        window.OVTheme.toggle();
    });

    /* Het versienummer stond hier hardgecodeerd en liep daardoor achter: bij
       v0.28.0 wees de balk nog naar v0.26.0. Nu komt hij uit data/stats.json,
       dat build_stats.py bij elke uitgave bijwerkt — zo kan hij niet meer
       verouderen. Mislukt het ophalen (offline, eerste bezoek zonder cache),
       dan blijft het beletselteken staan; een verkeerd nummer tonen is erger
       dan geen nummer. */
    (function () {
        var el = document.getElementById('topnav-versie');
        if (!el) return;
        fetch('data/stats.json')
            .then(function (r) { return r.ok ? r.json() : null; })
            .then(function (s) { if (s && s.version) el.textContent = s.version; })
            .catch(function () { /* stil: de balk werkt ook zonder nummer */ });
    })();


    if (window.KASites) window.KASites.vulLinks(nav);

    var page = (location.pathname.split('/').pop() || 'index.html');
    var wikiPages = {
        'downloads.html': true
    };
    var links = nav.querySelectorAll('.opv-links a');
    for (var i = 0; i < links.length; i++) {
        var href = links[i].getAttribute('href') || '';
        var file = href.split('#')[0].split('?')[0];
        if (file === page || (file === 'wiki.html' && wikiPages[page])) {
            links[i].classList.add('active');
            links[i].setAttribute('aria-current', 'page');
        }
    }

    // Mobiele zoomregeling (zweefknop −/+) — self-contained, op elke pagina.
    if (!document.querySelector('script[src$="zoom.js"]')) {
        var zs = document.createElement('script'); zs.src = 'js/zoom.js'; zs.async = false;
        document.head.appendChild(zs);
    }

    // Scherm aan houden — alleen waar daadwerkelijk gelezen wordt, niet op
    // contact- of overzichtspagina's waar niemand lang blijft.
    var leespagina = lezer || (page === 'index.html' || page === 'lees.html' || page === '');
    if (leespagina && !document.querySelector('script[src$="wake-lock.js"]')) {
        var ws = document.createElement('script'); ws.src = 'js/wake-lock.js'; ws.async = false;
        document.head.appendChild(ws);
    }

    // Natuurgeluid onder de voorlezing. Doet niets zolang er geen opnames in
    // data/natuurgeluiden.json staan, dus veilig om altijd te laden.
    if (leespagina && !document.querySelector('script[src$="natuurgeluid.js"]')) {
        var ns = document.createElement('script'); ns.src = 'js/natuurgeluid.js'; ns.async = false;
        document.head.appendChild(ns);
    }
})();
