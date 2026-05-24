from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta
from xml.etree.ElementTree import Element, SubElement, tostring, register_namespace
from xml.dom import minidom
import json
import os

from config import (
    AUTHOR_URL,
    FEED_URL,
    SITE_URL,
    TITLE_RSS,
    DESCRIPTION_RSS,
    MAX_ARTICLES,
    TIMEOUT,
    base_date
)


def get_html(url: str) -> str:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, timeout=TIMEOUT)
        html = page.content()
        browser.close()
        return html


def parse_ld_json(article):
    ld = article.select_one('script[type="application/ld+json"]')
    if not ld or not ld.string:
        return {}

    try:
        data = json.loads(ld.string)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def normalize_url(link: str) -> str:
    if link.startswith("/"):
        return SITE_URL + link
    return link


def format_pubdate(pub_date: str | None, index: int) -> str:
    if pub_date:
        try:
            dt = datetime.fromisoformat(pub_date.replace("Z", "+00:00"))
            return dt.astimezone(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")
        except Exception:
            pass

    return (base_date - timedelta(minutes=index)).strftime(
        "%a, %d %b %Y %H:%M:%S GMT"
    )


def extract_title(article, a_tag, ld_data):
    title = ld_data.get("headline")

    if not title:
        h = article.select_one("h1, h2, h3")
        title = h.get_text(strip=True) if h else None

    if not title:
        title = a_tag.get("title") or a_tag.get_text(strip=True)

    return title


def extract_description(article, title, ld_data):
    desc = ld_data.get("description")

    if not desc:
        p = article.select_one("p, .excerpt, .summary")
        desc = p.get_text(strip=True) if p else title

    return (desc or "").strip()[:500]

def create_rss_root():
    register_namespace("atom", "http://www.w3.org/2005/Atom")

    rss = Element("rss", version="2.0")
    channel = SubElement(rss, "channel")

    SubElement(channel, "title").text = TITLE_RSS
    SubElement(channel, "link").text = AUTHOR_URL
    SubElement(channel, "description").text = DESCRIPTION_RSS
    SubElement(channel, "language").text = "it-it"

    SubElement(channel, "lastBuildDate").text = datetime.now(
        timezone.utc
    ).strftime("%a, %d %b %Y %H:%M:%S GMT")

    atom_link = SubElement(channel, "{http://www.w3.org/2005/Atom}link")
    atom_link.set("href", FEED_URL)
    atom_link.set("rel", "self")
    atom_link.set("type", "application/rss+xml")

    return rss, channel


def add_item(channel, title, link, pub_date, description):
    item = SubElement(channel, "item")

    SubElement(item, "title").text = title
    SubElement(item, "link").text = link

    guid = SubElement(item, "guid")
    guid.set("isPermaLink", "true")
    guid.text = link

    SubElement(item, "pubDate").text = pub_date
    SubElement(item, "description").text = description


def build_rss():
    html = get_html(AUTHOR_URL)
    soup = BeautifulSoup(html, "lxml")

    rss, channel = create_rss_root()

    articles = soup.select("article")

    for i, article in enumerate(articles[:MAX_ARTICLES]):
        a = article.select_one("a")
        if not a or not a.get("href"):
            continue

        link = normalize_url(a["href"])
        ld_data = parse_ld_json(article)

        title = extract_title(article, a, ld_data)
        if not title:
            continue

        pub_date = format_pubdate(ld_data.get("datePublished"), i)
        description = extract_description(article, title, ld_data)

        add_item(channel, title, link, pub_date, description)

    return rss


def save_rss(rss, path="docs/rss.xml"):
    xml = minidom.parseString(tostring(rss, encoding="utf-8")).toprettyxml(indent="  ")

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(xml)


if __name__ == "__main__":
    rss = build_rss()
    save_rss(rss)
    print("RSS Created")
