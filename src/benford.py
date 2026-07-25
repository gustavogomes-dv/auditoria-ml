"""Funcoes para teste de conformidade com a Lei de Benford."""

import numpy as np
import pandas as pd


def primeiro_digito(valores: pd.Series) -> pd.Series:
    """Extrai o primeiro digito significativo de cada valor positivo."""
    v = valores[valores > 0]
    # log10 do valor -> parte fracionaria -> 10^frac = mantissa entre 1 e 10
    # int() da mantissa = primeiro digito. Elegante e vetorizado.
    mantissa = 10 ** (np.log10(v) % 1)
    return mantissa.astype(int)


def benford_esperado() -> pd.Series:
    """Distribuicao teorica de Benford para digitos 1-9."""
    digitos = np.arange(1, 10)
    probs = np.log10(1 + 1 / digitos)
    return pd.Series(probs, index=digitos, name="esperado")


def comparar_benford(valores: pd.Series) -> pd.DataFrame:
    """Compara distribuicao observada dos primeiros digitos com Benford."""
    digitos = primeiro_digito(valores)
    observado = digitos.value_counts(normalize=True).sort_index()
    observado.name = "observado"
    tabela = pd.concat([benford_esperado(), observado], axis=1).fillna(0)
    tabela["desvio"] = tabela["observado"] - tabela["esperado"]
    return tabela