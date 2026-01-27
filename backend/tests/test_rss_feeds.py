"""Test RSS feeds with User-Agent header"""
import feedparser
import requests
from datetime import datetime, timedelta

# ✅ Add User-Agent
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/rss+xml, application/xml, text/xml'
}

feeds_to_test = [
    ("Indian Express Mumbai", "https://indianexpress.com/section/cities/mumbai/feed/"),
    ("The Hindu Mumbai", "https://www.thehindu.com/news/cities/mumbai/feeder/default.rss"),
    ("Mid-Day Mumbai", "https://www.mid-day.com/rss-feed/mumbai-news.xml"),
    ("Times of India Mumbai", "https://timesofindia.indiatimes.com/rssfeeds/2647163.cms"),
    ("ET TravelWorld", "https://travel.economictimes.indiatimes.com/rss/topstories"),
    ("Travel + Leisure", "https://www.travelandleisureindia.in/feed/"),
    ("Conde Nast Traveller", "https://www.cntraveller.in/feed/"),
    ("The Hindu Food", "https://www.thehindu.com/life-and-style/food/feeder/default.rss"),
]

print("Testing RSS Feeds with User-Agent...\n")
print("="*70)

for name, url in feeds_to_test:
    print(f"\n{name}")
    print(f"URL: {url}")
    
    try:
        # ✅ Use requests with headers
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        feed = feedparser.parse(response.content)
        
        total_entries = len(feed.entries)
        print(f"✅ Total entries: {total_entries}")
        
        if total_entries > 0:
            cutoff = datetime.now() - timedelta(days=30)
            recent = 0
            
            for entry in feed.entries[:10]:
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    from time import mktime
                    try:
                        pub_date = datetime.fromtimestamp(mktime(entry.published_parsed))
                        if pub_date > cutoff:
                            recent += 1
                    except:
                        pass
            
            print(f"   Recent (last 30 days): {recent}")
            if feed.entries:
                print(f"   Sample: {feed.entries[0].get('title', 'No title')[:60]}...")
        else:
            print(f"❌ No entries found")
    
    except Exception as e:
        print(f"❌ Error: {str(e)[:100]}")
    
    print("-"*70)
