"""Integration tests for the polished MolGenix demo flow."""

from collections import Counter

from fastapi.testclient import TestClient
from rdkit import Chem

from app.curated_data.molecules import CURATED_MOLECULES
from app.curated_data.targets import CURATED_TARGETS
from app.curated_data.validation import validate_curated_data


def _create_session(client: TestClient, query: str) -> dict:
    """Create a discovery session and return the response JSON."""

    response = client.post("/api/v1/sessions/", json={"query": query})
    assert response.status_code == 201, response.text
    return response.json()


def test_curated_data_validation_invariants() -> None:
    """Validate the strict curated prototype dataset."""

    validate_curated_data()
    assert len(CURATED_TARGETS) == 5
    assert len(CURATED_MOLECULES) == 40
    counts = Counter(str(molecule["target_key"]) for molecule in CURATED_MOLECULES)
    toxic_counts = Counter(str(molecule["target_key"]) for molecule in CURATED_MOLECULES if molecule["is_toxic"])

    for target in CURATED_TARGETS:
        assert counts[target["key"]] == 8
        assert toxic_counts[target["key"]] >= 1

    for molecule in CURATED_MOLECULES:
        assert Chem.MolFromSmiles(str(molecule["smiles"])) is not None
        assert float(molecule["docking_score"]) < 0


def test_health_and_static_frontend(client: TestClient) -> None:
    """Health endpoints and static frontend files should be reachable."""

    health = client.get("/health")
    readiness = client.get("/health/ready")
    frontend = client.get("/")
    styles = client.get("/styles/main.css")
    script = client.get("/js/app.js")

    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    assert readiness.status_code == 200
    assert readiness.json()["targets"] == 5
    assert readiness.json()["molecules"] == 40
    assert frontend.status_code == 200
    assert "MolGenix" in frontend.text
    assert styles.status_code == 200
    assert script.status_code == 200


def test_session_creation_and_target_identification(client: TestClient) -> None:
    """A plain-English query should create a complete session and identify EGFR."""

    session = _create_session(client, "Find drugs for EGFR mutated lung cancer")

    assert session["status"] == "COMPLETE"
    assert session["identified_target_name"] == "Epidermal Growth Factor Receptor"
    assert session["confidence_score"] > 0
    assert session["molecules_generated"] == 8
    assert session["molecules_passed_filter"] == 5


def test_molecule_retrieval_and_filtering_behavior(client: TestClient) -> None:
    """Molecule APIs should rank, detail, and filter while retaining toxic results by default."""

    session = _create_session(client, "JAK2 inhibitor for myelofibrosis")
    molecules = client.get(f"/api/v1/molecules/session/{session['id']}?sort=rank")
    lipinski = client.get(f"/api/v1/molecules/session/{session['id']}?lipinski_only=true")
    docking_sorted = client.get(f"/api/v1/molecules/session/{session['id']}?sort=docking")

    assert molecules.status_code == 200
    body = molecules.json()
    assert len(body) == 8
    assert any(molecule["is_toxic"] and molecule["is_filtered"] for molecule in body)
    assert all(molecule["rank"] is not None for molecule in body)

    assert lipinski.status_code == 200
    assert len(lipinski.json()) <= len(body)
    assert all(molecule["lipinski_pass"] for molecule in lipinski.json())

    assert docking_sorted.status_code == 200
    docking_scores = [molecule["docking_score"] for molecule in docking_sorted.json()]
    assert docking_scores == sorted(docking_scores)

    detail = client.get(f"/api/v1/molecules/{body[0]['id']}")
    assert detail.status_code == 200
    detail_body = detail.json()
    assert detail_body["admet"]
    assert detail_body["image_path"].endswith(".png")
    if detail_body["rank"] == 1:
        assert detail_body["docking_detail"] is not None


def test_report_generation_and_pdf_download(client: TestClient) -> None:
    """Report generation should create a downloadable PDF for the browser flow."""

    session = _create_session(client, "BACE1 Alzheimer amyloid therapy")
    report_response = client.post("/api/v1/reports/generate", json={"session_id": session["id"]})

    assert report_response.status_code == 201, report_response.text
    report = report_response.json()
    assert report["druggability_score"] > 0
    assert report["download_url"] == f"/api/v1/reports/{report['id']}/download"
    assert len([paragraph for paragraph in report["summary"].split("\n\n") if paragraph.strip()]) == 3

    reports = client.get(f"/api/v1/reports/session/{session['id']}")
    assert reports.status_code == 200
    assert any(item["id"] == report["id"] for item in reports.json())

    download = client.get(report["download_url"])
    assert download.status_code == 200
    assert download.headers["content-type"] == "application/pdf"
    assert download.content.startswith(b"%PDF")
