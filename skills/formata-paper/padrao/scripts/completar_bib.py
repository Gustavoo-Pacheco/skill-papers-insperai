"""completar_bib.py: confere e completa referências pelo arXiv, Crossref e DataCite (DOI), OpenAlex e Semantic Scholar.

Uso:
  python3 completar_bib.py refs.bib [--saida refs.bib] [--offline]
      Completa um .bib existente. As chaves do autor nunca mudam. Só acrescenta campos que faltam.
  python3 completar_bib.py --de-texto entrada.json --saida refs.bib [--offline]
      Cria um .bib a partir das referências em texto (campo "referencias" do JSON de extrair_entrada.py).
      As chaves seguem o formato sobrenome2024palavra.

Nunca inventa uma referência. O que não for confirmado em nenhuma fonte recebe note = {[VERIFICAR] ...}
e aparece no relatório. Um resultado só é aceito quando o título bate (similaridade >= 0,92) e o ano
não diverge mais de 1. Sem rede (ou com --offline), só converte e marca tudo como [VERIFICAR].
"""
import argparse
import difflib
import json
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from xml.etree import ElementTree as ET

UA = "skill-papers-insperai/0.1 (bibliography completion)"
PARADAS = {"a", "an", "the", "on", "of", "for", "and", "in", "to", "with", "o", "os", "as", "um", "uma", "de",
           "do", "da", "dos", "das", "e", "em", "para", "por", "com", "towards", "toward", "is", "are", "what", "how"}


# ----------------------------------------------------------------------------- utilidades
def ascii_(s):
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()


def norm_titulo(t):
    return re.sub(r"[^a-z0-9]+", " ", ascii_(t or "").lower()).strip()


def similar(a, b):
    return difflib.SequenceMatcher(None, norm_titulo(a), norm_titulo(b)).ratio()


def get(url, tentativas=3, aceitar="application/json"):
    for i in range(tentativas):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": aceitar})
            with urllib.request.urlopen(req, timeout=20) as r:
                return r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code in (429, 503) and i < tentativas - 1:
                time.sleep(3 * (i + 1))
                continue
            return None
        except Exception:  # noqa: BLE001
            if i < tentativas - 1:
                time.sleep(1.5)
                continue
            return None
    return None


# ----------------------------------------------------------------------------- referência em texto -> campos
INICIAL = re.compile(r"^(?:[A-ZÀ-ÝČŠŽ]h?\.)(?:-?[A-ZÀ-ÝČŠŽ]h?\.)*$")  # "J.", "J.-P.", "Ch."; "Ba." não


def parse_referencia(texto: str) -> dict:
    t = re.sub(r"\s+", " ", texto).strip()
    r = {"original": t}
    m = re.search(r"\bdoi:\s*(10\.\S+?)[.,;]?(\s|$)|doi\.org/(10\.\S+?)[.,;]?(\s|$)", t, re.I)
    if m:
        r["doi"] = m.group(1) or m.group(3)
    m = re.search(r"arXiv:\s*(\d{4}\.\d{4,5})(v\d+)?", t, re.I)
    if m:
        r["arxiv"] = m.group(1)
    m = re.search(r"https?://\S+", t)
    if m:
        r["url"] = re.sub(r"[.,;)]$", "", m.group(0))
    anos = re.findall(r"\b(19[5-9]\d|20[0-4]\d)\b", re.sub(r"https?://\S+|doi:\S+|arXiv:\S+", "", t))
    if anos:
        r["ano"] = anos[-1]
    m = re.search(r"\bpp?\.\s*(\d+)\s*[–-]\s*(\d+)", t)
    if m:
        r["paginas"] = f"{m.group(1)}--{m.group(2)}"
    m = re.search(r",\s*(\d+)\((\d+)\)(?::\s*([\w-]+))?", t)
    if m:
        r["volume"], r["numero"] = m.group(1), m.group(2)
        if m.group(3) and "paginas" not in r:
            r["paginas"] = m.group(3)
    else:
        m = re.search(r",\s*(\d+):(\d+)(?:\s*[–-]\s*(\d+))?,", t)
        if m:
            r["volume"] = m.group(1)
            r["paginas"] = m.group(2) + (f"--{m.group(3)}" if m.group(3) else "")

    # Autores: até o primeiro token terminado em ponto que não é inicial ("Čech.", "al.", "NCAP.")
    toks = t.split(" ")
    fim = next((i for i, tok in enumerate(toks) if tok.endswith(".") and not INICIAL.match(tok)), None)
    autores_txt = " ".join(toks[:fim + 1])[:-1] if fim is not None else ""
    resto = " ".join(toks[fim + 1:]) if fim is not None else t
    tem_inicial = any(INICIAL.match(x.rstrip(",")) for x in toks[:fim or 0])
    if autores_txt and not tem_inicial and len(autores_txt.split()) > 3:
        autores_txt, resto = "", t  # sem autores: começa pelo título
    r["autores"] = _autores(autores_txt)
    r["sobrenome_citado"] = r["autores"][0]["sobrenome"] if r["autores"] else ""
    # Título: até o próximo ". " seguido de maiúscula, dígito ou URL
    m = re.match(r"(.+?[.?!])(\s+(?=[A-ZÀ-Ý0-9(]|https?:|arXiv|doi)|$)", resto)
    if m:
        r["titulo"] = m.group(1).rstrip(".")
        r["local"] = resto[m.end():].strip()
    else:
        r["titulo"], r["local"] = resto.rstrip("."), ""
    return r


def _autores(txt):
    if not txt:
        return []
    outros = bool(re.search(r"\bet al\.?$", txt))
    txt = re.sub(r",?\s*et al\.?$", "", txt)
    partes = [p.strip() for p in re.split(r",\s*|\s+e\s+|\s+and\s+|\s*&\s*", txt) if p.strip()]
    out = []
    for p in partes:
        tk = p.split()
        if any(INICIAL.match(x) for x in tk):
            k = max(i for i, x in enumerate(tk) if INICIAL.match(x))
            out.append({"nome": " ".join(tk[:k + 1]), "sobrenome": " ".join(tk[k + 1:]) or tk[-1]})
        elif len(partes) == 1:
            out.append({"nome": "", "sobrenome": p, "instituicao": True})
        else:
            out.append({"nome": " ".join(tk[:-1]), "sobrenome": tk[-1]})
    if outros:
        out.append({"nome": "", "sobrenome": "others"})
    return out


# ----------------------------------------------------------------------------- fontes
def _crossref(m):
    tipo = m.get("type", "")
    data = (m.get("issued") or m.get("published") or {}).get("date-parts", [[None]])[0]
    r = {"titulo": (m.get("title") or [""])[0], "ano": str(data[0]) if data and data[0] else None,
         "autores": [{"nome": a.get("given", ""), "sobrenome": a.get("family", a.get("name", ""))} for a in m.get("author", [])],
         "fonte": "Crossref", "doi": m.get("DOI")}
    venue = (m.get("container-title") or [""])[0]
    if tipo == "journal-article":
        r["tipo"], r["journal"] = "article", venue
    elif tipo in ("proceedings-article", "book-chapter"):
        r["tipo"], r["booktitle"] = "inproceedings", venue
    else:
        r["tipo"] = "misc"
        if venue or m.get("publisher"):
            r["howpublished"] = venue or m.get("publisher")
    for k_api, k in (("volume", "volume"), ("issue", "numero"), ("page", "paginas")):
        if m.get(k_api):
            r[k] = m[k_api].replace("-", "--")
    return r


def por_doi(doi):
    txt = get("https://api.crossref.org/works/" + urllib.parse.quote(doi), tentativas=1)
    if not txt:
        return por_datacite(doi)
    return _crossref(json.loads(txt).get("message", {})) | {"doi": doi}


def por_arxiv(aid):
    txt = get("https://export.arxiv.org/api/query?id_list=" + aid, aceitar="application/atom+xml")
    if not txt:
        return None
    ns = {"a": "http://www.w3.org/2005/Atom"}
    e = ET.fromstring(txt).find("a:entry", ns)
    if e is None or not e.findtext("a:title", "", ns).strip():
        return None
    nomes = [x.findtext("a:name", "", ns) for x in e.findall("a:author", ns)]
    return {"titulo": re.sub(r"\s+", " ", e.findtext("a:title", "", ns)).strip(), "ano": e.findtext("a:published", "", ns)[:4],
            "autores": [{"nome": " ".join(n.split()[:-1]), "sobrenome": n.split()[-1]} for n in nomes if n],
            "tipo": "misc", "eprint": aid, "fonte": "arXiv"}


def por_openalex(titulo):
    txt = get("https://api.openalex.org/works?per-page=5&search=" + urllib.parse.quote(titulo))
    if not txt:
        return []
    try:
        res = json.loads(txt).get("results", [])
    except json.JSONDecodeError:
        return []
    out = []
    for w in res:
        fonte = ((w.get("primary_location") or {}).get("source") or {})
        venue, tipo_src = (fonte.get("display_name") or "").split("/")[0].strip(), fonte.get("type") or ""
        nomes = [a.get("author", {}).get("display_name", "") for a in w.get("authorships", [])]
        r = {"titulo": w.get("display_name") or w.get("title") or "", "ano": str(w.get("publication_year") or ""),
             "fonte": "OpenAlex", "autores": [{"nome": " ".join(n.split()[:-1]), "sobrenome": n.split()[-1]} for n in nomes if n]}
        if tipo_src == "journal" and "arxiv" not in venue.lower():
            r["tipo"], r["journal"] = "article", venue
        elif tipo_src == "conference" or re.search(r"proceedings|conference|workshop|symposium", venue, re.I):
            r["tipo"], r["booktitle"] = "inproceedings", venue
        else:
            r["tipo"] = "misc"
        b = w.get("biblio") or {}
        if b.get("volume"):
            r["volume"] = b["volume"]
        if b.get("issue"):
            r["numero"] = b["issue"]
        if b.get("first_page") and b.get("last_page") and b["first_page"] != b["last_page"]:
            r["paginas"] = f"{b['first_page']}--{b['last_page']}"
        if w.get("doi") and "arxiv" not in (w.get("doi") or "").lower():
            r["doi"] = w["doi"].replace("https://doi.org/", "")
        m = re.search(r"arxiv\.org/abs/(\d{4}\.\d{4,5})", json.dumps(w.get("locations", [])))
        if m and r["tipo"] == "misc":
            r["eprint"] = m.group(1)
        out.append(r)
    return out


def por_datacite(doi):
    """DOIs de datasets e repositórios (Zenodo, IEEE DataPort, Figshare) ficam no DataCite, não no Crossref."""
    txt = get("https://api.datacite.org/dois/" + urllib.parse.quote(doi))
    if not txt:
        return None
    a = json.loads(txt).get("data", {}).get("attributes", {})
    if not a.get("titles"):
        return None
    return {"titulo": a["titles"][0].get("title", ""), "ano": str(a.get("publicationYear") or ""), "tipo": "misc",
            "autores": [{"nome": c.get("givenName", "").split()[0] if c.get("givenName") else "", "sobrenome": c.get("familyName") or c.get("name", "")}
                        for c in a.get("creators", [])],
            "howpublished": a.get("publisher") if isinstance(a.get("publisher"), str) else (a.get("publisher") or {}).get("name"),
            "doi": doi, "fonte": "DataCite"}


def por_semantic_scholar(titulo):
    txt = get("https://api.semanticscholar.org/graph/v1/paper/search?limit=3&fields=title,year,venue,authors,externalIds"
              "&query=" + urllib.parse.quote(titulo), tentativas=2)
    if not txt:
        return []
    out = []
    for p in json.loads(txt).get("data", []) or []:
        r = {"titulo": p.get("title", ""), "ano": str(p.get("year") or ""), "fonte": "Semantic Scholar",
             "autores": [{"nome": " ".join(a["name"].split()[:-1]), "sobrenome": a["name"].split()[-1]}
                         for a in p.get("authors", []) if a.get("name")],
             "tipo": "inproceedings" if p.get("venue") else "misc", "booktitle": p.get("venue") or None}
        ext = p.get("externalIds") or {}
        if ext.get("DOI"):
            r["doi"] = ext["DOI"]
        if ext.get("ArXiv"):
            r["eprint"] = ext["ArXiv"]
        out.append(r)
    return out


def por_crossref_busca(texto):
    txt = get("https://api.crossref.org/works?rows=3&query.bibliographic=" + urllib.parse.quote(texto[:300]))
    if not txt:
        return []
    return [_crossref(m) for m in json.loads(txt).get("message", {}).get("items", [])]


def confirmar(ref: dict):
    """Procura a referência nas fontes. Devolve (metadados, fonte) ou (None, motivo)."""
    if ref.get("doi"):
        r = por_doi(ref["doi"])
        if r and (not ref.get("titulo") or similar(r["titulo"], ref["titulo"]) > 0.8):
            return r, "DOI"
    if ref.get("arxiv"):
        r = por_arxiv(ref["arxiv"])
        if r and (not ref.get("titulo") or similar(r["titulo"], ref["titulo"]) > 0.8):
            return r, "arXiv"
    titulo = ref.get("titulo", "")
    if len(norm_titulo(titulo)) < 12:
        return None, "título curto demais para buscar"
    def ano_dif(r):
        try:
            return abs(int(r["ano"]) - int(ref["ano"])) if ref.get("ano") and r.get("ano") else 0
        except ValueError:
            return 0
    for busca in (por_openalex, por_semantic_scholar, lambda t: por_crossref_busca(ref.get("original", t))):
        bons = [r for r in busca(titulo) if similar(r.get("titulo", ""), titulo) >= 0.92 and ano_dif(r) <= 1]
        if bons:
            # Prefere o mesmo ano do original e a versão publicada (conferência ou periódico) à preprint
            r = min(bons, key=lambda r: (ano_dif(r), r.get("tipo") == "misc"))
            return r, r["fonte"]
        time.sleep(0.3)
    return None, "não encontrada no arXiv, Crossref, DataCite, OpenAlex nem Semantic Scholar"


# ----------------------------------------------------------------------------- BibTeX
def bib_autor(a):
    if a.get("instituicao"):
        return "{" + a["sobrenome"] + "}"
    if a["sobrenome"] == "others":
        return "others"
    return f"{a['sobrenome']}, {a['nome']}".strip(", ")


def chave(autores, ano, titulo, usadas):
    sob = autores[0]["sobrenome"] if autores and autores[0]["sobrenome"] != "others" else "anon"
    sob = re.sub(r"[^a-z]", "", ascii_(sob.split()[-1] if sob.split() else "anon").lower()) or "anon"
    pal = next((w for w in norm_titulo(titulo).split() if w not in PARADAS and len(w) > 2), "x")
    base = f"{sob}{ano or 'sd'}{pal}"
    k, i = base, 0
    while k in usadas:
        i += 1
        k = base + "abcdefghij"[i - 1]
    usadas.add(k)
    return k


def bib_de_texto(referencias, online=True, sem_ano="s.d."):
    usadas, out = set(), []
    for item in referencias:
        ref = parse_referencia(item["texto"])
        meta, fonte = confirmar(ref) if online else (None, "sem consulta (offline)")
        e = {"n": item["n"], "_sobrenome": ref["sobrenome_citado"], "_original": ref["original"]}
        if meta:
            e |= {k: v for k, v in meta.items() if v}
            e["_fonte"] = fonte
            for k in ("paginas", "volume", "numero", "url", "doi"):  # o que a fonte não traz, mas o original traz
                if ref.get(k) and not e.get(k):
                    e[k] = ref[k]
            if not e.get("autores"):
                e["autores"] = ref["autores"]
        else:
            local = ref.get("local", "")
            for k in ("url", "doi", "arxiv"):
                if ref.get(k):
                    local = re.sub(r"(doi:\s*|arXiv:\s*)?" + re.escape(ref[k]), "", local, flags=re.I)
            local = re.sub(r",?\s*\b" + str(ref.get("ano", "x")) + r"\b", "", local).strip(" .,")
            e |= {"titulo": ref.get("titulo", ""), "ano": ref.get("ano"), "autores": ref["autores"], "tipo": "misc",
                  "howpublished": local, "note": f"[VERIFICAR] {fonte}"}
            for k in ("doi", "url", "paginas", "volume", "numero"):
                if ref.get(k):
                    e[k] = ref[k]
            if ref.get("arxiv"):
                e["eprint"] = ref["arxiv"]
        e["chave"] = chave(e["autores"], e.get("ano"), e.get("titulo", ""), usadas)
        if not e.get("ano"):
            e["ano"] = sem_ano  # citação autor-ano fica "(Ultralytics, s.d.)"
        out.append(e)
    return out


def _campo(v):
    v = str(v).replace("&", r"\&").replace("%", r"\%").replace("#", r"\#")
    return re.sub(r"(?<!\\)_", r"\_", v)


def entrada_bib(e):
    tipo = e.get("tipo", "misc")
    if tipo == "inproceedings" and not e.get("booktitle"):
        tipo = "misc"
    if tipo == "article" and not e.get("journal"):
        tipo = "misc"
    how = e.get("howpublished") or (f"arXiv:{e['eprint']}" if e.get("eprint") and tipo == "misc" else None)
    campos = [("author", " and ".join(bib_autor(a) for a in e.get("autores", []))),
              ("title", "{" + _campo(e.get("titulo", "")) + "}"),  # chaves duplas: o estilo não muda maiúsculas
              ("journal", e.get("journal")), ("booktitle", e.get("booktitle")), ("howpublished", how),
              ("year", e.get("ano")), ("volume", e.get("volume")), ("number", e.get("numero")),
              ("pages", e.get("paginas")), ("doi", e.get("doi")), ("eprint", e.get("eprint")),
              ("url", e.get("url")), ("note", e.get("note"))]
    linhas = [f"@{tipo}{{{e['chave']},"]
    for k, v in campos:
        if v:
            linhas.append(f"  {k} = {{{v if k in ('author', 'title', 'url', 'doi', 'eprint') else _campo(v)}}},")
    linhas.append("}")
    return "\n".join(linhas)


def escrever_bib(entradas, caminho: Path):
    cab = ["% refs.bib gerado por completar_bib.py (skill-papers-insperai).",
           "% Fontes: arXiv, Crossref e DataCite (DOI), OpenAlex, Semantic Scholar. Entradas com [VERIFICAR] não foram confirmadas.", ""]
    corpo = []
    for e in entradas:
        corpo += [f"% [{e['n']}] {e.get('_fonte', 'não confirmada')}: {e.get('_original', '')}"[:400], entrada_bib(e), ""]
    Path(caminho).write_text("\n".join(cab + corpo), encoding="utf-8")


# ----------------------------------------------------------------------------- .bib existente
def ler_bib(texto):
    entradas, i = [], 0
    padrao = re.compile(r"@(\w+)\s*\{\s*([^,\s]+)\s*,")
    while True:
        m = padrao.search(texto, i)
        if not m:
            break
        nivel, j = 1, m.end()
        while j < len(texto) and nivel:
            nivel += {"{": 1, "}": -1}.get(texto[j], 0)
            j += 1
        corpo, campos = texto[m.end():j - 1], {}
        for c in re.finditer(r"(\w+)\s*=\s*", corpo):
            k, p = c.group(1).lower(), c.end()
            if p < len(corpo) and corpo[p] == "{":
                n, q = 1, p + 1
                while q < len(corpo) and n:
                    n += {"{": 1, "}": -1}.get(corpo[q], 0)
                    q += 1
                campos.setdefault(k, corpo[p + 1:q - 1])
            else:
                v = re.match(r'"([^"]*)"|([^,\n]+)', corpo[p:])
                campos.setdefault(k, (v.group(1) or v.group(2) or "").strip() if v else "")
        entradas.append({"tipo_bib": m.group(1).lower(), "chave": m.group(2), "campos": campos, "ini": m.start(), "fim": j})
        i = j
    return entradas


def completar_arquivo(caminho: Path, saida: Path, online=True):
    texto = caminho.read_text(encoding="utf-8")
    relatorio, novo, pos = [], [], 0
    for e in ler_bib(texto):
        c = e["campos"]
        if e["tipo_bib"] in ("string", "comment", "preamble"):
            continue
        ref = {"titulo": re.sub(r"[{}]", "", c.get("title", "")), "ano": c.get("year"), "doi": c.get("doi"),
               "arxiv": (c.get("eprint") or "").replace("arXiv:", "") or None}
        if not ref["arxiv"]:
            m = re.search(r"(\d{4}\.\d{4,5})", " ".join(c.get(k, "") for k in ("journal", "url", "note", "howpublished")))
            if m and "arxiv" in " ".join(c.get(k, "") for k in ("journal", "url", "howpublished")).lower():
                ref["arxiv"] = m.group(1)
        meta, fonte = confirmar(ref) if online else (None, "sem consulta (offline)")
        acresc = {}
        if meta:
            mapa = {"year": meta.get("ano"), "doi": meta.get("doi"), "journal": meta.get("journal"),
                    "booktitle": meta.get("booktitle"), "volume": meta.get("volume"), "number": meta.get("numero"),
                    "pages": meta.get("paginas"), "eprint": meta.get("eprint")}
            if not c.get("author") and meta.get("autores"):
                mapa["author"] = " and ".join(bib_autor(a) for a in meta["autores"])
            for k, v in mapa.items():
                if v and not c.get(k) and not (k in ("journal", "booktitle") and (c.get("journal") or c.get("booktitle"))):
                    acresc[k] = v
            if c.get("year") and meta.get("ano") and c["year"].strip() != str(meta["ano"]):
                relatorio.append(f"{e['chave']}: ano no .bib ({c['year']}) difere da fonte ({meta['ano']}); confira")
            relatorio.append(f"{e['chave']}: confirmada ({fonte})" + (f"; acrescentado: {', '.join(acresc)}" if acresc else ""))
        elif "[VERIFICAR]" not in c.get("note", ""):
            acresc["note"] = f"[VERIFICAR] {fonte}"
            relatorio.append(f"{e['chave']}: [VERIFICAR] ({fonte})")
        bloco = texto[e["ini"]:e["fim"]]
        if acresc:
            if "note" in acresc and c.get("note"):
                bloco = re.sub(r"(note\s*=\s*)\{", lambda m: m.group(1) + "{" + acresc["note"] + ". ", bloco, count=1)
                acresc.pop("note")
            extra = "".join(f",\n  {k} = {{{v if k in ('doi', 'eprint', 'author') else _campo(v)}}}" for k, v in acresc.items())
            bloco = re.sub(r",?\s*\}\s*$", extra + "\n}", bloco)
        novo.append(texto[pos:e["ini"]] + bloco)
        pos = e["fim"]
    novo.append(texto[pos:])
    saida.write_text("".join(novo), encoding="utf-8")
    return relatorio


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("bib", nargs="?")
    ap.add_argument("--de-texto", help="JSON de extrair_entrada.py (usa o campo referencias)")
    ap.add_argument("--saida")
    ap.add_argument("--offline", action="store_true")
    a = ap.parse_args()
    if a.de_texto:
        dados = json.loads(Path(a.de_texto).read_text(encoding="utf-8"))
        entradas = bib_de_texto(dados.get("referencias", []), online=not a.offline)
        escrever_bib(entradas, Path(a.saida or "refs.bib"))
        for e in entradas:
            print(f"[{e['n']}] {e['chave']}: {e.get('_fonte') or e.get('note')}")
    elif a.bib:
        print("\n".join(completar_arquivo(Path(a.bib), Path(a.saida or a.bib), online=not a.offline)))
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
