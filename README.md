# SIGCHI HCI topic landscape

Interactive map of **297 SIGCHI award recipients** (1998–2026), arranged by research topic rather than geography.

Live topics come from the project spreadsheet plus Google Scholar interest tags and paper titles. The map is a Vite + React app.

[Русская версия README](README.ru.md)

Site: [https://lilalogos.github.io/SIGHCI_5september/](https://lilalogos.github.io/SIGHCI_5september/)

Push to `main` builds GitHub Pages via Actions (`Settings → Pages → GitHub Actions`).

## Run

```bash
npm install
npm run dev
```

Open [http://127.0.0.1:5173/](http://127.0.0.1:5173/). Use **RU / EN** in the header to switch the interface, cluster names, Scholar tags, and paper titles.

```bash
npm run build
npm run preview
```

## What you can do

- Pan and zoom the landscape; click a person for a card (affiliation, awards, Scholar tags, paper links, portrait).
- Filter by **Academy** / **Industry**. Corporate researchers stay as squares; deceased researchers are dashed diamonds.
- Click a cluster on the map or a chip in the bottom dock to highlight a topic. Click again to turn it off. Several topics can be on at once. **Clear topics** resets the selection.
- Search by name, Russian transcription, university, or topic.

## Data

Source spreadsheet (local): `SIGCHI_HCI_UX_researchers_FULL.xlsx`.

Rebuild `src/data/people.json` after changing cluster rules or caches:

```bash
npm run data
```

That script (`scripts/build_data.py`) merges the spreadsheet with a Google Scholar cache, assigns clusters, lays people out with TF–IDF + t-SNE, and translates paper titles into Russian when a cache miss needs the network.

Scholar and title-translation caches live under `data/` and are gitignored.

## Stack

- UI: Vite, React, TypeScript
- Layout / clustering: Python, pandas, scikit-learn
