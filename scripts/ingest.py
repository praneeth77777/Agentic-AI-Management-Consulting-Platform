from __future__ import annotations

import argparse
import csv
import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path

import fitz
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings

from app.config import get_settings
from app.models.contracts import Domain
from app.retrieval.fts import connect, upsert_chunk


SUPPORTED_SUFFIXES = {
    ".pdf",
    ".txt",
    ".md",
    ".csv",
}


def chunks(
    text: str,
    size: int = 1800,
    overlap: int = 250,
):
    text = re.sub(r"\s+", " ", text).strip()

    if not text:
        return

    i = 0

    while i < len(text):
        yield text[i:i + size]
        i += max(1, size - overlap)


def detect_organization(path: Path) -> str:
    value = str(path).lower()

    if "cisco" in value:
        return "Cisco"

    if "alphabet" in value or "google" in value:
        return "Alphabet"

    if "agilent" in value:
        return "Agilent"

    return ""


def metadata_for(
    path: Path,
    domain: Domain,
    page: int | None,
    idx: int,
    text: str,
    *,
    source_title: str | None = None,
    section: str = "",
) -> dict:
    org = detect_organization(path)

    title = source_title or path.stem

    raw = (
        f"{domain.value}|"
        f"{path}|"
        f"{page}|"
        f"{idx}|"
        f"{title}|"
        f"{text}"
    ).encode()

    evidence_id = hashlib.sha256(
        raw
    ).hexdigest()[:20]

    content_hash = hashlib.sha256(
        text.encode()
    ).hexdigest()

    return {
        "evidence_id": evidence_id,
        "source_title": title,
        "organization": org,
        "publication_date": "",
        "document_type": path.suffix.lstrip("."),
        "domain": domain.value,
        "company_or_product": org,
        "page_number": page if page is not None else -1,
        "section": section,
        "source_path": str(path),
        "chunk_index": idx,
        "content_hash": content_hash,
        "ingested_at": datetime.now(
            timezone.utc
        ).isoformat(),
    }


def csv_row_title(
    row: dict[str, str],
    fallback: str,
) -> str:
    """
    Try common ClinicalTrials/research CSV title fields.
    Fall back to the CSV filename if no title field is available.
    """

    preferred_fields = [
        "Brief Title",
        "BriefTitle",
        "Official Title",
        "OfficialTitle",
        "Study Title",
        "StudyTitle",
        "Title",
        "NCT Number",
        "NCTNumber",
        "NCTId",
    ]

    for field in preferred_fields:
        value = row.get(field)

        if value and str(value).strip():
            return str(value).strip()

    return fallback


def csv_row_to_text(
    row: dict[str, str],
) -> str:
    """
    Convert one CSV row into readable evidence text.

    Empty fields are excluded so the embedding does not waste space
    on missing ClinicalTrials columns.
    """

    fields = []

    for key, value in row.items():
        if value is None:
            continue

        value = str(value).strip()

        if not value:
            continue

        clean_key = re.sub(
            r"\s+",
            " ",
            str(key),
        ).strip()

        fields.append(
            f"{clean_key}: {value}"
        )

    return "\n".join(fields)


def load_pdf(
    path: Path,
    domain: Domain,
) -> list[tuple[str, dict]]:
    docs = []

    with fitz.open(path) as pdf:
        for page_number, page in enumerate(
            pdf,
            start=1,
        ):
            page_text = page.get_text(
                "text"
            )

            for chunk_index, text in enumerate(
                chunks(page_text) or []
            ):
                metadata = metadata_for(
                    path=path,
                    domain=domain,
                    page=page_number,
                    idx=chunk_index,
                    text=text,
                )

                docs.append(
                    (
                        text,
                        metadata,
                    )
                )

    return docs


def load_text(
    path: Path,
    domain: Domain,
) -> list[tuple[str, dict]]:
    docs = []

    raw_text = path.read_text(
        encoding="utf-8",
        errors="ignore",
    )

    for chunk_index, text in enumerate(
        chunks(raw_text) or []
    ):
        metadata = metadata_for(
            path=path,
            domain=domain,
            page=None,
            idx=chunk_index,
            text=text,
        )

        docs.append(
            (
                text,
                metadata,
            )
        )

    return docs


def load_csv(
    path: Path,
    domain: Domain,
) -> list[tuple[str, dict]]:
    """
    Treat each CSV row as an independent study/record.

    Large rows are split into multiple chunks using the same chunking
    strategy used for PDFs.
    """

    docs = []

    with path.open(
        "r",
        encoding="utf-8-sig",
        errors="ignore",
        newline="",
    ) as handle:
        reader = csv.DictReader(
            handle
        )

        for row_number, row in enumerate(
            reader,
            start=1,
        ):
            row_text = csv_row_to_text(
                row
            )

            if not row_text.strip():
                continue

            study_title = csv_row_title(
                row,
                path.stem,
            )

            source_title = (
                f"{path.stem} | "
                f"{study_title}"
            )

            for chunk_index, text in enumerate(
                chunks(row_text) or []
            ):
                # Unique index across CSV rows and chunks.
                global_index = (
                    row_number * 10000
                    + chunk_index
                )

                metadata = metadata_for(
                    path=path,
                    domain=domain,
                    page=None,
                    idx=global_index,
                    text=text,
                    source_title=source_title,
                    section=(
                        f"CSV row {row_number}"
                    ),
                )

                docs.append(
                    (
                        text,
                        metadata,
                    )
                )

    return docs


def ingest_file(
    path: Path,
    domain: Domain,
    vector: Chroma,
    conn,
) -> int:
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        docs = load_pdf(
            path,
            domain,
        )

    elif suffix in {
        ".txt",
        ".md",
    }:
        docs = load_text(
            path,
            domain,
        )

    elif suffix == ".csv":
        docs = load_csv(
            path,
            domain,
        )

    else:
        return 0

    for text, metadata in docs:
        # Chroma metadata values must be scalar and cannot be None.
        chroma_metadata = {
            key: (
                value
                if value is not None
                else ""
            )
            for key, value in metadata.items()
        }

        vector.add_texts(
            texts=[text],
            metadatas=[
                chroma_metadata
            ],
            ids=[
                metadata["evidence_id"]
            ],
        )

        sqlite_row = dict(
            metadata
        )

        sqlite_row["content"] = text

        sqlite_row["page_number"] = (
            None
            if metadata["page_number"] == -1
            else metadata["page_number"]
        )

        upsert_chunk(
            conn,
            sqlite_row,
        )

    return len(docs)


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--domain",
        required=True,
        choices=[
            domain.value
            for domain in Domain
        ],
    )

    parser.add_argument(
        "--path",
        required=True,
    )

    args = parser.parse_args()

    domain = Domain(
        args.domain
    )

    settings = get_settings()

    embeddings = OllamaEmbeddings(
        base_url=settings.ollama_base_url,
        model=settings.ollama_embed_model,
    )

    vector = Chroma(
        collection_name=(
            f"domain_{domain.value}"
        ),
        embedding_function=embeddings,
        persist_directory=settings.chroma_dir,
    )

    conn = connect(
        settings.fts_db
    )

    total = 0

    root = Path(
        args.path
    )

    if root.is_file():
        files = [
            root
        ]

    else:
        files = sorted(
            path
            for path in root.rglob("*")
            if path.is_file()
            and path.suffix.lower()
            in SUPPORTED_SUFFIXES
        )

    for file_path in files:
        count = ingest_file(
            file_path,
            domain,
            vector,
            conn,
        )

        total += count

        print(
            f"{file_path}: "
            f"{count} chunks"
        )

    conn.close()

    print(
        f"TOTAL {total} chunks "
        f"ingested for {domain.value}"
    )


if __name__ == "__main__":
    main()