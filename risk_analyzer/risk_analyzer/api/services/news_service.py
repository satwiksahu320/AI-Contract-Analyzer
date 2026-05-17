from urllib.parse import quote
from urllib.request import Request, urlopen
from xml.etree import ElementTree


NEWS_URL = (
    "https://news.google.com/rss/search?"
    "q={query}&hl=en-US&gl=US&ceid=US:en"
)
USER_AGENT = "RiskAI/1.0"
REQUEST_TIMEOUT = 8


def get_finance_news(query="financial markets risk", limit=8):
    url = NEWS_URL.format(query=quote(query))
    request = Request(url, headers={"User-Agent": USER_AGENT})

    try:
        with urlopen(request, timeout=REQUEST_TIMEOUT) as response:
            payload = response.read()
    except Exception as exc:
        raise ValueError("News is temporarily unavailable.") from exc

    try:
        root = ElementTree.fromstring(payload)
    except ElementTree.ParseError as exc:
        raise ValueError("News response could not be read.") from exc

    items = []

    for item in root.findall("./channel/item")[:limit]:
        items.append({
            "title": item.findtext("title", default="Market update"),
            "link": item.findtext("link", default=""),
            "source": item.findtext("source", default="Google News"),
            "published": item.findtext("pubDate", default=""),
        })

    if not items:
        raise ValueError("No news articles found.")

    return items
