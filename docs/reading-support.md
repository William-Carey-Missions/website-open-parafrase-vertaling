# Leeskolom en woordenboek

`python3 scripts/build_reading_support.py` maakt statische leesdata uit de bestaande bronnen. De site gebruikt de ingeschreven JSON-bestanden en heeft tijdens publicatie geen zusterrepo nodig.

- `reading-locations.json`: verwijzingen en coördinaten uit de geografielaag van Open Gods Woord, alleen records met status `agent-reviewed` en een plaatsnaam die in het OPV-vers staat. De kaartjes tonen een schematische ligging; coördinaten kunnen onzeker zijn.
- `reading-groundwords.json`: maximaal één belangrijk grondtekstwoord per OPV-tekstblok. De selectie gebruikt uitsluitend verskoppelingen met `reviewstatus: handmatig_gecontroleerd` uit `woordnummers-inline` en de bestaande Nederlandse lexiconprojecties. Het bronwoord en de korte betekenis zijn versgebonden. De selectie en de betekenis in de context zijn niet afzonderlijk redactioneel beoordeeld. De OPV blijft een parafrase en is geen woordelijke grondtekstvertaling.
- `reading-dictionary.json` en `reading-term-index.json`: bestaande OPV-begrippenlijsten en een beperkte set leeslinks. Het woordenboek is concept; onderbouwing vanuit de vroege kerk en menselijke eindcontrole ontbreken.

Kaarten worden in de lezer rechtstreeks geopend op `https://opengodsword.com/kaart.html?boek=BOEK&hoofdstuk=NUMMER`. Achtergrond verwijst naar het overeenkomstige hoofdstuk op Open Gods Word. De oude lokale locatie-snapshot wordt niet meer in de lezer geladen.

Genesis en Johannes laden extra woorduitleg rechtstreeks via `https://opengodsword.com/data/opw-begrippen.js`. Die bron wordt bij iedere OGW-publicatie opgebouwd uit de actuele begrippenlijsten; de uitleg wordt niet naar OPW gekopieerd. Bij onbereikbaarheid van OGW blijven tekst, afbeeldingen en gewone bronlinks bruikbaar.

Afbeeldingen openen in een toegankelijk dialoogvenster en zijn met Escape te sluiten. De Ethiopische boekgroep is standaard verborgen in het boekenoverzicht; de checkbox gebruikt dezelfde opgeslagen instelling als de boekkeuze van de lezer.
