"""extrair_entrada.py: lê um paper de entrada e devolve texto e estrutura num JSON comum.

Uso:
  python3 extrair_entrada.py <arquivo> <saida.json>

Formatos: .pdf, .docx (inclusive export do Google Docs), .md, .tex.
Dependência: PyMuPDF para PDF (`python3 -m pip install pymupdf`).

O JSON é o contrato entre as skills:
  meta        título, subtítulo, autores (com "ia": true para IA), afiliação, data, idioma
  resumo      lista de parágrafos
  blocos      sequência de {"tipo": "secao"|"paragrafo"|"lista"|"figura"|"tabela", ...}
  referencias lista de {"n", "texto"}
  avisos      o que a extração não conseguiu decidir sozinha (para a skill revisar)
Um parágrafo é uma lista de segmentos [texto, estilo]. Estilos: "" (normal), "b", "i", "bi", "tt" (monoespaçado),
"sub" e "sup" (índice e expoente),
"math" (LaTeX de matemática, como \\frac{1}{2}) e "tex" (LaTeX original de uma entrada .tex).
O texto dos segmentos é exatamente o da entrada; a formata nunca o altera.
"""
import json
import re
import sys
import zipfile
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET

NOMES_IA = re.compile(r"\b(claude|chatgpt|gpt-?\d|openai|anthropic|gemini|copilot|llama|mistral|deepseek|grok|perplexity)\b", re.I)
LEGENDA = re.compile(r"^\s*(Figura|Figure|Fig\.|Tabela|Table|Quadro)\s+(\d+)\s*[:.|–—-]\s*", re.I)
SECAO_RESUMO = re.compile(r"^\s*(Resumo|Abstract)\s*$", re.I)
SECAO_REFS = re.compile(r"^\s*(\d+\s+)?(Referências|Referências bibliográficas|Bibliografia|References|Bibliography)\s*$", re.I)
ITEM_LISTA = re.compile(r"^\s*(\d{1,2}[.)]|[•●▪◦–-])\s+")


def idioma(texto: str) -> str:
    pt = len(re.findall(r"\b(não|são|também|para|uma|dos|das|com|que|é)\b", texto, re.I))
    en = len(re.findall(r"\b(the|and|with|that|is|are|of|for|this)\b", texto, re.I))
    return "pt" if pt >= en else "en"


def autor(nome: str) -> dict:
    nome = nome.strip()
    return {"nome": nome, "ia": bool(NOMES_IA.search(nome))}


def juntar(segs):
    """Funde segmentos vizinhos de mesmo estilo."""
    out = []
    for t, s in segs:
        if out and out[-1][1] == s:
            out[-1][0] += t
        elif t:
            out.append([t, s])
    return out


def texto_de(segs) -> str:
    return "".join(t for t, _ in segs)


def cortar_inicio(segs, n):
    """Remove os n primeiros caracteres do texto, atravessando segmentos (ex.: marcador "5." ou "•")."""
    out = [list(x) for x in segs]
    while out and n > 0:
        if len(out[0][0]) <= n:
            n -= len(out[0][0])
            out.pop(0)
        else:
            out[0][0] = out[0][0][n:]
            n = 0
    while out and not out[0][0].strip():
        out.pop(0)
    if out:
        out[0][0] = out[0][0].lstrip()
    return out


# ----------------------------------------------------------------------------- PDF
def _estilo(span) -> str:
    f = span["font"].lower()
    flags = span["flags"]
    if "mono" in f or "courier" in f or re.search(r"(^|[^a-z])(lmmono|cmtt|sfmono|menlo|consol)", f) or flags & 8:
        return "tt"
    b = "bold" in f or "black" in f or "semibold" in f or flags & 16
    i = "italic" in f or "oblique" in f or flags & 2
    return ("b" if b else "") + ("i" if i else "")


def _linha(line):
    """Reconstrói o texto de uma linha a partir dos caracteres, inserindo espaços pelos vãos."""
    segs, prev = [], None
    maior = max((sp["size"] for sp in line["spans"]), default=0)
    centros = sorted((sp["bbox"][1] + sp["bbox"][3]) / 2 for sp in line["spans"] if sp["size"] == maior)
    base = centros[len(centros) // 2] if centros else None  # centro vertical do texto normal da linha
    for span in line["spans"]:
        if span.get("_pular"):
            continue
        if span.get("_fracao"):
            segs.append([span["_fracao"], "math"])
            prev = span["_x1"]
            continue
        st = _estilo(span)
        size = span["size"]
        buf = ""
        for ch in span["chars"]:
            c = ch["c"]
            x0, x1 = ch["bbox"][0], ch["bbox"][2]
            if prev is not None and c != " " and not buf.endswith(" "):
                gap = x0 - prev
                if gap > 0.18 * size and not (segs and segs[-1][0].endswith(" ")):
                    buf += " "
            buf += c
            prev = x1
        if st in ("i", "bi") and not re.search(r"[^\W\d_]", buf):
            st = st.replace("i", "")  # vírgula ou sinal em fonte itálica de matemática: sem itálico
        # Índice (F₁) ou expoente (x²): fonte menor, fora da linha de base
        if base is not None and span["size"] < 0.8 * maior and buf.strip() and len(buf.strip()) <= 12:
            dy = (span["bbox"][1] + span["bbox"][3]) / 2 - base
            if dy > 1.2:
                st = "sub"
            elif dy < -1.2:
                st = "sup"
        segs.append([buf, st])
    segs = juntar(segs)
    if segs:
        segs[0][0] = segs[0][0].lstrip()
        segs[-1][0] = segs[-1][0].rstrip()
    return segs


def _colunas(blocos, largura):
    meio = largura / 2
    esq = [b for b in blocos if b["bbox"][2] < meio + 10]
    dir_ = [b for b in blocos if b["bbox"][0] > meio - 10]
    total = sum(_n_chars(b) for b in blocos) or 1
    cheio = sum(_n_chars(b) for b in blocos if b not in esq and b not in dir_)
    if esq and dir_ and cheio < 0.3 * total and sum(_n_chars(b) for b in dir_) > 0.15 * total:
        cheios = [b for b in blocos if b not in esq and b not in dir_]
        chave = lambda b: b["bbox"][1]  # noqa: E731
        return sorted(cheios, key=chave) + sorted(esq, key=chave) + sorted(dir_, key=chave)
    return sorted(blocos, key=lambda b: (b["bbox"][1], b["bbox"][0]))


def _marcar_fracoes(blocos, corpo):
    """Fração em linha (\\frac{1}{2}): numerador e denominador pequenos, um sobre o outro. O PDF os guarda como
    texto solto em linhas diferentes; aqui viram um segmento "math" no lugar do numerador."""
    pequenos = [sp for b in blocos for ln in b["lines"] for sp in ln["spans"]
                if sp["size"] < 0.8 * corpo and "".join(c["c"] for c in sp["chars"]).strip()]
    n = 0
    for s1 in pequenos:
        if s1.get("_pular") or s1.get("_fracao"):
            continue
        for s2 in pequenos:
            if s2 is s1 or s2.get("_pular") or s2.get("_fracao"):
                continue
            a, b = s1["bbox"], s2["bbox"]
            sobrepoe = min(a[2], b[2]) - max(a[0], b[0])
            if sobrepoe > 0.5 * min(a[2] - a[0], b[2] - b[0]) and 2.5 < b[1] - a[1] < 9 and abs(s1["size"] - s2["size"]) < 0.5:
                num = "".join(c["c"] for c in s1["chars"]).strip()
                den = "".join(c["c"] for c in s2["chars"]).strip()
                s1["_fracao"] = "\\frac{%s}{%s}" % (num, den)
                s1["_x1"] = max(a[2], b[2])
                s2["_pular"] = True
                n += 1
                break
    return n


def _graficos(page):
    """Todos os elementos gráficos da página (traços, filetes de tabela, imagens)."""
    import pymupdf
    itens = [pymupdf.Rect(d["rect"]) for d in page.get_drawings() if d["rect"].width >= 1 or d["rect"].height >= 1]
    itens += [pymupdf.Rect(img["bbox"]) for img in page.get_image_info()]
    return itens


def _texto_tabela(page, reg):
    """Linhas da tabela, cada uma como lista de [x, texto] por célula (vãos grandes separam células)."""
    palavras = page.get_text("words", clip=reg)
    linhas = []
    for w in sorted(palavras, key=lambda w: (round(w[1]), w[0])):
        if linhas and abs(linhas[-1]["y"] - w[1]) < 2.5:
            linhas[-1]["w"].append(w)
        else:
            linhas.append({"y": w[1], "w": [w]})
    out = []
    for ln in linhas:
        ws = sorted(ln["w"], key=lambda w: w[0])
        celulas = [[round(ws[0][0], 1), ws[0][4]]]
        fim = ws[0][2]
        for w in ws[1:]:
            if w[0] - fim > 6:
                celulas.append([round(w[0], 1), w[4]])
            else:
                celulas[-1][1] += " " + w[4]
            fim = w[2]
        out.append(celulas)
    return out


def _n_chars(b):
    return sum(len(c["c"].strip()) for ln in b["lines"] for s in ln["spans"] for c in s["chars"])


def _regiao(page, cap, tipo, blocos_texto, graf, corpo_rects, limite_sup):
    """Região de uma figura (tudo entre o último parágrafo acima e a legenda) ou de uma tabela
    (tudo entre a legenda e o próximo parágrafo abaixo), restrita à coluna da legenda."""
    import pymupdf
    w = page.rect.width
    if cap.width < 0.6 * w:
        faixa_x = (cap.x0 - 5, cap.x1 + 5)
    else:
        faixa_x = (0, w)
    no_x = lambda r: r.x1 > faixa_x[0] and r.x0 < faixa_x[1]  # noqa: E731
    if tipo == "figura":
        ini = max([r.y1 for r in corpo_rects if r.y1 <= cap.y0 + 2 and no_x(r)] + [limite_sup])
        fim = cap.y0
    else:
        ini = cap.y1
        fim = min([r.y0 for r in corpo_rects if r.y0 >= cap.y1 - 2 and no_x(r)] + [page.rect.height * 0.94])
    dentro = [g for g in graf if g.y0 >= ini - 3 and g.y1 <= fim + 3 and no_x(g)]
    dentro += [pymupdf.Rect(b["bbox"]) for b in blocos_texto
               if b["bbox"][1] >= ini - 3 and b["bbox"][3] <= fim + 3 and no_x(pymupdf.Rect(b["bbox"]))]
    if tipo == "tabela" and dentro:
        # Uma tabela é um bloco contíguo: corta no primeiro vão vertical grande (o que vem depois é outra coisa)
        dentro.sort(key=lambda r: r.y0)
        fundo, manter = dentro[0].y1, [dentro[0]]
        for r in dentro[1:]:
            if r.y0 > fundo + 9:
                break
            manter.append(r)
            fundo = max(fundo, r.y1)
        dentro = manter
    if tipo == "tabela" and not dentro:
        return _regiao(page, cap, "figura", blocos_texto, graf, corpo_rects, limite_sup)
    if not dentro:
        return None
    reg = pymupdf.Rect(dentro[0])
    for r in dentro[1:]:
        reg |= r
    return reg if reg.height > 8 else None


def extrair_pdf(caminho: Path) -> dict:
    try:
        import pymupdf
    except ImportError:
        sys.exit("Falta o PyMuPDF. Instale com: python3 -m pip install pymupdf")
    doc = pymupdf.open(caminho)
    avisos = []

    # Tamanho do corpo e títulos pelo índice do PDF, quando existe
    tam = Counter()
    for page in doc:
        for b in page.get_text("dict")["blocks"]:
            for ln in b.get("lines", []):
                for s in ln["spans"]:
                    tam[round(s["size"], 1)] += len(s["text"].strip())
    corpo = tam.most_common(1)[0][0]
    toc = [(lvl, re.sub(r"\s+", "", t).lower(), t.strip(), p) for lvl, t, p in doc.get_toc()]

    # Cabeçalhos e rodapés repetidos
    repet = Counter()
    for page in doc:
        h = page.rect.height
        for b in page.get_text("blocks"):
            if b[1] < 0.06 * h or b[3] > 0.93 * h:
                repet[re.sub(r"\d+", "#", b[4].strip())] += 1
    lixo = {k for k, v in repet.items() if v >= max(3, len(doc) // 2)}

    linhas = []  # (pagina, bbox, segmentos, tamanho, bloco_id)
    figuras, tabelas = [], []
    for pno, page in enumerate(doc):
        h = page.rect.height
        raw = page.get_text("rawdict")
        blocos = [b for b in raw["blocks"] if b["type"] == 0 and b["lines"]]
        _marcar_fracoes(blocos, corpo)
        graf = _graficos(page)
        legendas = []
        for b in blocos:
            primeira = "".join(c["c"] for s in b["lines"][0]["spans"] for c in s["chars"])
            m = LEGENDA.match(primeira.replace("\u00a0", " "))
            if m:
                legendas.append((m, b))
        # Legenda que continua num bloco logo abaixo (mesma margem, sem vão) faz parte da legenda
        ids_leg = {id(b) for _, b in legendas}
        for _, b in legendas:
            fim = b["bbox"][3]
            for c in sorted(blocos, key=lambda c: c["bbox"][1]):
                if id(c) in ids_leg or c["bbox"][1] < fim - 1:
                    continue
                if c["bbox"][1] - fim < 4 and abs(c["bbox"][0] - b["bbox"][0]) < 4:
                    b["lines"] = b["lines"] + c["lines"]
                    b["bbox"] = (b["bbox"][0], b["bbox"][1], max(b["bbox"][2], c["bbox"][2]), c["bbox"][3])
                    ids_leg.add(id(c))
                    fim = c["bbox"][3]
                elif c["bbox"][1] - fim >= 4:
                    break
        corpo_rects = [pymupdf.Rect(b["bbox"]) for b in blocos if id(b) not in ids_leg and _n_chars(b) > 120
                       and abs(b["lines"][0]["spans"][0]["size"] - corpo) < 0.6]
        outros_textos = [b for b in blocos if id(b) not in ids_leg]
        # Figura: tudo entre o último parágrafo acima e a legenda. Tabela: entre a legenda e o próximo parágrafo.
        excluir = []
        for m, b in sorted(legendas, key=lambda mb: mb[1]["bbox"][1]):
            tipo = "tabela" if m.group(1).lower().startswith(("tab", "qua")) else "figura"
            lb = pymupdf.Rect(b["bbox"])
            outras_leg = [pymupdf.Rect(x["bbox"]) for _, x in legendas if x is not b]
            reg = _regiao(page, lb, tipo, outros_textos, graf, corpo_rects + excluir + outras_leg, 0)
            seg_leg = juntar([s for ln in b["lines"] for s in (_linha(ln) + [[" ", ""]])])
            item = {"tipo": tipo, "numero": int(m.group(2)), "rotulo": m.group(0).strip(),
                    "legenda": _limpar_legenda(seg_leg, m.group(0)), "pagina": pno + 1,
                    "bbox": [round(v, 1) for v in (reg if reg else lb)], "largura": "dupla", "_y": lb.y0}
            if reg is None:
                avisos.append(f"{tipo} {m.group(2)} (p. {pno + 1}): não achei a região gráfica; revise o bbox.")
            else:
                item["largura"] = "simples" if reg.width < 0.45 * page.rect.width else "dupla"
                excluir.append(reg + (-2, -2, 2, 2))
                if tipo == "tabela":
                    item["linhas"] = _texto_tabela(page, reg)
            excluir.append(lb)
            (tabelas if tipo == "tabela" else figuras).append(item)
        fora = lambda b: not any(pymupdf.Rect(b["bbox"]).intersects(e) and (pymupdf.Rect(b["bbox"]) & e).get_area()  # noqa: E731
                                 > 0.5 * pymupdf.Rect(b["bbox"]).get_area() for e in excluir)
        for b in _colunas([b for b in blocos if fora(b)], page.rect.width):
            txt = "".join(c["c"] for ln in b["lines"] for s in ln["spans"] for c in s["chars"]).strip()
            if re.sub(r"\d+", "#", txt) in lixo or re.fullmatch(r"\d{1,3}", txt):
                continue
            for ln in b["lines"]:
                segs = _linha(ln)
                if not texto_de(segs).strip():
                    continue
                ant = linhas[-1] if linhas else None
                if ant and ant["p"] == pno and abs(ant["bbox"][1] - ln["bbox"][1]) < 2.5 \
                        and 0 <= ln["bbox"][0] - ant["bbox"][2] < 30:
                    st = ant["segs"][-1][1] if ant["segs"][-1][1] == segs[0][1] else ""
                    ant["segs"] = juntar(ant["segs"] + [[" ", st]] + segs)
                    ant["partes"].append(texto_de(segs).strip())  # a capa usa as partes para separar autores
                    ant["bbox"] = (ant["bbox"][0], ant["bbox"][1], ln["bbox"][2], max(ant["bbox"][3], ln["bbox"][3]))
                    ant["tam"] = max(ant["tam"], max(s["size"] for s in ln["spans"]))
                    continue
                linhas.append({"p": pno, "bbox": tuple(ln["bbox"]), "segs": segs, "partes": [texto_de(segs).strip()],
                               "tam": max(s["size"] for s in ln["spans"]), "bloco": id(b), "bx0": b["bbox"][0],
                               "negrito": all("b" in x[1] for x in segs if x[0].strip()), "so": len(b["lines"]) == 1})

    # Número de seção que veio numa linha separada do título ("1" + "Introdução")
    juntas = []
    for ln in linhas:
        if juntas and re.fullmatch(r"\d+(\.\d+)*\.?", texto_de(juntas[-1]["segs"]).strip()) and ln["p"] == juntas[-1]["p"] \
                and abs(ln["bbox"][1] - juntas[-1]["bbox"][1]) < 4 and _titulo_toc(texto_de(ln["segs"]), toc):
            ant = juntas.pop()
            ln = dict(ln, segs=[[texto_de(ant["segs"]).strip() + " ", ln["segs"][0][1]]] + ln["segs"], bbox=ant["bbox"][:2] + ln["bbox"][2:])
        juntas.append(ln)
    linhas = juntas

    # Classificação das linhas
    out = {"fonte": {"arquivo": caminho.name, "formato": "pdf", "paginas": len(doc)}, "meta": {}, "resumo": [],
           "blocos": [], "referencias": [], "avisos": avisos}
    i = 0
    # Capa: tudo antes do "Resumo"/"Abstract" ou da primeira seção
    capa = []
    while i < len(linhas):
        t = texto_de(linhas[i]["segs"])
        if SECAO_RESUMO.match(t) or _titulo_toc(t, toc) or re.match(r"^\s*1\.?\s+[A-ZÁÉÍÓÚ]", t):
            break
        capa.append(linhas[i])
        i += 1
    _meta_da_capa(out, capa, corpo)

    if i < len(linhas) and SECAO_RESUMO.match(texto_de(linhas[i]["segs"])):
        i += 1
        paras = []
        while i < len(linhas) and not _titulo_toc(texto_de(linhas[i]["segs"]), toc) \
                and not re.match(r"^\s*1\.?\s+[A-ZÁÉÍÓÚ]", texto_de(linhas[i]["segs"])):
            paras.append(linhas[i])
            i += 1
        out["resumo"] = [p for p in _paragrafos(paras, corpo, toc)[0] if p["tipo"] == "paragrafo"]
        out["resumo"] = [p["segmentos"] for p in out["resumo"]]

    resto = linhas[i:]
    corte = next((k for k, ln in enumerate(resto) if SECAO_REFS.match(texto_de(ln["segs"]))), None)
    corpo_linhas = resto if corte is None else resto[:corte]
    refs_linhas = [] if corte is None else resto[corte + 1:]
    blocos, extra = _paragrafos(corpo_linhas, corpo, toc)
    out["avisos"] += extra
    # Insere figuras e tabelas na posição em que aparecem
    flutuantes = sorted(figuras + tabelas, key=lambda f: (f["pagina"], f["_y"]))
    final, fi = [], 0
    for blk in blocos:
        while fi < len(flutuantes) and (flutuantes[fi]["pagina"], flutuantes[fi]["_y"]) <= (blk.get("_p", 0) + 1, blk.get("_y", 0)):
            final.append(flutuantes[fi])
            fi += 1
        final.append(blk)
    final += flutuantes[fi:]
    for f in final:
        f.pop("_p", None)
        f.pop("_y", None)
    out["blocos"] = final
    out["referencias"] = _referencias(refs_linhas)
    n_frac = json.dumps(final, ensure_ascii=False).count('"math"')
    if n_frac:
        out["avisos"].append(f"{n_frac} fração(ões) em linha reconstruída(s) como \\frac: confira na imagem da página.")
    out["meta"]["idioma"] = idioma(" ".join(texto_de(ln["segs"]) for ln in linhas[:400]))
    return out


def _limpar_legenda(segs, rotulo):
    """Tira o rótulo ("Figura 3:") do começo da legenda; a classe recoloca no formato do lab."""
    segs = [list(s) for s in segs]
    resto = len(rotulo)
    while segs and resto > 0:
        t = segs[0][0]
        if len(t.strip()) == 0:
            segs.pop(0)
            continue
        ini = len(t) - len(t.lstrip())
        corte = min(len(t), ini + resto)
        consumido = t[:corte]
        resto -= len(consumido.strip()) + (1 if " " in consumido.strip() else 0)
        segs[0][0] = t[corte:]
        if not segs[0][0]:
            segs.pop(0)
        break
    if segs:
        segs[0][0] = segs[0][0].lstrip()
        segs[-1][0] = segs[-1][0].rstrip()
    return juntar(segs)


def _titulo_toc(texto, toc):
    chave = re.sub(r"\s+", "", re.sub(r"^\s*\d+(\.\d+)*\.?\s*", "", texto)).lower()
    if not chave:
        return None
    for lvl, k, original, _ in toc:
        if k == chave:
            return lvl, original
    return None


def _meta_da_capa(out, capa, corpo):
    if not capa:
        out["avisos"].append("Capa não identificada: preencha meta.titulo e meta.autores.")
        return
    maior = max(ln["tam"] for ln in capa)
    titulo = [ln for ln in capa if ln["tam"] >= maior - 0.5]
    resto = [ln for ln in capa if ln not in titulo]
    meta = out["meta"]
    meta["titulo"] = " ".join(texto_de(ln["segs"]) for ln in titulo).strip()
    sub = [ln for ln in resto if ln["tam"] > corpo + 0.6 and ln["bbox"][1] < titulo[-1]["bbox"][3] + 40]
    meta["subtitulo"] = " ".join(texto_de(ln["segs"]) for ln in sub).strip()
    outros = [texto_de(ln["segs"]).strip() for ln in resto if ln not in sub]
    data = next((t for t in outros if re.search(r"\b(19|20)\d\d\b", t) and re.search(r"(janeiro|fevereiro|março|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro|january|february|march|april|may|june|july|august|september|october|november|december)", t, re.I)), "")
    meta["data"] = data
    meta["links"] = [t for t in outros if re.search(r"https?://", t)]
    afil = [t for t in outros if re.search(r"insper|universi|institut|lab\b|school|faculdade", t, re.I) and t != data]
    meta["afiliacao"] = afil[0] if afil else ""
    candidatos = [t for t in outros if t not in afil and t != data and t not in meta["links"]]
    nomes = []
    # Linha com vários nomes separados por espaços largos vira vários autores
    for ln in resto:
        t = texto_de(ln["segs"]).strip()
        if t not in candidatos:
            continue
        partes = [p for parte in ln["partes"] for p in re.split(r"\s{2,}|,\s*| e | and |·", parte) if p.strip()]
        if all(re.fullmatch(r"[A-ZÀ-Ý][\wÀ-ÿ'.-]+(\s+[A-ZÀ-Ýa-zà-ÿ][\wÀ-ÿ'.-]+){0,4}(\s*\([^)]*\))?", p.strip()) for p in partes) and len(partes) <= 8:
            nomes += partes
    if not nomes:
        out["avisos"].append("Autores não identificados com segurança: revise meta.autores.")
    meta["autores"] = [autor(n) for n in nomes]
    meta["outras_linhas_capa"] = [t for t in candidatos if not any(t.find(n) >= 0 for n in nomes)]


def _paragrafos(linhas, corpo, toc):
    """Agrupa linhas em seções, parágrafos e listas."""
    blocos, avisos = [], []
    atual, lista = None, None

    def fecha():
        nonlocal atual, lista
        if atual is not None:
            atual["segmentos"] = juntar(atual["segmentos"])
            blocos.append(atual)
            atual = None
        if lista is not None:
            lista["itens"] = [juntar(it) for it in lista["itens"]]
            lista.pop("_x", None)
            blocos.append(lista)
            lista = None

    def acrescenta(destino, segs):
        if destino and destino[-1][0].endswith("-") and segs and segs[0][0][:1].islower():
            destino[-1][0] = destino[-1][0][:-1] + "\u00ad"  # hífen de fim de linha, resolvido depois
        elif destino and segs and re.match(r"[.,;:)\]]", segs[0][0]):
            pass
        elif destino and segs:
            destino.append([" ", destino[-1][1] if destino[-1][1] == segs[0][1] else ""])
        destino.extend([list(s) for s in segs])

    prev, tam_nivel = None, {}
    for ln in linhas:
        t = texto_de(ln["segs"]).strip()
        tt = _titulo_toc(t, toc)
        if tt is None and ln.get("so") and ln.get("negrito") and ln["tam"] > corpo * 1.25 and len(t) < 90 and not t.endswith("."):
            nivel = min((lv for lv, tam in tam_nivel.items() if abs(tam - ln["tam"]) < 0.6), default=2)
            tt = (nivel, re.sub(r"^\s*\d+(\.\d+)*\.?\s*", "", t))
        eh_titulo = tt is not None and (ln["tam"] > corpo + 0.4 or all("b" in s[1] for s in ln["segs"] if s[0].strip()))
        if eh_titulo:
            tam_nivel.setdefault(tt[0], ln["tam"])
            fecha()
            num = re.match(r"^\s*(\d+(\.\d+)*)\.?\s+", t)
            blocos.append({"tipo": "secao", "nivel": tt[0], "titulo": tt[1], "numero": num.group(1) if num else "",
                           "_p": ln["p"], "_y": ln["bbox"][1]})
            prev = None
            continue
        novo_bloco = prev is None or ln["bloco"] != prev["bloco"]
        recuo = ln["bbox"][0] - ln["bx0"] > 0.6 * corpo
        item = ITEM_LISTA.match(t)
        fim_frase = prev is not None and re.search(r"[.!?:;]['\"”’)]?$", texto_de(prev["segs"]).strip())
        # Parágrafo cortado por figura, tabela ou virada de página: a linha anterior não terminou a frase
        continua_pagina = prev is not None and not fim_frase and not item
        if item and (novo_bloco or recuo or fim_frase or lista is not None):
            if atual is not None:
                fecha_par = atual
                atual = None
                fecha_par["segmentos"] = juntar(fecha_par["segmentos"])
                blocos.append(fecha_par)
            if lista is None:
                lista = {"tipo": "lista", "ordenada": bool(re.match(r"\d", item.group(1))), "itens": [], "_p": ln["p"],
                         "_y": ln["bbox"][1], "_x": ln["bbox"][0]}
            bruto = texto_de(ln["segs"])
            lista["itens"].append(cortar_inicio(ln["segs"], len(bruto) - len(bruto.lstrip()) + len(item.group(0))))
        elif lista is not None and (not novo_bloco or ln["bbox"][0] > lista["_x"] + 3 or continua_pagina
                                    or (novo_bloco and not fim_frase and t[:1].islower())):
            # Continuação do item: mesma caixa, recuo pendente ou virada de página
            acrescenta(lista["itens"][-1], ln["segs"])
        elif atual is not None and (continua_pagina or (not novo_bloco and not recuo)):
            acrescenta(atual["segmentos"], ln["segs"])
        else:
            fecha()
            atual = {"tipo": "paragrafo", "segmentos": [list(s) for s in ln["segs"]], "_p": ln["p"], "_y": ln["bbox"][1]}
        prev = ln
    fecha()
    _resolver_hifens(blocos)
    return blocos, avisos


def _resolver_hifens(blocos):
    """Hífen de fim de linha: junta a palavra, a não ser que a forma com hífen apareça no texto."""
    todos = " ".join(texto_de(b.get("segmentos", [])) + " " + " ".join(texto_de(i) for i in b.get("itens", [])) for b in blocos)
    palavras = Counter(re.findall(r"[\wÀ-ÿ-]+", todos.replace("\u00ad", "")))

    def resolve(segs):
        for s in segs:
            while "\u00ad" in s[0]:
                k = s[0].index("\u00ad")
                esq = re.search(r"[\wÀ-ÿ-]*$", s[0][:k]).group(0)
                dir_ = re.match(r"[\wÀ-ÿ-]*", s[0][k + 1:]).group(0)
                junto, hifen = esq + dir_, esq + "-" + dir_
                s[0] = s[0][:k] + ("-" if palavras[hifen] > palavras[junto] else "") + s[0][k + 1:]

    for b in blocos:
        if "segmentos" in b:
            resolve(b["segmentos"])
        for it in b.get("itens", []):
            resolve(it)


def _referencias(linhas):
    refs, atual = [], None
    for ln in linhas:
        t = texto_de(ln["segs"]).strip()
        m = re.match(r"^\[(\d+)\]\s*(.*)", t)
        if m:
            if atual:
                refs.append(atual)
            atual = {"n": int(m.group(1)), "texto": m.group(2)}
        elif atual is not None:
            ult = atual["texto"].split(" ")[-1]
            if atual["texto"].endswith("-"):
                atual["texto"] += "\u00ad" + t  # hífen de fim de linha, resolvido abaixo
            elif atual["texto"].endswith(("/", "_")) or re.match(r"https?://", ult):
                atual["texto"] += t  # URL quebrada na linha
            else:
                atual["texto"] += " " + t
        else:
            atual = {"n": 1, "texto": t}
    if atual:
        refs.append(atual)
    todo = " ".join(r["texto"] for r in refs).replace("-\u00ad", "-")
    for r in refs:
        def resolve(m):
            # "ar-|Xiv" -> "arXiv" (a forma junta aparece em outra referência); "UL-|DD" -> "UL-DD"; "detec-|tion" -> "detection"
            junto, hifen = m.group(1) + m.group(2), m.group(1) + "-" + m.group(2)
            if re.search(r"\b" + re.escape(junto) + r"\b", todo):
                return junto
            if todo.count(hifen) > 1 or m.group(2)[:1].isupper():
                return hifen
            return junto
        r["texto"] = re.sub(r"(\w*)-\u00ad(\w*)", resolve, r["texto"])
        r["texto"] = re.sub(r"\s+", " ", r["texto"]).strip()
    return refs


# ----------------------------------------------------------------------------- DOCX / Google Docs
def extrair_docx(caminho: Path) -> dict:
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    with zipfile.ZipFile(caminho) as z:
        raiz = ET.fromstring(z.read("word/document.xml"))
    blocos, out = [], {"fonte": {"arquivo": caminho.name, "formato": "docx"}, "meta": {}, "resumo": [], "blocos": [], "referencias": [], "avisos": []}
    for p in raiz.iter(f"{{{ns['w']}}}p"):
        estilo = p.find("w:pPr/w:pStyle", ns)
        estilo = estilo.get(f"{{{ns['w']}}}val") if estilo is not None else ""
        segs = []
        for r in p.findall("w:r", ns):
            t = "".join(x.text or "" for x in r.findall("w:t", ns))
            rpr = r.find("w:rPr", ns)
            b = rpr is not None and rpr.find("w:b", ns) is not None
            i = rpr is not None and rpr.find("w:i", ns) is not None
            segs.append([t, ("b" if b else "") + ("i" if i else "")])
        segs = juntar(segs)
        if not texto_de(segs).strip():
            continue
        if estilo.lower() == "title":
            out["meta"]["titulo"] = texto_de(segs)
        elif re.match(r"(?i)heading(\d)", estilo):
            blocos.append({"tipo": "secao", "nivel": int(re.match(r"(?i)heading(\d)", estilo).group(1)), "titulo": texto_de(segs), "numero": ""})
        elif p.find("w:pPr/w:numPr", ns) is not None:
            if blocos and blocos[-1]["tipo"] == "lista":
                blocos[-1]["itens"].append(segs)
            else:
                blocos.append({"tipo": "lista", "ordenada": False, "itens": [segs]})
        else:
            blocos.append({"tipo": "paragrafo", "segmentos": segs})
    _separa_resumo_refs(out, blocos)
    out["avisos"].append("Figuras e tabelas de .docx não são extraídas automaticamente: insira-as a partir do arquivo original.")
    return out


# ----------------------------------------------------------------------------- Markdown
def _md_inline(t: str):
    segs, pos = [], 0
    for m in re.finditer(r"(\*\*\*|\*\*|\*|`)(.+?)\1", t):
        segs.append([t[pos:m.start()], ""])
        segs.append([m.group(2), {"***": "bi", "**": "b", "*": "i", "`": "m"}[m.group(1)]])
        pos = m.end()
    segs.append([t[pos:], ""])
    return juntar(segs)


def extrair_md(caminho: Path) -> dict:
    out = {"fonte": {"arquivo": caminho.name, "formato": "md"}, "meta": {}, "resumo": [], "blocos": [], "referencias": [], "avisos": []}
    blocos, buf = [], []

    def fecha():
        if buf:
            blocos.append({"tipo": "paragrafo", "segmentos": _md_inline(" ".join(buf)), "_linhas": list(buf)})
            buf.clear()

    for linha in caminho.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^(#{1,4})\s+(.*)", linha)
        it = re.match(r"^\s*([-*+]|\d+\.)\s+(.*)", linha)
        img = re.match(r"^!\[(.*?)\]\((.*?)\)", linha.strip())
        if m:
            fecha()
            if len(m.group(1)) == 1 and "titulo" not in out["meta"]:
                out["meta"]["titulo"] = m.group(2).strip()
            else:
                num = re.match(r"^(\d+(\.\d+)*)\.?\s+(.*)", m.group(2))
                blocos.append({"tipo": "secao", "nivel": len(m.group(1)) - 1, "titulo": num.group(3) if num else m.group(2).strip(), "numero": num.group(1) if num else ""})
        elif img:
            fecha()
            blocos.append({"tipo": "figura", "numero": sum(b["tipo"] == "figura" for b in blocos) + 1, "legenda": _md_inline(img.group(1)), "arquivo": img.group(2), "largura": "dupla"})
        elif it:
            fecha()
            if blocos and blocos[-1]["tipo"] == "lista":
                blocos[-1]["itens"].append(_md_inline(it.group(2)))
            else:
                blocos.append({"tipo": "lista", "ordenada": it.group(1)[0].isdigit(), "itens": [_md_inline(it.group(2))]})
        elif not linha.strip():
            fecha()
        else:
            buf.append(linha.strip())
    fecha()
    # Capa: parágrafos entre o título e a primeira seção (autores, afiliação, outras linhas)
    k = next((i for i, b in enumerate(blocos) if b["tipo"] != "paragrafo"), len(blocos))
    capa, blocos = blocos[:k], blocos[k:]
    _capa_texto(out, [texto_de(b["segmentos"]) for b in capa])
    _separa_resumo_refs(out, blocos)
    return out


def _capa_texto(out, linhas):
    """Capa de .md/.docx: primeira linha com nomes = autores; linha com instituição = afiliação."""
    meta = out["meta"]
    meta.setdefault("outras_linhas_capa", [])
    for t in linhas:
        partes = [p.strip() for p in re.split(r",\s*|\s+e\s+|\s+and\s+|;", t) if p.strip()]
        nomes = all(re.fullmatch(r"[A-ZÀ-Ý][\wÀ-ÿ'.-]+(\s+[A-ZÀ-Ýa-zà-ÿ][\wÀ-ÿ'.-]+){0,4}(\s*\([^)]*\))?", p) for p in partes)
        if not meta.get("autores") and nomes and len(partes) <= 10 and not re.search(r"insper|universi|institut", t, re.I):
            meta["autores"] = [autor(p) for p in partes]
        elif not meta.get("afiliacao") and re.search(r"insper|universi|institut|lab\b|school|faculdade", t, re.I):
            meta["afiliacao"] = t
        elif re.search(r"\b(19|20)\d\d\b", t) and not meta.get("data") and len(t) < 40:
            meta["data"] = t
        else:
            meta["outras_linhas_capa"].append(t)


# ----------------------------------------------------------------------------- LaTeX
def extrair_tex(caminho: Path) -> dict:
    src = caminho.read_text(encoding="utf-8")
    src = re.sub(r"(?<!\\)%.*", "", src)
    out = {"fonte": {"arquivo": caminho.name, "formato": "tex"}, "meta": {}, "resumo": [], "blocos": [], "referencias": [], "avisos": []}
    m = re.search(r"\\title\{(.+?)\}\s*\n", src, re.S)
    out["meta"]["titulo"] = m.group(1).strip() if m else ""
    m = re.search(r"\\author\{(.+?)\}\s*\n", src, re.S)
    out["meta"]["autores"] = [autor(a) for a in re.split(r"\\and|,", m.group(1)) if a.strip()] if m else []
    m = re.search(r"\\begin\{abstract\}(.+?)\\end\{abstract\}", src, re.S)
    if m:
        out["resumo"] = [[[p.strip(), ""]] for p in re.split(r"\n\s*\n", m.group(1)) if p.strip()]
    corpo = src.split("\\begin{document}", 1)[-1]
    corpo = re.sub(r"\\begin\{abstract\}.+?\\end\{abstract\}", "", corpo, flags=re.S)
    for parte in re.split(r"\n\s*\n", corpo):
        parte = parte.strip()
        sec = re.match(r"\\(sub)*section\*?\{(.+?)\}", parte)
        if sec:
            nivel = 1 + (sec.group(0).count("sub"))
            out["blocos"].append({"tipo": "secao", "nivel": nivel, "titulo": sec.group(2), "numero": ""})
            parte = parte[sec.end():].strip()
        if parte and not parte.startswith(("\\maketitle", "\\end{document}", "\\bibliography")):
            out["blocos"].append({"tipo": "paragrafo", "segmentos": [[parte, "tex"]]})
    out["avisos"].append("Entrada .tex: parágrafos ficam com estilo 'tex' (LaTeX original preservado). Revise ambientes de figura e tabela.")
    return out


def _separa_resumo_refs(out, blocos):
    k = next((i for i, b in enumerate(blocos) if b["tipo"] == "secao" and SECAO_RESUMO.match(b["titulo"])), None)
    if k is not None:
        fim = next((i for i in range(k + 1, len(blocos)) if blocos[i]["tipo"] == "secao"), len(blocos))
        out["resumo"] = [b["segmentos"] for b in blocos[k + 1:fim] if b["tipo"] == "paragrafo"]
        blocos = blocos[:k] + blocos[fim:]
    k = next((i for i, b in enumerate(blocos) if b["tipo"] == "secao" and SECAO_REFS.match(b["titulo"])), None)
    if k is not None:
        for b in blocos[k + 1:]:
            if b.get("_linhas"):  # Markdown: uma referência por linha que começa com [n]
                textos = []
                for ln in b["_linhas"]:
                    if re.match(r"^\s*\[\d+\]", ln) or not textos:
                        textos.append(ln.strip())
                    else:
                        textos[-1] += " " + ln.strip()
            else:
                textos = [texto_de(segs) for segs in ([b["segmentos"]] if b["tipo"] == "paragrafo" else b.get("itens", []))]
            for t in textos:
                m = re.match(r"^\[(\d+)\]\s*(.*)", t)
                out["referencias"].append({"n": int(m.group(1)) if m else len(out["referencias"]) + 1, "texto": m.group(2) if m else t})
        blocos = blocos[:k]
    for b in blocos:
        b.pop("_linhas", None)
    out["blocos"] = blocos
    out["meta"].setdefault("autores", [])
    out["meta"]["idioma"] = idioma(" ".join(texto_de(b.get("segmentos", [])) for b in blocos))


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    entrada, saida = Path(sys.argv[1]), Path(sys.argv[2])
    ext = entrada.suffix.lower()
    if ext == ".pdf":
        dados = extrair_pdf(entrada)
    elif ext == ".docx":
        dados = extrair_docx(entrada)
    elif ext in (".md", ".markdown"):
        dados = extrair_md(entrada)
    elif ext == ".tex":
        dados = extrair_tex(entrada)
    else:
        sys.exit(f"Formato não suportado: {ext}. Use .pdf, .docx, .md ou .tex (exporte o Google Docs como .docx).")
    ia = [a["nome"] for a in dados["meta"].get("autores", []) if a["ia"]]
    if ia:
        dados["avisos"].append(f"Autor(es) IA detectado(s): {', '.join(ia)}. Pela regra do lab, saem da lista de autores.")
    Path(saida).write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")
    n = Counter(b["tipo"] for b in dados["blocos"])
    print(f"{entrada.name}: {dict(n)}; resumo {len(dados['resumo'])} parágrafo(s); {len(dados['referencias'])} referências; {len(dados['avisos'])} aviso(s).")
    for a in dados["avisos"]:
        print("  aviso:", a)


if __name__ == "__main__":
    main()
