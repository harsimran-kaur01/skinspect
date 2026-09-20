"""
SkinSpect recommendation engine.

Drop-in replacement: generate_recommendations(scan_result, questionnaire) -> dict.

How it works
1. Normalise the questionnaire into one profile (tolerates different field names).
2. Merge scan findings + questionnaire concerns + skin type + age into one scored
   list of "findings". A concern seen in BOTH the scan and the questionnaire scores
   higher than one seen in only one.
3. Score every product against those findings, drop anything unsafe for the user
   (pregnancy, sensitivity, allergies, vegan, ...), then pick a routine with one
   product per family, no conflicting actives and a cap on irritation load.
4. Explain every pick ("Why this for you") and build AM/PM routines.
5. Add safety/referral notes and a few lifestyle tips, rotating tips the user
   already saw on their previous scan.
"""

import json
import logging
import re
from typing import Dict, List, Optional, Set

from .product_db import PRODUCTS

logger = logging.getLogger(__name__)

SEV_RANK = {"none": 0, "mild": 1, "moderate": 2, "severe": 3}
RANK_SEV = {v: k for k, v in SEV_RANK.items()}
CONF_MIN = 0.4
STRENGTH = {"gentle": 0, "moderate": 1, "strong": 2}
BUDGET_TIER = {"budget": 0, "mid-range": 1, "premium": 2}
ACTIVE_CATEGORIES = {"serum", "treatment", "exfoliant", "spot", "mask", "eye"}
BASE_CATEGORIES = ("cleanser", "moisturizer", "sunscreen")
MIN_ACTIVE_SCORE = 0.6
PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}
KIND_ORDER = {"referral": 0, "safety": 0, "product": 1, "routine": 2, "lifestyle": 3}

LABELS = {
    "acne": "acne",
    "wrinkles": "wrinkles and fine lines",
    "oiliness": "excess oil",
    "dryness": "dryness",
    "hyperpigmentation": "dark spots and uneven tone",
    "dullness": "dullness",
    "redness": "redness",
    "sensitivity": "sensitivity",
    "blackheads": "blackheads",
    "texture": "uneven texture and pores",
    "dark_circles": "dark circles",
}

# (regex prefix, canonical condition) - first match wins
_KEYWORDS = [
    ("dark circle", "dark_circles"),
    ("under eye", "dark_circles"),
    ("uneven textur", "texture"),
    ("dark spot", "hyperpigmentation"),
    ("pigment", "hyperpigmentation"),
    ("melasma", "hyperpigmentation"),
    ("uneven", "hyperpigmentation"),
    ("scar", "hyperpigmentation"),
    ("tan", "hyperpigmentation"),
    ("acne", "acne"),
    ("pimple", "acne"),
    ("breakout", "acne"),
    ("zit", "acne"),
    ("blackhead", "blackheads"),
    ("whitehead", "blackheads"),
    ("wrinkle", "wrinkles"),
    ("fine line", "wrinkles"),
    ("aging", "wrinkles"),
    ("ageing", "wrinkles"),
    ("sagging", "wrinkles"),
    ("oil", "oiliness"),
    ("shin", "oiliness"),
    ("dry", "dryness"),
    ("flak", "dryness"),
    ("dull", "dullness"),
    ("red", "redness"),
    ("sensitiv", "sensitivity"),
    ("itch", "sensitivity"),
    ("irritat", "sensitivity"),
    ("pore", "texture"),
    ("textur", "texture"),
    ("rough", "texture"),
]

_KNOWN_KEYS = {
    "skin_type",
    "skinType",
    "age",
    "age_group",
    "ageGroup",
    "age_range",
    "concerns",
    "skin_concerns",
    "concern",
    "primary_concern",
    "secondary_concern",
    "sensitivity",
    "skin_sensitivity",
    "sensitive_skin",
    "sensitivity_level",
    "pregnant",
    "pregnancy",
    "is_pregnant",
    "pregnant_or_nursing",
    "breastfeeding",
    "budget",
    "price_preference",
    "fragrance_free",
    "fragrance_free_only",
    "vegan",
    "vegan_only",
    "allergies",
    "allergens",
    "avoid_ingredients",
    "ingredients_to_avoid",
    "routine",
    "current_routine",
    "skincare_routine",
    "lifestyle",
    "lifestyle_factors",
    "previous_scan",
    "previous_recommendations",
    "version",
}

_NO_EXACT = {"no", "n", "false", "none", "never", "0", "na", "n/a", "nil"}
_NO_PREFIX = ("no ", "not ", "non", "never", "don't", "dont")
_YES_WORDS = (
    "yes",
    "true",
    "daily",
    "often",
    "regular",
    "sometimes",
    "occasional",
    "heavy",
    "pregnan",
    "nursing",
    "breastfeeding",
    "trying",
)


# --------------------------------------------------------------------------
# Small parsing helpers
# --------------------------------------------------------------------------
def _get(q: Dict, *keys, default=None):
    for k in keys:
        v = q.get(k)
        if v not in (None, "", [], {}):
            return v
    return default


def _truthy(v) -> bool:
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return v > 0
    if isinstance(v, str):
        s = v.strip().lower()
        if not s or s in _NO_EXACT or s.startswith(_NO_PREFIX):
            return False
        return any(w in s for w in _YES_WORDS)
    return False


def _as_list(v) -> List[str]:
    if v is None:
        return []
    if isinstance(v, str):
        return [s.strip() for s in re.split(r"[,;/]", v) if s.strip()]
    if isinstance(v, dict):
        return [str(k) for k, val in v.items() if _truthy(val)]
    if isinstance(v, (list, tuple, set)):
        return [str(x).strip() for x in v if x not in (None, "")]
    return [str(v)]


def _norm_condition(name) -> Optional[str]:
    text = str(name or "").lower().replace("_", " ").strip()
    for kw, cond in _KEYWORDS:
        if re.search(r"\b" + re.escape(kw), text):
            return cond
    return None


def _norm_skin_type(v) -> Optional[str]:
    s = str(v or "").lower()
    if "comb" in s:
        return "combination"
    for t in ("oily", "dry", "sensitive", "normal"):
        if t in s:
            return t
    return None


def _norm_budget(v) -> str:
    s = str(v or "").lower()
    if any(w in s for w in ("budget", "low", "cheap", "afford", "economy")):
        return "budget"
    if any(w in s for w in ("premium", "high", "luxury", "splurge")):
        return "premium"
    return "mid-range"


def _parse_age(q: Dict) -> Optional[int]:
    age = _get(q, "age")
    try:
        if age is not None:
            return int(float(age))
    except (TypeError, ValueError):
        pass
    grp = _get(q, "age_group", "ageGroup", "age_range")
    if grp:
        nums = [int(n) for n in re.findall(r"\d+", str(grp))]
        if len(nums) >= 2:
            return (nums[0] + nums[1]) // 2
        if len(nums) == 1:
            return nums[0]
    return None


def _sensitivity_level(q: Dict, skin_type: str) -> int:
    """0 = not sensitive ... 3 = very sensitive."""
    v = _get(
        q, "sensitivity", "skin_sensitivity", "sensitive_skin", "sensitivity_level"
    )
    level = 0
    if isinstance(v, bool):
        level = 2 if v else 0
    elif isinstance(v, (int, float)):
        level = 0 if v <= 1 else 1 if v == 2 else 2 if v == 3 else 3
    elif isinstance(v, str):
        s = v.strip().lower()
        if s in _NO_EXACT or s.startswith(_NO_PREFIX):
            level = 0
        elif any(w in s for w in ("very", "highly", "extreme", "severe", "high")):
            level = 3
        elif any(w in s for w in ("moderate", "medium", "quite", "somewhat")):
            level = 2
        elif any(w in s for w in ("slight", "mild", "little", "low")):
            level = 1
        elif "sensitive" in s or s.startswith("yes"):
            level = 2
    if skin_type == "sensitive":
        level = max(level, 2)
    return level


def _lifestyle_flags(ls) -> Set[str]:
    flags: Set[str] = set()
    if not ls:
        return flags
    if isinstance(ls, str):
        text = ls.lower()
        if re.search(r"\bsmok", text) and not re.search(
            r"\b(non|no|not|don'?t)\W*smok", text
        ):
            flags.add("smoker")
        if re.search(
            r"(poor|little|less|bad|not enough) sleep|sleep\W+(is\W+|has been\W+)?(poor|bad|deprived|little)",
            text,
        ):
            flags.add("low_sleep")
        if re.search(r"high stress|stressed|stressful", text):
            flags.add("high_stress")
        if re.search(r"outdoor|sun exposure|lot of sun|in the sun", text):
            flags.add("high_sun")
        if re.search(r"(little|low|not enough) water|dehydrat", text):
            flags.add("low_water")
        return flags

    d = {str(k).lower().replace(" ", "_"): v for k, v in dict(ls).items()}

    def val(*keys):
        for k in keys:
            for dk, dv in d.items():
                if k in dk and dv not in (None, ""):
                    return dv
        return None

    def num(v):
        m = re.findall(r"\d+(?:\.\d+)?", str(v))
        return float(m[0]) if m else None

    sleep = val("sleep")
    if sleep is not None:
        n, s = num(sleep), str(sleep).lower()
        if n is not None and (n < 6 or (n == 6 and ("less" in s or "<" in s))):
            flags.add("low_sleep")
        elif n is None and any(
            w in s
            for w in ("poor", "bad", "little", "insufficient", "irregular", "less")
        ):
            flags.add("low_sleep")
    smoke = val("smok")
    if smoke is not None and _truthy(smoke):
        flags.add("smoker")
    stress = val("stress")
    if stress is not None:
        n, s = num(stress), str(stress).lower()
        if (n is not None and n >= 7) or any(
            w in s for w in ("high", "very", "a lot", "severe", "extreme")
        ):
            flags.add("high_stress")
    sun = val("sun", "outdoor")
    if sun is not None:
        n, s = num(sun), str(sun).lower()
        if (n is not None and n >= 2) or any(
            w in s
            for w in ("high", "a lot", "long", "daily", "often", "frequent", "heavy")
        ):
            flags.add("high_sun")
    water = val("water", "hydrat")
    if water is not None:
        n, s = num(water), str(water).lower()
        if (n is not None and n < 1.5) or any(
            w in s for w in ("low", "little", "less", "poor", "rarely", "not enough")
        ):
            flags.add("low_water")
    return flags


# --------------------------------------------------------------------------
# Step 1: profile
# --------------------------------------------------------------------------
def build_profile(questionnaire: Dict, scan_result: Dict) -> Dict:
    q = questionnaire or {}
    skin_type = (
        _norm_skin_type(_get(q, "skin_type", "skinType"))
        or _norm_skin_type(scan_result.get("skin_type"))
        or "combination"
    )
    sens = _sensitivity_level(q, skin_type)

    raw = _as_list(_get(q, "concerns", "skin_concerns", "concern"))
    raw += [
        str(_get(q, k)) for k in ("primary_concern", "secondary_concern") if _get(q, k)
    ]
    concerns: List[str] = []
    for r in raw:
        c = _norm_condition(r)
        if c and c not in concerns:
            concerns.append(c)

    routine = _get(q, "routine", "current_routine", "skincare_routine")
    routine_text = json.dumps(routine, default=str).lower() if routine else ""
    avoid = [
        a.lower()
        for a in _as_list(
            _get(
                q, "allergies", "allergens", "avoid_ingredients", "ingredients_to_avoid"
            )
        )
        if a.lower() not in _NO_EXACT
    ]

    ignored = sorted(set(q) - _KNOWN_KEYS)
    if ignored:
        logger.warning("Questionnaire fields not used by the engine: %s", ignored)

    return {
        "skin_type": skin_type,
        "skin_flags": {skin_type} | ({"sensitive"} if sens >= 2 else set()),
        "age": _parse_age(q),
        "concerns": concerns,
        "sens": sens,
        "max_strength": 2 if sens == 0 else 1 if sens == 1 else 0,
        "load_cap": 3 if sens == 0 else 2 if sens == 1 else 1,
        "pregnant": _truthy(
            _get(
                q,
                "pregnant",
                "pregnancy",
                "is_pregnant",
                "pregnant_or_nursing",
                "breastfeeding",
            )
        ),
        "budget": _norm_budget(_get(q, "budget", "price_preference")),
        "fragrance_free": sens >= 2
        or _truthy(_get(q, "fragrance_free", "fragrance_free_only")),
        "vegan": _truthy(_get(q, "vegan", "vegan_only")),
        "avoid": avoid,
        "using_retinoid": any(
            w in routine_text
            for w in ("retinol", "retinoid", "tretinoin", "adapalene", "retin-a")
        ),
        "flags": _lifestyle_flags(_get(q, "lifestyle", "lifestyle_factors")),
        "previous_titles": set(_as_list(q.get("previous_recommendations"))),
        "previous_scan": q.get("previous_scan") or {},
    }


# --------------------------------------------------------------------------
# Step 2: findings (scan + questionnaire + skin type + age, merged)
# --------------------------------------------------------------------------
def build_findings(scan_result: Dict, profile: Dict) -> Dict[str, Dict]:
    findings: Dict[str, Dict] = {}

    def new(cond):
        return {
            "condition": cond,
            "rank": 0,
            "confidence": 0.0,
            "area": 0.0,
            "sources": set(),
            "preventive": False,
            "score": 0.0,
        }

    for c in scan_result.get("skin_conditions", []) or []:
        cond = _norm_condition(c.get("condition"))
        if not cond:
            continue
        conf = float(c.get("confidence") or 0)
        sev = str(c.get("severity") or "none").lower()
        rank = SEV_RANK.get(sev, 0) if conf >= CONF_MIN else 0
        f = findings.setdefault(cond, new(cond))
        f["rank"] = max(f["rank"], rank)
        f["confidence"] = max(f["confidence"], conf)
        f["area"] = max(f["area"], float(c.get("affected_area_percentage") or 0))
        if rank > 0:
            f["sources"].add("scan")

    # Self-reported concerns. The scan is the authority on severity, so a concern
    # the scan did not detect enters as "mild".
    for cond in profile["concerns"]:
        f = findings.setdefault(cond, new(cond))
        f["sources"].add("self")
        f["rank"] = max(f["rank"], 1)

    # Skin type / sensitivity imply baseline needs.
    implied = {"oily": "oiliness", "dry": "dryness"}
    st = profile["skin_type"]
    if st in implied:
        f = findings.setdefault(implied[st], new(implied[st]))
        f["sources"].add("skin type")
        f["rank"] = max(f["rank"], 1)
    if profile["sens"] >= 2:
        f = findings.setdefault("sensitivity", new("sensitivity"))
        f["sources"].add("skin type")
        f["rank"] = max(f["rank"], 1)

    # Early prevention of wrinkles from age 30, even if nothing is visible yet.
    age = profile["age"]
    w = findings.get("wrinkles")
    if age and age >= 30 and (w is None or w["rank"] == 0):
        w = findings.setdefault("wrinkles", new("wrinkles"))
        w["preventive"] = True
        w["sources"].add("age")

    for f in findings.values():
        if f["rank"] == 0 and not f["preventive"]:
            f["score"] = 0.0
            continue
        if f["preventive"]:
            f["score"] = 0.45
            continue
        base = float(f["rank"])
        area_bonus = min(f["area"], 40.0) / 40.0 * 0.5
        agree = 0.5 if {"scan", "self"} <= f["sources"] else 0.0
        conf_factor = (0.7 + 0.3 * f["confidence"]) if "scan" in f["sources"] else 1.0
        f["score"] = (base + area_bonus + agree) * conf_factor
    return findings


def _sev_label(f: Dict) -> str:
    return "mild" if f["preventive"] else RANK_SEV[f["rank"]]


def _describe(f: Dict, profile: Dict) -> str:
    label = LABELS.get(f["condition"], f["condition"])
    src = f["sources"]
    if f["preventive"]:
        return f"early prevention of {label} at your age"
    if {"scan", "self"} <= src:
        return (
            f"{_sev_label(f)} {label} in your scan, which you also flagged as a concern"
        )
    if "scan" in src:
        area = (
            f" (about {int(f['area'])}% of the analysed area)"
            if f["area"] >= 10
            else ""
        )
        return f"{_sev_label(f)} {label} detected in your scan{area}"
    if "self" in src:
        return f"you told us {label} is a concern"
    return f"your {profile['skin_type']} skin"


# --------------------------------------------------------------------------
# Step 3: product scoring and selection
# --------------------------------------------------------------------------
def _eligible(p: Dict, profile: Dict) -> bool:
    if profile["pregnant"] and not p["pregnancy_safe"]:
        return False
    if STRENGTH[p["strength"]] > profile["max_strength"]:
        return False
    if profile["fragrance_free"] and not p["fragrance_free"]:
        return False
    if profile["vegan"] and not p["vegan"]:
        return False
    if profile["using_retinoid"] and p["family"] in ("retinoid", "retinoid_alt"):
        return False
    if profile["avoid"]:
        blob = " ".join(p["key_ingredients"] + [p["name"]]).lower()
        if any(a in blob for a in profile["avoid"]):
            return False
    return True


def _match(
    p: Dict, findings: Dict[str, Dict], coverage: Optional[Dict[str, float]] = None
):
    """Score a product against the findings. `coverage` discounts concerns that
    already-chosen products handle, so the routine spreads across ALL findings
    (acne AND wrinkles AND questionnaire needs) instead of stacking one."""
    coverage = coverage or {}
    total, hits = 0.0, []
    for cond, w in p["targets"].items():
        f = findings.get(cond)
        if not f or f["score"] <= 0:
            continue
        if p["severity"] and _sev_label(f) not in p["severity"]:
            continue
        total += f["score"] * w * (1.0 - min(1.0, coverage.get(cond, 0.0)))
        hits.append(f)
    return total, hits


def _fit(p: Dict, profile: Dict) -> float:
    s = 0.0
    if "all" in p["skin_types"] or profile["skin_flags"] & set(p["skin_types"]):
        s += 0.3
    else:
        s -= 0.8
    diff = BUDGET_TIER[p["price_range"]] - BUDGET_TIER[profile["budget"]]
    if diff > 0:
        s -= 0.6 * diff
    return s


def _conflicts(p: Dict, chosen: List[Dict], profile: Dict) -> bool:
    fam = p["family"]
    fams = {c["family"] for c in chosen}
    if fam in fams:
        return True
    if {fam} | fams >= {"retinoid", "retinoid_alt"}:
        return True
    if (fam == "acid" and "retinoid" in fams) or (fam == "retinoid" and "acid" in fams):
        return True
    if profile["sens"] > 0 and {fam} | fams >= {"bpo", "retinoid"}:
        return True
    return False


def _load(chosen: List[Dict]) -> int:
    return sum(STRENGTH[c["strength"]] for c in chosen)


def select_products(findings: Dict[str, Dict], profile: Dict):
    top_rank = max([f["rank"] for f in findings.values()] or [0])
    active_cap = 4 if top_rank >= 2 else 3
    chosen: List[Dict] = []
    hits_by_name: Dict[str, List[Dict]] = {}

    # Phase 1: actives, chosen greedily by *marginal* benefit
    coverage: Dict[str, float] = {}
    pool = [
        p
        for p in PRODUCTS
        if p["category"] in ACTIVE_CATEGORIES and _eligible(p, profile)
    ]
    while len(chosen) < active_cap:
        best = None
        for p in pool:
            if p in chosen or _conflicts(p, chosen, profile):
                continue
            if _load(chosen) + STRENGTH[p["strength"]] > profile["load_cap"]:
                continue
            m, hits = _match(p, findings, coverage)
            if m < MIN_ACTIVE_SCORE:
                continue
            s = m + _fit(p, profile)
            if best is None or s > best[0]:
                best = (s, p, hits)
        if not best:
            break
        _, p, hits = best
        chosen.append(p)
        hits_by_name[p["name"]] = [h for h in _match(p, findings)[1]]
        for h in hits:
            coverage[h["condition"]] = (
                coverage.get(h["condition"], 0.0) + p["targets"][h["condition"]]
            )

    # Phase 2: cleanser / moisturizer / sunscreen
    load = _load(chosen)
    chosen_tags = {t for c in chosen for t in c["tags"]}
    for cat in BASE_CATEGORIES:
        best = None
        for p in PRODUCTS:
            if p["category"] != cat or not _eligible(p, profile):
                continue
            if (
                load + STRENGTH[p["strength"]] > profile["load_cap"]
                and p["strength"] != "gentle"
            ):
                continue
            if "bha" in p["tags"] and "bha" in chosen_tags:
                continue
            m, hits = _match(p, findings)
            s = m + _fit(p, profile)
            if cat == "moisturizer" and load >= 2 and "barrier" in p["tags"]:
                s += 1.0
            if best is None or s > best[0]:
                best = (s, p, hits)
        if best:
            chosen.append(best[1])
            hits_by_name[best[1]["name"]] = best[2]
            load += STRENGTH[best[1]["strength"]]
    return chosen, hits_by_name


# --------------------------------------------------------------------------
# Step 4: turn picks into recommendations
# --------------------------------------------------------------------------
def _priority(p: Dict, hits: List[Dict], chosen: List[Dict]) -> str:
    if p["category"] == "sunscreen":
        photosens = any(
            c["family"] in ("retinoid", "acid", "vitc", "bpo") for c in chosen
        )
        wants = any(
            h["condition"] in ("wrinkles", "hyperpigmentation", "acne") for h in hits
        )
        return "high" if photosens or wants else "medium"
    if not hits:
        return "low"
    return "high" if max(h["rank"] for h in hits) >= 2 else "medium"


def _product_rec(p, hits, chosen, profile) -> Dict:
    top = sorted(hits, key=lambda f: -f["score"])[:2]
    reason = "; ".join(_describe(f, profile) for f in top)
    if not reason:
        if p["category"] == "moisturizer" and _load(chosen) >= 2:
            reason = "it supports your skin barrier while you use active treatments"
        else:
            reason = f"a well-matched daily basic for {profile['skin_type']} skin"
    extras = []
    if profile["pregnant"]:
        extras.append("chosen as a pregnancy-safe option")
    if profile["sens"] >= 2 and p["strength"] == "gentle":
        extras.append("kept gentle because your skin is sensitive")
    reason = reason + ("; " + "; ".join(extras) if extras else "")
    return {
        "type": "product",
        "category": p["category"],
        "title": p["name"],
        "description": f"{p['description']} Why this for you: {reason}. How to use: {p['usage']}",
        "priority": _priority(p, hits, chosen),
        "product_details": {
            "brand": "SkinSpect",
            "price_range": p["price_range"],
            "key_ingredients": p["key_ingredients"],
            "link": p["link"],
        },
    }


_AM_ORDER = [
    "cleanser",
    "bpo",
    "vitc",
    "niacinamide",
    "azelaic",
    "soothing",
    "peptide",
    "hydrator",
    "eye",
    "moisturizer",
    "sunscreen",
]
_PM_ORDER = [
    "cleanser",
    "acid",
    "retinoid",
    "retinoid_alt",
    "bpo",
    "azelaic",
    "niacinamide",
    "soothing",
    "peptide",
    "hydrator",
    "eye",
    "moisturizer",
]


def _steps(chosen: List[Dict], when: str, order: List[str]) -> List[str]:
    items = [p for p in chosen if p["time"] in (when, "both")]
    items.sort(key=lambda p: order.index(p["family"]) if p["family"] in order else 99)
    return [p["name"] for p in items]


def _routine_recs(chosen: List[Dict], profile: Dict) -> List[Dict]:
    recs = []
    am = _steps(chosen, "am", _AM_ORDER)
    pm = _steps(chosen, "pm", _PM_ORDER)
    if am:
        recs.append(
            {
                "type": "routine",
                "category": "am_routine",
                "priority": "high",
                "title": "Your morning routine",
                "description": "In this order: "
                + " -> ".join(f"{i}. {n}" for i, n in enumerate(am, 1))
                + ". Sunscreen is the last step and the one you should never skip.",
            }
        )
    if pm:
        note = []
        fams = {c["family"] for c in chosen}
        if fams & {"retinoid", "acid"}:
            note.append(
                "Introduce the retinoid/exfoliant slowly (see its usage notes) and never on the same night as each other."
            )
        note.append(
            "Add only one new active at a time, about 2 weeks apart, and patch-test behind the ear first."
        )
        extras = [p["name"] for p in chosen if p["time"] in ("weekly", "as_needed")]
        if extras:
            note.append("Extras as needed: " + ", ".join(extras) + ".")
        recs.append(
            {
                "type": "routine",
                "category": "pm_routine",
                "priority": "high",
                "title": "Your evening routine",
                "description": "In this order: "
                + " -> ".join(f"{i}. {n}" for i, n in enumerate(pm, 1))
                + ". "
                + " ".join(note),
            }
        )
    return recs


def _safety_recs(findings: Dict[str, Dict], profile: Dict, chosen: List[Dict]):
    recs, notes = [], []
    if profile["pregnant"]:
        msg = (
            "Retinoids, leave-on salicylic acid and bakuchiol are left out because you're pregnant or nursing. "
            "Please confirm every active with your doctor."
        )
        notes.append(msg)
        recs.append(
            {
                "type": "routine",
                "category": "safety",
                "priority": "high",
                "title": "Pregnancy-safe selection",
                "description": msg,
            }
        )
    severe = [f for f in findings.values() if f["rank"] >= 3]
    acne = findings.get("acne")
    if severe or (acne and acne["rank"] >= 2 and profile["sens"] >= 2):
        cond = LABELS.get((severe[0] if severe else acne)["condition"], "skin concern")
        msg = (
            f"Your {cond} looks significant enough that over-the-counter products may not be enough. "
            "A dermatologist can prescribe stronger treatment - try the Dermatologist Locator in the app."
        )
        notes.append(msg)
        recs.append(
            {
                "type": "routine",
                "category": "referral",
                "priority": "high",
                "title": "Consider seeing a dermatologist",
                "description": msg,
            }
        )
    if profile["using_retinoid"] and (findings.get("wrinkles") or findings.get("acne")):
        notes.append(
            "You already use a retinoid, so we did not add another. Keep going with it."
        )
    return recs, notes


_TIPS = [
    {
        "title": "Don't pick or squeeze breakouts",
        "conds": {"acne", "blackheads"},
        "flags": set(),
        "need_flag": False,
        "desc": "Picking pushes bacteria deeper and leaves dark marks that outlast the pimple by months. Use a hydrocolloid patch or a dab of your spot treatment instead.",
    },
    {
        "title": "Cleanse after sweating and wash pillowcases weekly",
        "conds": {"acne", "oiliness", "blackheads"},
        "flags": set(),
        "need_flag": False,
        "desc": "Rinse sweat off soon after workouts, wash pillowcases at least weekly and wipe your phone screen - all easy ways to reduce clogged pores.",
    },
    {
        "title": "Reapply sunscreen every 2-3 hours outdoors",
        "conds": {"hyperpigmentation", "wrinkles"},
        "flags": {"high_sun"},
        "need_flag": False,
        "desc": "UV is the biggest driver of dark spots and premature lines. Shade and a hat between late morning and mid-afternoon help more than any serum.",
    },
    {
        "title": "Protect your sleep",
        "conds": {"wrinkles", "dullness", "acne", "dark_circles"},
        "flags": {"low_sleep"},
        "need_flag": True,
        "desc": "Aim for 7-8 hours. Short sleep is linked to duller skin, darker circles and slower repair overnight.",
    },
    {
        "title": "Smoking speeds up skin ageing",
        "conds": {"wrinkles", "dullness"},
        "flags": {"smoker"},
        "need_flag": True,
        "desc": "Smoking reduces blood flow and breaks down collagen. Cutting down is one of the most effective anti-ageing steps you can take.",
    },
    {
        "title": "Drink water steadily through the day",
        "conds": {"dryness", "dullness"},
        "flags": {"low_water"},
        "need_flag": True,
        "desc": "Water won't replace moisturizer, but consistently low intake can leave skin looking duller and feeling tighter.",
    },
    {
        "title": "Give stress a release valve",
        "conds": {"acne", "redness", "oiliness"},
        "flags": {"high_stress"},
        "need_flag": True,
        "desc": "Stress hormones can raise oil production and flare breakouts. Short walks, breathing exercises or time offline all help.",
    },
    {
        "title": "Be gentle with your skin barrier",
        "conds": {"sensitivity", "redness", "dryness"},
        "flags": set(),
        "need_flag": False,
        "desc": "Use lukewarm water, pat dry, skip scrubs and very hot showers, and avoid layering new actives.",
    },
    {
        "title": "Give the routine 8-12 weeks",
        "conds": {"acne", "wrinkles", "hyperpigmentation", "texture"},
        "flags": set(),
        "need_flag": False,
        "desc": "Actives take 6-12 weeks to show results. Rescan every 2-4 weeks in the same lighting rather than judging day to day.",
    },
]


def _lifestyle_recs(findings: Dict[str, Dict], profile: Dict) -> List[Dict]:
    scored = []
    for t in _TIPS:
        flag_hits = len(t["flags"] & profile["flags"])
        if t["need_flag"] and not flag_hits:
            continue
        rel = (
            sum(findings[c]["score"] for c in t["conds"] if c in findings)
            + 1.5 * flag_hits
        )
        if rel <= 0:
            continue
        if t["title"] in profile["previous_titles"]:
            rel -= 1.0  # rotate tips the user already saw last time
        scored.append((rel, t))
    scored.sort(key=lambda x: -x[0])
    return [
        {
            "type": "lifestyle",
            "category": "lifestyle",
            "priority": "medium" if rel > 1.5 else "low",
            "title": t["title"],
            "description": t["desc"],
        }
        for rel, t in scored[:3]
    ]


# --------------------------------------------------------------------------
# Progress tracking
# --------------------------------------------------------------------------
def _progress(scan_result: Dict, profile: Dict) -> Optional[Dict]:
    prev = profile["previous_scan"]
    if not prev or prev.get("overall_health_score") is None:
        return None
    prev_score = prev["overall_health_score"]
    current = scan_result.get("overall_health_score") or 0
    diff = current - prev_score
    trend = "improved" if diff > 5 else "declined" if diff < -5 else "stable"
    msg = f"Your skin health has {trend} by {abs(diff)} points since your last scan."

    prev_sev = {}
    for c in prev.get("conditions", []) or []:
        cond = _norm_condition(c.get("condition"))
        if cond:
            prev_sev[cond] = SEV_RANK.get(str(c.get("severity") or "none").lower(), 0)
    changes = []
    for c in scan_result.get("skin_conditions", []) or []:
        cond = _norm_condition(c.get("condition"))
        now = SEV_RANK.get(str(c.get("severity") or "none").lower(), 0)
        if cond in prev_sev and prev_sev[cond] != now:
            direction = "improved" if now < prev_sev[cond] else "worsened"
            changes.append(
                f"{LABELS.get(cond, cond)} {direction} ({RANK_SEV[prev_sev[cond]]} -> {RANK_SEV[now]})"
            )
    if changes:
        msg += " " + "; ".join(changes).capitalize() + "."
    return {
        "score_change": diff,
        "trend": trend,
        "previous_score": prev_score,
        "current_score": current,
        "message": msg,
    }


# --------------------------------------------------------------------------
# Public API
# --------------------------------------------------------------------------
def generate_recommendations(scan_result: Dict, questionnaire: Dict) -> Dict:
    scan_result = scan_result or {}
    profile = build_profile(questionnaire or {}, scan_result)
    findings = build_findings(scan_result, profile)
    chosen, hits_by_name = select_products(findings, profile)

    product_recs = [
        _product_rec(p, hits_by_name[p["name"]], chosen, profile) for p in chosen
    ]
    # Show treatments first, then basics
    product_recs.sort(
        key=lambda r: (r["category"] in BASE_CATEGORIES, PRIORITY_ORDER[r["priority"]])
    )

    routine_recs = _routine_recs(chosen, profile)
    safety_recs, safety_notes = _safety_recs(findings, profile, chosen)
    lifestyle_recs = _lifestyle_recs(findings, profile)

    seen, unique = set(), []
    for r in safety_recs + product_recs + routine_recs + lifestyle_recs:
        if r["title"] not in seen:
            seen.add(r["title"])
            unique.append(r)
    unique.sort(
        key=lambda r: KIND_ORDER.get(
            r["category"] if r["category"] in ("referral", "safety") else r["type"], 3
        )
    )

    focus = sorted(
        (
            {
                "condition": f["condition"],
                "severity": _sev_label(f),
                "score": round(f["score"], 2),
                "sources": sorted(f["sources"]),
            }
            for f in findings.values()
            if f["score"] > 0
        ),
        key=lambda x: -x["score"],
    )
    return {
        "recommendations": unique,
        "safety_notes": safety_notes,
        "progress_summary": _progress(scan_result, profile),
        "overall_health_score": scan_result.get("overall_health_score"),
        "skin_type": profile["skin_type"],
        "focus_areas": focus,
    }
