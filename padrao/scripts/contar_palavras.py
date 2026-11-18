"""contar_palavras.py: conta as palavras do corpo de um paper e compara com o original (regra de ±10% da refaz).

Uso:
  python3 contar_palavras.py <original> [<novo>] [--tolerancia 0.10]

<original> e <novo> podem ser .pdf, .json (de extrair_entrada.py) ou main.tex.
Corpo = seções, parágrafos e listas, sem capa, resumo, legendas, tabelas, referências e apêndice.
Com dois arquivos, sai com 1 se a diferença passar da tolerância.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
PALAVRA = re.compile(r"[A-Za-zÀ-ÿ0-9]+(?:[-'][A-Za-zÀ-ÿ0-9]+)*")
APENDICE = re.compile(r"^(ap[êe]ndice|appendix)", re.I)


def contar_json(d):
    T = lambda segs: "".join(t for t, st in segs if st not in ("math", "tex"))  # noqa: E731
    n, no_apendice = 0, False
    for b in d.get("blocos", []):
        if b["tipo"] == "secao":
            no_apendice = no_apendice or bool(APENDICE.match(b["titulo"]))
            continue
        if no_apendice:
            continue
        if b["tipo"] == "paragrafo":
            n += len(PALAVRA.findall(T(b["segmentos"])))
        elif b["tipo"] == "lista":
            n += sum(len(PALAVRA.findall(T(i))) for i in b["itens"])
    return n


def contar_tex(tex):
    tex = re.sub(r"(?<!\\)%.*", "", tex)
    corpo = tex.split("\\maketitle", 1)[-1]
    corpo = re.split(r"\\bibliography\{|\\begin\{thebibliography\}|\\appendix\b", corpo)[0]
    corpo = re.sub(r"\\begin\{(figure|table|equation|align|tabular)\*?\}.*?\\end\{\1\*?\}", " ", corpo, flags=re.S)
    corpo = re.sub(r"\\(section|subsection|subsubsection|secaofaltando)\*?\{[^}]*\}", " ", corpo)
    corpo = re.sub(r"\$[^$]*\$", " x ", corpo)
    corpo = re.sub(r"\\(cite[tp]?|ref|label|url|href|includegraphics|setcounter)\*?(\[[^\]]*\])*\{[^}]*\}(\{[^}]*\})?", " ", corpo)
    corpo = re.sub(r"\\[a-zA-Z@]+\*?", " ", corpo)
    corpo = re.sub(r"[{}\\~]", " ", corpo)
    return len(PALAVRA.findall(corpo))


def contar(caminho):
    p = Path(caminho)
    if p.suffix == ".json":
        return contar_json(json.loads(p.read_text(encoding="utf-8")))
    if p.suffix == ".tex":
        return contar_tex(p.read_text(encoding="utf-8"))
    if p.suffix == ".pdf":
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            saida = Path(tmp) / "x.json"
            subprocess.run([sys.executable, str(AQUI / "extrair_entrada.py"), str(p), str(saida)], check=True,
                           capture_output=True)
            return contar_json(json.loads(saida.read_text(encoding="utf-8")))
    sys.exit(f"Formato não suportado: {p.suffix}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("original")
    ap.add_argument("novo", nargs="?")
    ap.add_argument("--tolerancia", type=float, default=0.10)
    a = ap.parse_args()
    n0 = contar(a.original)
    if not a.novo:
        print(f"{a.original}: {n0} palavras no corpo")
        return
    n1 = contar(a.novo)
    dif = (n1 - n0) / n0 if n0 else 0
    dentro = abs(dif) <= a.tolerancia
    print(f"original: {n0} palavras | novo: {n1} palavras | diferença: {dif:+.1%} "
          f"(limite ±{a.tolerancia:.0%}, faixa {round(n0 * (1 - a.tolerancia))}–{round(n0 * (1 + a.tolerancia))})")
    print("DENTRO DA FAIXA" if dentro else ("CURTO DEMAIS" if dif < 0 else "LONGO DEMAIS"))
    sys.exit(0 if dentro else 1)


if __name__ == "__main__":
    main()
