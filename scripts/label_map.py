"""Map Guess vendor fields onto Item Tree Apparel + FCO color palette."""

from __future__ import annotations

import re
from dataclasses import dataclass

GH1_TO_CATEGORY = {
    "T-SHIRTS": "T-shirt",
    "OUTERWEAR": "Outerwear",
    "BLAZER": "Outerwear",
    "PANTS": "Bottoms",
    "DENIM PANTS": "Bottoms",
    "SHORTS": "Bottoms",
    "SKIRTS": "Bottoms",
    "DRESSES": "Dresses",
    "SWEATERS": "Tops",
    "KNIT TOPS": "Tops",
    "WOVEN TOPS": "Tops",
    "SWEATSHIRT": "Tops",
    "SET": "Suits & Sets",
    "ONE PIECE": "Dresses",
    "SNEAKER": "Sneakers",
    "DRESS SHOES": "Court shoes",
    "CASUAL SHOES": "Shoes",
    "BAGS": "Bags",
    "MINI-BAGS": "Bags",
    "EVENINGS-BAGS": "Bags",
    "TRAVEL BAGS": "Bags",
    "WALLETS": "Small Leather Goods",
    "BELTS": "Belts",
    "TEXTILE": "Soft Accessories",
    "ACCESSORIES": "Soft Accessories",
    "MISCELLANEOUS": "Other Accessories",
    "GIFT BOX-SET": "Other Accessories",
}

# Used only when Part Desc / GH2 has no keyword hit.
GH1_TO_SUBCATEGORY = {
    "BLAZER": "Blazer",
    "SKIRTS": "Skirt",
    "SHORTS": "Shorts",
    "DENIM PANTS": "Jeans",
    "T-SHIRTS": "T-shirt",
    "SWEATSHIRT": "Sweatshirt",
    "SWEATERS": "Knit sweater",
    "DRESSES": "Dresses",
    "PANTS": "Trousers",
    "KNIT TOPS": "Top",
    "WOVEN TOPS": "Shirt",
    "SET": "Sets",
    "ONE PIECE": "Jumpsuit",
    "SNEAKER": "Sneakers",
    "DRESS SHOES": "Court shoes",
    "CASUAL SHOES": "Casual Shoes",
    "BAGS": "Handbag",
    "MINI-BAGS": "Handbag",
    "EVENINGS-BAGS": "Handbag",
    "TRAVEL BAGS": "Handbag",
    "WALLETS": "Wallets",
    "BELTS": "Belts",
    "TEXTILE": "Soft Accessories",
    "ACCESSORIES": "Other Accessories",
    "MISCELLANEOUS": "Other Accessories",
    "GIFT BOX-SET": "Other Accessories",
}

LEVI_SUBCATEGORY = {
    "JEANS": ("Bottoms", "Jeans"),
    "TEES": ("T-shirt", "T-shirt"),
    "BEYOND DENIM": ("Bottoms", "Trousers"),
    "WOVEN TOPS": ("Tops", "Shirt"),
    "SWEATSHIRTS": ("Tops", "Sweatshirt"),
    "OUTERWEAR": ("Outerwear", "Jacket"),
    "TRUCKERS": ("Outerwear", "Jacket"),
    "SWEATERS": ("Tops", "Knit sweater"),
    "SKIRTS": ("Bottoms", "Skirt"),
    "POLOS": ("T-shirt", "Polo shirt"),
    "DRESSES": ("Dresses", "Dresses"),
    "SHORTS": ("Bottoms", "Shorts"),
}

BOSS_SPG = {
    "T-SHIRT": ("T-shirt", "T-shirt"),
    "POLO": ("T-shirt", "Polo shirt"),
    "JACKETS": ("Outerwear", "Jacket"),
    "DENIM JACKETS": ("Outerwear", "Jacket"),
    "LEATHER JACKETS": ("Outerwear", "Leather Jacket"),
    "LEATHER": ("Outerwear", "Leather Jacket"),
    "COATS": ("Outerwear", "Coat"),
    "OUTERWEAR": ("Outerwear", "Jacket"),
    "KNITWEAR": ("Tops", "Knit sweater"),
    "KNITWEAR PULLOVERS/SWEATERS": ("Tops", "Knit sweater"),
    "BLOUSES": ("Tops", "Blouse"),
    "SWEATSHIRT": ("Tops", "Sweatshirt"),
    "JEANS": ("Bottoms", "Jeans"),
    "TROUSERS": ("Bottoms", "Trousers"),
    "JERSEY TROUSERS": ("Bottoms", "Sweatpants"),
    "SKIRTS": ("Bottoms", "Skirt"),
    "DRESSES": ("Dresses", "Dresses"),
    "JERSEY DRESSES": ("Dresses", "Dresses"),
    "NIGHTWEAR": ("Sleepwear", "Pajama Set"),
    "HATS": ("Soft Accessories", "Hats"),
    "BELTS": ("Belts", "Belts"),
    "INFORMAL BELTS": ("Belts", "Belts"),
    "SHIRTS": ("Tops", "Shirt"),
    "DENIM SHIRTS": ("Tops", "Shirt"),
    "SHORTS": ("Bottoms", "Shorts"),
    "TOPS": ("Tops", "Top"),
    "JERSEY TOPS": ("Tops", "Top"),
    "JERSEY": ("T-shirt", "T-shirt"),
}

LEVI_COLOR_FAMILY = {
    "BLACKS": "Black",
    "WHITES": "White",
    "GREYS": "Grey",
    "BLUES": "Blue",
    "GREENS": "Green",
    "REDS": "Red",
    "PINKS": "Pink",
    "YELLOWS": "Yellow",
    "PURPLES": "Purple",
    "BROWNS": "Brown",
    "TANS": "Brown",
    "NEUTRALS": "Neutral",
    "MULTI-COLOR": "Multicolor",
    "MED INDIGO - WORN IN": "Blue",
    "DARK INDIGO - WORN IN": "Blue",
    "LIGHT INDIGO - WORN IN": "Blue",
    "DARK INDIGO - FLAT FINISH": "Blue",
    "MED INDIGO - FLAT FINISH": "Blue",
    "LIGHT INDIGO - FLAT FINISH": "Blue",
}

# More specific patterns first.
PART_DESC_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bsneaker"), "Sneakers"),
    (re.compile(r"\b(bootie|boots?)\b"), "Boots"),
    (re.compile(r"\b(pump|sling)\b"), "Court shoes"),
    (re.compile(r"\bsandal"), "Sandals"),
    (re.compile(r"\b(loafer|moccasin|mocassin)\b"), "Loafers"),
    (re.compile(r"\b(sabot|clog|slides?|flip-?flop)\b"), "Clogs"),
    (re.compile(r"\bslipper"), "Home slippers"),
    (re.compile(r"\bbackpack"), "Backpack"),
    (re.compile(r"\b(suitcase|trolley|roller|luggage)\b"), "Suitcase"),
    (re.compile(r"\b(clutch|satchel|tote|hobo|crossbody|shoulder|handbag|mini-?bag)\b"), "Handbag"),
    (re.compile(r"\b(wallet|bifold|card case|zip around)\b"), "Wallets"),
    (re.compile(r"\bbelts?\b"), "Belts"),
    (re.compile(r"\b(beanie|hat)\b"), "Hats"),
    (re.compile(r"\bcaps?\b"), "Caps"),
    (re.compile(r"\b(scarf|bandana)\b"), "Scarf/Bandana"),
    (re.compile(r"\bglove"), "Gloves"),
    (re.compile(r"\bbleather\b.*\b(jacket|jacke|jkt|aviator|biker)\b"), "Leather Jacket"),
    (re.compile(r"\bfur\s+coat\b"), "Fur Coat"),
    (re.compile(r"\bpeacoat\b"), "Coat"),
    (re.compile(r"\bfur\b"), "Fur Coat"),
    (re.compile(r"\btrench\b"), "Trench coat"),
    (re.compile(r"\bparka\b"), "Parka"),
    (re.compile(r"\bponcho\b"), "Poncho"),
    (re.compile(r"\bcape\b"), "Cape"),
    (re.compile(r"\bblazer\b"), "Blazer"),
    (re.compile(r"\b(caban|coat)\b"), "Coat"),
    (re.compile(r"\b(jkt|bomber|biker|aviator|trucker|shacket|overshirts?|overshi|overs|jackets?|jacke|jack|jac|puffer|down|sherpa|shearling|padded)\b"), "Jacket"),
    (re.compile(r"\bvest\b"), "Vest"),
    (re.compile(r"\b(hoodie|hooded|hodeed|hoode)\b"), "Hoodie"),
    (re.compile(r"\bsweatshirt\b"), "Sweatshirt"),
    (re.compile(r"\b(cardigan|cardi)\b"), "Cardigan"),
    (re.compile(r"\b(turtle|roll-?neck|mock\s*nk|dolcevit)\b"), "Roll-neck"),
    (re.compile(r"\bpolo\b"), "Polo shirt"),
    (re.compile(r"\bblouse\b"), "Blouse"),
    (re.compile(r"\btunic\b"), "Tunic"),
    (re.compile(r"\b(body|bodysuit)\b"), "Body"),
    (re.compile(r"\b(jumpsuit|overall)\b"), "Jumpsuit"),
    (re.compile(r"\bmaxi\b.*\bdress\b|\bdress\b.*\bmaxi\b"), "Maxi dress"),
    (re.compile(r"\bmidi\b.*\bdress\b|\bdress\b.*\bmidi\b"), "Midi dress"),
    (re.compile(r"\bmini\b.*\bdress\b|\bdress\b.*\bmini\b"), "Mini dress"),
    (re.compile(r"\bdress\b"), "Dresses"),
    (re.compile(r"\blegging\b"), "Leggings"),
    (re.compile(r"\bbermuda\b"), "Bermudas"),
    (re.compile(r"\b(shorts?|short)\b"), "Shorts"),
    (re.compile(r"\bskirt\b"), "Skirt"),
    (re.compile(r"\b(sweatpant|jogger)\b"), "Sweatpants"),
    (re.compile(r"\bjeans?\b"), "Jeans"),
    (re.compile(r"\b(chino|trouser|pants?|pant)\b"), "Trousers"),
    (re.compile(r"\b(tee|t-shirt|tshirt)\b"), "T-shirt"),
    (re.compile(r"\b(sweater|swtr)\b"), "Knit sweater"),
    (re.compile(r"\bcamisol"), "Top"),
    (re.compile(r"\bcorset\b"), "Top"),
    (re.compile(r"\bbustier\b"), "Top"),
    (re.compile(r"\bhenley\b"), "Top"),
    (re.compile(r"\bshir"), "Shirt"),
    (re.compile(r"\btop\b"), "Top"),
    (re.compile(r"\bbikini\b"), "Bikini"),
    (re.compile(r"\b(pajama|pyjama)\b"), "Pajama Set"),
    (re.compile(r"\brobe\b"), "Robe"),
    (re.compile(r"\b(brief|briefs)\b"), "Briefs"),
    (re.compile(r"\bboxer"), "Boxers"),
    (re.compile(r"\bpanties\b"), "Panties"),
    (re.compile(r"\bsocks?\b"), "Socks"),
    (re.compile(r"\btights\b"), "Tights"),
]

COLOR_CODE_FAMILY = {
    "BLA": "Black",
    "BLK": "Black",
    "JBLK": "Black",
    "BLACK": "Black",
    "WHI": "White",
    "WHT": "White",
    "WHITE": "White",
    "GRY": "Grey",
    "GREY": "Grey",
    "GRAY": "Grey",
    "TAN": "Brown",
    "BRO": "Brown",
    "BROWN": "Brown",
    "BEI": "Neutral",
    "BEIGE": "Neutral",
    "NUDE": "Neutral",
    "RED": "Red",
    "NAVY": "Blue",
    "BLU": "Blue",
    "BLUE": "Blue",
    "GRN": "Green",
    "GREEN": "Green",
    "PNK": "Pink",
    "PINK": "Pink",
    "PUR": "Purple",
    "YEL": "Yellow",
    "ORG": "Orange",
    "ORANGE": "Orange",
}

# Family keywords, longer / more specific first within the list.
FAMILY_KEYWORDS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\b(multi|multicolor|printed|print|allover|aop|leopard|paisley|jacquard|check|stripe)\b"), "Multicolor"),
    (re.compile(r"\b(navy|denim|blue|turquoise|teal|petrol|ocean|sky|rinse|rinsed|timeless)\b"), "Blue"),
    (re.compile(r"\b(green|olive|mint|sage|khaki|army|forest|emerald|grape|jade|beryl|planter|mossy|chenille green)\b"), "Green"),
    (re.compile(r"\b(burgundy|wine|cherry|maroon|red|rust|brick|peony)\b"), "Red"),
    (re.compile(r"\b(pink|blush|rose|fuchsia|salmon|magenta)\b"), "Pink"),
    (re.compile(r"\b(purple|lilac|lavender|violet|plum|aubergine|mauve)\b"), "Purple"),
    (re.compile(r"\b(yellow|mustard|lemon|gold|prosecco)\b"), "Yellow"),
    (re.compile(r"\b(orange|peach|apricot|terracotta|coral)\b"), "Orange"),
    (re.compile(r"\b(brown|tan|camel|mocha|chocolate|choco|cognac|chestnut|rum|coffee|espresso|cocoa|moccasin)\b"), "Brown"),
    (re.compile(r"\b(beige|nude|taupe|stone|sand|ecru|latte|creme|brulee|earthenware|quicksand)\b"), "Neutral"),
    (re.compile(r"\b(grey|gray|silver|charcoal|graphite|smoke|ash|melange|heather|cloud|asphalt)\b"), "Grey"),
    (re.compile(r"\b(white|ivory|cream|chalk|pearl|snow|milk)\b"), "White"),
    (re.compile(r"\b(black|jet|noir|coal|licorice)\b"), "Black"),
]


@dataclass
class CategoryMatch:
    category: str | None
    subcategory: str | None
    source: str
    confidence: str


@dataclass
class ColorMatch:
    color_name: str | None
    color_family: str | None
    source: str


def _norm_text(value) -> str:
    if value is None:
        return ""
    text = str(value).replace("_", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _norm_key(value) -> str:
    return _norm_text(value).upper()


def map_category(
    gh1,
    part_desc,
    subcategory_to_category: dict[str, str],
    gh0=None,
    gh2=None,
) -> CategoryMatch:
    gh1_key = _norm_key(gh1)
    gh2_key = _norm_key(gh2)

    search_parts = " ".join(
        [_norm_text(part_desc), _norm_text(gh2), _norm_text(gh1)]
    ).lower()
    keyword_sub = None
    for pattern, subcategory in PART_DESC_RULES:
        if pattern.search(search_parts):
            keyword_sub = subcategory
            break

    gh1_category = GH1_TO_CATEGORY.get(gh1_key)
    gh1_sub = GH1_TO_SUBCATEGORY.get(gh1_key)

    if keyword_sub:
        category = subcategory_to_category.get(keyword_sub, gh1_category)
        return CategoryMatch(category, keyword_sub, "part_desc_keyword", "high")

    if gh2_key:
        gh2_text = _norm_text(gh2).lower()
        for pattern, subcategory in PART_DESC_RULES:
            if pattern.search(gh2_text):
                category = subcategory_to_category.get(subcategory, gh1_category)
                return CategoryMatch(category, subcategory, "gh2_keyword", "high")

    if gh1_sub:
        category = subcategory_to_category.get(gh1_sub, gh1_category)
        return CategoryMatch(category, gh1_sub, "gh1_fallback", "medium")

    if gh1_category:
        return CategoryMatch(gh1_category, None, "gh1_category_only", "none")

    return CategoryMatch(None, None, "unmapped_gh1", "none")


def _strip_color_codes(text: str) -> str:
    cleaned = re.sub(r"\b[a-z]?\d{2,4}\b", " ", text)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" -_/")
    return cleaned


def map_color(color_code, color_desc, palette: dict) -> ColorMatch:
    name_to_family: dict[str, str] = palette.get("name_to_family", {})
    names_by_length = sorted(name_to_family.keys(), key=len, reverse=True)

    desc = _norm_text(color_desc).lower()
    coded = re.match(r"^(\d{3})-(.+)$", _norm_text(color_desc))
    if coded:
        desc = coded.group(2).lower()
    desc_stripped = _strip_color_codes(desc)
    code = _norm_key(color_code)

    levi_family = LEVI_COLOR_FAMILY.get(_norm_key(color_desc))
    if levi_family:
        return ColorMatch(None, levi_family, "levis_color_family")

    for name in names_by_length:
        needle = name.lower()
        if needle and (needle == desc_stripped or needle in desc_stripped or needle in desc):
            return ColorMatch(name, name_to_family[name], "exact_color_name")

    search_text = f"{desc_stripped} {code.lower()}".strip()
    for pattern, family in FAMILY_KEYWORDS:
        if pattern.search(search_text):
            return ColorMatch(None, family, "family_keyword")

    if code in COLOR_CODE_FAMILY:
        return ColorMatch(None, COLOR_CODE_FAMILY[code], "color_code")

    return ColorMatch(None, None, "unmapped")


def map_levis(category, subcategory, subcategory_to_category: dict[str, str]) -> CategoryMatch:
    sub_key = _norm_key(subcategory)
    if sub_key in LEVI_SUBCATEGORY:
        cat, sub = LEVI_SUBCATEGORY[sub_key]
        cat = subcategory_to_category.get(sub, cat)
        return CategoryMatch(cat, sub, "levis_subcategory", "high")

    cat_key = _norm_key(category).replace("MENS-", "").replace("WOMENS-", "")
    if cat_key == "TOPS":
        return CategoryMatch("Tops", "Top", "levis_category_fallback", "medium")
    if cat_key == "BOTTOMS":
        return CategoryMatch("Bottoms", "Trousers", "levis_category_fallback", "medium")
    return CategoryMatch(None, None, "unmapped_levis", "none")


def map_boss(mpg, spg, subcategory_to_category: dict[str, str]) -> CategoryMatch:
    spg_key = _norm_key(spg)
    if spg_key in BOSS_SPG:
        cat, sub = BOSS_SPG[spg_key]
        cat = subcategory_to_category.get(sub, cat)
        return CategoryMatch(cat, sub, "boss_spg", "high")

    mpg_key = _norm_key(mpg)
    if mpg_key in BOSS_SPG:
        cat, sub = BOSS_SPG[mpg_key]
        cat = subcategory_to_category.get(sub, cat)
        return CategoryMatch(cat, sub, "boss_mpg", "medium")

    text = f"{_norm_text(spg)} {_norm_text(mpg)}"
    return map_category(mpg, text, subcategory_to_category)

