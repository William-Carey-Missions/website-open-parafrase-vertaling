// De mobiele weergave: de Bijbeltekst staat voorop, de hulp klapt open.
const { test } = require('node:test');
const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const { resolve } = require('node:path');
const lees = pad => readFileSync(resolve(__dirname, '..', pad), 'utf8');

test('de statistiekknop drijft op de telefoon niet over de tekst', () => {
    assert.match(lees('js/analytics.js'), /@media\(max-width:768px\),\(pointer:coarse\)\{#analytics-settings\{position:static/);
});

test('de zustersites zijn op de telefoon goed te raken', () => {
    assert.match(lees('js/topnav.js'), /\.ka-fam-links a::after/);
});

test('de kaart staat op de telefoon ingeklapt boven de tekst', () => {
    const bron = lees('js/reading-details.js');
    assert.match(bron, /node\('details', 'opw-mobile-kaart'\)/);
    assert.match(bron, /help\.querySelector\('\.opw-mobile-words'\)\.hidden = !unique\.size/);
    assert.match(bron, /help\.querySelector\('\.opw-mobile-kaart'\)\.hidden = !map/);
});

test('de stamboom staat op de telefoon ingeklapt en op de computer open', () => {
    const bron = lees('js/reading-genealogy.js');
    assert.match(bron, /createElement\('details'\)/);
    assert.match(bron, /klap\.open = !mobile/);
});
test('een hoofdstuk begint op de telefoon met tekst, niet met een beeld', () => {
    assert.match(lees('js/reading-support.js'), /row\.after\(figure\)/);
});

