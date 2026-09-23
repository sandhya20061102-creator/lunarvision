# backend/routers/news_routes.py

"""
Router providing a lightweight proxy for the official ISRO news RSS feed.

Why a proxy?
- Avoids CORS issues in the browser when fetching directly.
- Allows us to transform XML → JSON once and reuse the parsed result.
- Keeps the frontend offline‑first: the client only talks to our FastAPI server.
"""

from fastapi import APIRouter, HTTPException
import httpx
import xml.etree.ElementTree as ET
from typing import List, Dict

router = APIRouter()

# URL of the public ISRO news RSS feed (can be changed via env var if needed)
NEWS_RSS_URL = "https://www.isro.gov.in/NewsRss.xml"

def _parse_rss_item(item: ET.Element) -> Dict:
    """Extract a subset of fields from an <item> element.
    Returns a dict with keys: title, link, pubDate, description.
    """
    def _text(tag: str) -> str:
        el = item.find(tag)
        return el.text.strip() if el is not None and el.text else ""

    return {
        "title": _text("title"),
        "link": _text("link"),
        "date": _text("pubDate"),
        "summary": _text("description"),
        "source": "ISRO",
    }

@router.get("/news", response_model=List[Dict[str, str]])
async def get_latest_news():
    """Fetch the ISRO RSS feed, parse items, and return a JSON array.
    Errors are reported as HTTP 502 (Bad Gateway) because they originate
    from an upstream external service.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(NEWS_RSS_URL)
            resp.raise_for_status()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch ISRO news: {e}")

    try:
        root = ET.fromstring(resp.content)
        # The RSS <channel> contains many <item> elements.
        channel = root.find("channel")
        items = channel.findall("item") if channel is not None else []
        news = [_parse_rss_item(it) for it in items]
        return news
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse RSS feed: {e}")
