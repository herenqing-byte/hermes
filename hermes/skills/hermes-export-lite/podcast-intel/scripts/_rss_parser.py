"""
_rss_parser.py - Robust RSS/Atom feed parser using regex (no namespace issues).
Handles CDATA, namespaces, and malformed XML gracefully.
"""
import re
import html
from typing import List, Dict, Optional


def _cdata_to_text(s: str) -> str:
    """Extract content from CDATA sections."""
    return re.sub(r'<!\[CDATA\[(.*?)\]\]>', lambda m: m.group(1), s, flags=re.DOTALL)


def _strip_tags(s: str) -> str:
    """Strip HTML tags and decode entities."""
    if not s:
        return ""
    # Remove script/style
    s = re.sub(r'<(script|style)[^>]*>.*?</\1>', ' ', s, flags=re.DOTALL | re.IGNORECASE)
    # Preserve newlines
    s = re.sub(r'<br\s*/?>', '\n', s, flags=re.IGNORECASE)
    s = re.sub(r'<p[^>]*>', '\n', s, flags=re.IGNORECASE)
    s = re.sub(r'</p>', '\n', s, flags=re.IGNORECASE)
    # Strip tags
    s = re.sub(r'<[^>]+>', ' ', s)
    # Decode HTML entities
    s = html.unescape(s)
    # Collapse whitespace
    s = re.sub(r'\n{3,}', '\n\n', s)
    s = re.sub(r'[ \t]+', ' ', s)
    return s.strip()


def _extract_tag(content: str, tag: str, default: str = "") -> str:
    """Extract first occurrence of tag content, handles CDATA."""
    # Handle namespaced tags like content:encoded, dc:creator etc.
    pattern = rf'<{re.escape(tag)}[^>]*>(.*?)</{re.escape(tag)}>'
    m = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
    if not m:
        return default
    raw = m.group(1)
    return _cdata_to_text(raw).strip()


def parse_rss(content: str, source_name: str, max_items: int = 50) -> List[Dict]:
    """
    Parse RSS/Atom feed content using regex (no XML parser).
    Returns list of dicts with: title, url, date, description, content_html
    """
    items = []
    
    # Find all <item> blocks (RSS) or <entry> blocks (Atom)
    item_pattern = r'<item[^>]*>(.*?)</item>|<entry[^>]*>(.*?)</entry>'
    
    for match in re.finditer(item_pattern, content, re.DOTALL | re.IGNORECASE):
        item_content = match.group(1) or match.group(2)
        if not item_content:
            continue
        
        # Extract fields
        title = _strip_tags(_extract_tag(item_content, 'title'))
        
        # URL: try <link> href attribute first (Atom), then text content
        link_match = re.search(r'<link[^>]+href=["\']([^"\']+)["\']', item_content, re.IGNORECASE)
        if link_match:
            url = link_match.group(1)
        else:
            url = _cdata_to_text(_extract_tag(item_content, 'link')).strip()
            # Clean up any CDATA or whitespace
            url = re.sub(r'\s+', '', url)
        
        if not url:
            url = _cdata_to_text(_extract_tag(item_content, 'guid')).strip()
        
        # Date: try multiple fields
        date = (_extract_tag(item_content, 'pubDate') or
                _extract_tag(item_content, 'published') or
                _extract_tag(item_content, 'dc:date') or "")
        # Normalize to YYYY-MM-DD
        if date:
            date_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', date)
            if not date_match:
                # Try to parse "Mon, 15 Mar 2026" format
                months = {'jan':1,'feb':2,'mar':3,'apr':4,'may':5,'jun':6,
                         'jul':7,'aug':8,'sep':9,'oct':10,'nov':11,'dec':12}
                m2 = re.search(r'(\d{1,2})\s+(\w{3})\s+(\d{4})', date, re.IGNORECASE)
                if m2:
                    day, mon, year = m2.group(1), m2.group(2).lower()[:3], m2.group(3)
                    month_num = months.get(mon, 1)
                    date = f"{year}-{month_num:02d}-{int(day):02d}"
                else:
                    date = date[:10]
            else:
                date = date_match.group(0)
        
        # Description
        desc_html = (_extract_tag(item_content, 'description') or
                     _extract_tag(item_content, 'summary') or
                     _extract_tag(item_content, 'itunes:summary') or "")
        description = _strip_tags(desc_html)[:500]
        
        # Full content (content:encoded is the richest for RSS)
        # Use raw regex since tag has colon
        content_match = re.search(
            r'<content:encoded[^>]*>(.*?)</content:encoded>',
            item_content, re.DOTALL | re.IGNORECASE
        )
        if content_match:
            content_html = _cdata_to_text(content_match.group(1))
        else:
            content_html = desc_html
        
        content_text = _strip_tags(content_html)
        
        if title or url:
            items.append({
                'title': title,
                'url': url,
                'date': date,
                'description': description,
                'content': content_text[:60000],
                'source': source_name,
            })
        
        if len(items) >= max_items:
            break
    
    return items
