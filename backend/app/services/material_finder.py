import urllib.request
import urllib.parse
import json
import logging
from typing import Optional, Tuple, Dict, Any

logger = logging.getLogger("second_brain.material_finder")

def find_learning_materials(topic: str) -> Dict[str, Any]:
    """
    Searches for authoritative educational and encyclopedic materials for any topic
    using Wikipedia API (free, open, no API key required).
    Returns title, extract, url, and source info.
    """
    clean_topic = topic.strip()
    # Remove common filler phrases from prompt like 'хочу выучить', 'курс по', 'научи меня', 'с нуля'
    cleaned_query = clean_topic
    for prefix in [
        "хочу изучить ", "хочу выучить ", "создай курс по ", "создай курс ",
        "курс по ", "научи меня ", "изучение ", "основы ", "как научиться ",
        "хочу освоить ", "подготовь меня к "
    ]:
        if cleaned_query.lower().startswith(prefix):
            cleaned_query = cleaned_query[len(prefix):].strip()
    
    for suffix in [" с нуля", " для начинающих", " за год", " за 6 месяцев", " за месяц", " для чайников"]:
        if cleaned_query.lower().endswith(suffix):
            cleaned_query = cleaned_query[:-len(suffix)].strip()

    # Normalize grammatical case for common language learning prompts
    lower_cq = cleaned_query.lower()
    if "японск" in lower_cq and "язык" in lower_cq:
        cleaned_query = "Японский язык"
    elif "английск" in lower_cq and "язык" in lower_cq:
        cleaned_query = "Английский язык"
    elif "немецк" in lower_cq and "язык" in lower_cq:
        cleaned_query = "Немецкий язык"
    elif "китайск" in lower_cq and "язык" in lower_cq:
        cleaned_query = "Китайский язык"
    
    if not cleaned_query:
        cleaned_query = clean_topic

    try:
        # 1. Search Wikipedia
        search_url = f"https://ru.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(cleaned_query)}&format=json&utf8=1&srlimit=3"
        req = urllib.request.Request(
            search_url,
            headers={"User-Agent": "SecondBrainAI/1.0 (educational app; contact: mirzo@localhost)"}
        )
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            results = data.get("query", {}).get("search", [])
            if not results:
                # Try original topic
                search_url2 = f"https://ru.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(clean_topic)}&format=json&utf8=1&srlimit=1"
                req2 = urllib.request.Request(search_url2, headers={"User-Agent": "SecondBrainAI/1.0"})
                with urllib.request.urlopen(req2, timeout=6) as resp2:
                    data = json.loads(resp2.read().decode("utf-8"))
                    results = data.get("query", {}).get("search", [])
            
            if not results:
                return {
                    "title": clean_topic,
                    "extract": f"Образовательный курс и материалы по теме: {clean_topic}.",
                    "source_url": "",
                    "snippets": []
                }

            best_match = results[0]
            page_title = best_match["title"]
            snippets = [r.get("snippet", "").replace("<span class=\"searchmatch\">", "").replace("</span>", "") for r in results]

        # 2. Get full introductory extract and sections
        extract_url = f"https://ru.wikipedia.org/w/api.php?action=query&prop=extracts&explaintext=1&exintro=0&titles={urllib.parse.quote(page_title)}&format=json&utf8=1"
        req3 = urllib.request.Request(
            extract_url,
            headers={"User-Agent": "SecondBrainAI/1.0 (educational app; contact: mirzo@localhost)"}
        )
        with urllib.request.urlopen(req3, timeout=8) as resp3:
            data3 = json.loads(resp3.read().decode("utf-8"))
            pages = data3.get("query", {}).get("pages", {})
            first_page = list(pages.values())[0] if pages else {}
            extract = first_page.get("extract", "")
            # If extract is very long, take first 4000 characters for high relevance
            if len(extract) > 5000:
                extract = extract[:5000] + "\n\n... (материал продолжается в полной энциклопедии)"

        return {
            "title": page_title,
            "extract": extract or "\n".join(snippets),
            "source_url": f"https://ru.wikipedia.org/wiki/{urllib.parse.quote(page_title)}",
            "snippets": snippets
        }
    except Exception as e:
        logger.warning(f"Could not retrieve web material for '{topic}': {e}")
        return {
            "title": clean_topic,
            "extract": f"Тематические учебные материалы по курсу «{clean_topic}». Изучите ключевые принципы, практические примеры и сценарии применения.",
            "source_url": "",
            "snippets": []
        }
