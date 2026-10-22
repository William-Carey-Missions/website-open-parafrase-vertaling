/* Beeldvergroting en actuele uitleg: Open Gods Word blijft de bron. */
(function () {
    const root = document.getElementById('verses-container');
    if (!root) return;
    const origin = 'https://opengodsword.com';
    const supported = new Set(['genesis', 'johannes']);
    const selected = new Set(('afgrond|firmament|hemelgewelf|Eden|adem des levens|levende ziel|boom des levens|boom van de kennis van goed en kwaad|scheppen|sabbat|heilig|zegen|vloek|zonde|verbond|ark|brandoffer|altaar|offer|aartsvader|eerstgeboorterecht|eerstgeborene|besnijdenis|bijvrouw|hongersnood|balsemen|farao|engel|tienden|gelofte|erfenis|erfgenaam|barmhartigheid|genade|gerechtigheid|geloof|Almachtige|Allerhoogste|verzoening|Messias|Christus|Woord|Lam van God|Zoon van God|Zoon van de Mensen|Heilige Geest|doop|dopen|discipel|discipelen|apostel|Rabbi|Rabbouni|Farizeeën|Samaritanen|tempel|synagoge|Pascha|Vernieuwingsfeest|opnieuw geboren|wedergeboorte|eeuwig leven|brood des levens|levend water|opstanding|Trooster|waarheid|wereld|vlees geworden|voetwassing|Wijnstok|ranken|profeet|profetie|Schrift|wet|heerlijkheid|verheerlijken|teken|gelijkenis|aanbidden').toLocaleLowerCase('nl').split('|'));
    const sources = new Map();
    let sourceScript;

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
            script.src = `${origin}/data/opw-begrippen.js`;
            script.async = true;
            script.onload = () => resolve(window.OGWReadingTerms || {});
            script.onerror = () => resolve({});
            document.head.append(script);
        });
        if (!sources.has(book)) sources.set(book, sourceScript.then(books => {
            const entries = books[book] || [];
            return entries.filter(entry => selected.has(String(entry.woord).toLocaleLowerCase('nl')) && entry.uitleg);
        }));
        return sources.get(book);
    }

    function wordLink(link, entry, book, chapter) {
        link.classList.add('opw-word-link');
        link.href = `${origin}/index.html#${encodeURIComponent(book)}/${chapter}`;
        link.title = entry.uitleg;
        link.setAttribute('aria-haspopup', 'dialog');
        if (link.dataset.wordReady) return;
        link.dataset.wordReady = 'true';
        link.addEventListener('click', event => {
            if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
            event.preventDefault();
            explain(entry, book, chapter);
        });
    }

    async function words(layout, book, chapter) {
        if (!supported.has(book)) return;
        const entries = await loadTerms(book);
        if (!entries.length || !layout.isConnected) return;
        const lookup = new Map();
        for (const entry of entries) for (const word of [entry.woord, ...(entry.ook || [])]) lookup.set(word.toLocaleLowerCase('nl'), entry);
        const pattern = new RegExp(`(?<![\\p{L}\\p{N}])(${[...lookup.keys()].sort((a, b) => b.length - a.length).map(word => word.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|')})(?![\\p{L}\\p{N}])`, 'giu');
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
})();
