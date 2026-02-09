"""
RSS Feed service for scraping travel and food blogs
"""
import feedparser
import requests
from typing import List, Dict, Optional
from datetime import datetime, timedelta,timezone
from bs4 import BeautifulSoup
import re
import logging

from app.core.config import settings
from app.core.mongo import get_database
from app.models.poi import BlogPost, IngestionMetadata


logger = logging.getLogger(__name__)


class RSSService:
    """Service for fetching and parsing RSS feeds from travel/food blogs"""
    
    # ✅ VERIFIED 2026 RSS FEEDS
    BLOG_FEEDS = {
        "mumbai": [
            {
                "name": "Indian Express - Mumbai",
                "url": "https://indianexpress.com/section/cities/mumbai/feed/",
                "city": "mumbai",
                "categories": ["news", "food", "culture"]
            },
            {
                "name": "The Hindu - Mumbai",
                "url": "https://www.thehindu.com/news/cities/mumbai/feeder/default.rss",
                "city": "mumbai",
                "categories": ["news", "events"]
            },
            {
                "name": "Mid-Day Mumbai News",
                "url": "https://www.mid-day.com/rss-feed/mumbai-news.xml",
                "city": "mumbai",
                "categories": ["news", "food", "lifestyle"]
            },
            {
                "name": "Times of India - Mumbai",
                "url": "https://timesofindia.indiatimes.com/rssfeeds/2647163.cms",
                "city": "mumbai",
                "categories": ["news", "food", "lifestyle"]
            },
        ],
        "delhi": [
            {
                "name": "Indian Express - Delhi",
                "url": "https://indianexpress.com/section/cities/delhi/feed/",
                "city": "delhi",
                "categories": ["news", "food", "culture"]
            },
            {
                "name": "The Hindu - Delhi",
                "url": "https://www.thehindu.com/news/cities/Delhi/feeder/default.rss",
                "city": "delhi",
                "categories": ["news", "events"]
            },
            {
                "name": "Times of India - Delhi",
                "url": "https://timesofindia.indiatimes.com/rssfeeds/1353607.cms",
                "city": "delhi",
                "categories": ["news", "food"]
            },
        ],
        "bangalore": [
            {
                "name": "Indian Express - Bangalore",
                "url": "https://indianexpress.com/section/cities/bangalore/feed/",
                "city": "bangalore",
                "categories": ["news", "food", "tech"]
            },
            {
                "name": "The Hindu - Bangalore",
                "url": "https://www.thehindu.com/news/cities/bangalore/feeder/default.rss",
                "city": "bangalore",
                "categories": ["news", "events"]
            },
            {
                "name": "Times of India - Bangalore",
                "url": "https://timesofindia.indiatimes.com/rssfeeds/2950623.cms",
                "city": "bangalore",
                "categories": ["news", "food", "tech"]
            },
        ],
        "pune": [
            {
                "name": "Indian Express - Pune",
                "url": "https://indianexpress.com/section/cities/pune/feed/",
                "city": "pune",
                "categories": ["news", "food"]
            },
            {
                "name": "Times of India - Pune",
                "url": "https://timesofindia.indiatimes.com/rssfeeds/4118245.cms",
                "city": "pune",
                "categories": ["news", "food"]
            },
        ],
        "goa": [
            {
                "name": "Times of India - Goa",
                "url": "https://timesofindia.indiatimes.com/rssfeeds/3012535.cms",
                "city": "goa",
                "categories": ["news", "tourism"]
            },
        ],
        "general": [
            {
                "name": "ET TravelWorld",
                "url": "https://travel.economictimes.indiatimes.com/rss/topstories",
                "city": "india",
                "categories": ["tourism", "trade", "news"]
            },
            {
                "name": "Travel + Leisure India",
                "url": "https://www.travelandleisureindia.in/feed/",
                "city": "india",
                "categories": ["luxury", "travel", "hotels"]
            },
            {
                "name": "Conde Nast Traveller India",
                "url": "https://www.cntraveller.in/feed/",
                "city": "india",
                "categories": ["lifestyle", "food", "travel"]
            },
            {
                "name": "The Hindu - Food",
                "url": "https://www.thehindu.com/life-and-style/food/feeder/default.rss",
                "city": "india",
                "categories": ["culinary", "restaurants"]
            },
            {
                "name": "Indian Express - Food & Wine",
                "url": "https://indianexpress.com/section/lifestyle/food-wine/feed/",
                "city": "india",
                "categories": ["food", "wine", "recipes"]
            },
            {
                "name": "The Better India",
                "url": "https://www.thebetterindia.com/feed/",
                "city": "india",
                "categories": ["culture", "travel", "stories"]
            },
            {
                "name": "Outlook Traveller",
                "url": "https://www.outlooktraveller.com/feed",
                "city": "india",
                "categories": ["travel", "guides", "tips"]
            },
        ]
    }
    
    # ✅ User-Agent to prevent 403 Forbidden errors
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/rss+xml, application/xml, text/xml, */*'
    }
    
    def __init__(self):
        """Initialize RSS service"""
        self._db = None
        self._blog_posts_collection = None
        self._metadata_collection = None
        
        logger.info("✅ RSSService initialized")
    
    @property
    def db(self):
        """Lazy load database connection"""
        if self._db is None:
            self._db = get_database()
        return self._db
    
    @property
    def blog_posts_collection(self):
        """Lazy load blog_posts collection"""
        if self._blog_posts_collection is None:
            self._blog_posts_collection = self.db["blog_posts"]
        return self._blog_posts_collection
    
    @property
    def metadata_collection(self):
        """Lazy load metadata collection"""
        if self._metadata_collection is None:
            self._metadata_collection = self.db["ingestion_metadata"]
        return self._metadata_collection
    
    def clean_html(self, html_content: str) -> str:
        """
        Clean HTML content and extract plain text
        
        Args:
            html_content: HTML string
        
        Returns:
            Clean plain text
        """
        if not html_content:
            return ""
        
        # Parse HTML
        soup = BeautifulSoup(html_content, 'lxml')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text
        text = soup.get_text()
        
        # Clean whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text
    
    def extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text"""
        keywords_list = [
            "restaurant", "cafe", "food", "street food", "breakfast", "lunch", "dinner",
            "beach", "temple", "museum", "park", "attraction", "heritage", "culture",
            "guide", "itinerary", "tour", "tips", "hidden gem", "local", "authentic",
            "vada pav", "biryani", "dosa", "chai", "seafood", "vegetarian",
            "weekend", "getaway", "festival", "event", "new opening"
        ]
        
        text_lower = text.lower()
        found_keywords = []
        
        for keyword in keywords_list:
            if keyword in text_lower:
                found_keywords.append(keyword)
        
        return found_keywords[:10]
    
    def fetch_feed(
        self,
        feed_url: str,
        days_back: int = 7
    ) -> List[Dict]:
        """
        Fetch entries from an RSS feed with User-Agent header
        
        Args:
            feed_url: RSS feed URL
            days_back: How many days back to fetch
        
        Returns:
            List of feed entries
        """
        logger.info(f"📥 Fetching feed: {feed_url}")
        
        try:
            # ✅ Use requests with User-Agent header to avoid 403
            response = requests.get(
                feed_url,
                headers=self.HEADERS,
                timeout=10
            )
            response.raise_for_status()
            
            # Parse feed from response content
            feed = feedparser.parse(response.content)
            
            # Check for parsing errors
            if feed.bozo and not feed.entries:
                logger.warning(f"⚠️ Feed has issues and no entries: {feed_url}")
                return []
            
            # Calculate cutoff date
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_back)
            
            entries = []
            for entry in feed.entries:
                # Parse published date
                published_dt = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    from time import mktime
                    try:
                        published_dt = datetime.fromtimestamp(mktime(entry.published_parsed),tz=timezone.utc)
                    except Exception:
                        published_dt = datetime.now(timezone.utc)
                elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                    from time import mktime
                    try:
                        published_dt = datetime.fromtimestamp(mktime(entry.updated_parsed),tz=timezone.utc)
                    except Exception:
                        published_dt = datetime.now(timezone.utc)
                else:
                    published_dt = datetime.now(timezone.utc)
                
                # ✅ Ensure published_dt is timezone-aware before comparison
                if published_dt.tzinfo is None:
                    published_dt = published_dt.replace(tzinfo=timezone.utc)
                # Filter by date
                if published_dt < cutoff_date:
                    continue
                
                # Extract content
                content = ""
                if hasattr(entry, 'content'):
                    content = entry.content[0].value
                elif hasattr(entry, 'summary'):
                    content = entry.summary
                elif hasattr(entry, 'description'):
                    content = entry.description
                
                # Clean HTML
                clean_content = self.clean_html(content)
                
                # Skip if too short
                if len(clean_content) < 50:
                    continue
                
                entries.append({
                    "title": entry.get('title', 'Untitled'),
                    "content": clean_content,
                    "url": entry.get('link', ''),
                    "author": entry.get('author', None),
                    "published_at": published_dt
                })
            
            logger.info(f"✅ Found {len(entries)} entries from {feed_url}")
            return entries
        
        except requests.exceptions.HTTPError as e:
            logger.error(f"❌ HTTP error fetching {feed_url}: {e.response.status_code if e.response else 'unknown'}")
            return []
        except Exception as e:
            logger.error(f"❌ Error fetching feed {feed_url}: {str(e)[:100]}")
            return []
    
    def fetch_blog_feeds(
        self,
        city: str,
        days_back: int = 7,
        include_general: bool = True
    ) -> List[BlogPost]:
        """
        Fetch blog posts from multiple feeds for a city
        
        Args:
            city: City name
            days_back: How many days back to fetch
            include_general: Include general India feeds
        
        Returns:
            List of BlogPost objects
        """
        logger.info(f"📰 Fetching blog feeds for {city} (last {days_back} days)")
        
        # Get feeds for city
        feeds = self.BLOG_FEEDS.get(city.lower(), [])
        
        # Add general feeds if requested
        if include_general:
            feeds.extend(self.BLOG_FEEDS.get("general", []))
        
        if not feeds:
            logger.warning(f"No feeds configured for {city}")
            return []
        
        all_posts = []
        
        for feed_info in feeds:
            entries = self.fetch_feed(feed_info["url"], days_back)
            
            for entry in entries:
                # Extract keywords
                keywords = self.extract_keywords(entry["title"] + " " + entry["content"])
                
                # Create BlogPost object
                blog_post = BlogPost(
                    title=entry["title"],
                    content=entry["content"],
                    author=entry.get("author"),
                    url=entry["url"],
                    published_at=entry["published_at"],
                    blog_name=feed_info["name"],
                    city=city.lower(),
                    tags=keywords
                )
                
                all_posts.append(blog_post)
        
        logger.info(f"✅ Total posts fetched: {len(all_posts)}")
        return all_posts
    
    async def store_blog_posts(self, posts: List[BlogPost]) -> int:
        """Store blog posts in MongoDB (upsert based on URL)"""
        if not posts:
            return 0
        
        count = 0
        for post in posts:
            result = await self.blog_posts_collection.update_one(
                {"url": post.url},
                {"$set": post.dict(by_alias=True, exclude={"id"})},
                upsert=True
            )
            if result.upserted_id or result.modified_count > 0:
                count += 1
        
        logger.info(f"✅ Stored {count} blog posts in MongoDB")
        return count
    
    async def get_last_ingested_date(self, source: str, city: str) -> Optional[datetime]:
        """Get the last time blog feeds were ingested for a city"""
        metadata = await self.metadata_collection.find_one({
            "source": source,
            "city": city
        })
        
        return metadata.get("last_scraped_at") if metadata else None
    
    async def update_ingestion_metadata(
        self,
        source: str,
        city: str,
        records_processed: int,
        status: str = "success",
        error_message: Optional[str] = None
    ):
        """Update ingestion metadata after scraping"""
        metadata = IngestionMetadata(
            source=source,
            city=city,
            last_scraped_at=datetime.now(timezone.utc),
            records_processed=records_processed,
            status=status,
            error_message=error_message
        )
        
        await self.metadata_collection.update_one(
            {"source": source, "city": city},
            {"$set": metadata.dict(by_alias=True, exclude={"id"})},
            upsert=True
        )
        
        logger.info(f"✅ Updated metadata: {source} for {city}")


# Singleton instance
rss_service = RSSService()
