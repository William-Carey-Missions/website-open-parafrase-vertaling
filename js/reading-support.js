/* Meebewegende hoofdstukbeelden, schematische locatiekaartjes en lemma-links. */
(function () {
    const NS = 'http://www.w3.org/2000/svg';
    const root = document.getElementById('verses-container');
    if (!root) return;
    const support = {
        locations: fetch('/data/reading-locations.json').then(r => r.ok ? r.json() : { books: {} }).catch(() => ({ books: {} })),
        ground: fetch('/data/reading-groundwords.json').then(r => r.ok ? r.json() : { books: {} }).catch(() => ({ books: {} })),
        terms: fetch('/data/reading-term-index.json').then(r => r.ok ? r.json() : []).catch(() => []),
        busy: false,
    };

    function svg(tag, attributes) {
        const node = document.createElementNS(NS, tag);
        for (const [name, value] of Object.entries(attributes)) node.setAttribute(name, String(value));
        return node;
    }

    function mapCard(card) {
        const section = document.createElement('section');
        section.className = 'opw-sidecar-item opw-kaartkaart';
        section.dataset.verse = card.verse;
        const label = document.createElement('p');
        label.className = 'opw-sidecar-label';
        label.textContent = `Locaties bij ${card.heading}`;
        section.appendChild(label);

        const map = svg('svg', { viewBox: '0 0 320 180', role: 'img', 'aria-label':
            `Schematische ligging van ${card.places.map(place => place.naam).join(', ')}` });
        map.appendChild(svg('rect', { x: 0, y: 0, width: 320, height: 180, rx: 14, class: 'opw-map-bg' }));
        for (let n = 1; n < 4; n++) {
            map.appendChild(svg('path', { d: `M ${n * 80} 0 V 180 M 0 ${n * 45} H 320`, class: 'opw-map-grid' }));
        }
        const lons = card.places.map(place => place.lon);
        const lats = card.places.map(place => place.lat);
        const lonMid = (Math.min(...lons) + Math.max(...lons)) / 2;
        const latMid = (Math.min(...lats) + Math.max(...lats)) / 2;
        const lonSpan = Math.max(1.5, (Math.max(...lons) - Math.min(...lons)) * 1.5);
        const latSpan = Math.max(1.5, (Math.max(...lats) - Math.min(...lats)) * 1.5);
        const plotted = [];
        card.places.forEach((place, index) => {
            const x = Math.min(294, Math.max(26, 160 + (place.lon - lonMid) / lonSpan * 260));
            const y = Math.min(153, Math.max(27, 90 - (place.lat - latMid) / latSpan * 125));
            const cluster = plotted.find(dot => Math.hypot(dot.x - x, dot.y - y) < 25);
            if (cluster) cluster.numbers.push(index + 1);
            else plotted.push({ x, y, numbers: [index + 1] });
        });
        plotted.forEach(dot => {
            map.appendChild(svg('circle', { cx: dot.x, cy: dot.y, r: dot.numbers.length > 1 ? 17 : 12, class: 'opw-map-dot' }));
            const number = svg('text', { x: dot.x, y: dot.y + 4, 'text-anchor': 'middle', class: 'opw-map-number' });
            number.textContent = dot.numbers.length > 1 ? `${dot.numbers[0]}–${dot.numbers[dot.numbers.length - 1]}` : dot.numbers[0];
            map.appendChild(number);
        });
        section.appendChild(map);
        const list = document.createElement('ol');
        list.className = 'opw-map-places';
        card.places.forEach(place => {
            const item = document.createElement('li');
            const link = document.createElement('a');
            link.href = `https://opengodsword.com/plaats.html?plaats=${encodeURIComponent(place.id)}`;
            link.dataset.ogwHref = `plaats.html?plaats=${encodeURIComponent(place.id)}`;
            link.textContent = place.naam;
            link.title = `${place.zekerheid}; ${place.precisie}`;
            item.appendChild(link);
            list.appendChild(item);
        });
        section.appendChild(list);
        const note = document.createElement('p');
        note.className = 'opw-map-note';
        note.textContent = `Schematische ligging${card.more ? ` · ${card.more} meer in de bron` : ''}. Locaties zijn niet allemaal zeker.`;
        section.appendChild(note);
        return section;
    }

    function groundCard(card) {
        const section = document.createElement('section');
        section.className = 'opw-sidecar-item opw-grondkaart';
        section.dataset.verse = card.verse;
        section.setAttribute('aria-label', `Grondtekst bij vers ${card.verse}`);
        const label = document.createElement('p');
        label.className = 'opw-sidecar-label';
        label.textContent = `Grondtekst · vers ${card.verse}`;
        section.appendChild(label);
        const word = document.createElement('p');
        word.className = 'opw-grondwoord';
        word.lang = card.taal === 'Hebreeuws' ? 'he' : 'el';
        word.dir = card.taal === 'Hebreeuws' ? 'rtl' : 'ltr';
        word.textContent = card.woord;
        section.appendChild(word);
        const meaning = document.createElement('p');
        meaning.className = 'opw-grondbetekenis';
        meaning.textContent = card.betekenis;
        section.appendChild(meaning);
        const link = document.createElement('a');
        const path = `lexicon-viewer.html?taal=${card.taal === 'Hebreeuws' ? 'hebreeuws' : 'grieks'}&entry=${encodeURIComponent(card.strongs)}`;
        link.href = `https://opengodsword.com/${path}`;
        link.dataset.ogwHref = path;
        link.textContent = `Lees meer · ${card.strongs}`;
        section.appendChild(link);
        const note = document.createElement('p');
        note.className = 'opw-map-note';
        note.textContent = 'Lexiconbetekenis; de precieze betekenis hangt af van de tekst. De OPV is een parafrase.';
        section.appendChild(note);
        return section;
    }

    function linkTerms(layout, terms) {
        if (!terms.length) return;
        const book = layout.querySelector('.verse-row')?.dataset.book || '';
        const escaped = [...terms].sort((a, b) => b.length - a.length)
            .map(word => word.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
        const pattern = new RegExp(`(?<![\\p{L}\\p{N}])(${escaped.join('|')})(?![\\p{L}\\p{N}])`, 'giu');
        layout.querySelectorAll('.verse-cell.col-2026').forEach(cell => {
            if (cell.dataset.readingTerms) return;
            const walker = document.createTreeWalker(cell, NodeFilter.SHOW_TEXT, {
                acceptNode(node) {
                    if (node.parentElement?.closest('a,button,.begrip-link,.geo-locatie')) return NodeFilter.FILTER_REJECT;
                    return NodeFilter.FILTER_ACCEPT;
                },
            });
            const nodes = [];
            while (walker.nextNode()) nodes.push(walker.currentNode);
            for (const node of nodes) {
                const content = node.textContent;
                pattern.lastIndex = 0;
                if (!pattern.test(content)) continue;
                pattern.lastIndex = 0;
                const fragment = document.createDocumentFragment();
                let at = 0;
                for (const match of content.matchAll(pattern)) {
                    fragment.appendChild(document.createTextNode(content.slice(at, match.index)));
                    const link = document.createElement('a');
                    link.className = 'opw-lemma-link';
                    link.href = `/woordenboek.html?boek=${encodeURIComponent(book)}#${encodeURIComponent(match[0].toLocaleLowerCase('nl'))}`;
                    link.textContent = match[0];
                    link.title = `Bekijk het begrip ${match[0]} in het woordenboek`;
                    fragment.appendChild(link);
                    at = match.index + match[0].length;
                }
                fragment.appendChild(document.createTextNode(content.slice(at)));
                node.replaceWith(fragment);
            }
            cell.dataset.readingTerms = 'true';
        });
    }

    function enhanceLayout(layout, locations, ground, terms) {
        if (layout.dataset.readingReady) return;
        const rows = layout.querySelectorAll('.verse-row');
        if (!rows.length) return;
        const book = rows[0].dataset.book;
        const chapter = rows[0].dataset.chapter;
        const chapterCards = locations.books?.[book]?.[chapter] || [];
        const groundCards = ground.books?.[book]?.[chapter] || [];
        let gallery = layout.querySelector('.opw-hoofdstukbeelden');
        if (!gallery && (chapterCards.length || groundCards.length)) {
            gallery = document.createElement('aside');
            gallery.className = 'opw-hoofdstukbeelden';
            gallery.setAttribute('aria-label', 'Beelden en locaties bij dit hoofdstuk');
            layout.appendChild(gallery);
        }
        if (gallery) {
            gallery.classList.add('opw-sidecar');
            layout.classList.add('heeft-beelden');
            const figures = [...gallery.querySelectorAll('.opw-hoofdstukbeeld')];
            const maxVerse = Number(rows[rows.length - 1].dataset.verse) || rows.length;
            figures.forEach((figure, index) => {
                figure.classList.add('opw-sidecar-item');
                if (!Number(figure.dataset.verse)) {
                    figure.dataset.verse = Math.max(1, Math.round(index * maxVerse / Math.max(1, figures.length)));
                }
            });
            chapterCards.forEach(card => gallery.appendChild(mapCard(card)));
            groundCards.forEach(card => gallery.appendChild(groundCard(card)));
            const cards = [...gallery.querySelectorAll('.opw-sidecar-item')];
            cards.sort((a, b) => Number(a.dataset.verse) - Number(b.dataset.verse));
            cards.forEach(card => gallery.appendChild(card));
        }
        linkTerms(layout, terms);
        layout.dataset.readingReady = 'true';
        if (window.KASites) window.KASites.vulLinks(layout);
    }

    async function enhance() {
        const [locations, ground, terms] = await Promise.all([support.locations, support.ground, support.terms]);
        root.querySelectorAll('.opw-leesindeling').forEach(layout => enhanceLayout(layout, locations, ground, terms));
        activate();
    }

    function activate() {
        for (const layout of root.querySelectorAll('.opw-leesindeling.heeft-beelden')) {
            const rect = layout.getBoundingClientRect();
            if (rect.bottom < 130 || rect.top > window.innerHeight) continue;
            const rows = layout.querySelectorAll('.verse-row');
            let verse = Number(rows[rows.length - 1]?.dataset.verse) || 1;
            for (const row of rows) {
                if (row.getBoundingClientRect().bottom > 170) {
                    verse = Number(row.dataset.verse) || 1;
                    break;
                }
            }
            const cards = [...layout.querySelectorAll('.opw-sidecar-item')];
            const activeByType = { visual: null, ground: null };
            for (const card of cards) {
                if (Number(card.dataset.verse) <= verse) {
                    const type = card.classList.contains('opw-grondkaart') ? 'ground' : 'visual';
                    activeByType[type] = Number(card.dataset.verse);
                }
                else break;
            }
            for (const card of cards) {
                const type = card.classList.contains('opw-grondkaart') ? 'ground' : 'visual';
                if (activeByType[type] === null && Number(card.dataset.verse) <= verse + 5) {
                    activeByType[type] = Number(card.dataset.verse);
                }
            }
            cards.forEach(card => {
                const type = card.classList.contains('opw-grondkaart') ? 'ground' : 'visual';
                card.classList.toggle('is-active', activeByType[type] !== null && Number(card.dataset.verse) === activeByType[type]);
            });
        }
    }

    function onScroll() {
        if (support.busy) return;
        support.busy = true;
        requestAnimationFrame(() => { support.busy = false; activate(); });
    }
    document.addEventListener('DOMContentLoaded', enhance);
    document.addEventListener('opv:hoofdstuk-getoond', enhance);
    window.addEventListener('scroll', onScroll, { passive: true });
    document.getElementById('content')?.addEventListener('scroll', onScroll, { passive: true });
})();
