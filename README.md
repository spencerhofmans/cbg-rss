# CBG-MEB News → RSS (auto-updating)

Dit project maakt gratis een **RSS-feed** van de CBG-website en publiceert die via **GitHub Pages** (dagelijks automatisch).

## Snelstart (5 minuten)
1. Maak een nieuwe GitHub-repo, bijvoorbeeld `cbg-rss` (public).
2. Upload *alle* bestanden uit deze map naar de repo (of upload `cbg_rss.zip`).
3. Ga naar **Settings → Pages** en kies:
   - **Source**: `Deploy from a branch`
   - **Branch**: `gh-pages` (root)
4. Wacht 1–2 minuten tot Pages live is. Je feed staat dan op:
   ```
   https://<jouw-gebruikersnaam>.github.io/cbg-rss/feed.xml
   ```
5. Abonneer je op die URL in je RSS-lezer of zet hem in **Blogtrottr** voor e-mail.

## Wat doet het?
- `generate_cbg_rss.py` haalt de laatste nieuwsitems op van:
  - https://www.cbg-meb.nl/actueel/nieuws
- De workflow (`.github/workflows/build.yml`) draait **elke 4 uur** en bij elke push:
  - runt de scraper,
  - maakt/actualiseert `feed.xml`,
  - pusht het naar de branch **gh-pages** waar GitHub Pages het als statisch bestand serveert.

## Opties
- Je kunt de interval aanpassen (cron) in de workflow.
- Wil je ook de Engelstalige site meenemen? Zet `INCLUDE_EN=1` bij de workflow (env-var) of run lokaal met `--include-en`.

## E-mail notificaties
- Gebruik **https://blogtrottr.com**:
  - Plak de feed-URL en je e-mailadres → kies frequentie → klaar.

## Licentie
MIT — gebruik vrijelijk.
