# Leeskolom en woordenboek

`python3 scripts/build_reading_support.py` maakt statische leesdata uit de bestaande bronnen. De site gebruikt de ingeschreven JSON-bestanden en heeft tijdens publicatie geen zusterrepo nodig.

- `reading-locations.json`: verwijzingen en coördinaten uit de geografielaag van Open Gods Woord, alleen records met status `agent-reviewed` en een plaatsnaam die in het OPV-vers staat. De kaartjes tonen een schematische ligging; coördinaten kunnen onzeker zijn.
- `reading-groundwords.json`: maximaal één belangrijk grondtekstwoord per OPV-tekstblok. De selectie gebruikt uitsluitend verskoppelingen met `reviewstatus: handmatig_gecontroleerd` uit `woordnummers-inline` en de bestaande Nederlandse lexiconprojecties. Het bronwoord en de korte betekenis zijn versgebonden. De selectie en de betekenis in de context zijn niet afzonderlijk redactioneel beoordeeld. De OPV blijft een parafrase en is geen woordelijke grondtekstvertaling.
- `reading-dictionary.json` en `reading-term-index.json`: bestaande OPV-begrippenlijsten en een beperkte set leeslinks. Het woordenboek is concept; onderbouwing vanuit de vroege kerk en menselijke eindcontrole ontbreken.

Voor het opnieuw opbouwen van locatiekaartjes moet `../website-open-gods-woord/data/geografie-runtime.geojson` lokaal beschikbaar zijn. De overige bronnen staan in deze repository. De leeskolom werkt ook als een van de JSON-bestanden niet geladen kan worden.
