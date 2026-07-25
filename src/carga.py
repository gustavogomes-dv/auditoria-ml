"""Carga e consolidacao dos CSVs de licitacoes."""

from pathlib import Path

import pandas as pd


def carregar_licitacoes(pasta: str = "data/raw") -> pd.DataFrame:
    """Le todos os CSVs de licitacao da pasta e empilha num unico DataFrame."""
    arquivos = sorted(
    arq for arq in Path(pasta).glob("2*_Licita*.csv")
)

    frames = []
    for arq in arquivos:
        df = pd.read_csv(arq, sep=";", encoding="latin-1", decimal=",")
        df["arquivo_origem"] = arq.name  # rastreabilidade: de onde veio cada linha
        frames.append(df)

    return pd.concat(frames, ignore_index=True)

def carregar_participantes(pasta: str = "data/raw") -> pd.DataFrame:
    """Le todos os CSVs de participantes da pasta e empilha num unico DataFrame."""
    arquivos = sorted(Path(pasta).glob("*_ParticipantesLicita*.csv"))
    if not arquivos:
        raise FileNotFoundError(f"Nenhum CSV de participantes em {pasta}")

    frames = []
    for arq in arquivos:
        df = pd.read_csv(arq, sep=";", encoding="latin-1", decimal=",")
        df["arquivo_origem"] = arq.name
        frames.append(df)

    return pd.concat(frames, ignore_index=True)