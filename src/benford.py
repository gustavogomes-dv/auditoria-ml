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

from scipy.stats import chisquare


def benford_por_grupo(
    df: pd.DataFrame,
    coluna_valor: str,
    coluna_grupo: str,
    min_amostras: int = 300,
) -> pd.DataFrame:
    """Roda o teste qui-quadrado de Benford para cada grupo.

    Retorna um ranking ordenado pelo chi2 (maior = mais desviante).
    """
    esperado = benford_esperado()
    resultados = []

    for grupo, sub in df.groupby(coluna_grupo):
        valores = sub[coluna_valor]
        n = int((valores > 0).sum())
        if n < min_amostras:
            continue  # grupo pequeno demais para teste confiavel

        digitos = primeiro_digito(valores)
        obs_prop = digitos.value_counts(normalize=True).sort_index()
        obs_prop = obs_prop.reindex(range(1, 10), fill_value=0)

        obs_abs = (obs_prop * n).round()
        esp_abs = esperado * n

        chi2, p = chisquare(f_obs=obs_abs, f_exp=esp_abs)

        # MAD (Mean Absolute Deviation) - metrica padrao em auditoria Benford,
        # independente do tamanho da amostra
        mad = (obs_prop - esperado).abs().mean()

        resultados.append({
            coluna_grupo: grupo,
            "n": n,
            "chi2": chi2,
            "p_valor": p,
            "mad": mad,
        })
        

    ranking = pd.DataFrame(resultados)
    return ranking.sort_values("mad", ascending=False).reset_index(drop=True)


def plotar_grupo(df, coluna_valor, coluna_grupo, nome_grupo, salvar=None):
    """Plota a distribuicao de primeiros digitos de um grupo vs Benford."""
    import matplotlib.pyplot as plt

    sub = df[df[coluna_grupo] == nome_grupo]
    tabela = comparar_benford(sub[coluna_valor])

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(tabela.index, tabela["observado"], alpha=0.7, label=f"Observado")
    ax.plot(tabela.index, tabela["esperado"], "ro--", label="Benford teórico")
    ax.set_xticks(range(1, 10))
    ax.set_xlabel("Primeiro dígito")
    ax.set_ylabel("Proporção")
    ax.set_title(f"Benford — {nome_grupo}")
    ax.legend()
    if salvar:
        plt.savefig(salvar, dpi=150, bbox_inches="tight")
    plt.show()
    return tabela