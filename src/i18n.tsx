import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import type { Cluster, Person } from "./types";

export type Locale = "ru" | "en";

const STORAGE = "sighci-locale";

const DEATH_NOTE_EN: Record<string, string> = {
  "20 января 2026": "20 January 2026",
  "27 декабря 2013": "27 December 2013",
  "памятная сессия CHI 2016": "CHI 2016 memorial session",
};

export const copy = {
  ru: {
    docTitle: "SIGCHI — ландшафт тем HCI",
    title: "Ландшафт HCI",
    subtitle: (people: number) => `${people} лауреатов SIGCHI`,
    sector: "Сектор",
    all: "Все",
    academy: "Академия",
    corporation: "Корпорация",
    industry: "индустрия",
    academia: "академия",
    search: "Имя, транскрипция, университет, тема…",
    interests: "Интересы",
    deceased: "Умершие",
    deceasedShort: "умер",
    deceasedBadge: "Умер",
    clearTopics: "Сбросить темы",
    close: "Закрыть",
    mapAria: "Ландшафт тем HCI",
    awards: "Награды SIGCHI",
    topics: "Темы интересов",
    noTableTopics: "В таблице нет описания.",
    noScholarTags: "Нет тегов Google Scholar (нет профиля или не удалось прочитать).",
    papers: "Работы в Google Scholar",
    links: "Ссылки",
    website: "Сайт",
    noLinks: "Ссылок нет.",
    citations: (n: number) => `Google Scholar: ${n.toLocaleString("ru-RU")} цитирований`,
    sectorUnknown: "Сектор не указан",
    sectorAcademic: "Академия",
    sectorCorporate: "Индустрия",
  },
  en: {
    docTitle: "SIGCHI — HCI topic landscape",
    title: "HCI landscape",
    subtitle: (people: number) => `${people} SIGCHI awardees`,
    sector: "Sector",
    all: "All",
    academy: "Academy",
    corporation: "Industry",
    industry: "industry",
    academia: "academia",
    search: "Name, university, topic…",
    interests: "Interests",
    deceased: "Deceased",
    deceasedShort: "deceased",
    deceasedBadge: "Deceased",
    clearTopics: "Clear topics",
    close: "Close",
    mapAria: "HCI topic landscape",
    awards: "SIGCHI awards",
    topics: "Research interests",
    noTableTopics: "No description in the spreadsheet.",
    noScholarTags: "No Google Scholar tags (missing profile or the page could not be read).",
    papers: "Google Scholar papers",
    links: "Links",
    website: "Website",
    noLinks: "No links.",
    citations: (n: number) => `Google Scholar: ${n.toLocaleString("en-US")} citations`,
    sectorUnknown: "Sector not listed",
    sectorAcademic: "Academy",
    sectorCorporate: "Industry",
  },
} as const;

export type Copy = (typeof copy)[Locale];

type Ctx = {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: Copy;
};

const LocaleContext = createContext<Ctx | null>(null);

function readStored(): Locale {
  try {
    const saved = localStorage.getItem(STORAGE);
    if (saved === "en" || saved === "ru") return saved;
  } catch {
    /* ignore */
  }
  return "ru";
}

export function LocaleProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>(readStored);

  function setLocale(next: Locale) {
    setLocaleState(next);
    try {
      localStorage.setItem(STORAGE, next);
    } catch {
      /* ignore */
    }
  }

  useEffect(() => {
    document.documentElement.lang = locale;
    document.title = copy[locale].docTitle;
  }, [locale]);

  const value = useMemo(() => ({ locale, setLocale, t: copy[locale] }), [locale]);
  return <LocaleContext.Provider value={value}>{children}</LocaleContext.Provider>;
}

export function useLocale(): Ctx {
  const ctx = useContext(LocaleContext);
  if (!ctx) throw new Error("useLocale must be used inside LocaleProvider");
  return ctx;
}

export function prettyEn(value: string): string {
  const trimmed = value.trim();
  if (!trimmed) return trimmed;
  if (/^[A-Z0-9][A-Z0-9 /+-]*$/.test(trimmed) && trimmed.length <= 12) return trimmed;
  return trimmed.charAt(0).toUpperCase() + trimmed.slice(1);
}

export function clusterPrimary(cluster: Cluster, locale: Locale): string {
  if (locale === "en") return prettyEn(cluster.labelEn || cluster.label);
  return cluster.label;
}

export function clusterSecondary(cluster: Cluster, locale: Locale): string | undefined {
  if (locale === "en") return cluster.labelEn ? cluster.label : undefined;
  return cluster.labelEn;
}

export function deathNoteFor(person: Person, locale: Locale): string | null {
  if (!person.deathNote) return null;
  if (locale === "en") return DEATH_NOTE_EN[person.deathNote] ?? person.deathNote;
  return person.deathNote;
}
