from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta
from xml.etree.ElementTree import Element, SubElement, tostring, register_namespace
from xml.dom import minidom
import os

AUTHOR_URL = "https://www.cibotoday.it/author/profile/davide-merlo/49729159100110/"
FEED_URL = "https://jackydangelo.github.io/rss-feeder-cibo-today-merlo/feed.xml"

MAX_ARTICLES = 20

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
SubElement(channel, "lastBuildDate").text = datetime.now(timezone.utc).strftime(
    "%a, %d %b %Y %H:%M:%S GMT"
)

atom_link = SubElement(channel, "{http://www.w3.org/2005/Atom}link")
atom_link.set("href", FEED_URL)
atom_link.set("rel", "self")
atom_link.set("type", "application/rss+xml")

articles = soup.select("article")

base_date = datetime(2025, 1, 1, tzinfo=timezone.utc)

os.makedirs("docs", exist_ok=True)

for i, article in enumerate(articles[:MAX_ARTICLES]):

    a = article.select_one("a")
    if not a:
        continue

    title = a.get_text(strip=True)
    link = a.get("href")

    if link.startswith("/"):
        link = "https://www.cibotoday.it" + link

    item = SubElement(channel, "item")

    SubElement(item, "title").text = title
    SubElement(item, "link").text = link
    SubElement(item, "guid").text = link

    fake_date = base_date - timedelta(minutes=i)
    SubElement(item, "pubDate").text = fake_date.strftime(
        "%a, %d %b %Y %H:%M:%S GMT"
    )

xml = minidom.parseString(
    tostring(rss, encoding="utf-8")
).toprettyxml(indent="  ")

with open("docs/feed.xml", "w") as f:
    f.write(xml)

print("RSS Created")
