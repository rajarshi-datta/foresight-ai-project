import yfinance as yf
from transformers import pipeline
import feedparser
from urllib.parse import quote_plus

# --- THIS IS THE KEY CHANGE ---
# 1. Don't load the model immediately. Initialize it as None.
sentiment_pipeline = None

def get_sentiment_pipeline():
    """
    This function loads the sentiment model on demand and caches it.
    """
    global sentiment_pipeline
    # 2. If the model hasn't been loaded yet, load it now.
    if sentiment_pipeline is None:
        print("--- Initializing sentiment analysis model for the first time... ---")
        sentiment_pipeline = pipeline("sentiment-analysis", model="ProsusAI/finbert")
    return sentiment_pipeline

def get_news_sentiment(ticker: str):
    """
    Fetches news and analyzes sentiment, using the lazy-loaded model.
    """
    print(f"--- Fetching and analyzing news for {ticker} ---")
    try:
        # 3. Call the function to get the model.
        #    The first time this runs, it will be slow. Subsequent times, it will be instant.
        pipeline_to_use = get_sentiment_pipeline()
        
        stock = yf.Ticker(ticker)
        news = stock.news
        headlines_to_process = []

        # ... (The rest of your news fetching logic remains exactly the same) ...
        if news:
            print(f"Found {len(news)} headlines for {ticker} via yfinance.")
            for article in news[:8]:
                title = article.get('title')
                if title:
                    headlines_to_process.append(title)

        if not headlines_to_process:
            print(f"yfinance failed for {ticker}, falling back to Google News RSS...")
            company_name = stock.info.get('longName', ticker)
            query = quote_plus(f"{company_name} stock")
            feed_url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:8]:
                if entry.title:
                    headlines_to_process.append(entry.title)

        if not headlines_to_process:
            return {
                "overall_sentiment": "Neutral", "score": 0.5,
                "headlines": [{"title": "No recent news found for this stock.", "sentiment": "neutral"}]
            }

        analyzed_headlines = []
        positive_score = 0
        count = 0

        for title in headlines_to_process:
            # 4. Use the loaded model.
            result = pipeline_to_use(title)[0]
            analyzed_headlines.append({"title": title, "sentiment": result['label'].lower()})
            if result['label'].lower() == 'positive':
                positive_score += 1
            count += 1
        
        overall_score = positive_score / count if count > 0 else 0.5
        overall_sentiment = "Positive" if overall_score > 0.6 else "Negative" if overall_score < 0.4 else "Neutral"

        return {
            "overall_sentiment": overall_sentiment, "score": overall_score,
            "headlines": analyzed_headlines
        }
    except Exception as e:
        print(f"Could not get news sentiment for {ticker}: {e}")
        return {"error": str(e)}