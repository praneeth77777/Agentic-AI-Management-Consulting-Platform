# Data Catalog

Update this file whenever a source is added, removed, parsed, or indexed. Do not mark a source ingested until the chunk count and metadata validation are recorded.

## Technology

| Source | Organization | Type | Status | Notes |
|---|---|---|---|---|
| `DataSource-Cisco.txt` | Cisco | Source links | Available, not ingested | Download only required authoritative documents |
| `Google GCP.txt` | Google | Source link | Available, not ingested | Confirm document relevance before ingestion |
| IBM documents | IBM | Unknown | Missing | No IBM source was identified in the supplied archive |

## Clinical

| Source group | Type | Status | Notes |
|---|---|---|---|
| COVID studies | CSV and PDFs | Available, not ingested | Includes trial data and research papers |
| Diabetes studies | CSV and PDFs | Available, not ingested | Includes clinical and AI research |
| Heart attack studies | CSV and PDFs | Available, not ingested | Includes monitoring and prediction research |
| Knee injury studies | CSV and PDFs | Available, not ingested | Includes detection, surgery, and rehabilitation research |
| `Agilent.txt` | Source information | Available, not ingested | Validate intended role and authoritative URLs |

## SEC

| Source group | Organization | Type | Status | Notes |
|---|---|---|---|---|
| Cisco filings | Cisco | SEC PDF filings | Available, not ingested | Two supplied PDFs |
| Agilent filing | Agilent | SEC PDF filing | Available, not ingested | One supplied PDF |
| Alphabet filings | Alphabet | SEC PDF filings | Available, not ingested | Two supplied PDFs |

## Corporate Responsibility

| Source | Organization | Type | Status | Notes |
|---|---|---|---|---|
| `SOFI-2023.pdf` | FAO and partners | Food security report | Available, not ingested | Preserve page and section metadata |
| `SOFI-2024.pdf` | FAO and partners | Food security report | Available, not ingested | Preserve page and section metadata |

## Excluded Challenge Data

| Source | Status | Reason |
|---|---|---|
| `CMPE256_Hackathon_market_basket_analysis_Release.csv` | Excluded | Belongs to the separate Market Basket Recommendation challenge |

## Required Metadata

Every indexed chunk or record should contain:

- `evidence_id`
- `source_title`
- `organization`
- `publication_date`
- `document_type`
- `domain`
- `company_or_product`
- `page_number` when applicable
- `section`
- `source_path`
- `chunk_index`
- `content_hash`
- `ingested_at`

## Ingestion Validation

For each collection, record:

- File count
- Parsed file count
- Failed file count
- Chunk count
- Pages sampled visually
- Table extraction limitations
- Duplicate detection result
- Index build date
- Embedding model and version

