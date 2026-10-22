# Open Parafrase Weergave (OPW)

Gods Woord in begrijpelijke taal. **Proef**: alle verzen hebben de status *concept*.

🌐 **open-parafrase-weergave.nl** (definitief domein)

## Publicatie

Elke push naar `main` publiceert deze repository op
**https://open-parafrase-weergave.nl**. De workflow bouwt de zoekindex voor
`nl-opv`, de HTML-leespagina's, tekstbestanden, AI-bronnengids en sitemap.
Daarna synchroniseert hij naar `/var/www/open-parafrase-weergave.nl` op
`167.235.54.105`. Handmatig publiceren kan via **Actions → Deploy website → Run workflow**.

De repository heeft `DEPLOY_SSH_KEY` als repositorysecret, omdat private repositories
op GitHub Free geen organisatiesecrets kunnen gebruiken. De deploymentvariabelen
zijn `DEPLOY_HOST=167.235.54.105`, `DEPLOY_PORT=22` en `DEPLOY_USER=root`.

De geïnstalleerde Nginx-configuratie staat in `deploy/nginx.conf`. HTTP en `www`
verwijzen met een 301 naar het HTTPS-hoofddomein; pad en querystring blijven behouden.
Certbot vernieuwt het certificaat automatisch. Serverconfiguratiewijzigingen worden
apart geïnstalleerd in `/etc/nginx/sites-available/open-parafrase-weergave.nl`,
getest met `nginx -t` en geactiveerd met `systemctl reload nginx`.

De oude repository `kleine-ark/open-parafrase-weergave` publiceert niet meer.
Bronbestanden voor redactie, ontwikkelinstructies, scripts, tests en hostingconfiguratie
worden door de deployment uitgesloten; de leeseditie gaat wel naar de website.

## Drie sites

| Site | Repo | Inhoud |
|---|---|---|
| Open Parafrase Weergave | deze repo | de parafrase |
| Open Vertaling | `website-open-bijbelvertaling` | de herziene Statenvertaling met alle opties |
| Open Gods Woord | `website-open-gods-woord` | wiki, Bijbelachtergrond en broninformatie |

De adressen van de drie sites staan op één plek: `js/sites.js`.

## Werken aan de parafrase

- Werkbron: `data/edities/opv/chapters/{boek}/{hoofdstuk}.json`
  (met `data/edities/opv/manifest.json` en `concepten.json`).
- Leeseditie bouwen: `python3 scripts/opv_leeseditie.py` schrijft
  `data/vertalingen/nl-opv/` en werkt `data/vertalingen/manifest.json` bij.
- Controleren: `python3 scripts/validate_opv.py`.
- Voortgang van drie beelden per hoofdstuk: `python3 scripts/check_book_image_coverage.py`.
- Zoekindex: `python3 scripts/build_search_index.py --editie nl-opv`.
- Publieke leespagina's, tekstbestanden, sitemap en AI-bronnengids:
  `python3 scripts/build_leespaginas.py`. Dezelfde stap draait bij elke publicatie.
  De gegenereerde map `bijbel/` en `llms-full.txt` worden niet in Git bewaard.
  `llms.txt` en `LLM.txt` worden samen uit de beschikbare leeseditie opgebouwd.
  Elk hoofdstuk op `/bijbel/{boek}/{hoofdstuk}.html` gebruikt de volledige
  lezer met instellingen en bevat de tekst ook zonder JavaScript.
  Oude links zoals `/index.html#genesis/1` openen hetzelfde hoofdstuk.
  Boekillustraties staan in `images/boeken/`. De fotorealistische reeks staat in
  `images/boekseries/{boek}/`. `data/book-images.json` koppelt de beelden aan
  hoofdstukken. De uitbreiding naar drie beelden per hoofdstuk is in uitvoering;
  de boekpagina toont drie voorbeelden uit het boek.
- Redactionele besluiten: `docs/opv/besluitregister.md`.

De directe bron is SV1888 in `data/{boek}/{hoofdstuk}.json` (veld
`textSV1888`). Die hoofdstukken komen uit de Open Vertaling en dienen als
controlebron. De lezer op deze site toont alleen de parafrase.

## Lokaal draaien

```
python3 -m http.server 8002 --bind 127.0.0.1
```

Open http://127.0.0.1:8002/. Draaien de OV (:8000) en OGW (:8001) ook, dan
werken de kruislinks lokaal.

## Tests

```
python3 -m unittest discover -s tests
```

## Licentie

De tekst van de parafrase is publiek domein.
