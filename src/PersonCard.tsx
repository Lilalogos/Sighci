import { useState } from "react";
import type { Person } from "./types";
import { deathNoteFor, useLocale } from "./i18n";
import { topicLabel } from "./topicRu";

function LinkRow({ href, label }: { href: string | null; label: string }) {
  if (!href) return null;
  const url = href.startsWith("@") ? `https://x.com/${href.slice(1)}` : href;
  return (
    <a href={url} target="_blank" rel="noreferrer">
      {label}
    </a>
  );
}

function initials(name: string) {
  return name
    .split(/\s+/)
    .filter((w) => /[A-Za-zА-Яа-яЁё]/.test(w) && !w.startsWith("("))
    .slice(0, 2)
    .map((w) => w.replace(/[^A-Za-zА-Яа-яЁё]/g, "")[0])
    .join("")
    .toUpperCase();
}

export default function PersonCard({
  person,
  onClose,
  onTag,
  topicOn,
}: {
  person: Person;
  onClose: () => void;
  onTag?: (tag: string) => void;
  topicOn?: (tag: string) => boolean;
}) {
  const { locale, t } = useLocale();
  const [imgFailed, setImgFailed] = useState(false);
  const showPhoto = person.portraitUrl && !imgFailed;
  const deathNote = deathNoteFor(person, locale);
  const sectorLabel =
    person.sector === "academic"
      ? t.sectorAcademic
      : person.sector === "corporate"
        ? t.sectorCorporate
        : t.sectorUnknown;

  return (
    <aside className="card">
      <button className="card-close" onClick={onClose} aria-label={t.close}>
        ×
      </button>
      <div className="card-head">
        {showPhoto ? (
          <img
            className="portrait"
            src={person.portraitUrl!}
            alt=""
            referrerPolicy="no-referrer"
            onError={() => setImgFailed(true)}
          />
        ) : (
          <div className="portrait initials">{initials(person.name)}</div>
        )}
        <div>
          <h2>
            {person.name}
            {locale === "ru" && person.nameRu && person.nameRu !== person.name ? (
              <span className="trans"> · {person.nameRu}</span>
            ) : null}
          </h2>
          {person.deceased ? (
            <div className="badge">
              {t.deceasedBadge}
              {person.deathYear ? ` · ${person.deathYear}` : deathNote ? ` · ${deathNote}` : ""}
            </div>
          ) : null}
        </div>
      </div>

      {person.university ? <p className="meta">{person.university}</p> : null}
      {person.affiliation && person.affiliation !== person.university ? (
        <p className="meta">{person.affiliation}</p>
      ) : null}
      <p className="meta">{sectorLabel}</p>
      {person.citedBy ? <p className="meta">{t.citations(person.citedBy)}</p> : null}

      <div className="section">
        <h3>{t.awards}</h3>
        <ul className="awards">
          {person.awards.map((a) => (
            <li key={a.label}>{a.label}</li>
          ))}
        </ul>
      </div>

      <div className="section">
        <h3>{t.topics}</h3>
        {person.topicsTable ? (
          <p className="meta">{person.topicsTable}</p>
        ) : (
          <p className="empty-note">{t.noTableTopics}</p>
        )}
        {person.topicsScholar.length ? (
          <div className="pills" style={{ marginTop: 10 }}>
            {person.topicsScholar.map((tag) => (
              <button
                key={tag}
                type="button"
                className={topicOn?.(tag) ? "active" : ""}
                aria-pressed={topicOn?.(tag) ?? false}
                onClick={() => onTag?.(tag)}
              >
                {topicLabel(tag, locale)}
              </button>
            ))}
          </div>
        ) : (
          <p className="empty-note">{t.noScholarTags}</p>
        )}
      </div>

      {person.papersScholar.length ? (
        <div className="section">
          <h3>{t.papers}</h3>
          <ul className="awards papers">
            {person.papersScholar.slice(0, 6).map((paper) => {
              const label = locale === "ru" ? paper.titleRu || paper.title : paper.title;
              return (
                <li key={paper.title}>
                  {paper.url ? (
                    <a href={paper.url} target="_blank" rel="noreferrer">
                      {label}
                    </a>
                  ) : (
                    label
                  )}
                </li>
              );
            })}
          </ul>
        </div>
      ) : null}

      <div className="section">
        <h3>{t.links}</h3>
        <div className="links">
          <LinkRow href={person.links.website} label={t.website} />
          <LinkRow href={person.links.scholar} label="Google Scholar" />
          <LinkRow href={person.links.dblp} label="DBLP" />
          <LinkRow href={person.links.linkedin} label="LinkedIn" />
          <LinkRow href={person.links.twitter} label="X / Twitter" />
          {!person.links.website &&
          !person.links.scholar &&
          !person.links.dblp &&
          !person.links.linkedin &&
          !person.links.twitter ? (
            <p className="empty-note">{t.noLinks}</p>
          ) : null}
        </div>
      </div>
    </aside>
  );
}
