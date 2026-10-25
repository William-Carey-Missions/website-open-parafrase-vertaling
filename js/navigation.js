/* Statenvertaling 2026 — Navigatie */

const Navigation = {
    currentBook: null,
    currentChapter: null,

    chapterUrl(bookId, chapter, verse) {
        return `/bijbel/${encodeURIComponent(bookId)}/${Number(chapter)}.html` +
            (verse ? `#vers-${Number(verse)}` : '');
    },

    init() {
        if (this._initialized) return;
        this._initialized = true;
        window.addEventListener('hashchange', () => this.handleHash());
        window.addEventListener('popstate', () => this.handleHash());
        document.addEventListener('click', event => {
            if (event.defaultPrevented || event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
            const link = event.target.closest('a[href]');
            if (!link || link.hasAttribute('download') || (link.target && link.target !== '_self')) return;
            const url = new URL(link.href, location.href);
            const route = url.pathname.match(/^\/bijbel\/([a-z0-9]+)\/(\d+)\.html$/);
            if (url.origin !== location.origin || url.search || !route || (url.hash && !/^#vers-\d+$/.test(url.hash))) return;
            event.preventDefault();
            this.navigateChapter(route[1], Number(route[2]), url.hash ? Number(url.hash.slice(6)) : null);
        });
    },

    navigateChapter(bookId, chapter, verse = null) {
        const target = this.chapterUrl(bookId, chapter, verse);
        if (location.pathname + location.search + location.hash !== target) history.pushState(null, '', target);
        return this.handleHash();
    },

    _updateDocument(bookId, chapter) {
        const title = document.querySelector('#verses-container h1')?.textContent || `${bookId} ${chapter}`;
        const url = new URL(this.chapterUrl(bookId, chapter), location.origin).href;
        document.title = `${title} | Open Parafrase Weergave`;
        const canonical = document.querySelector('link[rel="canonical"]');
        if (canonical) canonical.href = url;
        const description = document.querySelector('.verse-cell.col-2026')?.textContent.trim().slice(0, 200) || title;
        for (const [selector, value] of [
            ['meta[property="og:url"]', url], ['meta[property="og:title"]', title],
            ['meta[name="twitter:title"]', title], ['meta[name="description"]', description],
            ['meta[property="og:description"]', description], ['meta[name="twitter:description"]', description],
        ]) document.querySelector(selector)?.setAttribute('content', value);
        const picture = document.querySelector('.opw-hoofdstukbeeld img');
        if (picture) for (const selector of ['meta[property="og:image"]', 'meta[name="twitter:image"]']) {
            document.querySelector(selector)?.setAttribute('content', picture.src);
        }
        const json = document.querySelector('link[rel="alternate"][type="application/json"]');
        if (json) json.href = `/data/llm/${bookId}/${chapter}.json`;
        const plain = document.querySelector('link[rel="alternate"][type="text/plain"][href*="/bijbel/"]');
        if (plain) plain.href = `/bijbel/${bookId}/${chapter}.txt`;
        const schema = document.querySelector('script[type="application/ld+json"]');
        if (schema) schema.textContent = JSON.stringify({
            '@context': 'https://schema.org', '@type': 'WebPage', '@id': url,
            url, name: title, description, inLanguage: 'nl-NL',
            isPartOf: { '@id': location.origin + '/#website' },
        });
    },

    async renderBookNav() {
        const manifest = await DataLoader.loadManifest();
        const nav = document.getElementById('book-nav');
        nav.innerHTML = '';
        nav.className = 'nav-bar book-nav-grouped';

        // Boekvolgorde uit gebruikersopties (canoniek / tenach / chronologisch / auteur / lengte)
        const mode = (typeof Opties !== 'undefined' && Opties.state && Opties.state.boekvolgorde) || 'canoniek';
        const bookOrder = getBookOrderGroups(mode, manifest);

        const bookById = {};
        for (const b of manifest.books) bookById[b.id] = b;

        const addGroup = (label, books) => {
            if (books.length === 0) return;
            const group = document.createElement('div');
            group.className = 'nav-group';
            const lbl = document.createElement('span');
            lbl.className = 'nav-group-label';
            lbl.textContent = label;
            group.appendChild(lbl);
            for (const book of books) {
                const btn = document.createElement('button');
                btn.textContent = book.nameDutch;
                btn.dataset.bookId = book.id;
                btn.addEventListener('click', () => {
                    const firstCh = book.chaptersIncluded[0];
                    Navigation.navigateChapter(book.id, firstCh);
                });
                group.appendChild(btn);
            }
            nav.appendChild(group);
        };

        for (const [label, ids] of Object.entries(bookOrder)) {
            const books = ids.map(id => bookById[id]).filter(Boolean);
            addGroup(label, books);
        }
        // Eventuele ontbrekende boeken
        const assignedIds = new Set(Object.values(bookOrder).flat());
        const unassigned = manifest.books.filter(b => !assignedIds.has(b.id) &&
            isBookVisibleInNavigation(b));
        if (unassigned.length > 0) addGroup('Overig', unassigned);
    },

    async renderChapterNav(bookId, isCurrent = () => true) {
        const manifest = await DataLoader.loadManifest();
        const bookMeta = manifest.books.find(b => b.id === bookId);
        if (!bookMeta) return;

        // Laad boekdata om status per hoofdstuk te bepalen
        const book = await DataLoader.loadBook(bookId);
        if (!isCurrent()) return;
        const nav = document.getElementById('chapter-nav');
        nav.innerHTML = '';
        nav.className = 'nav-bar';

        for (const ch of bookMeta.chaptersIncluded) {
            const btn = document.createElement('button');
            btn.textContent = ch;
            btn.dataset.chapter = ch;
            btn.addEventListener('click', () => {
                Navigation.navigateChapter(bookId, ch);
            });

            // Groen kleuren als alle verzen "final" zijn
            if (book) {
                const chapter = book.chapters.find(c => c.number === ch);
                if (chapter && chapter.verses.length > 0) {
                    const allFinal = chapter.verses.every(v => v.status === 'final');
                    if (allFinal) btn.classList.add('chapter-approved');
                }
            }

            nav.appendChild(btn);
        }
    },

    updateActiveButtons() {
        // Book buttons
        document.querySelectorAll('#book-nav button').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.bookId === this.currentBook);
        });
        // Chapter buttons
        document.querySelectorAll('#chapter-nav button').forEach(btn => {
            btn.classList.toggle('active', parseInt(btn.dataset.chapter) === this.currentChapter);
        });
    },

    async handleHash() {
        const generation = this._routeGeneration = (this._routeGeneration || 0) + 1;
        const current = () => this._routeGeneration === generation;
        let hash = location.hash.slice(1);
        const legacy = hash.match(/^([a-z0-9]+)\/(\d+)(?:\/(\d+)|\?v=(\d+))?$/);
        if (legacy) {
            const target = this.chapterUrl(legacy[1], legacy[2], legacy[3] || legacy[4]);
            history.replaceState(history.state, '', target);
            hash = `${legacy[1]}/${legacy[2]}` + ((legacy[3] || legacy[4]) ? `/${legacy[3] || legacy[4]}` : '');
        }
        const route = location.pathname.match(/^\/bijbel\/([a-z0-9]+)\/(\d+)\.html$/);
        if (route) {
            const verse = location.hash.slice(1).match(/^vers-(\d+)$/);
            hash = `${route[1]}/${route[2]}` + (verse ? `/${verse[1]}` : '');
        }
        if (!hash) {
            // Zonder #boek/hoofdstuk toont de site het startscherm (opv.js).
            if (document.getElementById('opv-start')) {
                document.documentElement.classList.add('opv-startscherm');
                document.dispatchEvent(new CustomEvent('opv:startscherm'));
                return;
            }
            // Default: eerste boek, eerste hoofdstuk
            const manifest = await DataLoader.loadManifest();
            if (manifest.books.length > 0) {
                const first = manifest.books[0];
                this.navigateChapter(first.id, first.chaptersIncluded[0]);
            }
            return;
        }

        document.documentElement.classList.remove('opv-startscherm');
        const parts = hash.split('/');
        const bookId = parts[0];
        const chapter = parseInt(parts[1]) || 1;
        const targetVerse = parts[2] ? parseInt(parts[2]) : null;

        const holder = document.getElementById('verses-container');
        const previous = { book: this.currentBook, chapter: this.currentChapter, url: this._lastRenderedUrl };
        holder?.setAttribute('aria-busy', 'true');
        try {
        this.currentBook = bookId;
        this.currentChapter = chapter;
        await this.renderChapterNav(bookId, current);
        if (!current()) return;
        this.currentChapter = chapter;
        this.updateActiveButtons();

        // Synchroniseer sidebar
        if (typeof Sidebar !== 'undefined') {
            Sidebar.updateActive(bookId, chapter);
            Sidebar.markApprovedChapters(bookId);
        }

        // Laad en render het hoofdstuk
        const key = `${bookId}/${chapter}`;
        if (this._renderedChapter !== key) {
            await App.renderChapter(bookId, chapter, { isCurrent: current });
        }
        if (!current()) return;
        this._renderedChapter = key;
        this._lastRenderedUrl = location.pathname + location.search + location.hash;
        if (typeof MobileNav !== 'undefined') MobileNav.syncFromState();
        document.getElementById('chapter-load-error')?.remove();
        this._updateDocument(bookId, chapter);

        // Naar een specifiek vers scrollen + selecteren, anders naar boven
        if (targetVerse && App.focusVerse) {
            App.focusVerse(bookId, chapter, targetVerse);
        } else {
            // Naar boven uitlijnen — ook het werkelijke scroll-element (#content op
            // mobiel), anders bleef de gekozen hoofdstuktekst halverwege ('gecentreerd').
            window.scrollTo(0, 0);
            const sc = (App._getScroller && App._getScroller()) || document.getElementById('content');
            if (sc && sc !== document.scrollingElement && sc !== document.documentElement) sc.scrollTop = 0;
        }
        } catch (error) {
            if (!current()) return;
            console.warn('[Navigation] Hoofdstuk kon niet worden geladen.', error);
            this.currentBook = previous.book;
            this.currentChapter = previous.chapter;
            if (previous.url) history.replaceState(history.state, '', previous.url);
            document.getElementById('chapter-load-error')?.remove();
            const message = document.createElement('p');
            message.id = 'chapter-load-error';
            message.setAttribute('role', 'alert');
            message.textContent = 'Dit hoofdstuk kon niet worden geladen. ';
            const retry = document.createElement('button');
            retry.type = 'button';
            retry.textContent = 'Opnieuw proberen';
            retry.addEventListener('click', () => this.navigateChapter(bookId, chapter, targetVerse));
            message.append(retry);
            holder?.before(message);
        } finally {
            if (current()) holder?.removeAttribute('aria-busy');
        }
    },

    async navigateRelative(offset) {
        if (!this.currentBook) return;
        const chapterBtns = document.querySelectorAll('#chapter-nav button');
        const chapters = Array.from(chapterBtns).map(b => parseInt(b.dataset.chapter));
        const idx = chapters.indexOf(this.currentChapter);
        const newIdx = idx + offset;
        if (newIdx >= 0 && newIdx < chapters.length) {
            return this.navigateChapter(this.currentBook, chapters[newIdx]);
        }
        // Voorbij de boekgrens → naar het aangrenzende boek (in de actieve volgorde)
        try {
            const manifest = await DataLoader.loadManifest();
            const mode = (window.Opties && Opties.state && Opties.state.boekvolgorde) || 'canoniek';
            const orderIds = (typeof getFlatBookOrder === 'function')
                ? getFlatBookOrder(mode, manifest)
                : manifest.books.map(b => b.id);
            const byId = Object.fromEntries(manifest.books.map(b => [b.id, b]));
            const bIdx = orderIds.indexOf(this.currentBook);
            if (bIdx < 0) return;
            if (newIdx < 0 && bIdx > 0) {
                // Laatste hoofdstuk van het vorige boek
                const prev = byId[orderIds[bIdx - 1]];
                const last = prev.chaptersIncluded[prev.chaptersIncluded.length - 1];
                return this.navigateChapter(prev.id, last);
            } else if (newIdx >= chapters.length && bIdx < orderIds.length - 1) {
                // Eerste hoofdstuk van het volgende boek
                const next = byId[orderIds[bIdx + 1]];
                return this.navigateChapter(next.id, next.chaptersIncluded[0]);
            }
        } catch (e) { console.warn('[Navigation] cross-book nav faalde:', e); }
    }
};
