from flask import Flask
import feedparser
from datetime import datetime, timedelta
import time
import re
import pytz
import os
import threading

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

METAL_KEYWORDS = [
    "gold", "silver", "bullion", "precious metal",
    "gold reserves", "silver reserves", "central bank reserves",
    "commodity", "mcx", "futures", "spot price",
    "dedollarisation", "de-dollarisation",
    "currency debasement", "currency depreciation",
    "forex reserves", "dollar dominance"
]

AI_KEYWORDS = [
    "artificial intelligence", "ai model", "machine learning",
    "generative ai", "openai", "ai chip", "nvidia",
    "semiconductor", "deep learning",
    "large language model", "llm", "chatgpt"
]

CRISIS_KEYWORDS = [
    "war", "conflict", "recession", "banking crisis",
    "inflation", "geopolitical", "central bank",
    "interest rate", "rate hike", "rate cut",
    "global debt", "sovereign debt", "job data",
    "jobs report", "unemployment", "layoffs",
    "economic slowdown", "market crash",
    "financial instability", "brics", "tariffs",
    "trade war", "currency depreciation",
    "currency debasement", "dedollarisation",
    "de-dollarisation"
]

news_cache = []
last_updated_time = None
last_fetch_time = None


# ---------------- IST TIME ---------------- #

def get_ist_time():
    ist = pytz.timezone("Asia/Kolkata")
    return datetime.now(ist)


# ---------------- FETCH NEWS ---------------- #

def fetch_news():
    global news_cache, last_updated_time, last_fetch_time

    print("Fetching news...")

    articles = []
    seen_titles = set()
    three_days_ago = datetime.utcnow() - timedelta(days=3)

    for source, (url, region) in RSS_FEEDS.items():
        feed = feedparser.parse(url)

        for entry in feed.entries:
            if not hasattr(entry, "published_parsed") or not entry.published_parsed:
                continue

            published_dt = datetime.fromtimestamp(time.mktime(entry.published_parsed))

            if published_dt < three_days_ago:
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
                "published": published_dt.strftime('%b %d, %H:%M'),
                "category": category,
                "color": color
            })

    articles.sort(key=lambda x: x["published"], reverse=True)

    news_cache = articles
    last_updated_time = get_ist_time().strftime("%d %b %Y, %I:%M %p IST")
    last_fetch_time = datetime.utcnow()

    print("News updated.")


# ---------------- ROUTE ---------------- #

@app.route("/")
def home():
    global last_fetch_time

    if last_fetch_time is None:
        fetch_news()
    elif (datetime.utcnow() - last_fetch_time).total_seconds() > 300:
        fetch_news()

    html = f"""
    <html>
    <head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Metals & AI Intelligence</title>
    <style>
    body {{
        margin:0;
        font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
        background:#f3f4f6;
        color:#111827;
        transition:0.3s;
    }}

    body.dark {{
        background:#0f172a;
        color:#e5e7eb;
    }}

    .header {{
        padding:15px;
        font-size:20px;
        font-weight:700;
        display:flex;
        justify-content:space-between;
        align-items:center;
    }}

    .tabs {{
        display:flex;
        gap:10px;
        padding:10px 15px;
        overflow-x:auto;
    }}

    .tab {{
        padding:6px 12px;
        border-radius:20px;
        background:#111827;
        color:white;
        font-size:12px;
        cursor:pointer;
    }}

    body.dark .tab {{
        background:#334155;
    }}

    .card {{
        margin:12px;
        padding:16px;
        border-radius:16px;
        background:white;
        box-shadow:0 3px 10px rgba(0,0,0,0.05);
    }}

    body.dark .card {{
        background:#1e293b;
        box-shadow:none;
    }}

    .badge {{
        font-size:11px;
        font-weight:700;
        padding:4px 8px;
        border-radius:6px;
        display:inline-block;
        margin-bottom:8px;
        color:black;
    }}

    .headline {{
        font-size:17px;
        font-weight:700;
        margin-bottom:8px;
    }}

    .summary {{
        font-size:14px;
        margin-bottom:10px;
    }}

    .meta {{
        font-size:12px;
        opacity:0.6;
    }}

    a {{ text-decoration:none; color:inherit; }}

    .toggle {{
        cursor:pointer;
        font-size:14px;
        margin-left:10px;
    }}

    /* Scroll To Top Button */
    #scrollTopBtn {{
        display:none;
        position:fixed;
        bottom:25px;
        right:20px;
        z-index:99;
        border:none;
        background:#111827;
        color:white;
        padding:12px 15px;
        border-radius:50%;
        font-size:16px;
        cursor:pointer;
        box-shadow:0 4px 8px rgba(0,0,0,0.2);
    }}

    body.dark #scrollTopBtn {{
        background:#e5e7eb;
        color:black;
    }}
    </style>

    <script>
    function filterCategory(cat) {{
        let cards = document.querySelectorAll(".card");
        cards.forEach(card => {{
            if (cat === "ALL" || card.dataset.category === cat) {{
                card.style.display = "block";
            }} else {{
                card.style.display = "none";
            }}
        }});
    }}

    function toggleTheme() {{
        document.body.classList.toggle("dark");
        localStorage.setItem("theme",
            document.body.classList.contains("dark") ? "dark" : "light");
    }}

    window.onload = function() {{
        if(localStorage.getItem("theme") === "dark") {{
            document.body.classList.add("dark");
        }}
    }}

    // Scroll detection
    window.onscroll = function() {{
        let btn = document.getElementById("scrollTopBtn");
        if (document.body.scrollTop > 300 ||
            document.documentElement.scrollTop > 300) {{
            btn.style.display = "block";
        }} else {{
            btn.style.display = "none";
        }}
    }};

    function scrollToTop() {{
        window.scrollTo({{ top: 0, behavior: "smooth" }});
    }}
    </script>
    </head>

    <body>
    <div class="header">
        Metals & AI Intelligence
        <div>
            <span class="toggle" onclick="toggleTheme()">🌙 / ☀️</span>
            <span class="toggle" onclick="location.reload()">🔄 Refresh</span>
        </div>
    </div>

    <div class="tabs">
        <div class="tab" onclick="filterCategory('ALL')">All</div>
        <div class="tab" onclick="filterCategory('METALS')">🪙 Metals</div>
        <div class="tab" onclick="filterCategory('AI')">🤖 AI</div>
        <div class="tab" onclick="filterCategory('CRISIS')">⚠️ Crisis</div>
    </div>

    <div style="padding:0 15px 10px 15px;font-size:12px;opacity:0.6;">
        Last Updated: {last_updated_time}
    </div>
    """

    for a in news_cache:
        html += f"""
        <div class="card" data-category="{a['category']}">
            <span class="badge" style="background:{a['color']}">{a['category']}</span>
            <a href="{a['link']}" target="_blank">
                <div class="headline">{a['title']}</div>
                <div class="summary">{a['summary']}</div>
            </a>
            <div class="meta">{a['source']} • {a['region']} • {a['published']}</div>
        </div>
        """

    html += """
    <button onclick="scrollToTop()" id="scrollTopBtn">⬆</button>
    </body></html>
    """

    return html


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
