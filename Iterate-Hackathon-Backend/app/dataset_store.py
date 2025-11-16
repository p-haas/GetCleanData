"""Utilities for persisting uploaded datasets and capturing metadata."""

from __future__ import annotations

import csv
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal, Optional

ALLOWED_EXTENSIONS = {".csv", ".xls", ".xlsx"}
CSV_DELIMITERS = [",", ";", "\t", "|"]


def generate_dataset_id() -> str:
    """Return a unique dataset identifier."""

    return f"dataset_{uuid.uuid4().hex}"


def normalize_extension(filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise ValueError("Unsupported file extension. Allowed: .csv, .xls, .xlsx")
    return suffix


def infer_file_type(extension: str) -> Literal["csv", "excel"]:
    return "csv" if extension == ".csv" else "excel"


def infer_delimiter(file_bytes: bytes, fallback: str = ",") -> str:
    """Try to guess delimiter for CSV files, fallback to comma if unknown."""

    try:
        sample = file_bytes[:4096].decode("utf-8", errors="ignore")
        if not sample.strip():
            return fallback
        dialect = csv.Sniffer().sniff(sample, delimiters=CSV_DELIMITERS)
        return dialect.delimiter
    except csv.Error:
        return fallback


def persist_dataset_file(
    data_dir: Path,
    dataset_id: str,
    original_filename: str,
    file_bytes: bytes,
    content_type: Optional[str],
    delimiter: Optional[str],
) -> dict:
    """Store the uploaded bytes under /data/{dataset_id}/raw.{ext} and write metadata."""

    extension = normalize_extension(original_filename)
    dataset_dir = data_dir / dataset_id
    dataset_dir.mkdir(parents=True, exist_ok=True)

    raw_path = dataset_dir / f"raw{extension}"
    raw_path.write_bytes(file_bytes)

    metadata = {
        "dataset_id": dataset_id,
        "original_filename": original_filename,
        "stored_file": str(raw_path.relative_to(data_dir.parent)),
        "file_size_bytes": len(file_bytes),
        "file_type": infer_file_type(extension),
        "delimiter": delimiter if extension == ".csv" else None,
        "content_type": content_type,
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
    }

    metadata_path = dataset_dir / "metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    return metadata
