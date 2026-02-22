from flask import Flask
import feedparser
from datetime import datetime, timedelta
import time
import re

app = Flask(__name__)

# ---------------- SOURCES (6 GLOBAL + 6 INDIA) ---------------- #

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

MACRO_CONTEXT = ["market", "stocks", "economy", "gold", "silver", "central bank", "interest rate"]
EXCLUDE_WORDS = ["401(k)", "loyalty", "credit card", "travel", "entertainment"]

@app.route("/")
def home():

    articles = []
    seen_titles = set()

    # ✅ 3 DAY FILTER
    three_days_ago = datetime.now() - timedelta(days=3)
    now_time = datetime.now().strftime("%b %d, %H:%M IST")


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

            # Dedup
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

            elif (
                any(k in content for k in CRISIS_KEYWORDS)
                and any(m in content for m in MACRO_CONTEXT)
                and not any(e in content for e in EXCLUDE_WORDS)
            ):
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

    # Sort newest first
    articles.sort(key=lambda x: x["published"], reverse=True)

    # ---------------- UI ---------------- #

    html = f"""
    <html>
    <head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Metals & AI Intelligence</title>

    <style>
    body {{
        margin:0;
        font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        transition:0.3s;
    }}

    body.light {{ background:#f3f4f6; color:#111827; }}
    body.dark {{ background:#0b1220; color:#e5e7eb; }}

    .header {{
        padding:15px;
        font-weight:700;
        font-size:20px;
        display:flex;
        justify-content:space-between;
        align-items:center;
    }}

    .sub-info {{
        font-size:12px;
        opacity:0.7;
        padding:0 15px 10px 15px;
    }}

    .chip-bar {{
        display:flex;
        gap:8px;
        overflow-x:auto;
        padding:10px;
    }}

    .chip {{
        padding:8px 14px;
        border-radius:20px;
        font-size:13px;
        border:none;
        cursor:pointer;
        white-space:nowrap;
    }}

    .chip.active {{
        background:#111827;
        color:white;
    }}

    body.dark .chip.active {{
        background:#facc15;
        color:black;
    }}

    .card {{
        margin:12px;
        padding:16px;
        border-radius:16px;
        background:white;
        box-shadow:0 3px 10px rgba(0,0,0,0.05);
    }}

    body.dark .card {{
        background:#111827;
        border:1px solid #1f2937;
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
        font-size:18px;
        font-weight:700;
        line-height:1.4;
        margin-bottom:8px;
    }}

    .summary {{
        font-size:14px;
        line-height:1.5;
        opacity:0.85;
        margin-bottom:10px;
    }}

    .meta {{
        font-size:12px;
        opacity:0.6;
    }}

    a {{ text-decoration:none; color:inherit; }}

    .footer-bar {{
        position:fixed;
        bottom:0;
        width:100%;
        padding:10px;
        display:flex;
        justify-content:center;
        background:inherit;
    }}

    .btn {{
        padding:8px 12px;
        border-radius:10px;
        border:none;
        cursor:pointer;
        font-size:13px;
    }}
    </style>

    <script>
    function filterCategory(cat){{
        let cards=document.querySelectorAll(".card");
        cards.forEach(c=>{{
            if(cat=="ALL" || c.dataset.category==cat){{
                c.style.display="block";
            }} else {{
                c.style.display="none";
            }}
        }});

        document.querySelectorAll(".chip").forEach(ch=>ch.classList.remove("active"));
        document.getElementById(cat).classList.add("active");
    }}

    function toggleTheme(){{
        document.body.classList.toggle("dark");
        document.body.classList.toggle("light");
    }}

    function refreshPage(){{ location.reload(); }}

    let timeLeft=300;
    setInterval(function(){{
        document.getElementById("timer").innerText =
            "Auto refresh in " + timeLeft + " sec";
        if(timeLeft<=0) location.reload();
        timeLeft--;
    }},1000);

    window.onload=function(){{
        document.body.classList.add("light");
        filterCategory("ALL");
    }}
    </script>
    </head>
    <body>

    <div class="header">
        <div>Metals & AI Intelligence</div>
        <button class="btn" onclick="toggleTheme()">Light/Dark</button>
    </div>

    <div class="sub-info">
        Last Updated: {now_time} • <span id="timer"></span>
    </div>

    <div class="chip-bar">
        <button class="chip active" id="ALL" onclick="filterCategory('ALL')">All</button>
        <button class="chip" id="METALS" onclick="filterCategory('METALS')">🪙 Metals</button>
        <button class="chip" id="AI" onclick="filterCategory('AI')">🤖 AI</button>
        <button class="chip" id="CRISIS" onclick="filterCategory('CRISIS')">⚠️ Crisis</button>
    </div>
    """

    for a in articles:
        html += f"""
        <div class="card" data-category="{a['category']}">
            <span class="badge" style="background:{a['color']}">
                {a['category']}
            </span>

            <a href="{a['link']}" target="_blank">
                <div class="headline">{a['title']}</div>
                <div class="summary">{a['summary']}</div>
            </a>

            <div class="meta">
                {a['source']} • {a['region']} • {a['published']}
            </div>
        </div>
        """

    html += """
    <div class="footer-bar">
        <button class="btn" onclick="refreshPage()">Refresh</button>
    </div>

    </body>
    </html>
    """

    return html


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
