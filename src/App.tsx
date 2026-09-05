import { useMemo, useState } from "react";
import Landscape from "./Landscape";
import PersonCard from "./PersonCard";
import data from "./data/people.json";
import type { LandscapeData, SectorFilter } from "./types";
import { findClusterForTopic, topicLabel } from "./topicRu";
import { clusterPrimary, clusterSecondary, useLocale } from "./i18n";

const landscape = data as LandscapeData;

function toggleId(list: string[], id: string): string[] {
  return list.includes(id) ? list.filter((item) => item !== id) : [...list, id];
}

export default function App() {
  const { locale, setLocale, t } = useLocale();
  const [query, setQuery] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [clusterFilters, setClusterFilters] = useState<string[]>([]);
  const [tagFilters, setTagFilters] = useState<string[]>([]);
  const [sectorFilter, setSectorFilter] = useState<SectorFilter>("all");

  const selected = useMemo(
    () => landscape.people.find((p) => p.id === selectedId) ?? null,
    [selectedId],
  );

  const academicN = landscape.people.filter((p) => p.sector === "academic").length;
  const corporateN = landscape.people.filter((p) => p.sector === "corporate").length;
  const hasTopicFilter = clusterFilters.length > 0 || tagFilters.length > 0;

  function toggleCluster(id: string) {
    setClusterFilters((list) => toggleId(list, id));
  }

  function toggleTag(tag: string) {
    const cluster = findClusterForTopic(tag, landscape.clusters);
    if (cluster) {
      toggleCluster(cluster.id);
      return;
    }
    const key = tag.toLowerCase();
    setTagFilters((list) => {
      const exists = list.some((item) => item.toLowerCase() === key);
      return exists ? list.filter((item) => item.toLowerCase() !== key) : [...list, tag];
    });
  }

  function clearTopics() {
    setClusterFilters([]);
    setTagFilters([]);
  }

  return (
    <div className={selected ? "app" : "app no-card"}>
      <div className="map-pane">
        <div className="topbar">
          <div className="brand">
            <div className="brand-row">
              <h1>{t.title}</h1>
              <div className="lang-switch" role="group" aria-label="Language">
                <button
                  type="button"
                  className={locale === "ru" ? "active" : ""}
                  onClick={() => setLocale("ru")}
                >
                  RU
                </button>
                <button
                  type="button"
                  className={locale === "en" ? "active" : ""}
                  onClick={() => setLocale("en")}
                >
                  EN
                </button>
              </div>
            </div>
            <p>{t.subtitle(landscape.peopleCount)}</p>
            <div className="sector-switch" role="group" aria-label={t.sector}>
              <button
                type="button"
                className={sectorFilter === "all" ? "active" : ""}
                onClick={() => setSectorFilter("all")}
              >
                {t.all}
              </button>
              <button
                type="button"
                className={sectorFilter === "academic" ? "active" : ""}
                onClick={() => setSectorFilter("academic")}
              >
                {t.academy}
                <span>{academicN}</span>
              </button>
              <button
                type="button"
                className={sectorFilter === "corporate" ? "active" : ""}
                onClick={() => setSectorFilter("corporate")}
              >
                {t.corporation}
                <span>{corporateN}</span>
              </button>
            </div>
          </div>
          <input
            className="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={t.search}
          />
          {tagFilters.length ? (
            <div className="tag-filter">
              <span>{t.interests}</span>
              {tagFilters.map((tag) => (
                <button key={tag} type="button" onClick={() => toggleTag(tag)}>
                  {topicLabel(tag, locale)}
                  <b>×</b>
                </button>
              ))}
            </div>
          ) : null}
        </div>
        <div className="map-stage">
          <Landscape
            people={landscape.people}
            clusters={landscape.clusters}
            mapLabels={landscape.mapLabels ?? []}
            selectedId={selectedId}
            clusterFilters={clusterFilters}
            tagFilters={tagFilters}
            sectorFilter={sectorFilter}
            query={query}
            onSelect={setSelectedId}
            onToggleCluster={toggleCluster}
            onToggleTag={toggleTag}
          />
        </div>
        <div className="legend">
          {landscape.clusters.map((c) => (
            <button
              key={c.id}
              type="button"
              className={clusterFilters.includes(c.id) ? "active" : ""}
              aria-pressed={clusterFilters.includes(c.id)}
              onClick={() => toggleCluster(c.id)}
            >
              <i style={{ background: c.color }} />
              {clusterPrimary(c, locale)}
              {clusterSecondary(c, locale) ? <em>({clusterSecondary(c, locale)})</em> : null}
              <span style={{ color: "var(--faint)" }}>{c.count}</span>
            </button>
          ))}
          <button type="button" style={{ cursor: "default" }}>
            <i
              style={{
                background: "transparent",
                border: "1.5px dashed var(--deceased)",
                borderRadius: 0,
                transform: "rotate(45deg)",
              }}
            />
            {t.deceased}
          </button>
          {hasTopicFilter ? (
            <button type="button" className="legend-clear" onClick={clearTopics}>
              {t.clearTopics}
            </button>
          ) : null}
        </div>
      </div>
      {selected ? (
        <PersonCard
          key={selected.id}
          person={selected}
          onClose={() => setSelectedId(null)}
          onTag={toggleTag}
          topicOn={(tag) => {
            const cluster = findClusterForTopic(tag, landscape.clusters);
            if (cluster) return clusterFilters.includes(cluster.id);
            return tagFilters.some((item) => item.toLowerCase() === tag.toLowerCase());
          }}
        />
      ) : null}
    </div>
  );
}
