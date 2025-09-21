import yfinance as yf
from transformers import pipeline
import feedparser
from urllib.parse import quote_plus  # <-- NEW

# Initialize the sentiment analysis pipeline
sentiment_pipeline = pipeline("sentiment-analysis", model="ProsusAI/finbert")

def get_news_sentiment(ticker: str):
    """
    Fetches news for a ticker and analyzes the sentiment of the headlines.
    First tries yfinance, then falls back to Google News RSS.
    """
    print(f"--- Fetching and analyzing news for {ticker} ---")
    try:
        stock = yf.Ticker(ticker)
        news = stock.news
        headlines_to_process = []

        # --- Method 1: Try yfinance first ---
        if news:
            print(f"Found {len(news)} headlines for {ticker} via yfinance.")
            for article in news[:8]:
                title = article.get('title')
                if title:
                    headlines_to_process.append(title)

        # --- Method 2: Fallback to Google News RSS ---
        if not headlines_to_process:
            print(f"yfinance failed for {ticker}, falling back to Google News RSS...")
            company_name = stock.info.get('longName', ticker)
            encoded_query = quote_plus(f"{company_name} stock")  # <-- FIXED
            feed_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
            feed = feedparser.parse(feed_url)

            for entry in feed.entries[:8]:
                if entry.title:
                    headlines_to_process.append(entry.title)

        # --- Final Check and Analysis ---
        if not headlines_to_process:
            return {
                "overall_sentiment": "Neutral",
                "score": 0.5,
                "headlines": [{"title": "No recent news found for this stock.", "sentiment": "neutral"}]
            }

        analyzed_headlines = []
        positive_score = 0
        count = 0

        for title in headlines_to_process:
            result = sentiment_pipeline(title)[0]
            analyzed_headlines.append({
                "title": title,
                "sentiment": result['label'].lower()
            })
            if result['label'].lower() == 'positive':
                positive_score += 1
            count += 1
        
        overall_score = positive_score / count if count > 0 else 0.5
        overall_sentiment = "Positive" if overall_score > 0.6 else "Negative" if overall_score < 0.4 else "Neutral"

        return {
            "overall_sentiment": overall_sentiment,
            "score": overall_score,
            "headlines": analyzed_headlines
        }

    except Exception as e:
        print(f"Could not get news sentiment for {ticker}: {e}")
        return {"error": str(e)}
