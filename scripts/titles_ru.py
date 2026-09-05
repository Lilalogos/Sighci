"""Russian renderings of Google Scholar paper titles."""

from __future__ import annotations

import json
import re
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

PHRASES: list[tuple[str, str]] = [
    ("computer-supported cooperative work", "компьютерно-опосредованная совместная работа"),
    ("computer supported cooperative work", "компьютерно-опосредованная совместная работа"),
    ("human-computer interaction", "человеко-компьютерное взаимодействие"),
    ("human computer interaction", "человеко-компьютерное взаимодействие"),
    ("human-centered machine learning", "человеко-ориентированное машинное обучение"),
    ("human-centered data science", "человеко-ориентированная наука о данных"),
    ("human-centered computing", "человеко-ориентированные вычисления"),
    ("human-centered ai", "человеко-ориентированный ИИ"),
    ("human-ai interaction", "взаимодействие человека и ИИ"),
    ("human–ai interaction", "взаимодействие человека и ИИ"),
    ("human-ai collaboration", "сотрудничество человека и ИИ"),
    ("human-robot interaction", "взаимодействие человека и робота"),
    ("information retrieval", "информационный поиск"),
    ("information visualization", "визуализация информации"),
    ("visual analytics", "визуальная аналитика"),
    ("data visualization", "визуализация данных"),
    ("ubiquitous computing", "вездесущие вычисления"),
    ("pervasive computing", "вездесущие вычисления"),
    ("pervasive computing", "всепроникающие вычисления"),
    ("augmented reality", "дополненная реальность"),
    ("virtual reality", "виртуальная реальность"),
    ("mixed reality", "смешанная реальность"),
    ("extended reality", "расширенная реальность"),
    ("user experience", "пользовательский опыт"),
    ("interaction design", "дизайн взаимодействия"),
    ("participatory design", "партиципаторный дизайн"),
    ("value sensitive design", "дизайн, чувствительный к ценностям"),
    ("contextual design", "контекстный дизайн"),
    ("research through design", "исследование через дизайн"),
    ("end-user development", "разработка конечным пользователем"),
    ("recommender systems", "рекомендательные системы"),
    ("social computing", "социальные вычисления"),
    ("social media", "социальные медиа"),
    ("online communities", "онлайн-сообщества"),
    ("computer-mediated communication", "компьютерно-опосредованная коммуникация"),
    ("usable privacy and security", "удобство конфиденциальности и безопасности"),
    ("usable security", "удобство безопасности"),
    ("dark patterns", "тёмные паттерны"),
    ("digital wellbeing", "цифровое благополучие"),
    ("mental health", "психическое здоровье"),
    ("personal informatics", "личная информатика"),
    ("tangible user interfaces", "осязаемые пользовательские интерфейсы"),
    ("3d user interfaces", "трёхмерные пользовательские интерфейсы"),
    ("user interfaces", "пользовательские интерфейсы"),
    ("user interface", "пользовательский интерфейс"),
    ("machine learning", "машинное обучение"),
    ("artificial intelligence", "искусственный интеллект"),
    ("deep learning", "глубокое обучение"),
    ("large language models", "большие языковые модели"),
    ("wearable computing", "носимые вычисления"),
    ("wearable computers", "носимые компьютеры"),
    ("mobile computing", "мобильные вычисления"),
    ("urban computing", "городские вычисления"),
    ("crisis informatics", "информатика кризисов"),
    ("assistive technology", "ассистивные технологии"),
    ("accessible computing", "доступные вычисления"),
    ("universal design", "универсальный дизайн"),
    ("inclusive design", "инклюзивный дизайн"),
    ("eye tracking", "отслеживание взгляда"),
    ("text entry", "текстовый ввод"),
    ("fitts' law", "закон Фиттса"),
    ("fitts’s law", "закон Фиттса"),
    ("cognitive walkthrough", "когнитивный обход"),
    ("heuristic evaluation", "эвристическая оценка"),
    ("activity theory", "теория деятельности"),
    ("feminist hci", "феминистский HCI"),
    ("speculative design", "спекулятивный дизайн"),
    ("design fiction", "дизайн-фикшн"),
    ("exertion games", "игры на усилие"),
    ("serious games", "серьёзные игры"),
    ("game design", "игровой дизайн"),
    ("social capital", "социальный капитал"),
    ("social network sites", "сайты социальных сетей"),
    ("social network site", "сайт социальной сети"),
    ("workspace awareness", "осведомлённость о рабочем пространстве"),
    ("information foraging", "информационное фуражирование"),
    ("latent semantic analysis", "латентно-семантический анализ"),
    ("the paperless office", "миф о безбумажном офисе"),
    ("paperless office", "безбумажный офис"),
    ("older adults", "пожилые люди"),
    ("public health", "общественное здоровье"),
    ("well-being", "благополучие"),
    ("collaborative filtering", "совместная фильтрация"),
    ("online social network", "онлайн-социальная сеть"),
    ("college students", "студенты колледжей"),
    ("case study", "кейс-стади"),
    ("case studies", "кейсы"),
    ("empirical study", "эмпирическое исследование"),
    ("qualitative study", "качественное исследование"),
    ("field study", "полевое исследование"),
    ("literature review", "обзор литературы"),
    ("systematic review", "систематический обзор"),
    ("design implications", "выводы для дизайна"),
    ("towards a", "к"),
    ("a conceptual framework", "концептуальная рамка"),
    ("conceptual framework", "концептуальная рамка"),
    ("in the wild", "в естественных условиях"),
    ("real world", "реальный мир"),
    ("real-world", "реальный мир"),
]

WORDS: dict[str, str] = {
    "the": "",
    "a": "",
    "an": "",
    "of": "",
    "and": "и",
    "or": "или",
    "for": "для",
    "with": "с",
    "without": "без",
    "from": "из",
    "into": "в",
    "on": "по",
    "in": "в",
    "to": "к",
    "as": "как",
    "by": "",
    "using": "с помощью",
    "based": "на основе",
    "through": "через",
    "between": "между",
    "among": "среди",
    "over": "за",
    "under": "при",
    "about": "о",
    "against": "против",
    "new": "новый",
    "towards": "к",
    "toward": "к",
    "beyond": "за пределами",
    "understanding": "понимание",
    "designing": "проектирование",
    "evaluating": "оценка",
    "measuring": "измерение",
    "exploring": "исследование",
    "investigating": "изучение",
    "rethinking": "переосмысление",
    "fostering": "развитие",
    "supporting": "поддержка",
    "improving": "улучшение",
    "making": "создание",
    "building": "построение",
    "charting": "картография",
    "mapping": "картографирование",
    "sensing": "сенсорика",
    "interaction": "взаимодействие",
    "interactions": "взаимодействия",
    "interface": "интерфейс",
    "interfaces": "интерфейсы",
    "design": "дизайн",
    "designs": "дизайны",
    "system": "система",
    "systems": "системы",
    "technology": "технология",
    "technologies": "технологии",
    "computer": "компьютер",
    "computers": "компьютеры",
    "computing": "вычисления",
    "user": "пользователь",
    "users": "пользователи",
    "people": "люди",
    "human": "человек",
    "humans": "люди",
    "social": "социальный",
    "community": "сообщество",
    "communities": "сообщества",
    "collaboration": "совместная работа",
    "collaborative": "совместный",
    "cooperative": "кооперативный",
    "work": "работа",
    "workplace": "рабочее место",
    "future": "будущее",
    "health": "здоровье",
    "healthcare": "здравоохранение",
    "privacy": "конфиденциальность",
    "security": "безопасность",
    "safety": "безопасность",
    "trust": "доверие",
    "ethics": "этика",
    "ethical": "этический",
    "fairness": "справедливость",
    "bias": "предвзятость",
    "accessibility": "доступность",
    "accessible": "доступный",
    "disability": "инвалидность",
    "inclusive": "инклюзивный",
    "visualization": "визуализация",
    "visual": "визуальный",
    "search": "поиск",
    "query": "запрос",
    "information": "информация",
    "data": "данные",
    "model": "модель",
    "models": "модели",
    "modeling": "моделирование",
    "analysis": "анализ",
    "study": "исследование",
    "studies": "исследования",
    "research": "исследование",
    "evaluation": "оценка",
    "method": "метод",
    "methods": "методы",
    "framework": "рамка",
    "theory": "теория",
    "practice": "практика",
    "history": "история",
    "past": "прошлое",
    "present": "настоящее",
    "mobile": "мобильный",
    "wearable": "носимый",
    "sensor": "сенсор",
    "sensors": "сенсоры",
    "input": "ввод",
    "gesture": "жест",
    "gestures": "жесты",
    "touch": "касание",
    "haptic": "тактильный",
    "haptics": "осязание",
    "tangible": "осязаемый",
    "embodied": "воплощённый",
    "body": "тело",
    "bodies": "тела",
    "gaze": "взгляд",
    "eye": "глаз",
    "speech": "речь",
    "voice": "голос",
    "sound": "звук",
    "audio": "аудио",
    "game": "игра",
    "games": "игры",
    "play": "игра",
    "playful": "игровой",
    "robot": "робот",
    "robots": "роботы",
    "robotics": "робототехника",
    "vehicle": "транспорт",
    "vehicles": "транспорт",
    "driving": "вождение",
    "autonomous": "автономный",
    "automated": "автоматизированный",
    "learning": "обучение",
    "education": "образование",
    "educational": "образовательный",
    "children": "дети",
    "child": "ребёнок",
    "family": "семья",
    "families": "семьи",
    "aging": "старение",
    "elderly": "пожилые",
    "women": "женщины",
    "gender": "гендер",
    "feminist": "феминистский",
    "critical": "критический",
    "sustainable": "устойчивый",
    "environment": "среда",
    "climate": "климат",
    "energy": "энергия",
    "home": "дом",
    "domestic": "домашний",
    "urban": "городской",
    "city": "город",
    "africa": "Африка",
    "global": "глобальный",
    "development": "развитие",
    "digital": "цифровой",
    "online": "онлайн",
    "internet": "интернет",
    "web": "веб",
    "website": "сайт",
    "facebook": "Facebook",
    "wikipedia": "Википедия",
    "github": "GitHub",
    "google": "Google",
    "microsoft": "Microsoft",
    "ai": "ИИ",
    "hci": "HCI",
    "cscw": "CSCW",
    "ux": "UX",
    "ui": "UI",
    "vr": "VR",
    "ar": "AR",
    "xr": "XR",
    "ml": "ML",
    "llm": "LLM",
    "goms": "GOMS",
    "toolkit": "инструментарий",
    "tool": "инструмент",
    "tools": "инструменты",
    "prototype": "прототип",
    "prototyping": "прототипирование",
    "sketching": "скетчинг",
    "programming": "программирование",
    "software": "ПО",
    "hardware": "аппаратура",
    "device": "устройство",
    "devices": "устройства",
    "display": "дисплей",
    "displays": "дисплеи",
    "screen": "экран",
    "keyboard": "клавиатура",
    "mouse": "мышь",
    "pen": "перо",
    "paper": "бумага",
    "book": "книга",
    "survey": "обзор",
    "review": "обзор",
    "overview": "обзор",
    "introduction": "введение",
    "principles": "принципы",
    "guidelines": "рекомендации",
    "challenges": "вызовы",
    "opportunities": "возможности",
    "benefits": "польза",
    "cost": "стоимость",
    "costs": "издержки",
    "performance": "производительность",
    "behavior": "поведение",
    "behaviour": "поведение",
    "attention": "внимание",
    "memory": "память",
    "cognition": "познание",
    "cognitive": "когнитивный",
    "psychology": "психология",
    "emotion": "эмоция",
    "emotions": "эмоции",
    "affective": "аффективный",
    "experience": "опыт",
    "experiences": "опыты",
    "presence": "присутствие",
    "avatar": "аватар",
    "avatars": "аватары",
    "immersion": "погружение",
    "immersive": "иммерсивный",
    "multimodal": "мультимодальный",
    "context": "контекст",
    "aware": "осведомлённый",
    "awareness": "осведомлённость",
    "communication": "коммуникация",
    "conversation": "разговор",
    "conversational": "разговорный",
    "agent": "агент",
    "agents": "агенты",
    "recommendation": "рекомендация",
    "personalization": "персонализация",
    "personalized": "персонализированный",
    "adaptive": "адаптивный",
    "intelligent": "интеллектуальный",
    "smart": "умный",
    "ambient": "средовой",
    "organic": "органический",
    "physical": "физический",
    "digitalization": "цифровизация",
    "moderation": "модерация",
    "misinformation": "дезинформация",
    "disinformation": "дезинформация",
    "crisis": "кризис",
    "emergency": "чрезвычайная ситуация",
    "remote": "удалённый",
    "distance": "расстояние",
    "video": "видео",
    "telepresence": "телеприсутствие",
    "fabricating": "изготовление",
    "printing": "печать",
    "maker": "мейкер",
    "diy": "DIY",
    "open": "открытый",
    "source": "исходный",
    "what": "что",
    "how": "как",
    "why": "почему",
    "when": "когда",
    "where": "где",
    "who": "кто",
    "can": "может",
    "do": "",
    "does": "",
    "is": "",
    "are": "",
    "was": "",
    "were": "",
    "be": "",
    "been": "",
    "being": "",
    "its": "его",
    "their": "их",
    "our": "наш",
    "your": "ваш",
    "this": "это",
    "that": "то",
    "these": "эти",
    "those": "те",
    "we": "мы",
    "it": "это",
    "not": "не",
    "no": "нет",
    "yes": "да",
}

KEEP = {
    "chi", "uist", "assets", "tochi", "cscw", "hci", "ux", "ui", "vr", "ar", "xr",
    "ai", "ml", "llm", "goms", "epic", "lsa", "ir", "infovis", "ubicomp", "nime",
    "www", "ieee", "acm", "mit", "pair", "jaws", "html", "css", "xml", "rdfa",
    "xforms", "github", "facebook", "google", "microsoft", "apple", "kinect",
    "wikipedia", "movielens", "grouplens", "vizwiz", "sidewalk", "phidgets",
    "silk", "teddy", "alice", "xanadu", "fitts",
}

OVERRIDES: dict[str, str] = {
    "The benefits of Facebook “friends:” Social capital and college students’ use of online social network sites":
        "Польза Facebook-«друзей»: социальный капитал и то, как студенты пользуются сайтами социальных сетей",
    "Where the Action Is": "Там, где действие",
    "The Psychology of Human-Computer Interaction": "Психология человеко-компьютерного взаимодействия",
    "The Myth of the Paperless Office": "Миф о безбумажном офисе",
    "Usability Engineering": "Инженерия удобства использования",
    "Designing with the Mind in Mind": "Дизайн с умом о сознании",
    "Sketching User Experiences": "Скетчинг пользовательского опыта",
    "The Last Lecture": "Последняя лекция",
    "Tangible Bits": "Осязаемые биты",
    "Groupware and social dynamics: eight challenges for developers":
        "Groupware и социальная динамика: восемь вызовов для разработчиков",
    "Distance Matters": "Расстояние имеет значение",
    "Information Foraging": "Информационное фуражирование",
    "A Solution to Plato's Problem: The Latent Semantic Analysis Theory of Acquisition, Induction, and Representation of Knowledge":
        "Решение задачи Платона: латентно-семантический анализ усвоения, индукции и представления знания",
    "How Games Move Us": "Как игры нас трогают",
    "Geek Heresy": "Ересь гика",
    "Humanistic HCI": "Гуманитарный HCI",
    "Adversarial Design": "Состязательный дизайн",
    "Experience Design": "Дизайн опыта",
    "Attention Span": "Продолжительность внимания",
    "GUI Bloopers 2.0": "Промахи GUI 2.0",
    "Computers as Theatre": "Компьютеры как театр",
    "The Design of Everyday Things": "Дизайн привычных вещей",
    "The Nurnberg Funnel": "Нюрнбергская воронка",
    "Through the Interface": "Сквозь интерфейс",
    "Designing with the Body: Somaesthetic Interaction Design":
        "Дизайн с телом: сомаэстетическое взаимодействие",
    "Technology as Experience": "Технология как опыт",
    "Contextual Design": "Контекстный дизайн",
    "Cultural Probes": "Культурные зонды",
    "Dark Patterns at Scale": "Тёмные паттерны в масштабе",
    "Should You Believe Wikipedia?": "Стоит ли верить Википедии?",
}


PAPER_CACHE_PATH = Path(__file__).resolve().parents[1] / "data" / "papers-ru-cache.json"

_paper_cache: dict[str, str] | None = None


def load_paper_cache() -> dict[str, str]:
    global _paper_cache
    if _paper_cache is None:
        if PAPER_CACHE_PATH.exists():
            _paper_cache = json.loads(PAPER_CACHE_PATH.read_text())
        else:
            _paper_cache = {}
    return _paper_cache


def save_paper_cache() -> None:
    if _paper_cache is None:
        return
    PAPER_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    PAPER_CACHE_PATH.write_text(json.dumps(_paper_cache, ensure_ascii=False, indent=2))


def _google_translate(text: str) -> str | None:
    url = (
        "https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=ru&dt=t&q="
        + urllib.parse.quote(text[:450])
    )
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8", "replace"))
        parts = [seg[0] for seg in (data[0] or []) if seg and seg[0]]
        out = "".join(parts).strip()
        return out or None
    except Exception:
        return None


def translate_titles(titles: list[str]) -> dict[str, str]:
    cache = load_paper_cache()
    unique = []
    seen = set()
    for t in titles:
        t = re.sub(r"\s+", " ", t).strip()
        if t and t not in cache and t not in OVERRIDES and t not in seen:
            unique.append(t)
            seen.add(t)
    print(f"  need network for {len(unique)} titles (cached {len(cache)})")
    if unique:
        done = 0
        with ThreadPoolExecutor(max_workers=12) as pool:
            futs = {pool.submit(_google_translate, t): t for t in unique}
            for fut in as_completed(futs):
                src = futs[fut]
                ru = fut.result()
                cache[src] = ru if ru else _glossary_translate(src)
                done += 1
                if done % 80 == 0:
                    save_paper_cache()
                    print(f"  {done}/{len(unique)}")
        save_paper_cache()
    out = {}
    for t in titles:
        raw = re.sub(r"\s+", " ", t).strip()
        if raw in OVERRIDES:
            out[t] = OVERRIDES[raw]
        else:
            out[t] = cache.get(raw, _glossary_translate(raw))
    return out


def _glossary_translate(raw: str) -> str:
    work = raw.lower()
    slots: list[str] = []
    for en, ru in sorted(PHRASES, key=lambda x: -len(x[0])):
        if en in work:
            token = f"«{len(slots)}»"
            work = work.replace(en, token)
            slots.append(ru)

    tokens = re.findall(r"«\d+»|[a-z0-9][a-z0-9'’+\-]*|[^\s]", work, flags=re.I)
    out: list[str] = []
    for tok in tokens:
        if re.fullmatch(r"«(\d+)»", tok):
            out.append(slots[int(tok[1:-1])])
            continue
        low = tok.lower()
        if low in KEEP or tok.isupper() or re.fullmatch(r"\d+", tok):
            out.append(tok.upper() if low in KEEP and len(tok) <= 5 else tok)
            continue
        if low in WORDS:
            w = WORDS[low]
            if w:
                out.append(w)
            continue
        out.append(tok)

    text = " ".join(out)
    text = re.sub(r"\s+([,.:;!?])", r"\1", text)
    text = re.sub(r"\(\s+", "(", text)
    text = re.sub(r"\s+\)", ")", text)
    text = re.sub(r"\s{2,}", " ", text).strip(" ,;:-")
    if text:
        text = text[0].upper() + text[1:]
    return text or raw
