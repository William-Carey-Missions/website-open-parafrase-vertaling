/* Hoofdstukbeelden bij de leestekst en woordverwijzingen. */
(function () {
    const root = document.getElementById('verses-container');
    if (!root) return;
    const termsPromise = fetch('/data/reading-term-index.json').then(r => r.ok ? r.json() : []).catch(() => []);
    let busy = false;
    function linkTerms(layout, terms) {
        if (!terms.length) return;
        const book = layout.querySelector('.verse-row')?.dataset.book || '';
        const escaped = [...terms].sort((a, b) => b.length - a.length)
            .map(word => word.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
        const pattern = new RegExp(`(^|[^\\p{L}\\p{N}])(${escaped.join('|')})(?![\\p{L}\\p{N}])`, 'giu');
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
                    fragment.appendChild(document.createTextNode(content.slice(at, match.index) + match[1]));
                    const link = document.createElement('a');
                    link.className = 'opw-lemma-link';
                    link.href = `/woordenboek.html?boek=${encodeURIComponent(book)}#${encodeURIComponent(match[2].toLocaleLowerCase('nl'))}`;
                    link.textContent = match[2];
                    link.title = `Bekijk het begrip ${match[2]} in het woordenboek`;
                    fragment.appendChild(link);
                    at = match.index + match[0].length;
                }
                fragment.appendChild(document.createTextNode(content.slice(at)));
                node.replaceWith(fragment);
            }
            cell.dataset.readingTerms = 'true';
        });
    }

    function arrangeImages(layout) {
        const mobile = window.matchMedia('(max-width: 1100px), (hover: none), (pointer: coarse)').matches;
        const placement = mobile ? 'inline' : 'aside';
        if (layout.dataset.imagePlacement === placement) return;
        const gallery = layout.querySelector('.opw-hoofdstukbeelden');
        const rows = [...layout.querySelectorAll('.verse-row')];
        const figures = [...layout.querySelectorAll('.opw-hoofdstukbeeld')];
        if (!gallery || !rows.length) return;
        figures.forEach((figure, index) => {
            if (mobile) {
                const row = rows.find(row => Number(row.dataset.verse) >= Number(figure.dataset.verse)) || rows[rows.length - 1];
                row.before(figure);
                if (index) figure.querySelector('img').loading = 'lazy';
            } else gallery.appendChild(figure);
        });
        layout.dataset.imagePlacement = placement;
    }

    function enhanceLayout(layout, terms) {
        if (layout.dataset.readingReady) return;
        const rows = layout.querySelectorAll('.verse-row');
        if (!rows.length) return;
        const gallery = layout.querySelector('.opw-hoofdstukbeelden');
        if (gallery) {
            gallery.classList.add('opw-sidecar');
            layout.classList.add('heeft-beelden');
            const figures = [...gallery.querySelectorAll('.opw-hoofdstukbeeld')];
            const maxVerse = Number(rows[rows.length - 1].dataset.verse) || rows.length;
            figures.forEach((figure, index) => {
                figure.classList.add('opw-sidecar-item');
                if (!Number(figure.dataset.verse)) figure.dataset.verse = Math.max(1, Math.round(index * maxVerse / Math.max(1, figures.length)));
            });
        }
        linkTerms(layout, terms);
        layout.dataset.readingReady = 'true';
        arrangeImages(layout);
        if (window.KASites) window.KASites.vulLinks(layout);
    }

    async function enhance() {
        const terms = await termsPromise;
        root.querySelectorAll('.opw-leesindeling').forEach(layout => enhanceLayout(layout, terms));
        activate();
    }

    function activate() {
        for (const layout of root.querySelectorAll('.opw-leesindeling.heeft-beelden')) {
            const rect = layout.getBoundingClientRect();
            if (rect.bottom < 130 || rect.top > window.innerHeight) continue;
            const rows = [...layout.querySelectorAll('.verse-row')];
            const row = rows.find(row => row.getBoundingClientRect().bottom > 170) || rows[rows.length - 1];
            const verse = Number(row?.dataset.verse) || 1;
            const figures = [...layout.querySelectorAll('.opw-hoofdstukbeeld')].sort((a,b) => Number(a.dataset.verse) - Number(b.dataset.verse));
            let active = figures[0];
            for (const figure of figures) if (Number(figure.dataset.verse) <= verse) active = figure;
            figures.forEach(figure => figure.classList.toggle('is-active', figure === active));
        }
    }

    function onScroll() {
        if (busy) return;
        busy = true;
        requestAnimationFrame(() => { busy = false; activate(); });
    }
    document.addEventListener('DOMContentLoaded', enhance);
    document.addEventListener('opv:hoofdstuk-getoond', enhance);
    window.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('resize', () => {
        root.querySelectorAll('.opw-leesindeling[data-reading-ready]').forEach(arrangeImages);
        onScroll();
    }, { passive: true });
    document.getElementById('content')?.addEventListener('scroll', onScroll, { passive: true });
})();
