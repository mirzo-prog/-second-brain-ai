import urllib.request
import urllib.parse
import json
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("second_brain.visual_materials")

def find_visual_materials(query: str, limit: int = 2) -> List[Dict[str, Any]]:
    """
    Retrieves authentic educational illustrations, diagrams, and photos
    from Wikimedia Commons API under Creative Commons / Public Domain licenses.
    """
    clean_query = query.strip()
    if not clean_query:
        return []

    # Map Russian topics to common English terms if needed for broader Wikimedia Commons index
    term_map = {
        "клетка": "animal cell structure",
        "биология": "biology diagram",
        "древний рим": "ancient rome historical",
        "рим": "ancient rome",
        "римская империя": "roman empire map",
        "хирагана": "hiragana chart",
        "японский язык": "hiragana chart",
        "массив": "array data structure",
        "дерево": "binary search tree",
        "граф": "graph theory diagram",
        "квадратное уравнение": "quadratic function parabola",
        "парабола": "parabola function graph",
        "астрономия": "astronomy solar system planets",
        "физика": "physics experiment diagram",
        "анатомия": "human anatomy organs",
        "алгоритм": "algorithm flowchart diagram",
    }
    
    search_term = clean_query
    lower_q = clean_query.lower()
    for k, v in term_map.items():
        if k in lower_q:
            search_term = v
            break

    try:
        url = (
            f"https://commons.wikimedia.org/w/api.php?action=query&generator=search"
            f"&gsrnamespace=6&gsrsearch={urllib.parse.quote(search_term)}"
            f"&gsrlimit={limit}&prop=imageinfo&iiprop=url|extmetadata&iiurlwidth=800&format=json"
        )
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "SecondBrainAI/1.0 (educational app; contact: mirzo@localhost)"}
        )
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            pages = data.get("query", {}).get("pages", {})
            results = []
            for pid, p in pages.items():
                imageinfo = p.get("imageinfo", [{}])[0]
                img_url = imageinfo.get("thumburl") or imageinfo.get("url")
                if not img_url:
                    continue
                meta = imageinfo.get("extmetadata", {})
                license_short = meta.get("LicenseShortName", {}).get("value", "CC BY-SA")
                artist = meta.get("Artist", {}).get("value", "Wikimedia Contributor")
                # Strip HTML tags from artist/desc
                artist_clean = artist.replace("<b>", "").replace("</b>", "").replace("<a>", "").replace("</a>", "")
                if len(artist_clean) > 80:
                    artist_clean = artist_clean[:80] + "..."
                obj_name = meta.get("ObjectName", {}).get("value") or p.get("title", "").replace("File:", "").replace(".svg", "").replace(".jpg", "").replace(".png", "")
                
                results.append({
                    "title": p.get("title", "").replace("File:", ""),
                    "image_url": img_url,
                    "description": obj_name,
                    "license": license_short,
                    "attribution": artist_clean,
                    "source_url": imageinfo.get("descriptionurl") or f"https://commons.wikimedia.org/wiki/{urllib.parse.quote(p.get('title', ''))}"
                })
            return results
    except Exception as e:
        logger.warning(f"Could not retrieve visual materials for '{query}': {e}")
        return []
