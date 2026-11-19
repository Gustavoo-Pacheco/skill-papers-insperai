"""verificar_cobertura.py: avalia um paper gerado pela cria-paper (ou refaz-paper) contra o original do grupo.

Uso:
  python3 tests/verificar_cobertura.py <original.pdf> <novo/main.tex> --repo <pasta-do-repo> [--extra arquivo.md ...] [--cego]

Duas medidas, decididas para o teste da cria ("só cobertura"):
- **Cobertura:** que fração dos números-chave do original (resumo e tabelas) aparece no paper novo.
- **Números sem fonte:** números do paper novo que não estão no repositório, no paper original (o oráculo
  das respostas da entrevista) nem nos arquivos --extra. Cada um é um possível resultado inventado.
Um número do paper conta como presente na fonte se algum número da fonte, arredondado às mesmas casas, der ele.
Anos, inteiros até 12 e números dentro de comandos LaTeX não contam.
"""
import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
NUM = re.compile(r"(?<![\w.,])[-−+]?\d+(?:[.,]\d+)*%?")


def valor(tok):
    """'0,742' -> (0.742, 3); '90,7%' -> (90.7, 1); '1.126' (milhar) -> (1126, 0) e (1.126, 3)."""
    t = tok.replace("−", "-").rstrip("%")
    out = []
    if re.fullmatch(r"[-+]?\d{1,3}(\.\d{3})+", t):  # milhar com ponto
        out.append((float(t.replace(".", "")), 0))
    t2 = t.replace(",", ".")
    if t2.count(".") <= 1:
        try:
            out.append((float(t2), len(t2.split(".")[1]) if "." in t2 else 0))
        except ValueError:
            pass
    return out


def relevante(v, casas):
    if casas == 0 and (abs(v) <= 12 or 1900 <= v <= 2100):
        return False
    return True


def numeros(texto):
    achados = []
    for m in NUM.finditer(texto):
        for v, c in valor(m.group(0)):
            achados.append((m.group(0), v, c))
    return achados


def texto_tex(tex):
    tex = re.sub(r"(?<!\\)%.*", "", tex)
    tex = tex.replace("{,}", ",").replace("{.}", ".")  # 0{,}134 em modo matemático
    corpo = tex.split("\\begin{document}", 1)[-1]
    resumo = re.search(r"\\resumo\{(.*?)\}\s*\n", tex, re.S)
    corpo = (resumo.group(1) if resumo else "") + "\n" + corpo
    corpo = re.sub(r"\\(cite[tp]?|ref|label|url|href|includegraphics|setcounter|bibliography|bibliographystyle)\*?(\[[^\]]*\])*\{[^}]*\}", " ", corpo)
    corpo = re.sub(r"\\(begin|end)\{[^}]*\}(\{[^}]*\})?(\[[^\]]*\])?", " ", corpo)
    corpo = re.sub(r"\[[^\]]*(cm|pt|mm|em|ex|width|height)[^\]]*\]", " ", corpo)
    corpo = re.sub(r"[-+]?\d+(?:[.,]\d+)?\s*(?:cm|mm|pt|em|ex|in|bp)\b", " ", corpo)  # medidas (p{7.4cm}, 0.5em)
    corpo = re.sub(r"\\[a-zA-Z]+", " ", corpo)
    return corpo


def corpus_repo(pasta):
    partes = []
    for p in Path(pasta).rglob("*"):
        if not p.is_file() or any(x in p.parts for x in (".git", ".venv", "node_modules", "__pycache__")):
            continue
        if p.suffix == ".ipynb":
            try:
                nb = json.loads(p.read_text(encoding="utf-8"))
                for c in nb.get("cells", []):
                    partes.append("".join(c.get("source", [])))
                    for o in c.get("outputs", []):
                        partes.append("".join(o.get("text", [])) + "".join((o.get("data") or {}).get("text/plain", [])))
            except Exception:  # noqa: BLE001
                pass
        elif p.suffix in (".md", ".txt", ".csv", ".tsv", ".json", ".py", ".yaml", ".yml", ".toml", ".log", ".tex") and p.stat().st_size < 20_000_000:
            partes.append(p.read_text(encoding="utf-8", errors="replace"))
    return "\n".join(partes)


def carregar_original(pdf):
    """Extrai o paper original com extrair_entrada.py e devolve o JSON."""
    with tempfile.TemporaryDirectory() as tmp:
        saida = Path(tmp) / "original.json"
        subprocess.run([sys.executable, str(RAIZ / "padrao/scripts/extrair_entrada.py"), str(pdf), str(saida)],
                       check=True, capture_output=True)
        return json.loads(saida.read_text(encoding="utf-8"))


def avaliar(d, novo, repo, extras=(), original_como_fonte=True):
    """Compara o main.tex `novo` com o original `d` (JSON de extrair_entrada).

    original_como_fonte=False é o teste cego: só o repo e os `extras` contam como fonte.
    Devolve chaves (lista ordenada de {t, origem, presente}), cobertura, sem_fonte e total_novos.
    """
    T = lambda segs: "".join(t for t, _ in segs)  # noqa: E731
    resumo_txt = " ".join(T(p) for p in d.get("resumo", []))
    tabelas_txt = " ".join(c[1] for b in d["blocos"] if b["tipo"] == "tabela" for ln in b.get("linhas", []) for c in ln)
    original_txt = resumo_txt + " " + tabelas_txt + " " + " ".join(
        T(b.get("segmentos", [])) + " ".join(T(i) for i in b.get("itens", [])) + " " + T(b.get("legenda", []))
        for b in d["blocos"])
    original_txt += " " + " ".join(r["texto"] for r in d.get("referencias", []))
    novo_txt = texto_tex(Path(novo).read_text(encoding="utf-8"))
    fontes_txt = corpus_repo(repo) + "\n" + "\n".join(Path(x).read_text(encoding="utf-8") for x in extras)
    if original_como_fonte:
        fontes_txt += "\n" + original_txt

    def tem(v, c, conjunto):
        return any(round(abs(y), c) == round(abs(v), c) for y in conjunto)  # o sinal pode estar fora ($-$0,1)

    novos = [(t, v, c) for t, v, c in numeros(novo_txt) if relevante(v, c)]
    novos_vals = [v for _, v, _ in numeros(novo_txt)]
    fonte_vals = [v for _, v, _ in numeros(fontes_txt)]
    chaves, por_token = [], {}
    for origem, txt in (("resumo", resumo_txt), ("tabela", tabelas_txt)):
        for t, v, c in numeros(txt):
            if not relevante(v, c):
                continue
            if t not in por_token:  # "1.126" tem duas leituras (milhar e decimal): basta uma bater
                por_token[t] = {"t": t, "origem": origem, "presente": False}
                chaves.append(por_token[t])
            por_token[t]["presente"] |= tem(v, c, novos_vals)
    sem_fonte = sorted({t for t, v, c in novos if not tem(v, c, fonte_vals)})
    cob = sum(k["presente"] for k in chaves) / max(1, len(chaves))
    return {"chaves": chaves, "cobertura": cob, "sem_fonte": sem_fonte, "total_novos": len({t for t, _, _ in novos})}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("original")
    ap.add_argument("novo")
    ap.add_argument("--repo", required=True)
    ap.add_argument("--extra", nargs="*", default=[])
    ap.add_argument("--cego", action="store_true", help="teste sem oráculo: o paper original não conta como fonte")
    a = ap.parse_args()

    r = avaliar(carregar_original(a.original), a.novo, a.repo, a.extra, original_como_fonte=not a.cego)
    presentes = sum(k["presente"] for k in r["chaves"])
    print(f"Cobertura dos números-chave do original (resumo e tabelas): {r['cobertura']:.0%} ({presentes} de {len(r['chaves'])})")
    ausentes = [k["t"] for k in r["chaves"] if not k["presente"]]
    if ausentes:
        print("  ausentes no paper novo:", ", ".join(ausentes[:60]))
    fontes = "repo ou --extra" if a.cego else "repo, original ou --extra"
    print(f"Números do paper novo sem fonte ({fontes}): {len(r['sem_fonte'])} de {r['total_novos']}")
    if r["sem_fonte"]:
        print("  sem fonte:", ", ".join(r["sem_fonte"][:80]))
    sys.exit(0 if not r["sem_fonte"] else 1)


if __name__ == "__main__":
    main()
