"""Download automatizado dos dados de licitacoes do Portal da Transparencia."""

import io
import zipfile
from pathlib import Path

import requests

URL_BASE = "https://dadosabertos-download.cgu.gov.br/PortalDaTransparencia/saida/licitacoes/{aaaamm}_Licitacoes.zip"
RAIZ_PROJETO = Path(__file__).resolve().parent.parent
PASTA_RAW = RAIZ_PROJETO / "data" / "raw"

# O portal recusa requisicoes sem cara de navegador; o User-Agent resolve
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


def baixar_mes(aaaamm: str, pasta_destino: Path = PASTA_RAW) -> None:
    """Baixa e extrai o ZIP de licitacoes de um mes (formato AAAAMM)."""
    destino = Path(pasta_destino)
    destino.mkdir(parents=True, exist_ok=True)

    # Se o CSV principal do mes ja existe, pula (idempotencia)
    if list(destino.glob(f"{aaaamm}_Licita*")):
        print(f"{aaaamm}: ja existe, pulando")
        return

    url = URL_BASE.format(aaaamm=aaaamm)
    print(f"{aaaamm}: baixando...")
    resposta = requests.get(url, headers=HEADERS, timeout=120)
    resposta.raise_for_status()  # explode com erro claro se vier 404/500

    with zipfile.ZipFile(io.BytesIO(resposta.content)) as zf:
        if not zf.namelist():
            print(f"{aaaamm}: ZIP VAZIO no servidor, pulando")
            return
        zf.extractall(destino)
    print(f"{aaaamm}: ok ({len(zf.namelist())} arquivos)")


def baixar_ano(ano: int, pasta_destino: Path = PASTA_RAW) -> None:
    """Baixa os 12 meses de um ano, sem parar se um mes falhar."""
    falhas = []
    for mes in range(1, 13):
        aaaamm = f"{ano}{mes:02d}"
        try:
            baixar_mes(aaaamm, pasta_destino)
        except Exception as erro:
            print(f"{aaaamm}: FALHOU ({erro})")
            falhas.append(aaaamm)
    if falhas:
        print(f"\nMeses com falha: {falhas}")


if __name__ == "__main__":
    baixar_ano(2023)
    for mes in range(1, 5):  # 2024 so tem ate abril
        baixar_mes(f"2024{mes:02d}")