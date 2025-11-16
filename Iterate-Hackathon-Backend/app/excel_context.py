# app/excel_context.py
from __future__ import annotations

from io import BytesIO
from typing import Optional

import pandas as pd


def build_excel_context(
    file_bytes: bytes,
    filename: Optional[str] = None,
    max_rows: int = 50,
) -> str:
    """
    Lit un fichier Excel et le transforme en texte lisible pour le LLM.

    - max_rows limite le nombre de lignes envoyées (important pour éviter
      d'exploser le contexte de l'IA).
    """
    buffer = BytesIO(file_bytes)
    df = pd.read_excel(buffer)

    # Limiter le nombre de lignes envoyées au LLM
    if len(df) > max_rows:
        df = df.head(max_rows)

    col_names = list(df.columns)

    lines: list[str] = []

    header = f"Les données suivantes proviennent du fichier Excel : {filename or 'fichier_sans_nom'}."
    lines.append(header)
    lines.append(f"Colonnes : {', '.join(map(str, col_names))}.")
    lines.append("Voici un aperçu des lignes :")

    for idx, row in df.iterrows():
        row_parts = []
        for col in col_names:
            val = row[col]
            if pd.isna(val):
                continue
            row_parts.append(f"{col} = {val}")
        if not row_parts:
            continue
        lines.append(f"Ligne {idx + 1} : " + "; ".join(row_parts))

    context_text = "\n".join(lines)
    print(f"Contexte Excel généré ({len(df)} lignes) :\n{context_text}")
    return context_text
