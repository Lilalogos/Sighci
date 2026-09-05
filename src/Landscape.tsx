import { useEffect, useRef, useState } from "react";
import type { Cluster, MapLabel, Person, SectorFilter } from "./types";
import { findClusterForTopic, topicLabel, topicRu } from "./topicRu";
import { clusterPrimary, clusterSecondary, useLocale } from "./i18n";

type Pt = { x: number; y: number };

function hull(points: Pt[]): Pt[] {
  const pts = [...points].sort((a, b) => a.x - b.x || a.y - b.y);
  if (pts.length <= 2) return pts;
  const cross = (o: Pt, a: Pt, b: Pt) =>
    (a.x - o.x) * (b.y - o.y) - (a.y - o.y) * (b.x - o.x);
  const lower: Pt[] = [];
  for (const p of pts) {
    while (lower.length >= 2 && cross(lower[lower.length - 2], lower[lower.length - 1], p) <= 0) {
      lower.pop();
    }
    lower.push(p);
  }
  const upper: Pt[] = [];
  for (let i = pts.length - 1; i >= 0; i--) {
    const p = pts[i];
    while (upper.length >= 2 && cross(upper[upper.length - 2], upper[upper.length - 1], p) <= 0) {
      upper.pop();
    }
    upper.push(p);
  }
  lower.pop();
  upper.pop();
  return lower.concat(upper);
}

function expand(points: Pt[], pad: number): Pt[] {
  if (!points.length) return points;
  const cx = points.reduce((s, p) => s + p.x, 0) / points.length;
  const cy = points.reduce((s, p) => s + p.y, 0) / points.length;
  return points.map((p) => ({
    x: cx + (p.x - cx) * pad,
    y: cy + (p.y - cy) * pad,
  }));
}

function matches(person: Person, q: string): boolean {
  if (!q) return true;
  const blob = [
    person.name,
    person.nameRu,
    person.university,
    person.topicsTable,
    person.clusterLabel,
    ...person.topicsScholar,
    ...person.topicsScholar.map(topicRu),
    ...(person.tags ?? []),
    ...(person.tags ?? []).map(topicRu),
    ...person.awards.map((a) => a.label),
  ]
    .join(" ")
    .toLowerCase();
  return blob.includes(q);
}

function hasAnyTag(person: Person, tags: string[]): boolean {
  if (!tags.length) return true;
  const have = new Set((person.tags ?? []).map((item) => item.toLowerCase()));
  return tags.some((tag) => have.has(tag.toLowerCase()));
}

type Props = {
  people: Person[];
  clusters: Cluster[];
  mapLabels: MapLabel[];
  selectedId: string | null;
  clusterFilters: string[];
  tagFilters: string[];
  sectorFilter: SectorFilter;
  query: string;
  onSelect: (id: string | null) => void;
  onToggleCluster: (id: string) => void;
  onToggleTag: (tag: string) => void;
};

const SIZE = 1000;
const PAD = 48;

export default function Landscape({
  people,
  clusters,
  mapLabels,
  selectedId,
  clusterFilters,
  tagFilters,
  sectorFilter,
  query,
  onSelect,
  onToggleCluster,
  onToggleTag,
}: Props) {
  const { locale, t } = useLocale();
  const svgRef = useRef<SVGSVGElement>(null);
  const drag = useRef<{ x: number; y: number; moved: boolean } | null>(null);
  const panMoved = useRef(false);
  const [view, setView] = useState({ x: -PAD, y: -PAD, w: SIZE + PAD * 2, h: SIZE + PAD * 2 });
  const viewRef = useRef(view);
  viewRef.current = view;
  const [hover, setHover] = useState<{ person: Person; left: number; top: number } | null>(null);
  const [dragging, setDragging] = useState(false);
  const color = Object.fromEntries(clusters.map((c) => [c.id, c.color]));
  const q = query.trim().toLowerCase();

  const regions = clusters
    .map((cluster) => {
      const members = people.filter(
        (p) =>
          p.cluster === cluster.id &&
          (sectorFilter === "all" || p.sector === sectorFilter),
      );
      const pts = members.map((p) => ({ x: p.x * SIZE, y: p.y * SIZE }));
      const shape = expand(hull(pts), 1.35);
      const cx = pts.reduce((s, p) => s + p.x, 0) / (pts.length || 1);
      const cy = pts.reduce((s, p) => s + p.y, 0) / (pts.length || 1);
      return { cluster, shape, cx, cy, n: members.length };
    })
    .filter((r) => r.n > 0);

  function clientToSvg(clientX: number, clientY: number) {
    const svg = svgRef.current;
    if (!svg) return { x: 0, y: 0 };
    const pt = svg.createSVGPoint();
    pt.x = clientX;
    pt.y = clientY;
    const ctm = svg.getScreenCTM();
    if (!ctm) return { x: 0, y: 0 };
    const loc = pt.matrixTransform(ctm.inverse());
    return { x: loc.x, y: loc.y };
  }

  function hintPos(clientX: number, clientY: number) {
    const svg = svgRef.current;
    if (!svg) return { left: 0, top: 0 };
    const rect = svg.getBoundingClientRect();
    return { left: clientX - rect.left, top: clientY - rect.top };
  }

  useEffect(() => {
    const svg = svgRef.current;
    if (!svg) return;
    const onWheel = (e: WheelEvent) => {
      e.preventDefault();
      const v = viewRef.current;
      const factor = e.deltaY < 0 ? 0.88 : 1.14;
      const nextW = Math.min(SIZE * 2.4, Math.max(220, v.w * factor));
      const nextH = (nextW * v.h) / v.w;
      const p = clientToSvg(e.clientX, e.clientY);
      setView({
        x: p.x - ((p.x - v.x) / v.w) * nextW,
        y: p.y - ((p.y - v.y) / v.h) * nextH,
        w: nextW,
        h: nextH,
      });
    };
    svg.addEventListener("wheel", onWheel, { passive: false });
    return () => svg.removeEventListener("wheel", onWheel);
  }, []);

  return (
    <>
      <svg
        ref={svgRef}
        className={dragging ? "canvas dragging" : "canvas"}
        viewBox={`${view.x} ${view.y} ${view.w} ${view.h}`}
        role="img"
        aria-label={t.mapAria}
        onPointerDown={(e) => {
          (e.currentTarget as SVGSVGElement).setPointerCapture(e.pointerId);
          panMoved.current = false;
          drag.current = { x: e.clientX, y: e.clientY, moved: false };
        }}
        onPointerMove={(e) => {
          if (!drag.current) return;
          const dx = e.clientX - drag.current.x;
          const dy = e.clientY - drag.current.y;
          if (!drag.current.moved && dx * dx + dy * dy < 25) return;
          drag.current.moved = true;
          panMoved.current = true;
          setDragging(true);
          drag.current.x = e.clientX;
          drag.current.y = e.clientY;
          const svg = svgRef.current;
          if (!svg) return;
          const rect = svg.getBoundingClientRect();
          setView((v) => ({
            ...v,
            x: v.x - (dx * v.w) / rect.width,
            y: v.y - (dy * v.h) / rect.height,
          }));
        }}
        onPointerUp={(e) => {
          const wasDrag = drag.current?.moved;
          drag.current = null;
          setDragging(false);
          if (!wasDrag && (e.target as Element).tagName === "svg") onSelect(null);
        }}
        onPointerLeave={() => setHover(null)}
      >
        {regions.map(({ cluster, shape, cx, cy }) => {
          const on = clusterFilters.length === 0 || clusterFilters.includes(cluster.id);
          return (
            <g
              key={cluster.id}
              className={clusterFilters.includes(cluster.id) ? "cluster-hit on" : "cluster-hit"}
              opacity={on ? 1 : 0.18}
              onClick={(e) => {
                e.stopPropagation();
                if (panMoved.current) return;
                onToggleCluster(cluster.id);
              }}
            >
              {shape.length >= 3 ? (
                <polygon
                  className="cluster-fill"
                  points={shape.map((p) => `${p.x},${p.y}`).join(" ")}
                  fill={cluster.color}
                  stroke={cluster.color}
                  strokeOpacity={clusterFilters.includes(cluster.id) ? 0.7 : 0.35}
                />
              ) : (
                <circle className="cluster-fill" cx={cx} cy={cy} r={48} fill={cluster.color} />
              )}
            </g>
          );
        })}

        {people.map((person) => {
          const x = person.x * SIZE;
          const y = person.y * SIZE;
          const r = 5 + person.awards.length * 1.4;
          const clusterOk =
            clusterFilters.length === 0 || clusterFilters.includes(person.cluster);
          const tagOk = tagFilters.length === 0 || hasAnyTag(person, tagFilters);
          const topicOk =
            clusterFilters.length === 0 && tagFilters.length === 0
              ? true
              : (clusterFilters.length > 0 && clusterOk) || (tagFilters.length > 0 && tagOk);
          const active =
            matches(person, q) &&
            topicOk &&
            (sectorFilter === "all" || person.sector === sectorFilter);
          const selected = person.id === selectedId;
          const fill = color[person.cluster] ?? "#9aa3b0";
          const corporate = person.sector === "corporate";
          return (
            <g
              key={person.id}
              className={active ? "node" : "node dim"}
              transform={`translate(${x} ${y})`}
              onPointerDown={(e) => e.stopPropagation()}
              onClick={(e) => {
                e.stopPropagation();
                onSelect(person.id);
              }}
              onPointerMove={(e) => {
                e.stopPropagation();
                setHover({ person, ...hintPos(e.clientX, e.clientY) });
              }}
            >
              {selected ? (
                <circle r={r + 6} fill="none" stroke="var(--accent)" strokeWidth={2} />
              ) : null}
              {person.deceased ? (
                <polygon
                  points={`0,${-r - 1} ${r + 1},0 0,${r + 1} ${-r - 1},0`}
                  fill={fill}
                  fillOpacity={0.35}
                  stroke={fill}
                  strokeWidth={1.6}
                  strokeDasharray="3 2"
                />
              ) : corporate ? (
                <rect
                  x={-r}
                  y={-r}
                  width={r * 2}
                  height={r * 2}
                  rx={1.5}
                  fill={fill}
                  stroke="#10131a"
                  strokeWidth={1}
                />
              ) : (
                <circle r={r} fill={fill} stroke="#10131a" strokeWidth={1} />
              )}
            </g>
          );
        })}

        {mapLabels.map((item) => {
          const linked = findClusterForTopic(item.label, clusters);
          const active = linked
            ? clusterFilters.includes(linked.id)
            : tagFilters.some((tag) => tag.toLowerCase() === item.id);
          const anyTopic = clusterFilters.length > 0 || tagFilters.length > 0;
          const fs = 10 + Math.min(6, item.count / 3);
          return (
            <g
              key={item.id}
              className={
                active ? "interest-label active" : anyTopic ? "interest-label dim" : "interest-label"
              }
              transform={`translate(${item.x * SIZE} ${item.y * SIZE})`}
              onPointerDown={(e) => e.stopPropagation()}
              onClick={(e) => {
                e.stopPropagation();
                if (linked) onToggleCluster(linked.id);
                else onToggleTag(item.label);
              }}
            >
              <text textAnchor="middle" fontSize={fs}>
                {topicLabel(item.label, locale)}
              </text>
            </g>
          );
        })}

        {regions.map(({ cluster, cx, cy }) => {
          const on = clusterFilters.includes(cluster.id);
          return (
            <g
              key={`${cluster.id}-label`}
              className={on ? "cluster-name on" : "cluster-name"}
              opacity={clusterFilters.length === 0 || on ? 1 : 0.28}
              onPointerDown={(e) => e.stopPropagation()}
              onClick={(e) => {
                e.stopPropagation();
                onToggleCluster(cluster.id);
              }}
            >
              <text
                className="cluster-label"
                x={cx}
                y={clusterSecondary(cluster, locale) ? cy - 7 : cy}
                textAnchor="middle"
              >
                {clusterPrimary(cluster, locale)}
              </text>
              {clusterSecondary(cluster, locale) ? (
                <text className="cluster-label-en" x={cx} y={cy + 10} textAnchor="middle">
                  ({clusterSecondary(cluster, locale)})
                </text>
              ) : null}
            </g>
          );
        })}
      </svg>
      {hover ? (
        <div className="hint" style={{ left: hover.left, top: hover.top }}>
          <b>
            {hover.person.name}
            {locale === "ru" && hover.person.nameRu ? ` · ${hover.person.nameRu}` : ""}
            {hover.person.deceased ? ` · ${t.deceasedShort}` : ""}
          </b>
          <span>
            {hover.person.university} ·{" "}
            {clusterPrimary(
              clusters.find((c) => c.id === hover.person.cluster) ?? {
                id: hover.person.cluster,
                label: hover.person.clusterLabel,
                color: "",
                count: 0,
              },
              locale,
            )}{" "}
            · {hover.person.sector === "corporate" ? t.industry : t.academia}
          </span>
        </div>
      ) : null}
    </>
  );
}
