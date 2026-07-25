"""Limpeza e preparacao dos dados de licitacoes para analise de valor."""

import pandas as pd

# Valores que representam "sem valor informado", nao transacoes reais.
# Criterio documentado: R$ 0, R$ 0,01 e R$ 1,00 sao placeholders de sistema
# (confirmado na fase 2 — 615 casos de R$ 1,00 concentrados no MJSP).
VALORES_PLACEHOLDER = [0, 0.01, 1.00]


def limpar_valores(
    df: pd.DataFrame,
    coluna_valor: str = "Valor Licitação",
    verbose: bool = True,
) -> pd.DataFrame:
    """Remove linhas com valores placeholder, retornando copia limpa.

    Nao altera o DataFrame original (dado bruto e imutavel).
    """
    n_antes = len(df)
    limpo = df[~df[coluna_valor].isin(VALORES_PLACEHOLDER)].copy()
    n_removido = n_antes - len(limpo)

    if verbose:
        print(f"Removidos {n_removido} registros placeholder "
              f"({n_removido / n_antes:.1%} do total)")
        print(f"Restaram {len(limpo)} licitacoes com valor economico real")

    return limpo