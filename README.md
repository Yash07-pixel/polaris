# MolGenix

**AI-powered biomedical drug discovery prototype**

MolGenix is a polished MVP/demo platform that turns plain-English biomedical queries into ranked mock drug candidates. It combines NLP target identification, pre-seeded molecule ranking, RDKit structure rendering, ADMET-style visualization, and downloadable PDF reports in a single hackathon-ready workflow.

> Built for hackathons, portfolios, AI engineering showcases, and biomedical AI demonstrations.

![Python](https://img.shields.io/badge/Python-3.13-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-API-009688)
![RDKit](https://img.shields.io/badge/RDKit-Cheminformatics-green)
![Gemini API](https://img.shields.io/badge/Gemini-AI-orange)
![License](https://img.shields.io/badge/License-MIT-lightgrey)


## Features

- Natural language biomedical query parsing
- AI-assisted target identification with Gemini
- Offline keyword fallback logic for reliable demos
- Controlled mock target database with exactly 5 predefined targets
- Ranked mock molecular candidates from pre-seeded data
- RDKit molecule structure rendering as local PNG images
- ADMET traffic-light visualization
- Safe/toxic/problematic molecule labeling
- Interactive vanilla JavaScript frontend
- Molecule detail modal with SMILES copy support
- AI-generated scientific report summaries
- Multi-page PDF report generation with ReportLab
- Docker support for single-command startup
- SQLite-only local persistence

---

## How It Works

1. User enters a plain-English biomedical query.
2. Gemini identifies one of the predefined demo targets.
3. If Gemini is unavailable, deterministic keyword fallback is used.
4. Mock candidates are retrieved from the local SQLite database.
5. Molecules are ranked using simulated docking, QED, and ADMET signals.
6. RDKit-rendered structures and ADMET indicators are displayed in the UI.
7. A multi-page PDF report is generated and downloaded.

```text
User Query
   |
   v
Gemini NLP Layer
   |
   v
Target Identification
   |
   v
Mock Molecule Database
   |
   v
ADMET + Simulated Docking Pipeline
   |
   v
Frontend Visualization
   |
   v
PDF Report
```

---

## Tech Stack

| Layer | Technology |
| ----- | ---------- |
| API Framework | FastAPI |
| ORM | SQLAlchemy 2.x |
| Database | SQLite |
| Cheminformatics | RDKit |
| AI/NLP | Google Gemini API |
| Reports | ReportLab |
| Frontend | HTML, CSS, Vanilla JavaScript |
| Deployment | Docker, Docker Compose |
| Testing | Pytest |

---

## Project Structure

```text
molgenix/
├── app/
│   ├── ml/
│   │   └── admet_predictor.py
│   ├── mock_data/
│   │   ├── molecules.py
│   │   ├── targets.py
│   │   └── validation.py
│   ├── models/
│   │   ├── discovery_report.py
│   │   ├── discovery_session.py
│   │   ├── drug_target.py
│   │   └── molecule.py
│   ├── routers/
│   │   ├── health.py
│   │   ├── molecules.py
│   │   ├── reports.py
│   │   └── sessions.py
│   ├── schemas/
│   ├── services/
│   │   ├── nlp_service.py
│   │   └── report_service.py
│   ├── utils/
│   │   ├── molecule_image.py
│   │   └── pdf_builder.py
│   ├── config.py
│   ├── database.py
│   ├── main.py
│   └── seed.py
├── js/
│   ├── api.js
│   ├── app.js
│   └── ui.js
├── styles/
│   ├── components.css
│   └── main.css
├── static/
│   ├── brand/
│   ├── molecules/
│   └── reports/
├── tests/
├── index.html
├── Dockerfile
├── docker-compose.yml
├── Makefile
└── requirements.txt
```

---

## Installation

### Clone Repo

```bash
git clone https://github.com/Yash07-pixel/polaris.git
cd polaris
```

### Backend Setup

```bash
python -m pip install -r requirements.txt
```

### Run Server

```bash
uvicorn app.main:app --reload
```

### Open Frontend

```text
http://localhost:8000/app
```

The root URL also serves the frontend:

```text
http://localhost:8000/
```

### Docker Setup

```bash
docker-compose up --build
```

Then open:

```text
http://localhost:8000/
```

---

## Environment Variables

Create a `.env` file using this example:

```env
DATABASE_URL=sqlite:///./molgenix.db
GEMINI_API_KEY=your_key_here
DEBUG=True
```

Gemini is optional for demo use. If no API key is configured, MolGenix uses deterministic keyword fallback for target identification and deterministic fallback text for reports.

---

## API Overview

| Method | Endpoint | Purpose |
| ------ | -------- | ------- |
| GET | `/health` | Basic health check |
| GET | `/health/ready` | Readiness check with target and molecule counts |
| POST | `/api/v1/sessions/` | Create a discovery session from a biomedical query |
| GET | `/api/v1/sessions/` | List discovery sessions |
| GET | `/api/v1/sessions/{session_id}` | Fetch one discovery session |
| GET | `/api/v1/molecules/` | List ranked seeded molecules |
| GET | `/api/v1/molecules/{id}` | Fetch molecule detail |
| GET | `/api/v1/molecules/session/{session_id}` | Fetch ranked molecules for a session target |
| POST | `/api/v1/reports/generate` | Generate a simulated research report |
| GET | `/api/v1/reports/{id}/download` | Download report PDF |
| GET | `/api/v1/reports/session/{session_id}` | List reports for a session |

---

## Example Workflow

Input:

```text
Find EGFR inhibitors for lung cancer
```

Output:

- Target identified as EGFR
- Mock molecules ranked by simulated score
- ADMET signals shown as traffic-light indicators
- Toxic/problematic molecules clearly marked
- PDF report generated for download

Example session response:

```json
{
  "id": 1,
  "name": "Find EGFR inhibitors for lung cancer",
  "query": "Find EGFR inhibitors for lung cancer",
  "objective": "Find EGFR inhibitors for lung cancer",
  "status": "COMPLETE",
  "identified_target_name": "Epidermal Growth Factor Receptor",
  "confidence_score": 0.75,
  "molecules_generated": 8,
  "molecules_passed_filter": 5,
  "failure_reason": null,
  "created_at": "2026-06-12T10:00:00",
  "updated_at": "2026-06-12T10:00:00"
}
```

Example molecule response:

```json
{
  "id": 1,
  "target_name": "Epidermal Growth Factor Receptor",
  "rank": 1,
  "name": "MGX-EGFR-001",
  "image_path": "static/molecules/1_mgx-egfr-001.png",
  "docking_score": -9.4,
  "qed_score": 0.518,
  "is_toxic": false,
  "lipinski_pass": true,
  "is_filtered": false
}
```

---

## Screenshots

### Hero UI

![Hero UI](./docs/screenshots/hero.png)

### Molecule Cards

![Molecule Cards](./docs/screenshots/molecule-cards.png)

### Report Generation

![Report Generation](./docs/screenshots/report-generation.png)

### PDF Preview

![PDF Preview](./docs/screenshots/pdf-preview.png)

---

## Testing

Run the test suite:

```bash
pytest
```

The tests cover:

- Health and readiness endpoints
- Session creation
- Target identification
- Molecule retrieval
- Filtering and sorting behavior
- Report generation
- PDF download
- Static frontend serving
- Mock-data validation invariants

---

## Roadmap

- Real molecular docking integration
- 3D protein and binding-pocket visualization
- Molecular generation workflows
- Cloud deployment templates
- Authentication and saved workspaces
- Multi-target comparison workflows
- Experiment history dashboards

---

## Disclaimer

> **MolGenix is a prototype/demo project only.**
>
> All targets, molecules, docking scores, ADMET values, rankings, and reports are mock or simulated. This project is not intended for medical use, clinical decision-making, regulatory work, pharmaceutical development, diagnosis, treatment selection, or real-world biomedical research conclusions.

---

## License

MIT License.

---

## Credits

MolGenix is built with:

- [FastAPI](https://fastapi.tiangolo.com/)
- [RDKit](https://www.rdkit.org/)
- [Google Gemini](https://ai.google.dev/)
- [ReportLab](https://www.reportlab.com/)
- [SQLAlchemy](https://www.sqlalchemy.org/)

