import os
import html
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

FEEDS = {
    "🌍 Мир": [
        "https://feeds.bbci.co.uk/russian/rss.xml",
        "https://meduza.io/rss/all",
    ],
    "💻 Технологии": [
        "https://habr.com/ru/rss/news/?fl=ru",
        "https://3dnews.ru/news/rss/",
    ],
    "🎮 Игры": [
        "https://rss.stopgame.ru/rss_news.xml",
        "https://dtf.ru/rss",
    ],
}
PER_FEED = 4  # сколько новостей брать из каждого источника
ATOM = "{http://www.w3.org/2005/Atom}"


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        root = ET.fromstring(r.read())
    items = []
    for it in root.iter("item"):  # обычный RSS
        title = (it.findtext("title") or "").strip()
        link = (it.findtext("link") or "").strip()
        if title and link:
            items.append((title, link))
    for e in root.iter(ATOM + "entry"):  # Atom
        title = (e.findtext(ATOM + "title") or "").strip()
        le = e.find(ATOM + "link")
        link = le.get("href", "") if le is not None else ""
        if title and link:
            items.append((title, link))
    return items


def send(text):
    data = urllib.parse.urlencode({
        "chat_id": os.environ["TG_CHAT_ID"],
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": "true",
    }).encode()
    url = f"https://api.telegram.org/bot{os.environ['TG_TOKEN']}/sendMessage"
    urllib.request.urlopen(url, data=data, timeout=20)


for category, urls in FEEDS.items():
    lines = [f"<b>{category}</b>"]
    for u in urls:
        try:
            for title, link in fetch(u)[:PER_FEED]:
                lines.append(
                    f'• <a href="{html.escape(link, quote=True)}">{html.escape(title)}</a>'
                )
        except Exception as err:
            print("Ошибка источника:", u, err)
    if len(lines) > 1:
        send("\n".join(lines))
