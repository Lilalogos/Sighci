export type Award = {
  type: string;
  year: number | null;
  label: string;
};

export type ScholarPaper = {
  title: string;
  titleRu?: string;
  url: string | null;
};

export type Person = {
  id: string;
  name: string;
  nameRu: string;
  deceased: boolean;
  deathYear: number | null;
  deathNote: string | null;
  university: string;
  affiliation: string;
  sector: "academic" | "corporate" | "unknown";
  awards: Award[];
  topicsTable: string;
  topicsScholar: string[];
  papersScholar: ScholarPaper[];
  citedBy: number | null;
  portraitUrl: string | null;
  cluster: string;
  clusterLabel: string;
  tags: string[];
  x: number;
  y: number;
  links: {
    scholar: string | null;
    dblp: string | null;
    website: string | null;
    linkedin: string | null;
    twitter: string | null;
  };
};

export type Cluster = {
  id: string;
  label: string;
  labelEn?: string;
  color: string;
  count: number;
};

export type MapLabel = {
  id: string;
  label: string;
  x: number;
  y: number;
  count: number;
};

export type LandscapeData = {
  source: string;
  peopleCount: number;
  deceasedCount: number;
  clusters: Cluster[];
  mapLabels: MapLabel[];
  people: Person[];
};

export type SectorFilter = "all" | "academic" | "corporate";
