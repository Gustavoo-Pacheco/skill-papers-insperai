"""recortar_figuras.py: recorta as figuras e tabelas de um PDF como PDFs vetoriais (para refaz e cria reaproveitarem).

Uso:
  python3 recortar_figuras.py <entrada.json> <original.pdf> <pasta-figuras> [--so figura-3,tabela-1]

Usa as regiões (página e bbox) que extrair_entrada.py achou. Gera figura-N.pdf e tabela-N.pdf, sem o texto
que fica fora da região. Inclua com \\includegraphics[width=\\linewidth]{figura-N.pdf}.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from montar_latex import recortar  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("json")
    ap.add_argument("pdf")
    ap.add_argument("pasta")
    ap.add_argument("--so", help="lista separada por vírgula, por exemplo figura-3,tabela-1")
    a = ap.parse_args()
    dados = json.loads(Path(a.json).read_text(encoding="utf-8"))
    pasta = Path(a.pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    filtro = set(a.so.split(",")) if a.so else None
    for b in dados.get("blocos", []):
        if b["tipo"] not in ("figura", "tabela") or not b.get("bbox"):
            continue
        nome = f"{b['tipo']}-{b['numero']}"
        if filtro and nome not in filtro:
            continue
        w = recortar(a.pdf, b["pagina"], b["bbox"], pasta / f"{nome}.pdf")
        leg = "".join(t for t, _ in b.get("legenda", []))[:70]
        print(f"{nome}.pdf  (p. {b['pagina']}, {w:.0f} pt de largura)  {leg}")


if __name__ == "__main__":
    main()
