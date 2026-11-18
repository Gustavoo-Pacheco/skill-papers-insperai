"""montar_latex.py: transforma o JSON de extrair_entrada.py num projeto LaTeX no padrão do Insper AI.

Uso:
  python3 montar_latex.py <entrada.json> <pasta_saida> [--original paper.pdf] [--citacao autorano|numerico]
                          [--idioma pt|en] [--offline]

Gera em <pasta_saida>: main.tex, refs.bib, figuras/ e os arquivos do template (classe, estilos de bibliografia, logo).

Regras (formata-paper):
- O texto dos segmentos entra exatamente como está no JSON. Só muda a forma: classe, capa, legendas, citações.
- A ordem e a numeração de seções, figuras e tabelas são as do original, porque o texto cita "seção 5" e "figura 2".
- Figuras e tabelas de um PDF entram como recortes vetoriais do original (o texto delas não muda).
  O JSON traz as linhas de cada tabela, para a skill recompor em booktabs se a pessoa quiser.
- Citações numéricas [n] viram \\citep/\\citet com as chaves do refs.bib (completar_bib.py monta e confere).
"""
import argparse
import json
import re
import shutil
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
TEMPLATE = AQUI.parent / "template"
sys.path.insert(0, str(AQUI))

# Caracteres que o XCharter não tem: vão para o modo matemático
MAT = {
    "α": r"\alpha", "β": r"\beta", "γ": r"\gamma", "δ": r"\delta", "ε": r"\varepsilon", "ζ": r"\zeta", "η": r"\eta",
    "θ": r"\theta", "κ": r"\kappa", "λ": r"\lambda", "μ": r"\mu", "ν": r"\nu", "ξ": r"\xi", "π": r"\pi", "ρ": r"\rho",
    "σ": r"\sigma", "τ": r"\tau", "φ": r"\varphi", "χ": r"\chi", "ψ": r"\psi", "ω": r"\omega", "Γ": r"\Gamma",
    "∆": r"\Delta", "Δ": r"\Delta", "Θ": r"\Theta", "Λ": r"\Lambda", "Π": r"\Pi", "Σ": r"\Sigma", "Φ": r"\Phi",
    "Ω": r"\Omega", "≥": r"\geq", "≤": r"\leq", "≈": r"\approx", "≠": r"\neq", "→": r"\rightarrow",
    "←": r"\leftarrow", "↑": r"\uparrow", "↓": r"\downarrow", "⇒": r"\Rightarrow", "∈": r"\in", "∞": r"\infty",
    "√": r"\surd", "−": "-", "∑": r"\sum", "⋆": r"\star", "∼": r"\sim", "′": r"\prime", "∗": r"\ast",
    "⊂": r"\subset", "∩": r"\cap", "∪": r"\cup", "∀": r"\forall", "∃": r"\exists", "∂": r"\partial",
    "∇": r"\nabla", "⊕": r"\oplus", "⊗": r"\otimes", "≡": r"\equiv", "∝": r"\propto", "ℓ": r"\ell",
}
ESPECIAIS = {"\\": r"\textbackslash{}", "{": r"\{", "}": r"\}", "$": r"\$", "&": r"\&", "#": r"\#",
             "^": r"\textasciicircum{}", "_": r"\_", "~": r"\textasciitilde{}", "%": r"\%"}
URL = re.compile(r"https?://[^\s]+[^\s.,;:)\]]")
CIT = re.compile(r"\[(\d+(?:\s*[,–-]\s*\d+)*)\]")


def esc(t: str) -> str:
    """Escapa um texto puro para LaTeX, com URLs em \\url e símbolos fora do XCharter em matemática."""
    out, pos = [], 0
    for m in URL.finditer(t):
        out.append(_esc(t[pos:m.start()]))
        out.append(r"\url{" + m.group(0).replace("%", r"\%").replace("#", r"\#") + "}")
        pos = m.end()
    out.append(_esc(t[pos:]))
    return "".join(out)


def _esc(t):
    r = []
    for c in t:
        if c in ESPECIAIS:
            r.append(ESPECIAIS[c])
        elif c in MAT:
            r.append("$" + MAT[c] + "$")
        elif c == " ":
            r.append("~")
        elif c == "­":
            continue
        else:
            r.append(c)
    return "".join(r).replace("$$", "")


class Citacoes:
    """Troca [n] por \\citep{chave}; "Autor et al. [n]" por \\citet{chave}."""

    def __init__(self, chaves: dict, sobrenomes: dict):
        self.chaves, self.sobrenomes, self.usadas, self.faltando = chaves, sobrenomes, set(), set()

    def _lista(self, grupo):
        nums = []
        for parte in re.split(r"\s*,\s*", grupo):
            m = re.match(r"(\d+)\s*[–-]\s*(\d+)$", parte)
            nums += list(range(int(m.group(1)), int(m.group(2)) + 1)) if m else [int(parte)]
        ks = []
        for n in nums:
            if n in self.chaves:
                ks.append(self.chaves[n])
                self.usadas.add(n)
            else:
                self.faltando.add(n)
        return nums, ks

    def troca(self, texto_latex: str) -> str:
        out, pos = [], 0
        for m in CIT.finditer(texto_latex):
            nums, ks = self._lista(m.group(1))
            if not ks:
                continue
            antes = texto_latex[pos:m.start()]
            sob = self.sobrenomes.get(nums[0], "")
            nome = re.search(r"(?<![\w-])" + re.escape(sob) + r"(\s+et al\.|\s+(?:e|and|\\&)\s+[\w\u00c0-\u024f-]+)?\s*$",
                             antes) if sob and len(ks) == 1 else None
            if nome:  # "Ilse et al. [11]" -> "\citet{ilse...}" (o nome sai do texto porque o \citet o imprime)
                out.append(antes[:nome.start()] + r"\citet{" + ks[0] + "}")
            else:
                out.append(antes.rstrip(" ") + (" " if antes.endswith(" ") else "") + r"\citep{" + ",".join(ks) + "}")
            pos = m.end()
        out.append(texto_latex[pos:])
        return "".join(out)


def segs_latex(segs, cit: Citacoes | None) -> str:
    partes = []
    for t, st in segs:
        if st == "math":
            partes.append("$" + t + "$")
        elif st == "tex":
            partes.append(t)
        else:
            e = esc(t)
            if not e.strip():
                partes.append(e)
                continue
            ini, fim = e[:len(e) - len(e.lstrip())], e[len(e.rstrip()):]
            nucleo = e.strip()
            if st == "b":
                nucleo = r"\textbf{" + nucleo + "}"
            elif st == "i":
                nucleo = r"\emph{" + nucleo + "}"
            elif st == "bi":
                nucleo = r"\textbf{\emph{" + nucleo + "}}"
            elif st == "tt":
                nucleo = r"\texttt{" + nucleo + "}"
            elif st == "sub":
                nucleo = r"\textsubscript{" + nucleo + "}"
            elif st == "sup":
                nucleo = r"\textsuperscript{" + nucleo + "}"
            partes.append(ini + nucleo + fim)
    s = "".join(partes)
    return cit.troca(s) if cit else s


def titulo_runin(segs):
    """Parágrafo que começa com um título em negrito terminado em ponto ("Limitações.") vira \\paragraph."""
    if not segs or "b" not in segs[0][1]:
        return None, segs
    t = segs[0][0].strip()
    if 2 <= len(t) <= 120 and t.endswith((".", ":")):
        return t, [list(s) for s in segs[1:]]
    return None, segs


def dividir_legenda(segs):
    """"Título. Descrição" -> (título, descrição). O título é a primeira frase; o texto não muda."""
    texto = "".join(t for t, _ in segs)
    m = re.search(r"[.:!?](\s|$)", texto)
    if not m or m.end() > 200:
        return segs, []
    corte = m.end()
    a, b, n = [], [], 0
    for t, st in segs:
        if n + len(t) <= corte:
            a.append([t, st])
        elif n >= corte:
            b.append([t, st])
        else:
            a.append([t[:corte - n], st])
            b.append([t[corte - n:], st])
        n += len(t)
    if a:
        a[-1][0] = a[-1][0].rstrip()
    if b:
        b[0][0] = b[0][0].lstrip()
    return a, b


def recortar(original, pagina, bbox, destino: Path):
    """Recorte vetorial de uma região do PDF original, sem o texto que fica fora dela."""
    import pymupdf
    src = pymupdf.open(original)
    tmp = pymupdf.open()
    tmp.insert_pdf(src, from_page=pagina - 1, to_page=pagina - 1)
    pg = tmp[0]
    r = pymupdf.Rect(bbox) + (-2, -2, 2, 2)
    W, H = pg.rect.width, pg.rect.height
    for fora in (pymupdf.Rect(0, 0, W, r.y0), pymupdf.Rect(0, r.y1, W, H),
                 pymupdf.Rect(0, r.y0, r.x0, r.y1), pymupdf.Rect(r.x1, r.y0, W, r.y1)):
        if not fora.is_empty:
            pg.add_redact_annot(fora)
    pg.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE, graphics=pymupdf.PDF_REDACT_LINE_ART_NONE)
    out = pymupdf.open()
    novo = out.new_page(width=r.width, height=r.height)
    novo.show_pdf_page(novo.rect, tmp, 0, clip=r)
    out.save(destino, garbage=3, deflate=True)
    return r.width


def montar(dados, saida: Path, original=None, citacao="autorano", idioma=None, offline=False):
    saida.mkdir(parents=True, exist_ok=True)
    (saida / "figuras").mkdir(exist_ok=True)
    for f in ("insperai.cls", "insperai-autorano-pt.bst", "insperai-numerico-pt.bst", "insperai.mplstyle"):
        shutil.copy(TEMPLATE / f, saida / f)
    shutil.copy(TEMPLATE / "logo-insperai.png", saida / "figuras" / "logo-insperai.png")
    meta = dados.get("meta", {})
    idioma = idioma or meta.get("idioma", "pt")
    avisos = list(dados.get("avisos", []))

    # Referências -> refs.bib
    chaves, sobrenomes = {}, {}
    if dados.get("referencias"):
        from completar_bib import bib_de_texto, escrever_bib
        entradas = bib_de_texto(dados["referencias"], online=not offline, sem_ano="n.d." if idioma == "en" else "s.d.")
        escrever_bib(entradas, saida / "refs.bib")
        for e in entradas:
            chaves[e["n"]] = e["chave"]
            sobrenomes[e["n"]] = e.get("_sobrenome", "")
            if e.get("note", "").startswith("[VERIFICAR]"):
                avisos.append(f"Referência [{e['n']}] não confirmada (arXiv, Crossref, DataCite, OpenAlex, Semantic Scholar): marcada [VERIFICAR].")
    elif not (saida / "refs.bib").exists():
        (saida / "refs.bib").write_text("% Sem referências na entrada.\n", encoding="utf-8")
    cit = Citacoes(chaves, sobrenomes) if chaves else None

    opcoes = [o for o in (("english" if idioma == "en" else ""), ("numerico" if citacao == "numerico" else "")) if o]
    L = [r"\documentclass" + ("[" + ",".join(opcoes) + "]" if opcoes else "") + "{insperai}", ""]
    L.append(r"\graphicspath{{figuras/}}")
    L.append(r"\title{" + esc(meta.get("titulo", "")) + "}")
    if meta.get("subtitulo"):
        L.append(r"\subtitulo{" + esc(meta["subtitulo"]) + "}")
    autores = [a for a in meta.get("autores", []) if not a.get("ia")]
    removidos = [a["nome"] for a in meta.get("autores", []) if a.get("ia")]
    if removidos:
        avisos.append("IA removida da lista de autores (regra do lab): " + ", ".join(removidos) + ".")
    L.append(r"\author{" + r" \and ".join(esc(a["nome"]) for a in autores) + "}")
    if meta.get("data"):
        L.append(r"\data{" + esc(meta["data"]) + "}")
    notas = [*meta.get("outras_linhas_capa", []), *meta.get("links", [])]
    if notas:
        L.append(r"\notacapa{" + r" \\ ".join(esc(n) for n in notas) + "}")
        avisos.append("Linhas da capa original sem lugar no padrão (ficaram como nota da capa; pergunte se movem para "
                      "\"Código e dados\" ou saem): " + " | ".join(notas))
    if dados.get("resumo"):
        L.append(r"\resumo{" + "\n\n".join(segs_latex(p, cit) for p in dados["resumo"]) + "}")
    L += ["", r"\begin{document}", r"\maketitle", ""]

    cont = {"section": 0, "subsection": 0, "subsubsection": 0, "figure": 0, "table": 0}
    larg_texto_orig = None
    if original:
        import pymupdf
        doc = pymupdf.open(original)
        xs = [b[0] for p in doc for b in p.get_text("blocks") if len(b[4]) > 200]
        xe = [b[2] for p in doc for b in p.get_text("blocks") if len(b[4]) > 200]
        if xs:
            larg_texto_orig = sorted(xe)[len(xe) // 2] - sorted(xs)[len(xs) // 2]
    COL, TXT = 241.0, 493.0  # largura da coluna e do texto na classe (pt)

    for b in dados["blocos"]:
        t = b["tipo"]
        if t == "secao":
            cmd = {1: "section", 2: "subsection"}.get(b["nivel"], "subsubsection")
            if b.get("numero"):
                partes = [int(x) for x in b["numero"].split(".") if x]
                alvo = partes[-1]
                if cont[cmd] + 1 != alvo:
                    L.append(r"\setcounter{%s}{%d}" % (cmd, alvo - 1))
                cont[cmd] = alvo
                if cmd == "section":
                    cont["subsection"] = cont["subsubsection"] = 0
                L += [r"\%s{%s}" % (cmd, esc(b["titulo"])), ""]
            else:
                L += [r"\%s*{%s}" % (cmd, esc(b["titulo"])), ""]
        elif t == "paragrafo":
            tit, resto = titulo_runin(b["segmentos"])
            corpo = segs_latex(resto, cit).strip()
            L += [(r"\paragraph{" + segs_latex([[tit, ""]], cit) + "} " if tit else "") + corpo, ""]
        elif t == "lista":
            amb = "enumerate" if b.get("ordenada") else "itemize"
            L.append(r"\begin{%s}" % amb)
            for it in b["itens"]:
                L.append(r"  \item " + segs_latex(it, cit).strip())
            L += [r"\end{%s}" % amb, ""]
        elif t in ("figura", "tabela"):
            cnt = "figure" if t == "figura" else "table"
            n = b["numero"]
            arq = f"{t}-{n}.pdf"
            if b.get("arquivo"):
                arq = Path(b["arquivo"]).name
                fonte = Path(b["arquivo"])
                if fonte.exists():
                    shutil.copy(fonte, saida / "figuras" / arq)
                largura = r"\linewidth"
                dupla = b.get("largura") == "dupla"
            elif original and b.get("bbox"):
                w = recortar(original, b["pagina"], b["bbox"], saida / "figuras" / arq)
                ref = larg_texto_orig or w
                natural = w * (TXT / ref) if ref > COL * 1.3 else w  # mesma proporção da página original
                dupla = natural > COL * 1.15
                largura = (r"%.2f\textwidth" % min(1, natural / TXT)) if dupla else r"\linewidth"
            else:
                avisos.append(f"{t} {n}: sem arquivo nem recorte; inserida como marcador.")
                arq, dupla, largura = None, True, r"\linewidth"
            amb = cnt + ("*" if dupla else "")
            tit, desc = dividir_legenda(b.get("legenda", []))
            leg = r"\legenda{" + segs_latex(tit, cit) + "}{" + segs_latex(desc, cit) + "}"
            if cont[cnt] + 1 != n:
                leg = r"\setcounter{%s}{%d}" % (cnt, n - 1) + "\n" + leg
            cont[cnt] = n
            img = (r"\includegraphics[width=%s]{%s}" % (largura, arq)) if arq else r"\fbox{[%s %d]}" % (t.upper(), n)
            corpo = [img, leg] if t == "figura" else [leg, img]
            L += [r"\begin{%s}[tbp]" % amb, r"\centering", *corpo, r"\label{%s:%d}" % ("fig" if t == "figura" else "tab", n),
                  r"\end{%s}" % amb, ""]

    if chaves:
        L += [r"\bibliography{refs}", ""]
        if cit and cit.faltando:
            avisos.append("Citações sem referência na lista: " + ", ".join(f"[{n}]" for n in sorted(cit.faltando)))
        sobra = sorted(set(chaves) - (cit.usadas if cit else set()))
        if sobra:
            L.insert(L.index(r"\bibliography{refs}"), r"\nocite{" + ",".join(chaves[n] for n in sobra) + "}")
    L += [r"\end{document}", ""]
    (saida / "main.tex").write_text("\n".join(L), encoding="utf-8")
    (saida / "avisos-montagem.json").write_text(json.dumps(avisos, ensure_ascii=False, indent=1), encoding="utf-8")
    return avisos


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("json")
    ap.add_argument("saida")
    ap.add_argument("--original", help="PDF original, para recortar figuras e tabelas")
    ap.add_argument("--citacao", choices=["autorano", "numerico"], default="autorano")
    ap.add_argument("--idioma", choices=["pt", "en"])
    ap.add_argument("--offline", action="store_true", help="não consulta arXiv/Crossref/Semantic Scholar")
    a = ap.parse_args()
    dados = json.loads(Path(a.json).read_text(encoding="utf-8"))
    avisos = montar(dados, Path(a.saida), a.original, a.citacao, a.idioma, a.offline)
    print(f"main.tex gerado em {a.saida} ({len(avisos)} aviso(s)).")
    for x in avisos:
        print("  aviso:", x)


if __name__ == "__main__":
    main()
