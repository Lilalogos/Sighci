#!/usr/bin/env python3
"""Build src/data/people.json from the SIGCHI spreadsheet + Google Scholar profiles."""

from __future__ import annotations

import html as html_lib
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.manifold import TSNE

sys.path.insert(0, str(Path(__file__).resolve().parent))
from names_ru import name_ru
from titles_ru import save_paper_cache, translate_titles

ROOT = Path(__file__).resolve().parents[1]
XLSX = Path("/Users/vitalij/Downloads/SIGCHI_HCI_UX_researchers_FULL (5).xlsx")
CACHE_PATH = ROOT / "data" / "scholar-cache.json"
OUT_PATH = ROOT / "src" / "data" / "people.json"

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

DECEASED = {
    "Vicki L. Hanson": {"year": 2026, "note": "20 января 2026"},
    "Gary Marsden": {"year": 2013, "note": "27 декабря 2013"},
    "Larry Tesler": {"year": 2020, "note": "2020"},
    "John Karat": {"year": None, "note": "памятная сессия CHI 2016"},
    "Randy Pausch": {"year": 2008, "note": "2008"},
    "Thomas K. Landauer": {"year": 2014, "note": "2014"},
    "Brian Shackel": {"year": None, "note": None},
    "William Newman": {"year": 2019, "note": "2019"},
    "Douglas C. Engelbart": {"year": 2013, "note": "2013"},
}

CLUSTERS = [
    (
        "video",
        "Видеозвонки",
        "video calls",
        r"video (call|communicat|conferenc|chat)|telepresence|media space|"
        r"видеозвон|видеоконферен",
    ),
    (
        "socialmedia",
        "Социальные медиа",
        "social media",
        r"social media|\bfacebook\b|\btwitter\b|online social network",
    ),
    (
        "socialcomputing",
        "Социальные вычисления",
        "social computing",
        r"social computing",
    ),
    (
        "gaze",
        "Отслеживание взгляда",
        "eye tracking",
        r"eye.?track|\bgaze\b|айтрек|взгляд",
    ),
    (
        "wearable",
        "Носимые устройства",
        "wearable",
        r"wearable|носим",
    ),
    (
        "datascience",
        "Наука о данных",
        "data science",
        r"human-centered data|data science|visual analytics",
    ),
    (
        "games",
        "Игры",
        "games and play",
        r"\bgames?\b|game design|игровой|exergame|exertion|chi play|playful|"
        r"player experience|игрового ux",
    ),
    (
        "hri",
        "Роботы и автопилот",
        "human-robot interaction",
        r"human-robot|\bhri\b|social robot|робот|autonomous vehicle|autonomous driv|"
        r"automated driv|driver-vehicle|automotive interaction|автономн",
    ),
    (
        "children",
        "Дети и семьи",
        "children and families",
        r"\bchildren\b|child-computer|для детей|семей и детей|parenting|детск|"
        r"childhood|\bkids\b",
    ),
    (
        "sustainability",
        "Устойчивость",
        "sustainability",
        r"sustainab|climate|e-waste|batteryless|biodegrad|устойчив|эколог|"
        r"electronic waste|unmaking",
    ),
    (
        "haptics",
        "Осязание и тело",
        "haptics",
        r"haptic|хаптик|soma design|somaesthetic|tactile|tangible user|"
        r"tangible bits|телесн|embodied interaction|body-centric|skin ",
    ),
    (
        "speech",
        "Речь и голос",
        "speech and voice",
        r"\bspeech\b|voice interface|vocal|telephony|голосо|речев|\bnime\b|"
        r"conversational agent",
    ),
    (
        "search",
        "Поиск",
        "information retrieval",
        r"information retrieval|information foraging|sensemaking|search engine|"
        r"информационн(ый)? поиск|query by|tilebars|web search|\bir\b",
    ),
    (
        "ubicomp",
        "Вездесущие вычисления",
        "ubiquitous computing",
        r"ubiquitous|ubicomp|context-aware|pervasive|ambient intelligence|"
        r"smart home|убиквитив|вездесущ",
    ),
    (
        "critical",
        "Критический дизайн",
        "critical design",
        r"design fiction|adversarial design|speculative|ludic design|cultural probes|"
        r"critically reflective|\bsts\b|science and technology studies|"
        r"критическ|дизайн-фикшн",
    ),
    (
        "aging",
        "Старение",
        "aging",
        r"older adult|aging|elderly|старен|пожилых|ageing",
    ),
    (
        "crowdsourcing",
        "Коллективный вклад",
        "crowdsourcing",
        r"crowdsourc|human computation|citizen science|краудсор",
    ),
    (
        "mobile",
        "Мобильное взаимодействие",
        "mobile HCI",
        r"mobile computing|smartphone|мобильн|mobile user interface|"
        r"mobile interaction|mobile hci",
    ),
    (
        "affective",
        "Эмоции",
        "affective computing",
        r"affective comput|affective|emotion recognition|аффективн|\bэмоц",
    ),
    (
        "ethics",
        "Этика и ИИ",
        "AI ethics",
        r"responsible ai|algorithmic fairness|\bethics\b|этик|"
        r"fairness|value sensitive|\bvsd\b",
    ),
    (
        "accessibility",
        "Доступность",
        "accessibility",
        r"accessib|assistive|disability|screen reader|jaws|inclusive design|"
        r"universal design|доступн|инвалид|"
        r"blind|low vision|caption|deaf |hard of hearing",
    ),
    (
        "cscw",
        "Совместная работа",
        "CSCW",
        r"\bcscw\b|online communit|groupware|collaborat|социальн|"
        r"сообществ|moderat|computer-mediated|computer-supported|"
        r"crisis informatic|дезинформ",
    ),
    (
        "ai",
        "Человек и ИИ",
        "human-AI",
        r"\bai\b|\bии\b|machine learning|\bllm\b|recommender|human-ai|human–ai|"
        r"intelligent agent|нейросет|artificial intelligence|"
        r"human computation|human-centered ai|interpretability",
    ),
    (
        "privacy",
        "Конфиденциальность",
        "privacy",
        r"privacy|security|приватн|dark pattern|usable privacy|surveillance|"
        r"digital safety|тёмн(ые|ых) паттерн",
    ),
    (
        "health",
        "Здоровье",
        "health",
        r"health|wellbeing|well-being|medical|хирург|психическ|healthcare|patient|"
        r"mental|autism|dement|благополуч|clinical|therapy|mhealth|цифровое благополуч",
    ),
    (
        "input",
        "Ввод и жесты",
        "input and gesture",
        r"sensor|input|gesture|touch|fitts|pointing|text entry|"
        r"keyboard|mouse|сенсор|жест|multimodal input|pen and|multitouch|мультитач",
    ),
    (
        "xr",
        "Виртуальная и дополненная реальность",
        "VR / AR",
        r"\bvr\b|\bar\b|\bxr\b|virtual real|augmented|3d user|immersive|mixed reality|"
        r"расширенная реальность|виртуальн|дополненн",
    ),
    (
        "vis",
        "Визуализация",
        "visualization",
        r"visualiz|infovis|визуализ|information visualization|"
        r"data visualization",
    ),
    (
        "methods",
        "Методы",
        "methods",
        r"design method|usability|ethnograph|user research|"
        r"практик|contextual design|\bgoms\b|cognitive walk|"
        r"heuristic|semiote|activity theory|"
        r"worth-centred|value-centred|юзабилити",
    ),
    (
        "justice",
        "HCI для развития и феминизм",
        "HCI4D",
        r"global south|ict4d|\bictd\b|hci4d|africa|деколони|diversity|inclusion|"
        r"гражданск|developing countr|feminist|феминист|humanistic hci|"
        r"малограмот|text-free|queer theory|decoloniz",
    ),
    (
        "making",
        "Изготовление и инструменты",
        "making",
        r"fabricat|diy|maker|3d print|end-user|ui tool|programming|design tool|"
        r"d\.tools|personal fabrication|прототип|инструмент|end.user development",
    ),
    (
        "learning",
        "Обучение",
        "learning",
        r"learn|educat|обучен|classroom|cs education|обучаю|curriculum|"
        r"educational technolog",
    ),
]

CLUSTER_COLORS = {
    "video": "#6ec4dc",
    "socialmedia": "#e07090",
    "socialcomputing": "#5b88c4",
    "gaze": "#8cbe6e",
    "wearable": "#4a9a8c",
    "datascience": "#e0b84a",
    "games": "#d08070",
    "hri": "#b890c8",
    "children": "#8fb8d0",
    "sustainability": "#7aab7a",
    "haptics": "#c9a07a",
    "speech": "#a0b8c8",
    "search": "#c4b060",
    "ubicomp": "#5b9e9a",
    "critical": "#c0a0c0",
    "aging": "#b8c49a",
    "crowdsourcing": "#6aabb8",
    "mobile": "#7aa8c4",
    "affective": "#d4a0b8",
    "ethics": "#c4a090",
    "accessibility": "#7eb8a8",
    "cscw": "#6ea8d8",
    "ai": "#c4a0e8",
    "privacy": "#d09090",
    "health": "#e0a070",
    "input": "#8fd0c8",
    "xr": "#9b9be8",
    "vis": "#d4c078",
    "methods": "#a8c47a",
    "justice": "#e090b0",
    "making": "#d4a574",
    "learning": "#7ec4d4",
    "foundations": "#9aa3b0",
}

BOILERPLATE = re.compile(
    r"тема уточняется[^.]*(?:\.|$)|"
    r"тема работ/публикаций:\s*|"
    r"см\. google scholar|"
    r"не проверено вручную|"
    r"не найден|"
    r"служение сообществу SIGCHI\.?|"
    r"служение сообществу\.?|"
    r",?\s*служение SIGCHI\.?|"
    r"Служение SIGCHI\s*(?:\([^)]*\))?|"
    r"https?://\S+",
    re.I,
)

STOP_EXTRA = {
    "тема",
    "работ",
    "публикаций",
    "google",
    "scholar",
    "dblp",
    "profile",
    "см",
    "the",
    "and",
    "for",
    "with",
    "from",
    "that",
    "this",
    "hci",
    "chi",
    "acm",
    "sigchi",
    "university",
    "research",
}


def slugify(name: str) -> str:
    s = name.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-") or "person"


def clean_link(value) -> str | None:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return None
    s = str(value).strip()
    if not s or s.startswith("не ") or s.startswith("неприменимо"):
        return None
    if s.startswith("http://") or s.startswith("https://") or s.startswith("@"):
        return s
    return None


def scholar_user_id(url: str | None) -> str | None:
    if not url:
        return None
    m = re.search(r"user=([A-Za-z0-9_-]+)", url)
    return m.group(1) if m else None


def parse_awards(raw: str) -> list[dict]:
    awards = []
    for part in re.split(r";", str(raw)):
        part = part.strip()
        if not part:
            continue
        year_m = re.search(r"(19|20)\d{2}", part)
        year = int(year_m.group()) if year_m else None
        kind = re.sub(r"\s*(19|20)\d{2}.*$", "", part).strip()
        awards.append({"type": kind, "year": year, "label": part})
    return awards


def extract_university(aff: str) -> str:
    s = str(aff)
    if re.search(r"служение сообществу", s, flags=re.I):
        return ""
    s = re.sub(r"[⚠].*$", "", s)
    s = re.sub(r"—\s*скончал.*$", "", s, flags=re.I)
    s = re.sub(r"\([^)]*скончал[^)]*\)", "", s, flags=re.I)
    s = re.sub(r"\([^)]*жив[^)]*\)", "", s, flags=re.I)
    first = s.split(",")[0]
    first = re.sub(r"\s*\([^)]*\)\s*", " ", first)
    first = re.sub(r"\s*\([^)]*$", "", first)
    first = re.sub(r"\s+", " ", first).strip(" -—/(")
    return first or str(aff).split(",")[0].strip()


def clean_topics_table(raw: str) -> str:
    s = BOILERPLATE.sub(" ", str(raw))
    s = re.sub(r"\bgoogle scholar\.?\s*", " ", s, flags=re.I)
    s = re.sub(r"\s+", " ", s).strip(" .;—-")
    return s


def load_cache() -> dict:
    if CACHE_PATH.exists():
        return json.loads(CACHE_PATH.read_text())
    return {}


def save_cache(cache: dict) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False, indent=2))


def fetch_url(url: str, timeout: int = 25, quiet: bool = False) -> str | None:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", "replace")
    except (urllib.error.URLError, TimeoutError, Exception) as exc:
        if not quiet:
            print(f"  fetch fail {url}: {exc}")
        return None


def parse_scholar_html(html: str, uid: str) -> dict:
    if "not a robot" in html.lower() or "unusual traffic" in html.lower():
        raise RuntimeError("scholar blocked")
    interests = re.findall(
        r'<a[^>]*class="gsc_prf_inta[^"]*"[^>]*>([^<]+)</a>', html
    )
    papers = []
    for attrs, title in re.findall(r'<a\s+([^>]*class="gsc_a_at"[^>]*)>([^<]+)</a>', html):
        href_m = re.search(r'href="([^"]+)"', attrs)
        href = html_lib.unescape(href_m.group(1)) if href_m else ""
        if href.startswith("/"):
            href = "https://scholar.google.com" + href
        title = html_lib.unescape(title.strip())
        if title:
            papers.append({"title": title, "url": href or None})
    papers = papers[:10]
    cited = None
    m = re.search(r"Cited by[^0-9]*(\d[\d,]*)", html)
    if m:
        cited = int(m.group(1).replace(",", ""))
    photo = None
    pm = re.search(r'src="([^"]+)"[^>]*id="gsc_prf_pup-img"', html) or re.search(
        r'id="gsc_prf_pup-img"[^>]*src="([^"]+)"', html
    )
    if pm:
        src = html_lib.unescape(pm.group(1))
        if "avatar_scholar" not in src:
            if src.startswith("//"):
                src = "https:" + src
            photo = src
    return {
        "interests": [
            html_lib.unescape(t.strip())
            for t in interests
            if t.strip() and len(t.strip()) < 80
        ][:12],
        "papers": papers,
        "citedBy": cited,
        "photo": photo,
    }


def _paper_records(raw) -> list[dict]:
    out = []
    for item in raw or []:
        if isinstance(item, str):
            out.append({"title": html_lib.unescape(item), "url": None})
        elif isinstance(item, dict) and item.get("title"):
            out.append(
                {
                    "title": html_lib.unescape(str(item["title"])),
                    "url": item.get("url"),
                }
            )
    return out


def _cache_stale(entry: dict) -> bool:
    papers = entry.get("papers") or []
    if not papers:
        return True
    if isinstance(papers[0], str):
        return True
    if isinstance(papers[0], dict) and not papers[0].get("url"):
        return True
    return "photo" not in entry


def enrich_scholar(people: list[dict], cache: dict) -> None:
    pending = []
    for p in people:
        uid = scholar_user_id(p["links"].get("scholar"))
        if not uid:
            continue
        entry = cache.get(uid)
        if entry and not _cache_stale(entry):
            p["topicsScholar"] = [html_lib.unescape(t) for t in (entry.get("interests") or [])]
            p["papersScholar"] = _paper_records(entry.get("papers"))
            p["citedBy"] = entry.get("citedBy")
            p["portraitUrl"] = entry.get("photo")
            continue
        pending.append((p, uid))

    print(f"Scholar profiles to fetch: {len(pending)}")

    def load_one(uid: str):
        url = f"https://scholar.google.com/citations?user={uid}&hl=en"
        page = fetch_url(url)
        if not page:
            return uid, None
        return uid, parse_scholar_html(page, uid)

    if pending:
        done = 0
        with ThreadPoolExecutor(max_workers=8) as pool:
            futs = {pool.submit(load_one, uid): (p, uid) for p, uid in pending}
            for fut in as_completed(futs):
                p, uid = futs[fut]
                try:
                    _uid, parsed = fut.result()
                except RuntimeError:
                    print("Google Scholar blocked; keeping partial cache.")
                    break
                except Exception as exc:
                    print(f"  parse fail {p['name']}: {exc}")
                    parsed = None
                if parsed:
                    cache[uid] = parsed
                    p["topicsScholar"] = parsed["interests"]
                    p["papersScholar"] = parsed["papers"]
                    p["citedBy"] = parsed["citedBy"]
                    p["portraitUrl"] = parsed.get("photo")
                else:
                    old = cache.get(uid) or {}
                    p["topicsScholar"] = [html_lib.unescape(t) for t in (old.get("interests") or [])]
                    p["papersScholar"] = _paper_records(old.get("papers"))
                    p["citedBy"] = old.get("citedBy")
                    p["portraitUrl"] = old.get("photo")
                done += 1
                if done % 40 == 0:
                    save_cache(cache)
                    print(f"  {done}/{len(pending)}")
        save_cache(cache)

    for p in people:
        p.setdefault("papersScholar", [])
        p.setdefault("topicsScholar", [])
        p.setdefault("portraitUrl", None)
        if p["papersScholar"] and isinstance(p["papersScholar"][0], str):
            p["papersScholar"] = _paper_records(p["papersScholar"])


def assign_cluster(table: str, scholar: list[str], papers: list[str]) -> str:
    core = f"{table} {' '.join(scholar)}".lower()
    full = f"{core} {' '.join(papers)}".lower()
    scholar_blob = " ".join(scholar).lower()
    methodish = {"methods", "socialcomputing"}

    # Large Scholar chips become classes before paper keywords (e.g. "social media") steal them.
    for cid, pat in [
        ("socialcomputing", r"social computing"),
        ("datascience", r"human-centered data|visual analytics|\bdata science\b"),
        ("socialmedia", r"social media"),
        ("wearable", r"wearable"),
        ("video", r"telepresence|video communication|media space"),
        ("gaze", r"eye.?track|\bgaze\b"),
    ]:
        if re.search(pat, scholar_blob, flags=re.I):
            return cid

    priority = [
        ("video", r"telepresence|media space|video (call|communicat|conferenc|chat)|videoconferenc|видеозвон"),
        ("socialmedia", r"social media|\bfacebook\b|\btwitter\b"),
        ("gaze", r"eye.?track|\bgaze\b|айтрек"),
        ("wearable", r"wearable|\bносим"),
        ("datascience", r"human-centered data|visual analytics|data science"),
        ("games", r"game design|exertion games|exergame|chi play|игровой ux|how games move"),
        ("hri", r"human-robot|\bhri\b|social robot|autonomous vehicle|automated driv|driver-vehicle"),
        ("aging", r"older adult|aging and|ageing|пожилых|старен"),
        ("children", r"\bchildren\b|для детей|семей и детей|parenting|детск"),
        ("sustainability", r"sustainab|e-waste|batteryless|biodegrad|electronic waste|unmaking"),
        ("haptics", r"haptic|soma design|somaesthetic|tangible bits|tactile feedback|хаптик"),
        ("speech", r"голосовые интерфейсы|voice communication|речевые интерфейсы|telephony|\bnime\b"),
        ("crowdsourcing", r"crowdsourc|human computation|citizen science"),
        ("mobile", r"mobile computing|smartphone|mobile user interface|мобильн"),
        ("affective", r"affective comput|affective|аффективн"),
        ("ethics", r"responsible ai|algorithmic fairness|value sensitive|\bvsd\b"),
        ("search", r"information retrieval|information foraging|tilebars|web search|sensemaking"),
        ("ubicomp", r"ubiquitous computing|\bubicomp\b|context-aware|ambient intelligence"),
        ("critical", r"design fiction|adversarial design|cultural probes|ludic|speculative design"),
        ("justice", r"hci4d|\bictd\b|ict4d|global south|деколони|феминист|feminist hci|decoloniz"),
        ("privacy", r"dark pattern|usable privacy|приватн"),
        ("accessibility", r"accessib|assistive technolog|screen reader|\bjaws\b|доступн"),
        ("health", r"mental health|healthcare|психическ|благополуч|mhealth"),
        ("xr", r"virtual real|augmented real|\bxr\b|3d user interface"),
        ("ai", r"human-ai|recommender|human-centered ai|interpretability"),
        ("making", r"fabricat|3d print|\bdiy\b|end-user development"),
        ("learning", r"educational technolog|cs education|обучен"),
        ("vis", r"infovis|information visualization"),
        ("input", r"fitts|text entry|multitouch"),
        ("cscw", r"\bcscw\b|groupware|online communit"),
    ]
    for cid, pat in priority:
        blob = core if cid in methodish else full
        if re.search(pat, blob, flags=re.I):
            return cid

    best_id, best_score = "foundations", 0.0
    for cid, _label, _en, pat in CLUSTERS:
        blob_papers = "" if cid in methodish else " ".join(papers)
        table_hits = len(re.findall(pat, table, flags=re.I))
        scholar_hits = len(re.findall(pat, " ".join(scholar), flags=re.I))
        paper_hits = len(re.findall(pat, blob_papers, flags=re.I))
        score = table_hits + 2.0 * scholar_hits + 1.0 * paper_hits
        if score > best_score:
            best_id, best_score = cid, score
    return best_id


def paper_titles(person: dict) -> list[str]:
    out = []
    for item in person.get("papersScholar") or []:
        if isinstance(item, dict):
            if item.get("title"):
                out.append(item["title"])
        elif item:
            out.append(str(item))
    return out


OG_IMAGE = re.compile(
    r'<meta[^>]+(?:property|name)=["\']og:image["\'][^>]+content=["\']([^"\']+)',
    re.I,
)
OG_IMAGE_REV = re.compile(
    r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:property|name)=["\']og:image["\']',
    re.I,
)


def _abs_url(base: str, src: str) -> str:
    src = html_lib.unescape(src.strip())
    if src.startswith("//"):
        return "https:" + src
    if src.startswith("http://") or src.startswith("https://"):
        return src
    return urllib.parse.urljoin(base, src)


def portrait_from_website(url: str) -> str | None:
    if "linkedin.com" in url or "x.com/" in url or "twitter.com" in url:
        return None
    page = fetch_url(url, timeout=8, quiet=True)
    if not page:
        return None
    m = OG_IMAGE.search(page) or OG_IMAGE_REV.search(page)
    if not m:
        return None
    img = _abs_url(url, m.group(1))
    if any(x in img.lower() for x in ("logo", "sprite", "icon-")):
        return None
    return img


def twitter_handle(raw: str | None) -> str | None:
    if not raw:
        return None
    m = re.search(r"(?:x\.com/|twitter\.com/)([A-Za-z0-9_]+)", raw)
    if m:
        return m.group(1)
    if raw.startswith("@") and len(raw) > 2:
        return raw[1:]
    return None


def enrich_portraits(people: list[dict]) -> None:
    need = [p for p in people if not p.get("portraitUrl") and p["links"].get("website")]
    print(f"Website portraits to try: {len(need)}")
    if not need:
        return

    def one(person: dict):
        return person["id"], portrait_from_website(person["links"]["website"])

    done = 0
    with ThreadPoolExecutor(max_workers=8) as pool:
        futs = [pool.submit(one, p) for p in need]
        by_id = {p["id"]: p for p in need}
        for fut in as_completed(futs):
            pid, url = fut.result()
            if url:
                by_id[pid]["portraitUrl"] = url
            done += 1
            if done % 40 == 0:
                print(f"  {done}/{len(need)}")
    # LinkedIn / X as last resort via unavatar
    for p in people:
        if p.get("portraitUrl"):
            continue
        handle = twitter_handle(p["links"].get("twitter"))
        if handle:
            p["portraitUrl"] = f"https://unavatar.io/x/{handle}"
            continue
        li = p["links"].get("linkedin") or ""
        m = re.search(r"linkedin\.com/in/([^/?#]+)", li)
        if m:
            p["portraitUrl"] = f"https://unavatar.io/linkedin/{m.group(1)}"


def embed_layout(people: list[dict]) -> None:
    docs = []
    for p in people:
        parts = [
            p.get("topicsTable") or "",
            " ".join(p.get("topicsScholar") or []),
            " ".join(paper_titles(p)),
            p["cluster"].replace("-", " "),
        ]
        docs.append(" ".join(parts))

    vectorizer = TfidfVectorizer(
        min_df=1,
        max_df=0.85,
        ngram_range=(1, 2),
        token_pattern=r"(?u)\b[\w+#.-]{2,}\b",
        stop_words=list(STOP_EXTRA),
    )
    tfidf = vectorizer.fit_transform(docs)
    n_comp = min(40, max(2, tfidf.shape[1] - 1), tfidf.shape[0] - 1)
    svd = TruncatedSVD(n_components=n_comp, random_state=42)
    reduced = svd.fit_transform(tfidf)

    perplexity = min(30, max(5, len(people) // 8))
    tsne = TSNE(
        n_components=2,
        perplexity=perplexity,
        random_state=42,
        init="pca",
        learning_rate="auto",
        max_iter=1500,
    )
    xy = tsne.fit_transform(reduced)

    # Spread clusters slightly apart so named regions don't collapse.
    cluster_ids = sorted({p["cluster"] for p in people})
    idx = {c: i for i, c in enumerate(cluster_ids)}
    angles = {c: 2 * np.pi * i / max(len(cluster_ids), 1) for i, c in enumerate(cluster_ids)}
    xy = xy.copy()
    for i, p in enumerate(people):
        a = angles[p["cluster"]]
        xy[i, 0] += 1.15 * np.cos(a)
        xy[i, 1] += 1.15 * np.sin(a)

    xs, ys = xy[:, 0], xy[:, 1]
    pad = 0.08
    x_min, x_max = xs.min(), xs.max()
    y_min, y_max = ys.min(), ys.max()
    for i, p in enumerate(people):
        p["x"] = float(pad + (1 - 2 * pad) * (xs[i] - x_min) / (x_max - x_min or 1))
        p["y"] = float(pad + (1 - 2 * pad) * (ys[i] - y_min) / (y_max - y_min or 1))

    # Clusters come from the taxonomy; SVD+t-SNE only places people.


GENERIC_TAGS = {
    "human-computer interaction",
    "human computer interaction",
    "hci",
    "computer science",
    "design",
    "human-centered computing",
    "interactive computing",
    "computer-human interaction",
    "hci and human-centered computing",
    "graphics",
    "computer graphics",
    "psychology",
}

DERIVED_TAGS = [
    ("видеозвонки", r"video (call|communicat|conferenc|chat|meeting)|telepresence|media space|videoconferenc|видеозвон|видеоконферен"),
    ("социальные медиа", r"social media|\bfacebook\b|\btwitter\b"),
    ("отслеживание взгляда", r"eye.?track|\bgaze\b"),
    ("носимые устройства", r"wearable"),
    ("рекомендательные системы", r"recommender"),
    ("настольные поверхности", r"\btabletop\b"),
    ("компьютерно-опосредованная связь", r"computer-mediated communication|\bcmc\b"),
]


def person_tags(person: dict) -> list[str]:
    tags: list[str] = []
    seen: set[str] = set()
    for raw in person.get("topicsScholar") or []:
        label = str(raw).strip()
        key = label.lower()
        if not label or key in GENERIC_TAGS or key in seen:
            continue
        tags.append(label)
        seen.add(key)
    blob = f"{person.get('topicsTable') or ''} {' '.join(paper_titles(person))}".lower()
    for label, pat in DERIVED_TAGS:
        key = label.lower()
        if key in seen:
            continue
        if re.search(pat, blob, flags=re.I):
            tags.append(label)
            seen.add(key)
    return tags


def build_map_labels(people: list[dict]) -> list[dict]:
    for p in people:
        p["tags"] = person_tags(p)

    buckets: dict[str, list[dict]] = defaultdict(list)
    display: dict[str, str] = {}
    for p in people:
        for tag in p.get("tags") or []:
            key = tag.lower()
            buckets[key].append(p)
            display.setdefault(key, tag)

    cluster_names = {str(p.get("clusterLabel") or "").lower() for p in people}
    cluster_en = {en.lower() for _cid, _ru, en, _pat in CLUSTERS if en}
    cluster_ru = {lab.lower() for _cid, lab, _en, _pat in CLUSTERS}
    cluster_en.add("hci foundations")
    cluster_ru.add("основания hci")
    labels = []
    for key, members in buckets.items():
        if len(members) < 4:
            continue
        if key in GENERIC_TAGS or key in cluster_names or key in cluster_en or key in cluster_ru:
            continue
        cx = sum(p["x"] for p in members) / len(members)
        cy = sum(p["y"] for p in members) / len(members)
        labels.append(
            {
                "id": key,
                "label": display[key],
                "x": float(cx),
                "y": float(cy),
                "count": len(members),
            }
        )

    labels.sort(key=lambda item: -item["count"])
    placed: list[dict] = []
    for item in labels:
        for other in placed:
            dx = item["x"] - other["x"]
            dy = item["y"] - other["y"]
            if dx * dx + dy * dy < 0.011:
                item["x"] = min(0.92, item["x"] + 0.055)
                item["y"] = max(0.08, item["y"] - 0.04)
        placed.append(item)
    return placed


def load_people() -> list[dict]:
    df = pd.read_excel(XLSX, sheet_name="HCI UX researchers")
    people = []
    seen = {}
    for _, row in df.iterrows():
        name = str(row["Имя"]).strip()
        sid = slugify(name)
        if sid in seen:
            seen[sid] += 1
            sid = f"{sid}-{seen[sid]}"
        else:
            seen[sid] = 1
        sector_raw = str(row["Тип (Академ/Корп)"]).strip()
        sector = {"Академ": "academic", "Корп": "corporate"}.get(sector_raw, "unknown")
        death = DECEASED.get(name)
        scholar = clean_link(row["Google Scholar"])
        aff = str(row["Аффилиация"]).strip()
        aff = re.sub(r"Служение сообществу SIGCHI\s*(?:\([^)]*\))?", "", aff, flags=re.I).strip(" —–-")
        person = {
            "id": sid,
            "name": name,
            "nameRu": name_ru(name),
            "deceased": bool(death),
            "deathYear": death["year"] if death else None,
            "deathNote": death["note"] if death else None,
            "university": extract_university(row["Аффилиация"]),
            "affiliation": aff,
            "sector": sector,
            "awards": parse_awards(row["Награды SIGCHI (все, с годами)"]),
            "topicsTable": clean_topics_table(row["Научные интересы и темы работ"]),
            "topicsScholar": [],
            "papersScholar": [],
            "citedBy": None,
            "portraitUrl": None,
            "links": {
                "scholar": scholar,
                "dblp": clean_link(row["DBLP"]),
                "website": clean_link(row["Сайт"]),
                "linkedin": clean_link(row["LinkedIn"]),
                "twitter": clean_link(row["X / Twitter / Bluesky"]),
            },
        }
        people.append(person)
    return people


def main() -> None:
    people = load_people()
    cache = load_cache()
    enrich_scholar(people, cache)
    enrich_portraits(people)
    for p in people:
        p["cluster"] = assign_cluster(
            p["topicsTable"], p.get("topicsScholar") or [], paper_titles(p)
        )
        p["clusterLabel"] = next(
            (f"{lab} ({en})" for cid, lab, en, _ in CLUSTERS if cid == p["cluster"]),
            "Основания HCI (HCI foundations)",
        )
        if p["cluster"] == "foundations":
            p["clusterLabel"] = "Основания HCI (HCI foundations)"
    print("Translating Scholar titles to Russian…")
    all_titles = [t for p in people for t in paper_titles(p)]
    mapped = translate_titles(all_titles)
    for p in people:
        for item in p.get("papersScholar") or []:
            if isinstance(item, dict):
                item["titleRu"] = mapped.get(item["title"], item["title"])
    save_paper_cache()
    print(f"  done ({len(set(all_titles))} unique titles)")
    embed_layout(people)
    map_labels = build_map_labels(people)

    payload = {
        "source": XLSX.name,
        "peopleCount": len(people),
        "deceasedCount": sum(1 for p in people if p["deceased"]),
        "clusters": [
            {
                "id": cid,
                "label": lab if cid != "foundations" else "Основания HCI",
                "labelEn": en if cid != "foundations" else "HCI foundations",
                "color": CLUSTER_COLORS[cid],
                "count": sum(1 for p in people if p["cluster"] == cid),
            }
            for cid, lab, en, _ in CLUSTERS
            + [("foundations", "Основания HCI", "HCI foundations", "")]
            if sum(1 for p in people if p["cluster"] == cid)
        ],
        "mapLabels": map_labels,
        "people": people,
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    print(f"Wrote {OUT_PATH} ({len(people)} people)")
    print("clusters:", {c["id"]: c["count"] for c in payload["clusters"]})
    print("map labels:", len(map_labels))
    print("with scholar interests:", sum(1 for p in people if p["topicsScholar"]))
    print("with portraits:", sum(1 for p in people if p.get("portraitUrl")))
    print("with paper links:", sum(1 for p in people for x in p.get("papersScholar") or [] if isinstance(x, dict) and x.get("url")))


if __name__ == "__main__":
    main()
