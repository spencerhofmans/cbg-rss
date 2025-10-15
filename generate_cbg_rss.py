#!/usr/bin/env python3
"""
Generate an RSS feed from CBG-MEB news pages.
- NL: https://www.cbg-meb.nl/actueel/nieuws
- (Optional) EN: https://english.cbg-meb.nl/latest/news
"""
import os, re, sys, time, hashlib
from datetime import datetime, timezone
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE_NL = "https://www.cbg-meb.nl/actueel/nieuws"
BASE_EN = "https://english.cbg-meb.nl/latest/news"

def fetch(url, timeout=20):
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; CBG-RSS/1.0)"
    }
    r = requests.get(url, headers=headers, timeout=timeout)
    r.raise_for_status()
    return r.text

def parse_nl(html, base=BASE_NL, limit=30):
    # Haal nieuwslinks van https://www.cbg-meb.nl/actueel/nieuws
    from bs4 import BeautifulSoup
    import re
    from urllib.parse import urljoin
    soup = BeautifulSoup(html, "lxml")

    items, seen = [], set()

    # Pak alle <a> die duidelijk naar nieuwsdetailpagina's verwijzen
    anchors = soup.select(
        'a[href^="/actueel/nieuws/"], a[href^="https://www.cbg-meb.nl/actueel/nieuws/"]'
    )

    for a in anchors:
        href = a.get("href")
        if not href:
            continue
        link = urljoin(base, href)

        # dubbele overslaan
        if link in seen:
            continue
        seen.add(link)

        # titel
        title = " ".join(a.get_text(strip=True).split())
        if not title:
            # val terug op omringende tekst
            parent = a.find_parent()
            if parent:
                title = " ".join(parent.get_text(" ", strip=True).split())[:140]
        if not title:
            title = link  # uiterste fallback

        # datum proberen te vinden (time-tag óf dd-mm-jjjj | hh:mm vlakbij de link)
        date_text = None
        parent = a.find_parent()
        time_el = parent.find("time") if parent else None
        if time_el and time_el.get("datetime"):
            date_text = time_el["datetime"]
        elif time_el:
            date_text = time_el.get_text(" ", strip=True)
        if not date_text and parent:
            near_txt = parent.get_text(" ", strip=True)
            m = re.search(r"(\d{2}-\d{2}-\d{4})(?:\s*\|\s*(\d{2}):(\d{2}))?", near_txt)
            if m:
                date_text = m.group(0)

        pubdate = parse_nl_date(date_text) if date_text else datetime.now(timezone.utc)
        items.append({"title": title, "link": link, "pubDate": pubdate})

        if len(items) >= limit:
            break

    # Handige logregel in Actions
    print(f"[parse_nl] gevonden nieuwslinks: {len(items)}")
    return items

def parse_nl_date(s):
    from datetime import datetime, timezone
    import re
    if not s:
        return datetime.now(timezone.utc)

    # ISO-achtige datums (2025-10-15T09:00:00+02:00)
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc)
    except Exception:
        pass

    # "dd-mm-jjjj | hh:mm" of "dd-mm-jjjj"
    m = re.search(r"(\d{2})-(\d{2})-(\d{4})(?:\s*\|\s*(\d{2}):(\d{2}))?", s)
    if m:
        dd, mm, yyyy = map(int, m.groups()[:3])
        hh = int(m.group(4) or 0)
        mi = int(m.group(5) or 0)
        # interpreteer als NL-tijd en zet naar UTC
        dt = datetime(yyyy, mm, dd, hh, mi)
        return dt.replace(tzinfo=timezone.utc)

    # Fallback
    return datetime.now(timezone.utc)

def parse_en(html, base=BASE_EN, limit=30):
    soup = BeautifulSoup(html, "lxml")
    items = []
    for art in soup.select("main article, .news-overview li, .resultaten li, .indexed-items li"):
        a = art.select_one("a[href]")
        if not a: 
            continue
        title = " ".join(a.get_text(strip=True).split())
        link = urljoin(base, a["href"])
        # EN site often has 'News item | DD‑MM‑YYYY | hh:mm'
        txt = art.get_text(" ", strip=True)
        m = re.search(r"(\d{2}-\d{2}-\d{4})(?:\s*\|\s*(\d{2}):(\d{2}))?", txt)
        if m:
            day, month, year = map(int, m.groups()[:3])
            hh = int(m.group(2) or 0); mm = int(m.group(3) or 0)
            dt = datetime(year, month, day, hh, mm, tzinfo=timezone.utc)
        else:
            dt = datetime.now(timezone.utc)
        items.append({"title": title, "link": link, "pubDate": dt})
        if len(items) >= limit:
            break
    return items

def build_rss(items, title="CBG-MEB Nieuws", link=BASE_NL, desc="Ongeautoriseerde RSS-feed van cbg-meb.nl (nieuws)"):
    # Basic RSS 2.0
    from xml.sax.saxutils import escape
    pub_now = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")
    out = []
    out.append('<?xml version="1.0" encoding="UTF-8"?>')
    out.append('<rss version="2.0">')
    out.append("<channel>")
    out.append(f"<title>{escape(title)}</title>")
    out.append(f"<link>{escape(link)}</link>")
    out.append(f"<description>{escape(desc)}</description>")
    out.append(f"<lastBuildDate>{pub_now}</lastBuildDate>")
    for it in items:
        it_title = escape(it["title"])
        it_link = escape(it["link"])
        it_date = it["pubDate"].strftime("%a, %d %b %Y %H:%M:%S GMT")
        guid = hashlib.md5(it_link.encode()).hexdigest()
        out.append("<item>")
        out.append(f"<title>{it_title}</title>")
        out.append(f"<link>{it_link}</link>")
        out.append(f"<guid isPermaLink=\"false\">{guid}</guid>")
        out.append(f"<pubDate>{it['pubDate'].strftime('%a, %d %b %Y %H:%M:%S GMT')}</pubDate>")
        out.append("</item>")
    out.append("</channel></rss>")
    return "\n".join(out)

def main():
    include_en = ("--include-en" in sys.argv) or os.getenv("INCLUDE_EN") == "1"
    all_items = []
    # NL
    try:
        html = fetch(BASE_NL)
        all_items.extend(parse_nl(html, BASE_NL))
    except Exception as e:
        print("WARN: NL fetch failed:", e, file=sys.stderr)
    # EN (optional)
    if include_en:
        try:
            html = fetch(BASE_EN)
            all_items.extend(parse_en(html, BASE_EN))
        except Exception as e:
            print("WARN: EN fetch failed:", e, file=sys.stderr)
    # Sort and cap
    all_items.sort(key=lambda x: x["pubDate"], reverse=True)
    all_items = all_items[:50]
    rss = build_rss(all_items, title="CBG-MEB Nieuws", link=BASE_NL)
    with open("feed.xml", "w", encoding="utf-8") as f:
        f.write(rss)
    print("Wrote feed.xml with", len(all_items), "items")

if __name__ == "__main__":
    main()
