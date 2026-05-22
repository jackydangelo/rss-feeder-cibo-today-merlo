import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta
from xml.etree.ElementTree import (
    Element,
    SubElement,
    tostring,
    register_namespace,
)
from xml.dom import minidom

AUTHOR_URL = "https://www.cibotoday.it/author/profile/davide-merlo/49729159100110/"
FEED_URL = "https://jackydangelo.github.io/rss-feeder-cibo-today-merlo/feed.xml"

SITE_NAME = "Davide Merlo - CiboToday"
SITE_DESCRIPTION = "Feed RSS personalizzato"

MAX_ARTICLES = 20

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

response = requests.get(AUTHOR_URL, headers=HEADERS)
response.raise_for_status()

soup = BeautifulSoup(response.text, "lxml")

register_namespace("atom", "http://www.w3.org/2005/Atom")

rss = Element("rss", version="2.0")

channel = SubElement(rss, "channel")

title = SubElement(channel, "title")
title.text = SITE_NAME

link = SubElement(channel, "link")
link.text = AUTHOR_URL

description = SubElement(channel, "description")
description.text = SITE_DESCRIPTION

language = SubElement(channel, "language")
language.text = "it-it"

last_build = SubElement(channel, "lastBuildDate")
last_build.text = datetime.now(timezone.utc).strftime(
    "%a, %d %b %Y %H:%M:%S GMT"
)

atom_link = SubElement(
    channel,
    "{http://www.w3.org/2005/Atom}link"
)

atom_link.set("href", FEED_URL)
atom_link.set("rel", "self")
atom_link.set("type", "application/rss+xml")

articles = soup.select("article")

base_date = datetime(
    2025,
    1,
    1,
    12,
    0,
    0,
    tzinfo=timezone.utc
)

for i, article in enumerate(articles[:MAX_ARTICLES]):

    a = article.select_one("a")

    if not a:
        continue

    article_title = a.get_text(strip=True)
    article_link = a.get("href")

    if not article_link:
        continue

    if article_link.startswith("/"):
        article_link = "https://www.cibotoday.it" + article_link

    item = SubElement(channel, "item")

    item_title = SubElement(item, "title")
    item_title.text = article_title

    item_link = SubElement(item, "link")
    item_link.text = article_link

    guid = SubElement(item, "guid")
    guid.text = article_link

    fake_date = base_date - timedelta(minutes=i)

    pub_date = SubElement(item, "pubDate")
    pub_date.text = fake_date.strftime(
        "%a, %d %b %Y %H:%M:%S GMT"
    )

xml_bytes = tostring(rss, encoding="utf-8")

pretty_xml = minidom.parseString(xml_bytes).toprettyxml(
    indent="  ",
    encoding="utf-8"
)

with open("docs/feed.xml", "wb") as f:
    f.write(pretty_xml)

print("feed.xml generato correttamente")
