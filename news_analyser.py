from deep_translator import GoogleTranslator
import requests
import pandas as pd
from textblob import TextBlob
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os

NEWS_API_KEY = os.environ["NEWS_API_KEY"]
SENDER_EMAIL = os.environ["SENDER_EMAIL"]
RECEIVER_EMAIL = os.environ["RECEIVER_EMAIL"]
APP_PASSWORD = os.environ["APP_PASSWORD"]

# Fetch news with images from NewsAPI
url = f"https://newsapi.org/v2/top-headlines?language=en&pageSize=30&apiKey={NEWS_API_KEY}"
response = requests.get(url)
data = response.json()

articles = []
for article in data.get("articles", []):
    articles.append({
        "source": article["source"]["name"],
        "title": article.get("title", ""),
        "summary": article.get("description", ""),
        "link": article.get("url", ""),
        "image": article.get("urlToImage", "")
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
# Translate to Swahili
print("Translating to Swahili...")
df["title"] = df["title"].apply(lambda x: GoogleTranslator(source='auto', target='sw').translate(str(x)))
df["summary"] = df["summary"].apply(lambda x: GoogleTranslator(source='auto', target='sw').translate(str(x)) if str(x) != "nan" else "")
print("Translation done!")
df["topic"] = df["title"].apply(categorize_topic)

# Build email
msg = MIMEMultipart("alternative")
msg["Subject"] = "Your Daily News Report " + pd.Timestamp.now().strftime("%B %d, %Y")
msg["From"] = SENDER_EMAIL
msg["To"] = RECEIVER_EMAIL

# Build news cards with images
cards = ""
for _, row in df.iterrows():
    image_html = ""
    if row["image"] and str(row["image"]) != "nan":
        image_html = f'<img src="{row["image"]}" width="400" style="border-radius:8px; margin-bottom:8px;"/><br/>'
    
    if row["sentiment"] == "Positive":
        sentiment_color = "green"
    elif row["sentiment"] == "Negative":
        sentiment_color = "red"
    else:
        sentiment_color = "gray"

    cards += f"""
    <div style="border:1px solid #ddd; border-radius:10px; padding:15px; margin-bottom:20px; font-family:Arial;">
        {image_html}
        <small style="color:#888;">{row['source']} &nbsp;|&nbsp; {row['topic']}</small><br/>
        <b style="font-size:16px;">{row['title']}</b><br/><br/>
        <p style="color:#555;">{row['summary']}</p>
        <span style="color:{sentiment_color}; font-weight:bold;">● {row['sentiment']}</span>
        &nbsp;&nbsp;
        <a href="{row['link']}" style="background:#1a73e8; color:white; padding:6px 12px; border-radius:5px; text-decoration:none;">Read More</a>
    </div>
    """

html = f"""
<div style="max-width:650px; margin:auto; font-family:Arial;">
    <h1 style="color:#1a73e8;">📰 Daily News Report</h1>
    <p>{pd.Timestamp.now().strftime("%B %d, %Y")} &nbsp;|&nbsp; {len(df)} articles analysed</p>
    <hr/>
    {cards}
    <p style="color:#aaa; font-size:12px;">Generated automatically by your News Analyser 🤖</p>
</div>
"""

msg.attach(MIMEText(html, "html"))

with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
    server.login(SENDER_EMAIL, APP_PASSWORD)
    server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())

print("Email sent successfully!")
