import os
import json
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
    "₿ Крипто-новости": [
        "https://forklog.com/feed/",
        "https://ru.cointelegraph.com/rss",
    ],
}
PER_FEED = 4  # сколько новостей брать из каждого источника
ATOM = "{http://www.w3.org/2005/Atom}"
UA = {"User-Agent": "Mozilla/5.0"}


def fetch(url):
    req = urllib.request.Request(url, headers=UA)
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


def get_json(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read())


def send(text):
    data = urllib.parse.urlencode({
        "chat_id": os.environ["TG_CHAT_ID"],
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": "true",
    }).encode()
    url = f"https://api.telegram.org/bot{os.environ['TG_TOKEN']}/sendMessage"
    urllib.request.urlopen(url, data=data, timeout=20)


def price(p):
    return f"{p:,.2f}" if p >= 1 else f"{p:.4f}"


def crypto_market():
    lines = ["<b>📊 Крипта: рынок (топ-10 по капитализации)</b>"]
    try:
        coins = get_json(
            "https://api.coingecko.com/api/v3/coins/markets"
            "?vs_currency=usd&order=market_cap_desc&per_page=10&page=1"
        )
        for c in coins:
            ch = c.get("price_change_percentage_24h") or 0
            mark = "🟢" if ch >= 0 else "🔴"
            lines.append(
                f"{mark} {html.escape(c['symbol'].upper())}: "
                f"${price(c['current_price'])} ({ch:+.1f}% за 24ч)"
            )
    except Exception as err:
        print("Ошибка рынка:", err)
    try:
        data = get_json("https://api.coingecko.com/api/v3/search/trending")
        names = [
            f"{html.escape(x['item']['name'])} ({html.escape(x['item']['symbol'])})"
            for x in data["coins"][:5]
        ]
        if names:
            lines.append("\n🔥 В тренде на CoinGecko: " + ", ".join(names))
    except Exception as err:
        print("Ошибка трендов:", err)
    if len(lines) > 1:
        lines.append("\n⚠️ Это информация, а не финансовый совет. Решения принимай сам.")
        send("\n".join(lines))


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

crypto_market()
