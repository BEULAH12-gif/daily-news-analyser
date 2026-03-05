import feedparser
import pandas as pd
from textblob import TextBlob
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os

# News RSS feeds
rss_feeds = {
    "BBC": "http://feeds.bbci.co.uk/news/rss.xml",
    "Reuters": "https://feeds.reuters.com/reuters/topNews",
    "AP News": "https://feeds.apnews.com/rss/apf-topnews",
    "Google News": "https://news.google.com/rss"
}

articles = []
for source, url in rss_feeds.items():
    feed = feedparser.parse(url)
    for entry in feed.entries[:10]:
        articles.append({
            "source": source,
            "title": entry.get("title", ""),
            "summary": entry.get("summary", ""),
            "link": entry.get("link", "")
        })

df = pd.DataFrame(articles)

# Sentiment
def get_sentiment(text):
    polarity = TextBlob(str(text)).sentiment.polarity
    if polarity > 0.1: return "Positive 😊"
    elif polarity < -0.1: return "Negative 😟"
    else: return "Neutral 😐"

df["sentiment"] = df["title"].apply(get_sentiment)

# Topics
def categorize_topic(text):
    text = text.lower()
    if any(w in text for w in ["war", "attack", "military", "missile", "strike"]):
        return "⚔️ War & Conflict"
    elif any(w in text for w in ["election", "president", "government", "minister"]):
        return "🏛️ Politics"
    elif any(w in text for w in ["stock", "economy", "market", "inflation", "bank"]):
        return "💰 Economy"
    elif any(w in text for w in ["climate", "weather", "earthquake", "flood"]):
        return "🌍 Environment"
    elif any(w in text for w in ["ai", "tech", "apple", "google", "microsoft"]):
        return "💻 Technology"
    elif any(w in text for w in ["health", "virus", "cancer", "hospital", "vaccine"]):
        return "🏥 Health"
    elif any(w in text for w in ["sport", "football", "basketball", "olympic"]):
        return "⚽ Sports"
    else:
        return "📌 General"

df["topic"] = df["title"].apply(categorize_topic)

# Email credentials from GitHub Secrets
SENDER_EMAIL = os.environ["SENDER_EMAIL"]
RECEIVER_EMAIL = os.environ["RECEIVER_EMAIL"]
APP_PASSWORD = os.environ["APP_PASSWORD"]

def send_news_report(df):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"📰 Your Daily News Report — {pd.Timestamp.now().strftime('%B %d, %Y')}"
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL

    html = f"""
    <h2>📰 Today's News Analysis</h2>
    <p>✅ <b>{len(df)} articles</b> analysed from {', '.join(df['source'].unique())}</p>

    <h3>📊 Sentiment Summary</h3>
    <ul>
    {"".join(f"<li>{s}: {c} articles</li>" for s, c in df['sentiment'].value_counts().items())}
    </ul>

    <h3>🗂️ Topic Summary</h3>
    <ul>
    {"".join(f"<li>{t}: {c} articles</li>" for t, c in df['topic'].value_counts().items())}
    </ul>

    <h3>📰 Top Headlines</h3>
    <table border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse; width:100%;">
        <tr style="background-color:#f2f2f2;">
            <th>Source</th>
            <th>Headline</th>
            <th>Topic</th>
            <th>Sentiment</th>
            <th>Link</th>
        </tr>
        {"".join(f'''
        <tr>
            <td><b>{row['source']}</b></td>
            <td>{row['title']}</td>
            <td>{row['topic']}</td>
            <td>{row['sentiment']}</td>
            <td><a href="{row['link']}" target="_blank">Read More 🔗</a></td>
        </tr>''' for _, row in df.iterrows())}
    </table>
    <br>
    <p><i>Generated automatically by your Jupyter News Analyser 🤖</i></p>
    """

    msg.attach(MIMEText(html, "html"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(SENDER_EMAIL, APP_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
    print("✅ Email sent successfully!")

send_news_report(df)
