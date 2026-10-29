"""Conservative normalization and explicit material classification."""
import re
import unicodedata

SUFFIXES = {"ltd", "limited", "inc", "incorporated", "llc", "corp", "corporation", "plc"}


def normalize_company(value: str) -> str:
    text = unicodedata.normalize("NFKC", value).casefold().replace("&", " and ")
    words = re.findall(r"[^\W_]+", text, flags=re.UNICODE)
    while words and words[-1] in SUFFIXES:
        words.pop()
    return " ".join(words)


def classify_materials(value: str) -> set[str]:
    text = value.casefold()
    categories = set()
    if re.search(r"\b(aluminum|aluminium)\s+scrap\b", text):
        categories.add("aluminum_scrap")
    if re.search(r"\bcopper\s+scrap\b", text):
        categories.add("copper_scrap")
    if re.search(r"\bingots?\b", text):
        categories.add("metal_ingot")
    return categories or {"unclassified"}
