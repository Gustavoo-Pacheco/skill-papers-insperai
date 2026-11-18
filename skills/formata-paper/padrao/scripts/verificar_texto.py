"""verificar_texto.py: confere se a formata-paper não mudou nenhuma palavra do paper.

Uso:
  python3 verificar_texto.py <original> <saida.pdf> [--relatorio relatorio.md]

<original> pode ser o PDF de entrada ou o JSON de extrair_entrada.py (para entradas .docx, .md e .tex,
em que o JSON é a leitura exata do arquivo).

Compara as palavras do original com as do PDF gerado. Normaliza só o que é forma:
- espaços, quebra de linha e hifenização de fim de linha;
- marcas de citação: [12] e (Silva et al., 2024) saem dos dois lados;
- números de página, a lista de referências (é refeita pelo .bib) e o texto fixo da capa do lab;
- blocos que só mudaram de lugar (figuras e tabelas flutuam) contam como "movidos", não como diferença.

Sai com 0 quando não há diferença real e com 1 quando há, listando cada trecho com contexto.
"""
import argparse
import difflib
import json
import re
import sys
import unicodedata
from pathlib import Path

# Texto fixo da capa do lab: logo, afiliação, e-mail, rótulo do resumo e a data (\\today quando o original não tem)
CAPA_LAB = {"insper", "ai", "contato", "insperai", "com", "br", "resumo", "abstract", "de", "janeiro", "fevereiro", "março",
            "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro", "january",
            "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"}
REFS = re.compile(r"^\s*(\d+\s+)?(Referências|Referências bibliográficas|Bibliografia|References|Bibliography)\s*$", re.M)
CIT_NUM = re.compile(r"\[\d+(?:\s*[,–-]\s*\d+)*\]")
ANO = r"(?:(?:19|20)\d\d[a-z]?|s\.d\.|n\.d\.)"
CIT_AUTOR = re.compile(r"\((?:[^()]{0,200}?" + ANO + r")(?:\s*[;,]\s*[^()]{0,200}?" + ANO + r")*\)")
ANO_SOLTO = re.compile(r"\b(?:et al\.|[A-ZÀ-Ý][\wÀ-ÿ-]+)\s*\(" + ANO + r"\)")
# Símbolos que viram token próprio (o espaço em volta deles depende do motor, não do texto)
SIMBOLOS = re.compile(r"([α-ωΑ-Ω∆∇∂∑∏√∞≈≠≤≥±×÷→←⇒∈∼])")


def texto_pdf(caminho):
    """Texto do PDF sem número de página e sem frações empilhadas (½), cuja ordem de leitura depende do desenho."""
    import pymupdf
    from collections import Counter
    doc = pymupdf.open(caminho)
    tam = Counter()
    for p in doc:
        for b in p.get_text("dict")["blocks"]:
            for ln in b.get("lines", []):
                for sp in ln["spans"]:
                    tam[round(sp["size"], 1)] += len(sp["text"])
    corpo = tam.most_common(1)[0][0] if tam else 10
    paginas = []
    for p in doc:
        H = p.rect.height
        spans = [(ln, sp) for b in p.get_text("dict")["blocks"] for ln in b.get("lines", []) for sp in ln["spans"]]
        pequenos = [sp for _, sp in spans if sp["size"] < 0.8 * corpo and 0 < len(sp["text"].strip()) <= 4]
        fracao = set()
        for s1 in pequenos:
            for s2 in pequenos:
                a, b = s1["bbox"], s2["bbox"]
                if s1 is not s2 and min(a[2], b[2]) - max(a[0], b[0]) > 0 and 2.5 < b[1] - a[1] < 9:
                    fracao.update((id(s1), id(s2)))
        linhas = []
        for b in p.get_text("dict")["blocks"]:
            for ln in b.get("lines", []):
                t = "".join(sp["text"] for sp in ln["spans"] if id(sp) not in fracao)
                y0, y1 = ln["bbox"][1], ln["bbox"][3]
                if re.fullmatch(r"\s*\d{1,3}\s*", t) and (y1 < 0.07 * H or y0 > 0.92 * H):
                    continue  # número de página
                if t.strip():
                    linhas.append(t)
        paginas.append("\n".join(linhas))
    return "\n".join(paginas)


def texto_json(caminho):
    d = json.loads(Path(caminho).read_text(encoding="utf-8"))
    T = lambda segs: "".join(t for t, st in segs if st != "math")  # noqa: E731
    partes = [d.get("meta", {}).get("titulo", ""), d.get("meta", {}).get("subtitulo", "")]
    partes += [a["nome"] for a in d.get("meta", {}).get("autores", []) if not a.get("ia")]
    partes += [T(p) for p in d.get("resumo", [])]
    for b in d.get("blocos", []):
        if b["tipo"] == "secao":
            partes.append(f"{b.get('numero', '')} {b['titulo']}")
        elif b["tipo"] == "paragrafo":
            partes.append(T(b["segmentos"]))
        elif b["tipo"] == "lista":
            partes += [T(i) for i in b["itens"]]
        elif b["tipo"] in ("figura", "tabela"):
            partes.append(f"{'Figura' if b['tipo'] == 'figura' else 'Tabela'} {b['numero']} " + T(b.get("legenda", [])))
    return "\n".join(partes)


def normalizar(texto):
    texto = unicodedata.normalize("NFKC", texto)
    corte = list(REFS.finditer(texto))
    if corte:
        texto = texto[:corte[-1].start()]
    texto = texto.replace("\u0394", "\u2206").replace("\u00b5", "\u03bc")  # Δ e ∆, µ e μ: mesmo símbolo
    texto = re.sub(r"(\w)-\n(\w)", r"\1\2", texto)  # hifenização de fim de linha
    texto = CIT_NUM.sub(" ", texto)
    texto = ANO_SOLTO.sub(lambda m: m.group(0)[:m.group(0).rfind("(")], texto)  # "Ho et al. (2020)" -> "Ho et al."
    texto = CIT_AUTOR.sub(" ", texto)
    texto = re.sub(r"(\w)[-‐‑](\w)", r"\1\2", texto)  # "pré-treinada" e "pré-\ntreinada" ficam iguais
    texto = SIMBOLOS.sub(r" \1 ", texto)
    return re.findall(r"\w+|[∆∇∂∑∏√∞≈≠≤≥±×÷→←⇒∈∼]", texto)


def comparar(a, b):
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    falta, sobra = [], []  # (índice inicial, tokens)
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op in ("delete", "replace"):
            falta.append((i1, a[i1:i2]))
        if op in ("insert", "replace"):
            sobra.append((j1, b[j1:j2]))
    # Trechos que só mudaram de lugar: casam entre o que falta e o que sobra
    fa = [t for _, ch in falta for t in ch + ["\x00"]]
    so = [t for _, ch in sobra for t in ch + ["\x01"]]
    sm2 = difflib.SequenceMatcher(None, fa, so, autojunk=False)
    movido_fa, movido_so = set(), set()
    for blk in sm2.get_matching_blocks():
        if blk.size >= 3:
            movido_fa.update(range(blk.a, blk.a + blk.size))
            movido_so.update(range(blk.b, blk.b + blk.size))

    def restos(lista, movidos, sep, origem):
        out, k = [], 0
        for ini, ch in lista:
            atual = []
            for off, t in enumerate(ch):
                if k + off not in movidos:
                    atual.append((ini + off, t))
            k += len(ch) + 1
            if atual:
                out.append(atual)
        return out

    n_mov = len(movido_fa)
    return restos(falta, movido_fa, "\x00", a), restos(sobra, movido_so, "\x01", b), n_mov, sm.ratio()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("original")
    ap.add_argument("saida")
    ap.add_argument("--relatorio")
    ap.add_argument("--ignorar", action="append", default=[],
                    help="palavra que pode sobrar ou faltar (ex.: nome de uma IA removida dos autores)")
    a = ap.parse_args()
    orig = texto_json(a.original) if a.original.endswith(".json") else texto_pdf(a.original)
    A, B = normalizar(orig), normalizar(texto_pdf(a.saida))
    falta, sobra, n_mov, ratio = comparar(A, B)
    ignorar = {w.lower() for w in a.ignorar}
    falta = [g for g in falta if any(t.lower() not in ignorar for _, t in g)]
    sobra = [g for g in sobra if any(t.lower() not in CAPA_LAB | ignorar and not t.isdigit() for _, t in g)]

    def ctx(seq, grupo):
        i0, i1 = grupo[0][0], grupo[-1][0] + 1
        return " ".join(seq[max(0, i0 - 6):i0]) + " [[" + " ".join(t for _, t in grupo) + "]] " + " ".join(seq[i1:i1 + 6])

    linhas = [f"# Verificação de texto idêntico", "",
              f"- Palavras no original: {len(A)}; na saída: {len(B)}",
              f"- Palavras que só mudaram de lugar (figuras e tabelas): {n_mov}",
              f"- Trechos que faltam na saída: {len(falta)} ({sum(len(g) for g in falta)} palavras)",
              f"- Trechos que sobram na saída: {len(sobra)} ({sum(len(g) for g in sobra)} palavras)", ""]
    if falta:
        linhas += ["## Faltam na saída", ""] + [f"- {ctx(A, g)}" for g in falta[:80]] + [""]
    if sobra:
        linhas += ["## Sobram na saída", ""] + [f"- {ctx(B, g)}" for g in sobra[:80]] + [""]
    ok = not falta and not sobra
    linhas.append("RESULTADO: " + ("TEXTO IDÊNTICO" if ok else "HÁ DIFERENÇAS (revise antes de entregar)"))
    rel = "\n".join(linhas)
    if a.relatorio:
        Path(a.relatorio).write_text(rel + "\n", encoding="utf-8")
    print(rel)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
