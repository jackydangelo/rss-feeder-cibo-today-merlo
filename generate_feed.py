from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta
from xml.etree.ElementTree import Element, SubElement, tostring, register_namespace
from xml.dom import minidom
import json
import os

AUTHOR_URL = "https://www.cibotoday.it/author/profile/davide-merlo/49729159100110/"
FEED_URL = "https://jackydangelo.github.io/rss-feeder-cibo-today-merlo/feed.xml"

MAX_ARTICLES = 20
base_date = datetime(2025, 1, 1, tzinfo=timezone.utc)

def get_html():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(AUTHOR_URL, timeout=60000)
        html = page.content()
        browser.close()
        return html

html = get_html()
soup = BeautifulSoup(html, "lxml")

register_namespace("atom", "http://www.w3.org/2005/Atom")

rss = Element("rss", version="2.0")
channel = SubElement(rss, "channel")

SubElement(channel, "title").text = "Davide Merlo - CiboToday"
SubElement(channel, "link").text = AUTHOR_URL
SubElement(channel, "description").text = "Feed RSS personalizzato"
SubElement(channel, "language").text = "it-it"

SubElement(channel, "lastBuildDate").text = datetime.now(
    timezone.utc
).strftime("%a, %d %b %Y %H:%M:%S GMT")

atom_link = SubElement(channel, "{http://www.w3.org/2005/Atom}link")
atom_link.set("href", FEED_URL)
atom_link.set("rel", "self")
atom_link.set("type", "application/rss+xml")

articles = soup.select("article")

for i, article in enumerate(articles[:MAX_ARTICLES]):

    a = article.select_one("a")

    if not a:
        continue

    link = a.get("href")

    if not link:
        continue

    if link.startswith("/"):
        link = "https://www.cibotoday.it" + link

    title = None
    pub_date = None

    ld = article.select_one('script[type="application/ld+json"]')

    if ld and ld.string:
        try:
            data = json.loads(ld.string)

            if isinstance(data, dict):
                title = data.get("headline")
                pub_date = data.get("datePublished")

        except Exception:
            pass

    if not title:
        h = article.select_one("h1, h2, h3")
        title = h.get_text(strip=True) if h else None

    if not title:
        title = a.get("title") or a.get_text(strip=True)

    if not title:
        continue

    item = SubElement(channel, "item")

    SubElement(item, "title").text = title
    SubElement(item, "link").text = link

    guid = SubElement(item, "guid")
    guid.set("isPermaLink", "true")
    guid.text = link

    if pub_date:
        try:
            dt = datetime.fromisoformat(
                pub_date.replace("Z", "+00:00")
            )

            pub_date = dt.astimezone(
                timezone.utc
            ).strftime("%a, %d %b %Y %H:%M:%S GMT")

        except Exception:
            pub_date = None

    if not pub_date:
        pub_date = (
            base_date - timedelta(minutes=i)
        ).strftime("%a, %d %b %Y %H:%M:%S GMT")

    SubElement(item, "pubDate").text = pub_date
    SubElement(item, "description").text = title

xml = minidom.parseString(
    tostring(rss, encoding="utf-8")
).toprettyxml(indent="  ")

os.makedirs("docs", exist_ok=True)

with open("docs/rss.xml", "w", encoding="utf-8") as f:
    f.write(xml)

print("RSS Created")
