from flask import Flask
import feedparser
from datetime import datetime, timedelta
import time
import re
import os

app = Flask(__name__)

# ---------------- SOURCES ---------------- #

RSS_FEEDS = {
    # Global
    "Reuters": ("https://feeds.reuters.com/reuters/businessNews", "Global"),
    "Bloomberg": ("https://feeds.bloomberg.com/markets/news.rss", "Global"),
    "CNBC": ("https://www.cnbc.com/id/100003114/device/rss/rss.html", "Global"),
    "MarketWatch": ("https://feeds.marketwatch.com/marketwatch/topstories/", "Global"),
    "Kitco": ("https://www.kitco.com/rss/news", "Global"),
    "Financial Times": ("https://www.ft.com/?format=rss", "Global"),

    # India
    "Economic Times": ("https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms", "India"),
    "Moneycontrol": ("https://www.moneycontrol.com/rss/marketreports.xml", "India"),
    "Mint": ("https://www.livemint.com/rss/markets", "India"),
    "Business Standard": ("https://www.business-standard.com/rss/markets-106.rss", "India"),
    "Hindu BusinessLine": ("https://www.thehindubusinessline.com/markets/?service=rss", "India"),
    "Financial Express": ("https://www.financialexpress.com/market/feed/", "India"),
}

# ---------------- KEYWORDS ---------------- #

METAL_KEYWORDS = ["gold", "silver", "bullion"]
AI_KEYWORDS = ["artificial intelligence", "ai model", "machine learning", "generative ai", "openai", "ai chip"]
CRISIS_KEYWORDS = ["war", "conflict", "recession", "banking crisis", "inflation", "geopolitical"]

# ---------------- CACHE ---------------- #

news_cache = []
last_updated_time = None
last_fetch_time = None


def fetch_news():
    global news_cache, last_updated_time, last_fetch_time

    print("Fetching news...")

    articles = []
    seen_titles = set()
    three_days_ago = datetime.now() - timedelta(days=3)

    for source, (url, region) in RSS_FEEDS.items():
        feed = feedparser.parse(url)

        for entry in feed.entries:
            if not hasattr(entry, "published_parsed") or not entry.published_parsed:
                continue

            published = datetime.fromtimestamp(time.mktime(entry.published_parsed))
            if published < three_days_ago:
                continue

            title = entry.title
            summary = re.sub('<.*?>', '', entry.get("summary", ""))
            content = (title + " " + summary).lower()

            if title in seen_titles:
                continue
            seen_titles.add(title)

            category = None
            color = ""

            if any(k in content for k in METAL_KEYWORDS):
                category = "METALS"
                color = "#facc15"

            elif any(k in content for k in AI_KEYWORDS):
                category = "AI"
                color = "#3b82f6"

            elif any(k in content for k in CRISIS_KEYWORDS):
                category = "CRISIS"
                color = "#ef4444"
            else:
                continue

            articles.append({
                "title": title,
                "summary": summary[:180] + "..." if len(summary) > 180 else summary,
                "link": entry.link,
                "source": source,
                "region": region,
                "published": published.strftime('%b %d, %H:%M'),
                "category": category,
                "color": color
            })

    articles.sort(key=lambda x: x["published"], reverse=True)

    news_cache = articles
    last_updated_time = datetime.now().strftime("%b %d, %H:%M IST")
    last_fetch_time = datetime.now()

    print("News updated.")


@app.route("/")
def home():
    global last_fetch_time

    # Fetch only if cache empty or older than 5 minutes
    if last_fetch_time is None or (datetime.now() - last_fetch_time).seconds > 300:
        fetch_news()

    html = f"""
    <html>
    <head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Metals & AI Intelligence</title>
    <style>
    body {{ font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif; margin:0; background:#f3f4f6; }}
    .header {{ padding:15px; font-weight:700; font-size:20px; }}
    .sub {{ font-size:12px; opacity:0.7; padding:0 15px 10px 15px; }}
    .chip-bar {{ display:flex; gap:8px; padding:10px; }}
    .chip {{ padding:6px 12px; border-radius:20px; background:#111827; color:white; cursor:pointer; font-size:12px; }}
    .card {{ margin:12px; padding:16px; border-radius:16px; background:white; box-shadow:0 3px 10px rgba(0,0,0,0.05); }}
    .badge {{ font-size:11px; font-weight:700; padding:4px 8px; border-radius:6px; display:inline-block; margin-bottom:8px; color:black; }}
    .headline {{ font-size:17px; font-weight:700; margin-bottom:8px; }}
    .summary {{ font-size:14px; margin-bottom:10px; }}
    .meta {{ font-size:12px; opacity:0.6; }}
    a {{ text-decoration:none; color:inherit; }}
    </style>
    </head>
    <body>
    <div class="header">Metals & AI Intelligence</div>
    <div class="sub">Last Updated: {last_updated_time}</div>
    """

    for a in news_cache:
        html += f"""
        <div class="card">
            <span class="badge" style="background:{a['color']}">{a['category']}</span>
            <a href="{a['link']}" target="_blank">
                <div class="headline">{a['title']}</div>
                <div class="summary">{a['summary']}</div>
            </a>
            <div class="meta">{a['source']} • {a['region']} • {a['published']}</div>
        </div>
        """

    html += "</body></html>"
    return html


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
