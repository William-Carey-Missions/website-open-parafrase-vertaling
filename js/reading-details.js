/* Beeldvergroting en actuele uitleg: Open Gods Word blijft de bron. */
(function () {
    const root = document.getElementById('verses-container');
    if (!root) return;
    const origin = 'https://opengodsword.com';
    const supported = new Set(['genesis', 'johannes']);
    const selected = new Set(('afgrond|firmament|hemelgewelf|Eden|adem des levens|levende ziel|boom des levens|boom van de kennis van goed en kwaad|scheppen|sabbat|heilig|zegen|vloek|zonde|verbond|ark|brandoffer|altaar|offer|aartsvader|eerstgeboorterecht|eerstgeborene|besnijdenis|bijvrouw|hongersnood|balsemen|farao|engel|tienden|gelofte|erfenis|erfgenaam|barmhartigheid|genade|gerechtigheid|geloof|Almachtige|Allerhoogste|verzoening|Messias|Christus|Woord|Lam van God|Zoon van God|Zoon van de Mensen|Heilige Geest|doop|dopen|discipel|discipelen|apostel|Rabbi|Rabbouni|Farizeeën|Samaritanen|tempel|synagoge|Pascha|Vernieuwingsfeest|opnieuw geboren|wedergeboorte|eeuwig leven|brood des levens|levend water|opstanding|Trooster|waarheid|wereld|vlees geworden|voetwassing|Wijnstok|ranken|profeet|profetie|Schrift|wet|heerlijkheid|verheerlijken|teken|gelijkenis|aanbidden').toLocaleLowerCase('nl').split('|'));
    const sources = new Map();
    const linkedWords = new WeakMap();
    const chosenWords = new WeakMap();
    let sourceScript;
    let scrollQueued = false;
    let explanationId = 0;

    function node(tag, className, text) {
        const element = document.createElement(tag);
        if (className) element.className = className;
        if (text != null) element.textContent = text;
        return element;
    }

    function dialog(className, title) {
        const box = node('dialog', className);
        const heading = node('h2', '', title);
        heading.id = className + '-title';
        box.setAttribute('aria-labelledby', heading.id);
        const close = node('button', 'opw-dialog-close', 'Sluiten');
        close.type = 'button';
        close.addEventListener('click', () => box.close());
        box.append(close, heading);
        box.addEventListener('click', event => {
            if (event.target !== box) return;
            const rect = box.getBoundingClientRect();
            if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) box.close();
        });
        box.addEventListener('close', () => { box.remove(); document.body.classList.remove('opw-dialog-open'); });
        document.body.appendChild(box);
        document.body.classList.add('opw-dialog-open');
        return box;
    }

    function enlarge(image) {
        const box = dialog('opw-image-dialog', 'Afbeelding bij dit hoofdstuk');
        const full = node('img');
        full.src = image.currentSrc || image.src;
        full.alt = image.alt;
        box.append(full, node('p', '', image.closest('figure')?.querySelector('figcaption')?.textContent || image.alt));
        box.showModal();
    }

    function explain(entry, book, chapter) {
        const box = dialog('opw-word-dialog', entry.woord);
        box.append(node('p', '', entry.uitleg));
        if (entry.ref) box.append(node('p', 'opw-word-reference', entry.ref));
        box.append(node('p', 'opw-word-source', 'Uitleg uit Open Gods Word · concept'));
        const link = node('a', '', 'Lees verder bij Open Gods Word →');
        link.href = `${origin}/index.html#${encodeURIComponent(book)}/${chapter}`;
        box.append(link);
        box.showModal();
    }

    function loadTerms(book) {
        if (!sourceScript) sourceScript = new Promise(resolve => {
            const script = node('script');
            // Eén verse bron per bezoek; hoofdstukwissels delen dezelfde bron.
            script.src = `${origin}/data/opw-begrippen.js?vers=${Date.now()}`;
            script.async = true;
            script.onload = () => resolve(window.OGWReadingTerms || {});
            script.onerror = () => resolve({});
            document.head.append(script);
        });
        if (!sources.has(book)) sources.set(book, sourceScript.then(books => {
            const entries = books[book] || [];
            return entries.filter(entry => entry.uitleg);
        }));
        return sources.get(book);
    }

    function wordLink(link, entry, book, chapter) {
        link.classList.add('opw-word-link');
        link.href = `${origin}/index.html#${encodeURIComponent(book)}/${chapter}`;
        link.title = entry.uitleg;
        if (!window.matchMedia('(min-width: 801px)').matches) link.setAttribute('aria-haspopup', 'dialog');
        if (link.dataset.wordReady) return;
        link.dataset.wordReady = 'true';
        linkedWords.set(link, { entry, book, chapter });
        link.addEventListener('focus', () => {
            if (window.matchMedia('(min-width: 801px)').matches) chooseExplanation(link);
        });
        link.addEventListener('click', event => {
            if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
            event.preventDefault();
            if (window.matchMedia('(min-width: 801px)').matches) chooseExplanation(link, true);
            else explain(entry, book, chapter);
        });
    }

    function readingPosition() {
        return `${window.scrollY}:${document.getElementById('content')?.scrollTop || 0}`;
    }

    function chooseExplanation(link, reveal = false) {
        const layout = link.closest('.opw-leesindeling');
        if (layout) chosenWords.set(layout, readingPosition());
        showExplanation(link, reveal);
    }

    function showExplanation(link, reveal = false) {
        const data = linkedWords.get(link);
        const layout = link.closest('.opw-leesindeling');
        const panel = layout?.querySelector('.opw-word-explanation');
        if (!data || !panel) return;
        layout.querySelectorAll('.opw-word-link.is-reading-word').forEach(previous => {
            previous.classList.remove('is-reading-word');
            previous.removeAttribute('aria-describedby');
        });
        link.classList.add('is-reading-word');
        link.setAttribute('aria-describedby', panel.id);
        panel.querySelector('h2').textContent = data.entry.woord;
        panel.querySelector('.opw-explanation-text').textContent = data.entry.uitleg;
        panel.querySelector('.opw-word-reference').textContent = data.entry.ref || '';
        panel.querySelector('a').href = link.href;
        panel.dataset.word = data.entry.woord;
        if (reveal) {
            const aside = panel.closest('.opw-sidecar');
            if (aside) {
                const hiddenBelow = panel.getBoundingClientRect().bottom - aside.getBoundingClientRect().bottom;
                if (hiddenBelow > 0) aside.scrollTop += hiddenBelow + 12;
            }
        }
    }

    function followReading() {
        if (!window.matchMedia('(min-width: 801px)').matches) return;
        const readingLine = Math.max(170, window.innerHeight * .3);
        root.querySelectorAll('.opw-leesindeling').forEach(layout => {
            const bounds = layout.getBoundingClientRect();
            if (bounds.bottom < readingLine || bounds.top > window.innerHeight) return;
            // Een nog wachtend scroll-event mag een klik of toetsenbordkeuze
            // niet overschrijven. Pas bij verder scrollen weer meelezen.
            if (chosenWords.get(layout) === readingPosition()) return;
            chosenWords.delete(layout);
            const links = [...layout.querySelectorAll('.opw-word-link')];
            const visible = links.filter(link => {
                const rect = link.getBoundingClientRect();
                return rect.bottom > 90 && rect.top < window.innerHeight - 60;
            });
            const nearest = visible.reduce((best, link) => !best ||
                Math.abs(link.getBoundingClientRect().top - readingLine) < Math.abs(best.getBoundingClientRect().top - readingLine)
                ? link : best, null);
            if (nearest) showExplanation(nearest);
            else if (links.length) {
                const previous = links.filter(link => link.getBoundingClientRect().top <= readingLine).pop();
                showExplanation(previous || links[0]);
            }
        });
    }

    function onScroll() {
        if (scrollQueued) return;
        scrollQueued = true;
        requestAnimationFrame(() => { scrollQueued = false; followReading(); });
    }

    async function words(layout, book, chapter) {
        if (!supported.has(book)) return;
        const entries = (await loadTerms(book)).filter(entry => Array.isArray(entry.hoofdstukken)
            ? entry.hoofdstukken.includes(Number(chapter))
            : selected.has(String(entry.woord).toLocaleLowerCase('nl')));
        if (!entries.length || !layout.isConnected) return;
        const lookup = new Map();
        for (const entry of entries) for (const word of [entry.woord, ...(entry.ook || [])]) lookup.set(word.toLocaleLowerCase('nl'), entry);
        const pattern = new RegExp(`(?<![\\p{L}\\p{N}])(${[...lookup.keys()].sort((a, b) => b.length - a.length).map(word => word.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|')})(?![\\p{L}\\p{N}])`, 'giu');
        // De hoofdstukuitleg herkent eerst volledige uitdrukkingen. Oude
        // woordenboeklinks om losse woorden mogen die niet opsplitsen.
        if (book === 'genesis' && Number(chapter) <= 3) {
            layout.querySelectorAll('.verse-cell.col-2026:not([data-live-words]) .opw-lemma-link:not(.opw-word-link)')
                .forEach(link => { const parent = link.parentNode; link.replaceWith(...link.childNodes); parent.normalize(); });
        }
        layout.querySelectorAll('.opw-lemma-link').forEach(link => {
            const entry = lookup.get(link.textContent.toLocaleLowerCase('nl'));
            if (entry) wordLink(link, entry, book, chapter);
        });
        layout.querySelectorAll('.verse-cell.col-2026').forEach(cell => {
            if (cell.dataset.liveWords) return;
            const walker = document.createTreeWalker(cell, NodeFilter.SHOW_TEXT, {
                acceptNode: text => text.parentElement.closest('a,button') ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT,
            });
            const texts = [];
            while (walker.nextNode()) texts.push(walker.currentNode);
            for (const text of texts) {
                const matches = [...text.textContent.matchAll(pattern)];
                if (!matches.length) continue;
                const fragment = document.createDocumentFragment();
                let offset = 0;
                for (const match of matches) {
                    fragment.append(document.createTextNode(text.textContent.slice(offset, match.index)));
                    const link = node('a', 'opw-lemma-link', match[0]);
                    wordLink(link, lookup.get(match[0].toLocaleLowerCase('nl')), book, chapter);
                    fragment.append(link);
                    offset = match.index + match[0].length;
                }
                fragment.append(document.createTextNode(text.textContent.slice(offset)));
                text.replaceWith(fragment);
            }
            cell.dataset.liveWords = 'true';
        });
        followReading();
    }

    function enhance() {
        root.querySelectorAll('.opw-leesindeling').forEach(layout => {
            const row = layout.querySelector('.verse-row');
            if (!row) return;
            const book = row.dataset.book;
            const chapter = row.dataset.chapter;
            layout.querySelectorAll('.opw-hoofdstukbeeld img').forEach(image => {
                if (image.closest('.opw-beeldzoom')) return;
                const link = node('a', 'opw-beeldzoom');
                link.href = image.getAttribute('src');
                link.setAttribute('aria-label', `Vergroot afbeelding: ${image.alt}`);
                link.setAttribute('aria-haspopup', 'dialog');
                link.addEventListener('click', event => {
                    if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
                    event.preventDefault(); enlarge(image);
                });
                image.replaceWith(link);
                link.append(image);
            });
            if (!layout.querySelector('.opw-background')) {
                let aside = layout.querySelector('.opw-hoofdstukbeelden');
                if (!aside) { aside = node('aside', 'opw-hoofdstukbeelden'); layout.append(aside); }
                layout.classList.add('heeft-beelden');
                aside.classList.add('opw-sidecar');
                const map = node('section', 'opw-chapter-map');
                const frame = node('iframe');
                frame.src = `${origin}/kaart.html?boek=${encodeURIComponent(book)}&hoofdstuk=${chapter}&embed=1`;
                frame.title = `Kaart bij ${book} ${chapter} — Open Gods Word`;
                frame.loading = 'lazy';
                const mapLink = node('a', '', 'Kaart bij dit hoofdstuk · Open Gods Word');
                mapLink.href = `${origin}/kaart.html?boek=${encodeURIComponent(book)}&hoofdstuk=${chapter}`;
                map.append(frame, mapLink);
                aside.prepend(map);
                const explanation = node('section', 'opw-word-explanation');
                explanation.id = `opw-uitleg-${++explanationId}`;
                explanation.setAttribute('aria-label', 'Uitleg bij de leestekst');
                explanation.append(node('h2', '', 'Uitleg bij de tekst'),
                    node('p', 'opw-explanation-text', 'Klik op een onderstreept woord voor uitleg. Tijdens het lezen volgt de uitleg het gemarkeerde woord.'),
                    node('p', 'opw-word-reference'), node('p', 'opw-word-source', 'Uitleg uit Open Gods Word · concept'));
                const source = node('a', '', 'Lees verder bij Open Gods Word');
                source.href = `${origin}/index.html#${encodeURIComponent(book)}/${chapter}`;
                explanation.append(source);
                aside.append(explanation);
                const card = node('section', 'opw-background');
                card.append(node('h2', '', 'Kaart en achtergrond'));
                for (const [kind, label, path] of [
                    ['map', 'Bekijk de kaart en plaatsen →', `kaart.html?boek=${encodeURIComponent(book)}&hoofdstuk=${chapter}`],
                    ['context', 'Lees de achtergrond bij dit hoofdstuk →', `index.html#${encodeURIComponent(book)}/${chapter}`],
                ]) {
                    const link = node('a', '', label);
                    link.href = `${origin}/${path}`;
                    link.dataset.background = kind;
                    card.append(link);
                }
                card.append(node('p', '', 'Bron: Open Gods Word. De links openen de actuele bronpagina’s.'));
                aside.append(card);
            }
            words(layout, book, chapter);
        });
    }
    document.addEventListener('DOMContentLoaded', enhance);
    document.addEventListener('opv:hoofdstuk-getoond', enhance);
    window.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('resize', onScroll, { passive: true });
    document.getElementById('content')?.addEventListener('scroll', onScroll, { passive: true });
})();
