import re
from typing import Dict, Any


def simple_stem(word: str) -> str:
    """
    Simple word stemming function to handle basic plural forms.
    """
    word = word.lower()
    if word.endswith("ies"):
        return word[:-3] + "y"
    elif word.endswith("s") and len(word) > 3:
        return word[:-1]
    return word


def is_keyword_present(text: str, keyword: str) -> bool:
    """
    Check if a keyword is present in text after stemming both.
    """
    tokens = re.findall(r"\w+", text.lower())
    stem_keyword = simple_stem(keyword)
    return any(simple_stem(token) == stem_keyword for token in tokens)


def is_keyword_in_video(video: Dict[str, Any], keyword: str) -> bool:
    """
    Check if a keyword is present in video's title or description.
    """
    title = video.get("title", "")
    description = video.get("description", "")
    return is_keyword_present(title, keyword) or is_keyword_present(
        description, keyword
    )
