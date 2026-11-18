"""inventario_repo.py: mapeia um repositório de código para a refaz-paper e a cria-paper.

Uso:
  python3 inventario_repo.py <caminho | URL do GitHub | arquivo.zip> [--saida inventario.json]

Lista, na ordem de prioridade de padrao/ler-repositorio.md, onde estão os resultados:
  1. CSV e JSON de resultados   2. notebooks com saída   3. logs e checkpoints   4. figuras e tabelas prontas
e também README, docs, licença, dependências, git (remote, commit, tags) e PDFs de paper no repo.
Para notebooks, guarda os títulos (células Markdown) e as saídas de texto com números, com a célula de origem,
para que todo número do paper possa ser rastreado até um arquivo.
Uma URL é clonada com `git clone --depth 1` (repositório público). Para repositório privado, use o
conector do GitHub, se houver, ou peça o .zip.
"""
import argparse
import csv
import json
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

IGNORAR = {".git", ".venv", "venv", "node_modules", "__pycache__", ".ipynb_checkpoints", ".mypy_cache", ".pytest_cache",
           "site-packages", ".idea", ".vscode", "dist", "build", ".cache"}
NUM = re.compile(r"(?<![\w.])[-+−]?\d+(?:[.,]\d+)?%?")


def obter(origem: str) -> tuple[Path, str | None]:
    if re.match(r"https?://|git@", origem):
        destino = Path(tempfile.mkdtemp(prefix="repo-")) / "repo"
        r = subprocess.run(["git", "clone", "--depth", "1", origem, str(destino)], capture_output=True, text=True)
        if r.returncode != 0:
            sys.exit("Não consegui clonar (repositório privado ou URL errada). Use o conector do GitHub ou envie um .zip.\n"
                     + r.stderr[-500:])
        return destino, origem
    p = Path(origem).expanduser()
    if p.suffix == ".zip":
        destino = Path(tempfile.mkdtemp(prefix="repo-"))
        with zipfile.ZipFile(p) as z:
            z.extractall(destino)
        filhos = [c for c in destino.iterdir() if not c.name.startswith("__MACOSX")]
        return (filhos[0] if len(filhos) == 1 and filhos[0].is_dir() else destino), None
    if not p.exists():
        sys.exit(f"Não achei {p}")
    return p.resolve(), None


def arquivos(raiz: Path):
    for p in sorted(raiz.rglob("*")):
        if p.is_file() and not any(part in IGNORAR for part in p.relative_to(raiz).parts):
            yield p


def git_info(raiz: Path):
    def g(*args):
        r = subprocess.run(["git", "-C", str(raiz), *args], capture_output=True, text=True)
        return r.stdout.strip() if r.returncode == 0 else None
    if not g("rev-parse", "--is-inside-work-tree"):
        return None
    return {"remote": g("config", "--get", "remote.origin.url"), "commit": g("rev-parse", "--short", "HEAD"),
            "data_commit": g("log", "-1", "--format=%cs"), "tags": (g("tag", "--list") or "").split()}


def resumo_notebook(p: Path, raiz: Path):
    try:
        nb = json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        return {"arquivo": str(p.relative_to(raiz)), "erro": str(e)[:200]}
    cells = nb.get("cells", [])
    titulos, saidas = [], []
    com_saida = 0
    for i, c in enumerate(cells):
        src = "".join(c.get("source", []))
        if c.get("cell_type") == "markdown":
            titulos += [ln.strip() for ln in src.splitlines() if ln.startswith("#")][:3]
        outs = c.get("outputs", []) if c.get("cell_type") == "code" else []
        if outs:
            com_saida += 1
        for o in outs:
            txt = "".join(o.get("text", [])) or "".join((o.get("data") or {}).get("text/plain", []))
            if txt and NUM.search(txt):
                saidas.append({"celula": i, "texto": txt.strip()[:1500]})
    return {"arquivo": str(p.relative_to(raiz)), "celulas": len(cells), "celulas_com_saida": com_saida,
            "titulos": titulos[:80], "saidas_com_numeros": saidas[:200],
            "imagens_nas_saidas": sum(1 for c in cells for o in c.get("outputs", []) if "image/png" in (o.get("data") or {}))}


def resumo_tabela(p: Path, raiz: Path):
    info = {"arquivo": str(p.relative_to(raiz)), "bytes": p.stat().st_size}
    try:
        if p.suffix == ".csv":
            with p.open(encoding="utf-8", errors="replace", newline="") as f:
                linhas = list(csv.reader(f))
            info |= {"colunas": linhas[0] if linhas else [], "linhas": max(0, len(linhas) - 1),
                     "amostra": linhas[1:6]}
        else:
            d = json.loads(p.read_text(encoding="utf-8"))
            info["chaves"] = list(d)[:40] if isinstance(d, dict) else f"lista com {len(d)} itens"
            info["amostra"] = json.dumps(d, ensure_ascii=False)[:800]
    except Exception as e:  # noqa: BLE001
        info["erro"] = str(e)[:200]
    return info


def inventario(raiz: Path, url=None):
    inv = {"raiz": str(raiz), "url": url, "git": git_info(raiz), "readme": None, "licenca": None, "dependencias": [],
           "docs": [], "resultados_tabulares": [], "notebooks": [], "logs": [], "checkpoints": [], "figuras": [],
           "papers_pdf": [], "codigo": [], "configs": [], "outros": 0}
    for p in arquivos(raiz):
        rel = str(p.relative_to(raiz))
        nome, suf = p.name.lower(), p.suffix.lower()
        if nome.startswith("readme") and inv["readme"] is None and p.parent == raiz:
            inv["readme"] = {"arquivo": rel, "texto": p.read_text(encoding="utf-8", errors="replace")[:12000]}
        elif nome.startswith(("license", "licence", "copying")):
            inv["licenca"] = {"arquivo": rel, "inicio": p.read_text(encoding="utf-8", errors="replace")[:300]}
        elif nome in ("requirements.txt", "pyproject.toml", "environment.yml", "setup.py", "package.json", "uv.lock", "poetry.lock"):
            inv["dependencias"].append(rel)
        elif suf == ".ipynb":
            inv["notebooks"].append(resumo_notebook(p, raiz))
        elif suf in (".csv", ".tsv") or (suf == ".json" and p.stat().st_size < 5_000_000 and not nome.endswith(("package.json", "tsconfig.json"))):
            inv["resultados_tabulares"].append(resumo_tabela(p, raiz))
        elif suf in (".log", ".out") or "tensorboard" in rel.lower() or nome.startswith("events.out.tfevents"):
            inv["logs"].append(rel)
        elif suf in (".pt", ".pth", ".ckpt", ".safetensors", ".h5", ".onnx", ".pkl", ".joblib", ".bin"):
            inv["checkpoints"].append({"arquivo": rel, "mb": round(p.stat().st_size / 1e6, 1)})
        elif suf in (".png", ".jpg", ".jpeg", ".svg", ".gif") or (suf == ".pdf" and "fig" in rel.lower()):
            inv["figuras"].append(rel)
        elif suf == ".pdf":
            inv["papers_pdf"].append(rel)
        elif suf in (".md", ".rst", ".txt") and not nome.startswith("readme"):
            inv["docs"].append({"arquivo": rel, "inicio": p.read_text(encoding="utf-8", errors="replace")[:600]})
        elif suf in (".py", ".r", ".jl", ".cpp", ".c", ".rs", ".js", ".ts", ".sh", ".m"):
            inv["codigo"].append({"arquivo": rel, "linhas": sum(1 for _ in p.open(errors="replace"))})
        elif suf in (".yaml", ".yml", ".toml", ".cfg", ".ini"):
            inv["configs"].append(rel)
        else:
            inv["outros"] += 1
    return inv


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("origem")
    ap.add_argument("--saida", default="inventario.json")
    a = ap.parse_args()
    raiz, url = obter(a.origem)
    inv = inventario(raiz, url)
    Path(a.saida).write_text(json.dumps(inv, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Inventário de {raiz} salvo em {a.saida}")
    print(f"  git: {inv['git']}")
    print(f"  README: {'sim' if inv['readme'] else 'NÃO'} | licença: {inv['licenca']['arquivo'] if inv['licenca'] else 'NÃO'}")
    print(f"  1. resultados CSV/JSON: {len(inv['resultados_tabulares'])}")
    print(f"  2. notebooks: {len(inv['notebooks'])} ({sum(n.get('celulas_com_saida', 0) for n in inv['notebooks'])} células com saída)")
    print(f"  3. logs: {len(inv['logs'])} | checkpoints: {len(inv['checkpoints'])}")
    print(f"  4. figuras: {len(inv['figuras'])} | PDFs (paper?): {inv['papers_pdf']}")
    print(f"  código: {len(inv['codigo'])} arquivos | docs: {len(inv['docs'])} | configs: {len(inv['configs'])}")


if __name__ == "__main__":
    main()
