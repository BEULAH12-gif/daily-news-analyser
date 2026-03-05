import feedparser
import pandas as pd
from textblob import TextBlob
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os

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

def get_sentiment(text):
    polarity = TextBlob(str(text)).sentiment.polarity
    if polarity > 0.1:
        return "Positive"
    elif polarity < -0.1:
        return "Negative"
    else:
        return "Neutral"

def categorize_topic(text):
    text = text.lower()
    if any(w in text for w in ["war", "attack", "military", "missile", "strike"]):
        return "War and Conflict"
    elif any(w in text for w in ["election", "president", "government", "minister"]):
        return "Politics"
    elif any(w in text for w in ["stock", "economy", "market", "inflation", "bank"]):
        return "Economy"
    elif any(w in text for w in ["climate", "weather", "earthquake", "flood"]):
        return "Environment"
    elif any(w in text for w in ["ai", "tech", "apple", "google", "microsoft"]):
        return "Technology"
    elif any(w in text for w in ["health", "virus", "cancer", "hospital", "vaccine"]):
        return "Health"
    elif any(w in text for w in ["sport", "football", "basketball", "olympic"]):
        return "Sports"
    else:
        return "General"

df["sentiment"] = df["title"].apply(get_sentiment)
df["topic"] = df["title"].apply(categorize_topic)

SENDER_EMAIL = os.environ["SENDER_EMAIL"]
RECEIVER_EMAIL = os.environ["RECEIVER_EMAIL"]
APP_PASSWORD = os.environ["APP_PASSWORD"]

msg = MIMEMultipart("alternative")
msg["Subject"] = "Your Daily News Report " + pd.Timestamp.now().strftime("%B %d, %Y")
msg["From"] = SENDER_EMAIL
msg["To"] = RECEIVER_EMAIL

rows = ""
for _, row in df.iterrows():
    rows += "<tr><td>" + row["source"] + "</td><td>" + row["title"] + "</td><td>" + row["topic"] + "</td><td>" + row["sentiment"] + "</td><td><a href='" + row["link"] + "'>Read More</a></td></tr>"

html = """
<h2>Today's News Analysis</h2>
<p>Total articles: """ + str(len(df)) + """</p>
<h3>Top Headlines</h3>
<table border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse; width:100%;">
<tr style="background-color:#f2f2f2;">
<th>Source</th><th>Headline</th><th>Topic</th><th>Sentiment</th><th>Link</th>
</tr>
""" + rows + """
</table>
<p>Generated automatically by your News Analyser</p>
"""

msg.attach(MIMEText(html, "html"))

with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
    server.login(SENDER_EMAIL, APP_PASSWORD)
    server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())

print("Email sent successfully!")
