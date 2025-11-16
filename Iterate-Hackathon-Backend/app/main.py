# app/main.py
from typing import List, Literal, Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from pydantic import BaseModel

from .chat import init_llm, chat_with_user
from .dataset_store import (
    generate_dataset_id,
    infer_delimiter,
    load_dataset_metadata,
    persist_dataset_file,
    resolve_raw_path,
)
from .excel_context import build_excel_context
from .tools import generate_error_analysis_script
import pandas as pd
from pathlib import Path
import subprocess
import sys

# Dossiers pour stocker fichiers + scripts
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
SCRIPTS_DIR = BASE_DIR / "scripts"

DATA_DIR.mkdir(parents=True, exist_ok=True)
SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)



app = FastAPI(title="Claude Excel Context API")


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    reply: str


class ColumnSummary(BaseModel):
    name: str
    dataType: Literal["string", "numeric", "date", "categorical", "boolean"]
    description: str
    sampleValues: Optional[List[str]] = None


class DatasetSummary(BaseModel):
    name: str
    description: str
    rowCount: int
    columnCount: int
    observations: List[str]


class DatasetUnderstandingResponse(BaseModel):
    summary: DatasetSummary
    columns: List[ColumnSummary]


class UploadDatasetResponse(BaseModel):
    dataset_id: str
    file_name: str
    file_type: str
    file_size_bytes: int
    delimiter: Optional[str]
    storage_path: str
    uploaded_at: str

class ChatDatasetRequest(BaseModel):
    session_id: str
    dataset_id: str
    message: str


@app.on_event("startup")
def startup_event():
    # Initialiser le LLM (Claude)
    init_llm()


@app.post("/datasets", response_model=UploadDatasetResponse)
async def upload_dataset(file: UploadFile = File(...)):
    """Persist an uploaded dataset and capture metadata for later steps."""

    if not file.filename:
        raise HTTPException(status_code=400, detail="Le fichier doit avoir un nom valide.")

    extension = Path(file.filename).suffix.lower()
    if extension not in [".csv", ".xlsx", ".xls"]:
        raise HTTPException(status_code=400, detail="Le fichier doit être un CSV ou un Excel.")

    file_bytes = await file.read()
    delimiter = infer_delimiter(file_bytes) if extension == ".csv" else None

    dataset_id = generate_dataset_id()
    metadata = persist_dataset_file(
        DATA_DIR,
        dataset_id,
        file.filename,
        file_bytes,
        file.content_type,
        delimiter,
    )

    return UploadDatasetResponse(
        dataset_id=dataset_id,
        file_name=file.filename,
        file_type=metadata["file_type"],
        file_size_bytes=metadata["file_size_bytes"],
        delimiter=metadata["delimiter"],
        storage_path=metadata["stored_file"],
        uploaded_at=metadata["uploaded_at"],
    )


def _infer_column_type(series: pd.Series) -> str:
    if pd.api.types.is_bool_dtype(series):
        return "boolean"
    if pd.api.types.is_numeric_dtype(series):
        return "numeric"
    if pd.api.types.is_datetime64_any_dtype(series):
        return "date"
    if pd.api.types.is_object_dtype(series):
        unique_ratio = 0
        try:
            unique_ratio = series.nunique(dropna=True) / max(len(series), 1)
        except Exception:
            unique_ratio = 0
        if unique_ratio <= 0.2:
            return "categorical"
    return "string"


def _build_column_summary(series: pd.Series) -> ColumnSummary:
    data_type = _infer_column_type(series)
    total = len(series)
    missing = int(series.isna().sum())
    unique = int(series.nunique(dropna=True))
    description = (
        f"Detected as {data_type}. {unique} unique values"
        f" with {missing} missing entries out of {total}."
    )

    samples: List[str] = []
    for value in series.dropna().head(3).tolist():
        samples.append(str(value))

    return ColumnSummary(
        name=str(series.name),
        dataType=data_type,  # type: ignore[arg-type]
        description=description,
        sampleValues=samples or None,
    )


@app.get("/datasets/{dataset_id}/understanding", response_model=DatasetUnderstandingResponse)
def get_dataset_understanding(dataset_id: str):
    try:
        metadata = load_dataset_metadata(DATA_DIR, dataset_id)
        raw_path = resolve_raw_path(DATA_DIR, metadata)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    file_type = metadata.get("file_type", "csv")
    delimiter = metadata.get("delimiter") or ","

    try:
        if file_type == "excel":
            df = pd.read_excel(raw_path)
        else:
            df = pd.read_csv(raw_path, delimiter=delimiter)
    except Exception as exc:  # pragma: no cover - runtime failure surfaced to caller
        raise HTTPException(status_code=500, detail=f"Erreur de lecture du dataset: {exc}") from exc

    columns = [
        _build_column_summary(df[col])
        for col in df.columns
    ]

    missing_counts = df.isna().sum().sort_values(ascending=False)
    observations: List[str] = []
    for col, count in missing_counts.head(3).items():
        if count > 0:
            observations.append(f"{col} contient {int(count)} valeurs manquantes")

    if not observations:
        observations.append("Aucun signal de qualité majeur détecté sur les 3 premières colonnes.")

    summary = DatasetSummary(
        name=metadata.get("original_filename", dataset_id),
        description=f"Dataset importé via {metadata.get('file_type', 'csv').upper()} le {metadata.get('uploaded_at', '')}",
        rowCount=int(df.shape[0]),
        columnCount=int(df.shape[1]),
        observations=observations,
    )

    return DatasetUnderstandingResponse(summary=summary, columns=columns)


@app.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest):
    """
    Chat simple sans fichier Excel.
    L'historique est stocké dans MongoDB.
    """
    reply = chat_with_user(
        session_id=payload.session_id,
        user_message=payload.message,
        excel_context=None,
    )
    return ChatResponse(reply=reply)


@app.post("/chat_excel", response_model=ChatResponse)
async def chat_excel(
    session_id: str = Form(...),
    message: str = Form(...),
    file: UploadFile = File(...),
):
    """
    Chat avec contexte Excel.

    - Le fichier Excel est lu à chaque requête
    - Son contenu est transformé en texte
    - Ce texte est passé comme contexte au LLM
    - L'historique de la conversation est stocké dans MongoDB
    """
    if not file.filename.lower().endswith((".xlsx", ".xls")):
        raise HTTPException(
            status_code=400,
            detail="Le fichier doit être un Excel (.xlsx ou .xls).",
        )

    file_bytes = await file.read()
    excel_context = build_excel_context(file_bytes, filename=file.filename)

    reply = chat_with_user(
        session_id=session_id,
        user_message=message,
        excel_context=excel_context,
    )

    return ChatResponse(reply=reply)



@app.post("/upload_and_analyze")
async def upload_and_analyze(
    dataset_id: str = Form(...),
    file: UploadFile = File(...),
    file_type: str = Form("excel"),  # "excel" ou "csv"
    delimiter: str = Form(","),
    meta_data: str = Form("")
):
    """
    Upload le dataset ET lance l'analyse en une seule étape.

    Étapes :
    1) Sauvegarde le fichier dans /data/{dataset_id}.{ext}
    2) Charge le fichier avec pandas pour récupérer colonnes + metadata
    3) Appelle le tool LLM generate_error_analysis_script pour générer un script Python
    4) Sauvegarde ce script dans /scripts/detect_errors_{dataset_id}.py
    5) Exécute le script sur le fichier
    6) Sauvegarde le rapport d'erreurs dans /data/{dataset_id}_errors.txt
    7) Retourne le rapport d'erreurs + chemins utiles
    """

    suffix = Path(file.filename).suffix.lower()
    if suffix not in [".xlsx", ".xls", ".csv"]:
        raise HTTPException(status_code=400, detail="Le fichier doit être un Excel ou un CSV.")

    # 1) Sauvegarder le fichier
    dataset_path = DATA_DIR / f"{dataset_id}{suffix}"
    print(f"Sauvegarde du fichier dataset à : {dataset_path}")
    file_bytes = await file.read()
    dataset_path.write_bytes(file_bytes)

    # 2) Charger avec pandas pour récupérer les colonnes + metadata
    if suffix in [".xlsx", ".xls"]:
        df = pd.read_excel(dataset_path)
        effective_file_type = "excel"
    else:
        df = pd.read_csv(dataset_path, delimiter=delimiter)
        effective_file_type = "csv"

    column_names = df.columns.tolist()

    metadata = (
        f"Dataset '{dataset_id}' - shape: {df.shape[0]} rows x {df.shape[1]} columns.\n"
        f"Premières lignes (head):\n{df.head(5).to_markdown(index=False)}",
        f"\nMetadata additionnelle fournie : {meta_data}" if meta_data else ""
    )

    # 3) Appeler le tool LLM pour générer le script d'analyse
    script_code = generate_error_analysis_script(   column_names,
                                                    metadata,
                                                    effective_file_type,
                                                    delimiter,
    )

    # 4) Sauvegarder le script généré
    script_path = SCRIPTS_DIR / f"detect_errors_{dataset_id}.py"
    script_path.write_text(script_code, encoding="utf-8")

    # 5) Exécuter le script sur le dataset
    result = subprocess.run(
        [sys.executable, str(script_path), str(dataset_path)],
        capture_output=True,
        text=True,
        cwd=BASE_DIR,
    )

    error_report = result.stdout
    if not error_report.strip() and result.stderr:
        error_report = "SCRIPT RUNTIME ERROR:\n" + result.stderr

    # 6) Sauvegarder le rapport d'erreurs
    error_report_path = DATA_DIR / f"{dataset_id}_errors.txt"
    error_report_path.write_text(error_report, encoding="utf-8")


    # 7) Retourner infos
    return {
        "status": "ok",
        "dataset_id": dataset_id,
        "dataset_path": str(dataset_path),
        "analysis_script_path": str(script_path),
        "error_report_path": str(error_report_path),
        "error_report": error_report,
    }


@app.post("/chat_dataset", response_model=ChatResponse)
def chat_dataset(payload: ChatDatasetRequest):
    """
    Discute avec l'IA à propos d'un dataset précis (dataset_id).
    Utilise le rapport d'erreurs texte comme contexte.
    """


    error_report_path = DATA_DIR / f"{payload.dataset_id}_errors.txt"
    if not error_report_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Aucun rapport d'erreurs trouvé pour ce dataset_id. "
                   "Appelle d'abord /upload_and_analyze."
        )

    

    dataset_path = DATA_DIR / f"{payload.dataset_id}.csv"
    if not dataset_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Aucun fichier dataset CSV trouvé pour ce dataset_id."
        )


    # 2) Charger avec pandas pour récupérer les colonnes + metadata
    df = pd.read_csv(dataset_path)
    effective_file_type = "csv"
    

    column_names = df.columns.tolist()


    error_report = error_report_path.read_text(encoding="utf-8")



    meta_data = f"""
    Metadata du dataset '{payload.dataset_id}':
        metadata = (
        f"Dataset '{payload.dataset_id}' - shape: {df.shape[0]} rows x {df.shape[1]} columns.\n"
        f"Premières lignes (head):\n{df.head(5).to_markdown(index=False)}",
    )

    Voici le rapport d'erreurs détectées dans le dataset :
    {error_report}
    """

    reply = chat_with_user(
        session_id=payload.session_id,
        user_message=payload.message,
        excel_context=error_report,  # on passe le rapport comme contexte
    )

    return ChatResponse(reply=reply)
@app.get("/health")
def health():
    return {"status": "up"}
