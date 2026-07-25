"""Construcao de grafos de coparticipacao em licitacoes para deteccao de conluio."""

from itertools import combinations

import networkx as nx
import pandas as pd


def filtrar_licitacoes_disputadas(
    part: pd.DataFrame,
    min_participantes: int = 2,
    max_participantes: int = 15,
) -> pd.DataFrame:
    """Mantem apenas licitacoes com numero de participantes na faixa de interesse.

    Licitacoes com 1 participante nao tem disputa; com muitos (>15) sao pregoes
    abertos super-concorridos, onde conluio e improvavel e o grafo explode.
    """
    tamanho = part.groupby(["Código UG", "Número Licitação"])["Código Participante"].transform("size")
    return part[(tamanho >= min_participantes) & (tamanho <= max_participantes)].copy()


def construir_grafo_coparticipacao(part: pd.DataFrame) -> nx.Graph:
    """Cria grafo onde nos = empresas e arestas = coparticipacao em licitacoes.

    O peso da aresta = numero de licitacoes em que as duas empresas coparticiparam.
    """
    G = nx.Graph()

    for _, grupo in part.groupby(["Código UG", "Número Licitação"]):
        empresas = grupo["Código Participante"].unique()
        # Cada par de empresas na mesma licitacao vira uma aresta
        for a, b in combinations(empresas, 2):
            if G.has_edge(a, b):
                G[a][b]["weight"] += 1  # ja coparticiparam antes: reforca o laco
            else:
                G.add_edge(a, b, weight=1)

    return G

def top_pares_coparticipacao(G: nx.Graph, n: int = 20) -> pd.DataFrame:
    """Retorna os pares de empresas que mais coparticiparam (maior peso de aresta)."""
    arestas = [
        {"empresa_a": a, "empresa_b": b, "coparticipacoes": dados["weight"]}
        for a, b, dados in G.edges(data=True)
    ]
    ranking = pd.DataFrame(arestas)
    return ranking.sort_values("coparticipacoes", ascending=False).head(n).reset_index(drop=True)

def detectar_comunidades(G: nx.Graph, peso_minimo: int = 2) -> list:
    """Detecta comunidades (grupos fechados) no grafo de coparticipacao.

    Filtra arestas fracas (coparticipacao unica pode ser coincidencia) antes
    de rodar o algoritmo de Louvain, que agrupa nos densamente conectados.
    """
    # Mantem so lacos que se repetem (peso >= minimo): sinal, nao ruido
    arestas_fortes = [(a, b, d) for a, b, d in G.edges(data=True) if d["weight"] >= peso_minimo]
    H = nx.Graph()
    H.add_edges_from(arestas_fortes)

    comunidades = nx.community.louvain_communities(H, weight="weight", seed=42)
    # Ordena da maior para a menor
    return sorted(comunidades, key=len, reverse=True)

def analisar_comunidade(part: pd.DataFrame, G: nx.Graph, comunidade: set) -> dict:
    """Analisa uma comunidade: coparticipacoes internas e distribuicao de vitorias.

    Rodizio de vitorias (varias empresas ganhando de forma equilibrada dentro de
    um grupo que sempre disputa junto) e assinatura classica de conluio.
    """
    membros = set(comunidade)

    # Licitacoes onde pelo menos 2 membros da comunidade participaram juntos
    part_membros = part[part["Código Participante"].isin(membros)].copy()

    lics_com_grupo = (
        part_membros.groupby(["Código UG", "Número Licitação"])["Código Participante"]
        .nunique()
    )
    lics_disputa_interna = lics_com_grupo[lics_com_grupo >= 2].index

    # Vitorias de cada membro nessas licitacoes de disputa interna
    mask = part_membros.set_index(["Código UG", "Número Licitação"]).index.isin(lics_disputa_interna)
    disputa = part_membros[mask]
    vitorias = disputa[disputa["Flag Vencedor"] == "SIM"]["Código Participante"].value_counts()

    return {
        "n_empresas": len(membros),
        "n_licitacoes_disputa_interna": len(lics_disputa_interna),
        "vitorias_por_empresa": vitorias,
    }

def desenhar_comunidade(G, comunidade, nomes, titulo, nucleo=None, salvar=None):
    """Desenha o subgrafo de uma comunidade, destacando o nucleo suspeito."""
    import matplotlib.pyplot as plt

    membros = list(comunidade)
    sub = G.subgraph(membros)
    nucleo = set(nucleo) if nucleo else set()

    fig, ax = plt.subplots(figsize=(13, 10))
    pos = nx.spring_layout(sub, k=0.8, seed=42, weight="weight")

    # Arestas: espessura proporcional ao peso (coparticipacoes)
    pesos = [sub[a][b]["weight"] for a, b in sub.edges()]
    nx.draw_networkx_edges(sub, pos, width=[p * 0.8 for p in pesos], alpha=0.4, ax=ax)

    # Nos: nucleo em vermelho, resto em azul
    cores = ["#e74c3c" if n in nucleo else "#3498db" for n in sub.nodes()]
    tamanhos = [sub.degree(n, weight="weight") * 80 + 200 for n in sub.nodes()]
    nx.draw_networkx_nodes(sub, pos, node_color=cores, node_size=tamanhos, alpha=0.9, ax=ax)

    # Rotulos: nome curto (primeiras 2 palavras)
    rotulos = {n: " ".join(str(nomes.get(n, n)).split()[:2]) for n in sub.nodes()}
    nx.draw_networkx_labels(sub, pos, rotulos, font_size=8, ax=ax)

    ax.set_title(titulo, fontsize=14)
    ax.axis("off")
    if salvar:
        plt.savefig(salvar, dpi=150, bbox_inches="tight")
    plt.show()