"""Curated drug target records for the MolGenix prototype."""

CURATED_TARGETS: list[dict[str, str]] = [
    {
        "key": "egfr",
        "name": "Epidermal Growth Factor Receptor",
        "gene_symbol": "EGFR",
        "uniprot_id": "P00533",
        "disease_area": "Non-small cell lung cancer",
        "mechanism": "ATP-competitive receptor tyrosine kinase inhibition",
        "description": "Curated oncology target used to evaluate kinase-like candidate profiles.",
    },
    {
        "key": "jak2",
        "name": "Janus Kinase 2",
        "gene_symbol": "JAK2",
        "uniprot_id": "O60674",
        "disease_area": "Myeloproliferative neoplasms",
        "mechanism": "Cytokine signaling pathway modulation through kinase inhibition",
        "description": "Curated hematology target for balancing potency, selectivity, and safety liabilities.",
    },
    {
        "key": "bace1",
        "name": "Beta-secretase 1",
        "gene_symbol": "BACE1",
        "uniprot_id": "P56817",
        "disease_area": "Alzheimer's disease",
        "mechanism": "Aspartyl protease inhibition to reduce amyloidogenic peptide formation",
        "description": "Curated neuroscience target with emphasis on CNS exposure and polar surface area.",
    },
    {
        "key": "tnf",
        "name": "Tumor Necrosis Factor",
        "gene_symbol": "TNF",
        "uniprot_id": "P01375",
        "disease_area": "Autoimmune inflammation",
        "mechanism": "Small-molecule disruption of inflammatory cytokine signaling",
        "description": "Curated immunology target for prototype ranking of inflammation-focused candidates.",
    },
    {
        "key": "hiv_integrase",
        "name": "HIV Integrase",
        "gene_symbol": "POL",
        "uniprot_id": "P04585",
        "disease_area": "Human immunodeficiency virus infection",
        "mechanism": "Metal-chelating inhibition of viral strand transfer",
        "description": "Curated antiviral target with docking scores modeled around integrase active-site binding.",
    },
]
