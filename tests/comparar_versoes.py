"""comparar_versoes.py: página HTML que compara o paper original com as versões geradas pelas skills.

Uso:
  python3 tests/comparar_versoes.py <original.pdf> --saida <pasta> \\
      --versao "Rótulo|skill|pasta-do-teste|repo|descrição[|cego]" [--versao ...]

- skill: formata, refaz ou cria (para o checklist).
- pasta-do-teste: a pasta de tests/rodar_teste_skill.sh, com sessao.jsonl, perguntas.md e <nome>-insperai/.
- repo: o repositório usado como fonte na verificação de números (no teste cego, a cópia limpa).
- cego: o paper original não conta como fonte, e o log é auditado atrás de acessos ao paper do grupo.
Versão sem main.pdf aparece como "em andamento". A página e as imagens ficam em <saida>/ (use tests/saidas/, fora do git).
"""
import argparse
import html
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pymupdf

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "padrao/scripts"))
sys.path.insert(0, str(RAIZ / "tests"))
import contar_palavras  # noqa: E402
import verificar_cobertura as vc  # noqa: E402
from verificar_checklist import OBRIGATORIAS  # noqa: E402

ESC = html.escape
# Acesso ao paper do grupo no teste cego: o PDF de teste, a pasta paper/ do repo ou o clone real do repo (que tem o paper)
_REPO_REAL = RAIZ / "tests/privado/repos/wakely"
ACESSO_PAPER = re.compile(r"tests/privado/papers|wakely-original|paper/wakely|/paper/"
                          + (f"|{re.escape(str(_REPO_REAL.resolve()))}" if _REPO_REAL.exists() else ""))


# ----------------------------------------------------------------------------- coleta

def renderizar(pdf, pasta, dpi=130):
    pasta.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open(pdf)
    caminhos = []
    for i, pg in enumerate(doc):
        destino = pasta / f"p{i + 1:02d}.jpg"
        pg.get_pixmap(dpi=dpi).save(destino)
        caminhos.append(destino)
    return caminhos


def chaves_balanceadas(tex, comando):
    """Conteúdo de \\comando{...} com chaves aninhadas, ou None."""
    i = tex.find(comando + "{")
    if i < 0:
        return None
    j, nivel = i + len(comando) + 1, 1
    while j < len(tex) and nivel:
        nivel += {"{": 1, "}": -1}.get(tex[j], 0) if tex[j - 1] != "\\" else 0
        j += 1
    return tex[i + len(comando) + 1:j - 1]


MATH = {r"\pm": "±", r"\times": "×", r"\approx": "≈", r"\le": "≤", r"\ge": "≥", r"\Delta": "Δ", r"\mu": "μ",
        r"\to": "→", r"\cdot": "·", r"\sim": "~", r"\%": "%", r"\,": " ", r"\;": " ", r"\!": ""}


def tex2html(s):
    s = re.sub(r"(?<!\\)%.*", "", s)
    s = ESC(s, quote=False)
    s = s.replace("{,}", ",").replace("{.}", ".").replace("~", " ").replace("---", "—").replace("--", "–")
    s = s.replace("``", "“").replace("''", "”")

    def math(m):
        t = m.group(1)
        for k, v in MATH.items():
            t = t.replace(k, v)
        t = re.sub(r"\^\{([^}]*)\}|\^(.)", lambda x: f"<sup>{x.group(1) or x.group(2)}</sup>", t)
        t = re.sub(r"_\{([^}]*)\}|_(.)", lambda x: f"<sub>{x.group(1) or x.group(2)}</sub>", t)
        t = re.sub(r"\\(text|mathrm|mathit|mathbf)\{([^}]*)\}", r"\2", t)
        return re.sub(r"\\[a-zA-Z]+", "", t).replace("{", "").replace("}", "")

    s = re.sub(r"\$([^$]+)\$", math, s)
    s = re.sub(r"\\cite[tp]?\*?(\[[^\]]*\])*\{[^}]*\}", '<span class="cit">[cit.]</span>', s)
    for _ in range(3):
        s = re.sub(r"\\textbf\{([^{}]*)\}", r"<strong>\1</strong>", s)
        s = re.sub(r"\\(emph|textit)\{([^{}]*)\}", r"<em>\2</em>", s)
        s = re.sub(r"\\(texttt|url)\{([^{}]*)\}", r"<code>\2</code>", s)
    for k, v in MATH.items():
        s = s.replace(k, v)
    s = re.sub(r"\\[a-zA-Z]+\*?", "", s).replace("{", "").replace("}", "").replace("\\", "")
    return "".join(f"<p>{p.strip()}</p>" for p in re.split(r"\n\s*\n|\\par\b", s) if p.strip())


def segs2html(segs):
    out = []
    for t, st in segs:
        t = ESC(t, quote=False)
        out.append(f"<strong><em>{t}</em></strong>" if st == "bi" else f"<strong>{t}</strong>" if st == "b"
                   else f"<em>{t}</em>" if st == "i" else f"<sub>{t}</sub>" if st == "sub"
                   else f"<sup>{t}</sup>" if st == "sup" else t)
    return "".join(out)


def n_palavras_html(h):
    return len(re.sub(r"<[^>]+>", " ", h).split())


def classificar(titulo):
    for i, (_, padrao) in enumerate(OBRIGATORIAS):
        if re.search(padrao, titulo, re.I):
            return i
    return None


def limpa_titulo(t):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", tex2html(t))).strip()


def secoes_tex(tex):
    tex = re.sub(r"(?<!\\)%.*", "", tex)
    corte = tex.find("\\appendix")
    out, n, n_ap = [], 0, 0
    for m in re.finditer(r"\\section(\*?)\{((?:[^{}]|\{[^{}]*\})*)\}", tex):
        estrela = m.group(1) == "*"
        apendice = 0 <= corte < m.start()
        if estrela:
            numero = ""
        elif apendice:
            n_ap += 1
            numero = chr(64 + n_ap)
        else:
            n += 1
            numero = str(n)
        titulo = limpa_titulo(m.group(2))
        out.append({"numero": numero, "titulo": titulo, "slot": classificar(titulo), "apendice": apendice})
    return out


def perguntas_md(p):
    """Perguntas registradas: linhas de tabela com id (1, C1, N1, P1) ou parágrafos **P1. Título.**"""
    if not p.exists():
        return []
    linhas = p.read_text(encoding="utf-8").splitlines()
    out = []
    for i, ln in enumerate(linhas):
        m = re.match(r"^\|\s*([PCN]?\d+)\s*\|(.*)\|\s*$", ln)
        if m:
            celulas = [c.strip() for c in m.group(2).split("|")]
            out.append({"id": m.group(1), "pergunta": celulas[0], "resposta": celulas[-1] if len(celulas) > 1 else ""})
            continue
        m = re.match(r"^\*\*(P?\d+)\.\s*(.*?)\*\*\s*(.*)$", ln)
        if m:
            resposta = ""
            for prox in linhas[i + 1:i + 25]:
                if re.match(r"^\*\*P?\d+\.", prox) or prox.startswith("## "):
                    break
                r = re.match(r"^[>\-\s]*\**(Resposta[^:]*):?\**:?\s*(.*)$", prox, re.I)
                if r:
                    resposta = r.group(2).strip()
                    break
            out.append({"id": m.group(1), "pergunta": (m.group(2) + " " + m.group(3)).strip(), "resposta": resposta})
    return out


def md_inline(t):
    t = ESC(t, quote=False)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    return re.sub(r"(?<![\w*])\*([^*]+)\*(?![\w*])", r"<em>\1</em>", t)


def sessao(p, cego):
    info = {"modelo": "", "custo": None, "min": None, "turnos": None, "chamadas": 0, "acessos": []}
    if not p.exists():
        return info
    for ln in p.read_text(encoding="utf-8").splitlines():
        try:
            e = json.loads(ln)
        except json.JSONDecodeError:
            continue
        if e.get("type") == "system" and e.get("subtype") == "init":
            info["modelo"] = e.get("model", "")
        elif e.get("type") == "result":
            info.update(custo=e.get("total_cost_usd"), min=(e.get("duration_ms") or 0) / 60000, turnos=e.get("num_turns"))
        elif e.get("type") == "assistant":
            for c in e["message"].get("content", []):
                if c.get("type") == "tool_use":
                    info["chamadas"] += 1
                    if cego:
                        s = json.dumps(c["input"], ensure_ascii=False)
                        m = ACESSO_PAPER.search(s)
                        if m:
                            info["acessos"].append(s[max(0, m.start() - 80):m.end() + 60])
    return info


def checklist(pasta, skill):
    r = subprocess.run([sys.executable, str(RAIZ / "padrao/scripts/verificar_checklist.py"), str(pasta), "--skill", skill],
                       capture_output=True, text=True)
    itens = [(m.group(1), m.group(2)) for m in re.finditer(r"^- (FALHA|AVISO): (.*)$", r.stdout, re.M)]
    return {"falhas": sum(1 for t, _ in itens if t == "FALHA"), "avisos": sum(1 for t, _ in itens if t == "AVISO"), "itens": itens}


def coletar_original(pdf, saida):
    d = vc.carregar_original(pdf)
    imgs = renderizar(pdf, saida / "img" / "original")
    secs = []
    for b in d["blocos"]:
        if b["tipo"] == "secao" and b.get("nivel", 1) == 1:
            t = b.get("titulo", "")
            secs.append({"numero": str(b.get("numero") or ""), "titulo": t, "slot": classificar(t), "apendice": False})
    resumo = "".join(f"<p>{segs2html(p)}</p>" for p in d.get("resumo", []))
    return {
        "d": d, "imgs": imgs, "secoes": secs, "resumo": resumo,
        "paginas": len(imgs), "palavras": contar_palavras.contar_json(d),
        "figuras": sum(1 for b in d["blocos"] if b["tipo"] == "figura"),
        "tabelas": sum(1 for b in d["blocos"] if b["tipo"] == "tabela"),
        "refs": len(d.get("referencias", [])),
    }


def coletar_versao(spec, original, saida, pdf_original):
    partes = spec.split("|")
    rotulo, skill, pasta, repo, desc = partes[:5]
    cego = len(partes) > 5 and partes[5] == "cego"
    pasta = Path(pasta)
    saidas = sorted(pasta.glob("*-insperai"))
    o = saidas[0] if saidas else pasta / "x-insperai"
    v = {"rotulo": rotulo, "skill": skill, "desc": desc, "cego": cego, "pasta": pasta,
         "sessao": sessao(pasta / "sessao.jsonl", cego), "perguntas": perguntas_md(pasta / "perguntas.md"),
         "pronto": (o / "main.pdf").exists() and (pasta / "resumo-entrega.md").exists()}
    conf = o / "trabalho" / "conflitos.md"
    v["conflitos"] = re.findall(r"^##\s+(C\d+\..*)$", conf.read_text(encoding="utf-8"), re.M) if conf.exists() else []
    v["entrega"] = (pasta / "resumo-entrega.md").read_text(encoding="utf-8") if (pasta / "resumo-entrega.md").exists() else ""
    if not v["pronto"]:
        return v
    tex = (o / "main.tex").read_text(encoding="utf-8")
    bib = (o / "refs.bib").read_text(encoding="utf-8") if (o / "refs.bib").exists() else ""
    slug = re.sub(r"[^a-z0-9]+", "-", rotulo.lower()).strip("-")
    v["imgs"] = renderizar(o / "main.pdf", saida / "img" / slug)
    v["paginas"] = len(v["imgs"])
    v["palavras"] = contar_palavras.contar(o / "main.tex")
    v["figuras"] = len(re.findall(r"\\begin\{figure\*?\}", tex))
    v["tabelas"] = len(re.findall(r"\\begin\{table\*?\}", tex))
    v["refs"] = len(re.findall(r"^@\w+\{", bib, re.M))
    v["verificar"] = len(re.findall(r"\[VERIFICAR\]", bib))
    v["secoes"] = secoes_tex(tex)
    r = chaves_balanceadas(tex, "\\resumo")
    v["resumo"] = tex2html(r) if r else ""
    v["checklist"] = checklist(o, skill)
    extras = [pasta / "perguntas.md"] if (pasta / "perguntas.md").exists() else []
    v["cob"] = vc.avaliar(original["d"], o / "main.tex", repo, extras, original_como_fonte=not cego)
    if skill == "formata":
        r = subprocess.run([sys.executable, str(RAIZ / "padrao/scripts/verificar_texto.py"), str(pdf_original), str(o / "main.pdf")],
                           capture_output=True, text=True)
        n = lambda rot: int(m.group(1)) if (m := re.search(rot + r": (\d+)", r.stdout)) else 0  # noqa: E731
        v["texto"] = {"ok": "TEXTO IDÊNTICO" in r.stdout, "falta": n("Trechos que faltam na saída"),
                      "sobra": n("Trechos que sobram na saída"), "relatorio": r.stdout}
    return v


# ----------------------------------------------------------------------------- página

CSS = r"""
:root{
  --bg:#f6f7fb; --surface:#ffffff; --surface-2:#eef1f7; --text:#151a24; --muted:#5b6474; --border:#dfe3ec;
  --ok:#15803d; --bad:#b91c1c; --warn:#b45309;
  --v0:#475569; --v1:#0f766e; --v2:#0058B8; --v3:#a21caf; --v4:#b45309;
  --s0:#2563eb; --s1:#7c3aed; --s2:#0891b2; --s3:#059669; --s4:#d97706; --s5:#db2777; --s6:#4b5563;
  --shadow:0 1px 2px rgba(16,24,40,.06),0 4px 16px rgba(16,24,40,.06);
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --bg:#0e1117; --surface:#161b24; --surface-2:#1e2532; --text:#e7eaf0; --muted:#9aa3b2; --border:#2a3240;
    --ok:#4ade80; --bad:#f87171; --warn:#fbbf24;
    --v0:#94a3b8; --v1:#2dd4bf; --v2:#5b9bff; --v3:#e879f9; --v4:#fbbf24;
    --s0:#60a5fa; --s1:#a78bfa; --s2:#22d3ee; --s3:#34d399; --s4:#fbbf24; --s5:#f472b6; --s6:#9ca3af;
    --shadow:none;
  }
}
:root[data-theme="dark"]{
  --bg:#0e1117; --surface:#161b24; --surface-2:#1e2532; --text:#e7eaf0; --muted:#9aa3b2; --border:#2a3240;
  --ok:#4ade80; --bad:#f87171; --warn:#fbbf24;
  --v0:#94a3b8; --v1:#2dd4bf; --v2:#5b9bff; --v3:#e879f9; --v4:#fbbf24;
  --s0:#60a5fa; --s1:#a78bfa; --s2:#22d3ee; --s3:#34d399; --s4:#fbbf24; --s5:#f472b6; --s6:#9ca3af;
  --shadow:none;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);font:15px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
.wrap{max-width:1280px;margin:0 auto;padding:0 16px 80px}
header.hero{padding:40px 0 20px}
.eyebrow{font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);font-weight:600}
h1{font-size:clamp(26px,4vw,38px);line-height:1.15;margin:6px 0 10px;letter-spacing:-.01em}
.lede{color:var(--muted);max-width:760px;margin:0 0 20px}
.legend{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:10px}
.vcard{background:var(--surface);border:1px solid var(--border);border-top:4px solid var(--c);border-radius:12px;padding:12px 14px;box-shadow:var(--shadow)}
.vcard b{display:block;font-size:15px}
.vcard span{color:var(--muted);font-size:13px}
.badge{display:inline-block;font-size:11px;font-weight:600;padding:2px 8px;border-radius:99px;margin-top:6px;background:var(--surface-2);color:var(--muted)}
.badge.ok{color:var(--ok)} .badge.bad{color:var(--bad)} .badge.run{color:var(--warn)}
nav.toc{position:sticky;top:0;z-index:5;background:color-mix(in srgb,var(--bg) 88%,transparent);backdrop-filter:blur(8px);
  border-bottom:1px solid var(--border);margin:0 -16px;padding:10px 16px;display:flex;gap:6px;overflow-x:auto}
nav.toc a{white-space:nowrap;color:var(--text);text-decoration:none;font-size:13px;padding:5px 11px;border-radius:99px;background:var(--surface);border:1px solid var(--border)}
nav.toc a:hover{border-color:var(--v1)}
section{padding-top:34px}
h2{font-size:22px;margin:0 0 4px}
.sub{color:var(--muted);margin:0 0 16px;font-size:14px;max-width:820px}
.panel{background:var(--surface);border:1px solid var(--border);border-radius:14px;box-shadow:var(--shadow)}
.scroll-x{overflow-x:auto}
table.kpi{border-collapse:collapse;width:100%;min-width:760px}
table.kpi th,table.kpi td{padding:10px 14px;border-bottom:1px solid var(--border);text-align:left;vertical-align:middle}
table.kpi thead th{font-size:13px;position:relative}
table.kpi thead th i{display:inline-block;width:10px;height:10px;border-radius:3px;background:var(--c);margin-right:6px}
table.kpi tbody th{font-weight:500;color:var(--muted);font-size:13px;width:230px}
table.kpi tr:last-child td,table.kpi tr:last-child th{border-bottom:0}
.val{font-variant-numeric:tabular-nums;font-weight:600}
.val small{font-weight:400;color:var(--muted);margin-left:4px}
.bar{height:6px;border-radius:99px;background:var(--surface-2);margin-top:6px;overflow:hidden}
.bar > div{height:100%;background:var(--c);border-radius:99px}
.na{color:var(--muted)}
.good{color:var(--ok)} .bad{color:var(--bad)}
.grid{display:grid;gap:14px;grid-template-columns:repeat(auto-fit,minmax(240px,1fr))}
.cover{padding:10px;border-top:4px solid var(--c)}
.cover h3,.colhead{margin:2px 4px 10px;font-size:14px;display:flex;justify-content:space-between;gap:8px;align-items:baseline}
.cover h3 small,.colhead small{color:var(--muted);font-weight:400;font-size:12px}
.cover img{width:100%;border-radius:6px;border:1px solid var(--border);cursor:zoom-in;display:block;background:#fff}
.pending{display:flex;align-items:center;justify-content:center;aspect-ratio:210/297;border-radius:6px;border:1px dashed var(--border);
  color:var(--muted);font-size:13px;text-align:center;padding:16px;background:repeating-linear-gradient(-45deg,var(--surface),var(--surface) 10px,var(--surface-2) 10px,var(--surface-2) 20px)}
.slots{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:14px}
.slot{font-size:12px;padding:3px 9px;border-radius:99px;border:1px solid color-mix(in srgb,var(--s) 45%,transparent);background:color-mix(in srgb,var(--s) 14%,transparent)}
.slot.extra{--s:var(--muted);border-style:dashed}
.cols{display:grid;gap:14px;grid-template-columns:repeat(auto-fit,minmax(230px,1fr))}
.col{padding:12px;border-top:4px solid var(--c)}
.sec{display:flex;gap:8px;align-items:baseline;padding:7px 10px;margin:5px 0;border-radius:8px;font-size:13.5px;
  background:color-mix(in srgb,var(--s) 12%,transparent);border-left:4px solid var(--s)}
.sec.extra{--s:var(--muted);background:transparent;border:1px dashed var(--border);border-left:4px dashed var(--muted)}
.sec .n{font-variant-numeric:tabular-nums;color:var(--muted);min-width:18px;font-size:12px}
.sec .tag{margin-left:auto;font-size:11px;color:var(--muted);white-space:nowrap}
.matrix{display:grid;gap:3px;align-items:center;padding:14px;min-width:max-content}
.matrix .rl{font-size:13px;font-weight:600;padding-right:10px;white-space:nowrap;position:sticky;left:0;background:var(--surface);z-index:1}
.matrix .rl small{display:block;font-weight:400;color:var(--muted)}
.matrix .h{writing-mode:vertical-rl;transform:rotate(180deg);font-size:10.5px;color:var(--muted);height:62px;text-align:left;font-variant-numeric:tabular-nums;line-height:14px}
.matrix .h.tab{color:var(--text)}
.cell{width:14px;height:14px;border-radius:3px;border:1.5px solid color-mix(in srgb,var(--c) 55%,transparent)}
.cell.on{background:var(--c);border-color:var(--c)}
.matrix .grp{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;padding-bottom:4px}
.chips{display:flex;flex-wrap:wrap;gap:6px}
.chip{font-size:12px;padding:2px 8px;border-radius:6px;background:var(--surface-2);font-variant-numeric:tabular-nums}
.abs{padding:14px 16px;border-top:4px solid var(--c);font-size:14px}
.abs p{margin:0 0 .6em}
.abs .cit{color:var(--muted);font-size:12px}
.qa{padding:12px 14px;border-top:4px solid var(--c)}
details{border-top:1px solid var(--border);padding:8px 0}
details:first-of-type{border-top:0}
summary{cursor:pointer;font-weight:600;font-size:14px}
summary small{color:var(--muted);font-weight:400}
.q{display:grid;grid-template-columns:auto 1fr;gap:4px 10px;padding:8px 0;border-bottom:1px dashed var(--border);font-size:13.5px}
.q:last-child{border-bottom:0}
.q .id{font-size:11px;font-weight:700;padding:2px 7px;border-radius:6px;background:color-mix(in srgb,var(--c) 16%,transparent);color:var(--text);height:fit-content}
.q .r{grid-column:2;color:var(--muted)}
pre.md{white-space:pre-wrap;font:12.5px/1.5 ui-monospace,SFMono-Regular,Menlo,monospace;background:var(--surface-2);padding:12px;border-radius:8px;max-height:420px;overflow:auto;margin:8px 0 0}
.strip{padding:12px;margin-bottom:14px;border-left:4px solid var(--c)}
.thumbs{display:flex;gap:10px;overflow-x:auto;padding:4px 2px 10px;scroll-snap-type:x proximity}
.thumbs figure{margin:0;flex:0 0 auto;scroll-snap-align:start;text-align:center}
.thumbs img{height:250px;width:auto;border-radius:5px;border:1px solid var(--border);cursor:zoom-in;display:block;background:#fff}
.thumbs figcaption{font-size:11px;color:var(--muted);margin-top:3px}
.lb{position:fixed;inset:0;background:rgba(5,8,14,.86);display:none;z-index:50;align-items:center;justify-content:center;flex-direction:column;padding:16px}
.lb.open{display:flex}
.lb img{max-width:min(980px,100%);max-height:calc(100vh - 90px);border-radius:6px;background:#fff}
.lb .bar2{color:#e7eaf0;font-size:14px;margin-top:10px;display:flex;gap:14px;align-items:center}
.lb button{background:#ffffff1f;color:#fff;border:1px solid #ffffff33;border-radius:8px;padding:6px 12px;font-size:14px;cursor:pointer}
code{font:12.5px ui-monospace,SFMono-Regular,Menlo,monospace;background:var(--surface-2);padding:1px 5px;border-radius:5px}
.note{font-size:13px;color:var(--muted);margin-top:10px}
footer{color:var(--muted);font-size:12.5px;margin-top:40px;border-top:1px solid var(--border);padding-top:14px}
@media (max-width:640px){ table.kpi tbody th{width:160px} .thumbs img{height:200px} }
"""

JS = r"""
const lb=document.querySelector('.lb'), lbImg=lb.querySelector('img'), lbTxt=lb.querySelector('.txt');
let grupo=[], idx=0;
function show(){ const el=grupo[idx]; lbImg.src=el.src; lbTxt.textContent=el.dataset.rotulo+' · página '+(idx+1)+' de '+grupo.length; }
document.querySelectorAll('img[data-grupo]').forEach(el=>el.addEventListener('click',()=>{
  grupo=[...document.querySelectorAll('img[data-grupo="'+el.dataset.grupo+'"][data-pag]')];
  if(!grupo.length) grupo=[el];
  idx=Math.max(0,grupo.findIndex(g=>g.src===el.src)); show(); lb.classList.add('open');
}));
function mv(d){ idx=(idx+d+grupo.length)%grupo.length; show(); }
lb.querySelector('.prev').onclick=e=>{e.stopPropagation();mv(-1)};
lb.querySelector('.next').onclick=e=>{e.stopPropagation();mv(1)};
lb.addEventListener('click',e=>{ if(e.target===lb) lb.classList.remove('open'); });
lb.querySelector('.close').onclick=()=>lb.classList.remove('open');
document.addEventListener('keydown',e=>{ if(!lb.classList.contains('open')) return;
  if(e.key==='Escape') lb.classList.remove('open'); if(e.key==='ArrowRight') mv(1); if(e.key==='ArrowLeft') mv(-1); });
"""


def fmt(x, casas=0):
    if x is None:
        return "—"
    s = f"{x:,.{casas}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def pagina(original, versoes, saida):
    cols = [{"rotulo": "Original", "desc": "Paper do grupo, como foi entregue", "cor": "var(--v0)", "o": True, **original}]
    for i, v in enumerate(versoes):
        cols.append({**v, "cor": f"var(--v{i + 1})", "o": False})
    rel = lambda p: p.relative_to(saida).as_posix()  # noqa: E731
    pronto = lambda c: c["o"] or c.get("pronto")  # noqa: E731

    # Legenda
    leg = []
    for c in cols:
        s = c.get("sessao", {})
        if c["o"]:
            badge = '<span class="badge">referência</span>'
        elif not c["pronto"]:
            badge = f'<span class="badge run">em andamento · {s.get("chamadas", 0)} chamadas</span>'
        elif c["cego"]:
            n = len(s.get("acessos", []))
            badge = (f'<span class="badge ok">teste cego confirmado: 0 acessos ao paper do grupo</span>' if n == 0
                     else f'<span class="badge bad">{n} acesso(s) ao paper do grupo no log</span>')
        else:
            badge = '<span class="badge ok">concluído</span>'
        modelo = f' · {ESC(s["modelo"])}' if s.get("modelo") else ""
        leg.append(f'<div class="vcard" style="--c:{c["cor"]}"><b>{ESC(c["rotulo"])}</b><span>{ESC(c["desc"])}{modelo}</span><br>{badge}</div>')

    # KPIs
    o = original

    def linha(rotulo, fn, maior=None):
        vals = []
        for c in cols:
            vals.append(fn(c) if pronto(c) else None)
        nums = [v[0] for v in vals if v and isinstance(v[0], (int, float))]
        mx = maior or (max(nums) if nums else 1) or 1
        tds = []
        for c, v in zip(cols, vals):
            if not pronto(c):
                tds.append('<td class="na">em andamento</td>')
            elif v is None or (v[0] is None and not v[1]):
                tds.append('<td class="na">—</td>')
            else:
                num, txt, extra = v
                barra = f'<div class="bar"><div style="width:{min(100, 100 * num / mx):.1f}%"></div></div>' if isinstance(num, (int, float)) else ""
                tds.append(f'<td style="--c:{c["cor"]}"><div class="val">{txt}{f"<small>{extra}</small>" if extra else ""}</div>{barra}</td>')
        return f"<tr><th>{rotulo}</th>{''.join(tds)}</tr>"

    def dif(c):
        if c["o"]:
            return ""
        d = 100 * (c["palavras"] - o["palavras"]) / o["palavras"]
        return f"{'+' if d >= 0 else '−'}{fmt(abs(d), 1)}% vs. original"

    def texto_igual(c):
        if c["o"] or not c.get("texto"):
            return (None, "", "")
        t = c["texto"]
        if t["ok"]:
            return (None, '<span class="good">texto idêntico</span>', "verificar_texto.py")
        return (None, f'<span class="bad">{t["falta"] + t["sobra"]} diferença(s)</span>', f'{t["falta"]} faltam, {t["sobra"]} sobram')

    linhas = [
        linha("Texto igual ao original (formata)", texto_igual),
        linha("Páginas", lambda c: (c["paginas"], fmt(c["paginas"]), "")),
        linha("Palavras do corpo", lambda c: (c["palavras"], fmt(c["palavras"]), dif(c))),
        linha("Figuras", lambda c: (c["figuras"], fmt(c["figuras"]), "")),
        linha("Tabelas", lambda c: (c["tabelas"], fmt(c["tabelas"]), "")),
        linha("Referências", lambda c: (c["refs"], fmt(c["refs"]), "" if c["o"] else f'{c["verificar"]} marcadas [VERIFICAR]')),
        linha("Números-chave do original presentes", lambda c: (None, "", "") if c["o"] else
              (100 * c["cob"]["cobertura"], f'{fmt(100 * c["cob"]["cobertura"])}%',
               f'{sum(k["presente"] for k in c["cob"]["chaves"])} de {len(c["cob"]["chaves"])}'), maior=100),
        linha("Números sem fonte", lambda c: (None, "", "") if c["o"] else
              (len(c["cob"]["sem_fonte"]), f'<span class="{"good" if not c["cob"]["sem_fonte"] else "bad"}">{len(c["cob"]["sem_fonte"])}</span>',
               f'de {c["cob"]["total_novos"]} números' + (" (só repo e respostas)" if c["cego"] else ""))),
        linha("Checklist automático", lambda c: (None, "", "") if c["o"] else
              (None, f'<span class="{"good" if not c["checklist"]["falhas"] else "bad"}">{c["checklist"]["falhas"]} falha(s)</span>',
               f'{c["checklist"]["avisos"]} aviso(s)')),
        linha("Perguntas registradas", lambda c: (None, "", "") if c["o"] else (len(c["perguntas"]), fmt(len(c["perguntas"])),
              f'{len(c["conflitos"])} conflitos' if c["conflitos"] else "")),
        linha("Tempo da sessão", lambda c: (None, "", "") if c["o"] else (c["sessao"]["min"], f'{fmt(c["sessao"]["min"], 1)} min',
              f'{c["sessao"]["turnos"]} turnos' if c["sessao"]["turnos"] else "")),
        linha("Custo da sessão", lambda c: (None, "", "") if c["o"] else (c["sessao"]["custo"], f'US$ {fmt(c["sessao"]["custo"], 2)}', "")),
    ]
    thead = "".join(f'<th style="--c:{c["cor"]}"><i></i>{ESC(c["rotulo"])}</th>' for c in cols)
    kpi = f'<div class="panel scroll-x"><table class="kpi"><thead><tr><th></th>{thead}</tr></thead><tbody>{"".join(linhas)}</tbody></table></div>'

    # Capas
    capas = []
    for c in cols:
        if pronto(c):
            g = "original" if c["o"] else re.sub(r"[^a-z0-9]+", "-", c["rotulo"].lower())
            capas.append(f'<div class="panel cover" style="--c:{c["cor"]}"><h3>{ESC(c["rotulo"])}<small>{c["paginas"]} páginas</small></h3>'
                         f'<img src="{rel(c["imgs"][0])}" alt="Capa: {ESC(c["rotulo"])}" data-grupo="{g}" data-rotulo="{ESC(c["rotulo"])}"></div>')
        else:
            capas.append(f'<div class="panel cover" style="--c:{c["cor"]}"><h3>{ESC(c["rotulo"])}</h3><div class="pending">Sessão em andamento.<br>Rode o script de novo quando terminar.</div></div>')

    # Estrutura
    slots = "".join(f'<span class="slot" style="--s:var(--s{i})">{i + 1}. {ESC(n)}</span>' for i, (n, _) in enumerate(OBRIGATORIAS))
    slots += '<span class="slot extra">fora do padrão</span>'
    estr = []
    for c in cols:
        if not pronto(c):
            estr.append(f'<div class="panel col" style="--c:{c["cor"]}"><div class="colhead">{ESC(c["rotulo"])}</div><div class="pending" style="aspect-ratio:auto;min-height:160px">em andamento</div></div>')
            continue
        itens = []
        ordem = [s["slot"] for s in c["secoes"] if s["slot"] is not None and not s["apendice"]]  # apêndice não conta
        for s in c["secoes"]:
            cls = "sec" if s["slot"] is not None else "sec extra"
            st = f' style="--s:var(--s{s["slot"]})"' if s["slot"] is not None else ""
            tag = OBRIGATORIAS[s["slot"]][0] if s["slot"] is not None else ("apêndice" if s["apendice"] else "")
            tag = "" if s["slot"] is not None and OBRIGATORIAS[s["slot"]][0].lower() == s["titulo"].lower() else tag
            itens.append(f'<div class="{cls}"{st}><span class="n">{ESC(s["numero"])}</span><span>{ESC(s["titulo"])}</span><span class="tag">{ESC(tag)}</span></div>')
        faltam = [OBRIGATORIAS[i][0] for i in range(len(OBRIGATORIAS)) if i not in ordem]
        na_ordem = ordem == sorted(ordem)
        resumo_estr = (f'<span class="good">7 de 7 obrigatórias</span>' if not faltam else f'<span class="bad">faltam: {ESC(", ".join(faltam))}</span>')
        resumo_estr += " · " + ('<span class="good">na ordem</span>' if na_ordem else '<span class="bad">fora de ordem</span>')
        estr.append(f'<div class="panel col" style="--c:{c["cor"]}"><div class="colhead">{ESC(c["rotulo"])}<small>{len(c["secoes"])} seções</small></div>'
                    f'{"".join(itens)}<div class="note">{resumo_estr}</div></div>')

    # Matriz dos números-chave
    ref = next((c["cob"]["chaves"] for c in cols if not c["o"] and c.get("pronto")), [])
    matriz = ""
    if ref:
        n = len(ref)
        cab = '<div class="rl"></div>' + "".join(f'<div class="h{" tab" if k["origem"] == "tabela" else ""}">{ESC(k["t"])}</div>' for k in ref)
        n_res = sum(1 for k in ref if k["origem"] == "resumo")
        grp = (f'<div class="rl"></div><div class="grp" style="grid-column:span {n_res}">do resumo</div>'
               f'<div class="grp" style="grid-column:span {n - n_res}">das tabelas</div>')
        linhas_m = []
        todos_aus = set(k["t"] for k in ref)
        for c in cols:
            if c["o"]:
                continue
            if not c.get("pronto"):
                linhas_m.append(f'<div class="rl" style="--c:{c["cor"]}">{ESC(c["rotulo"])}<small>em andamento</small></div>'
                                + "".join('<div></div>' for _ in ref))
                continue
            pres = {k["t"]: k["presente"] for k in c["cob"]["chaves"]}
            todos_aus -= {t for t, p in pres.items() if p}
            linhas_m.append(f'<div class="rl" style="--c:{c["cor"]}">{ESC(c["rotulo"])}<small>{fmt(100 * c["cob"]["cobertura"])}% presentes</small></div>'
                            + "".join(f'<div class="cell{" on" if pres.get(k["t"]) else ""}" style="--c:{c["cor"]}" title="{ESC(k["t"])}: {"presente" if pres.get(k["t"]) else "ausente"}"></div>' for k in ref))
        aus = "".join(f'<span class="chip">{ESC(t)}</span>' for t in [k["t"] for k in ref if k["t"] in todos_aus])
        matriz = (f'<div class="panel scroll-x"><div class="matrix" style="grid-template-columns:auto repeat({n},14px)">{grp}{cab}{"".join(linhas_m)}</div></div>'
                  f'<p class="note">Ausentes em todas as versões concluídas: {aus or "nenhum"}</p>')
        sem = [(c, c["cob"]["sem_fonte"]) for c in cols if not c["o"] and c.get("pronto") and c["cob"]["sem_fonte"]]
        if sem:
            matriz += "".join(f'<p class="note"><b>{ESC(c["rotulo"])}</b>, números sem fonte: ' +
                              "".join(f'<span class="chip">{ESC(t)}</span> ' for t in s) + "</p>" for c, s in sem)

    # Resumos
    resumos = []
    for c in cols:
        if not pronto(c):
            resumos.append(f'<div class="panel abs" style="--c:{c["cor"]}"><div class="colhead">{ESC(c["rotulo"])}</div><div class="na">em andamento</div></div>')
            continue
        resumos.append(f'<div class="panel abs" style="--c:{c["cor"]}"><div class="colhead">{ESC(c["rotulo"])}<small>{n_palavras_html(c["resumo"])} palavras</small></div>{c["resumo"]}</div>')

    # Perguntas, conflitos e entrega
    qas = []
    for c in cols:
        if c["o"]:
            continue
        perg = "".join(f'<div class="q"><span class="id">{ESC(q["id"])}</span><span>{md_inline(q["pergunta"])}</span>'
                       + (f'<span class="r">→ {md_inline(q["resposta"])}</span>' if q["resposta"] else "") + "</div>" for q in c["perguntas"])
        blocos = [f'<details open><summary>Perguntas <small>({len(c["perguntas"])})</small></summary>{perg or "<p class=na>nenhuma registrada ainda</p>"}</details>']
        if c["conflitos"]:
            blocos.append(f'<details><summary>Conflitos paper × repo <small>({len(c["conflitos"])})</small></summary>'
                          + "".join(f'<div class="q"><span class="id">{ESC(t.split(".")[0])}</span><span>{md_inline(t.split(".", 1)[1].strip())}</span></div>' for t in c["conflitos"]) + "</details>")
        if c.get("checklist"):
            blocos.append('<details><summary>Checklist automático</summary>' + ("".join(
                f'<div class="q"><span class="id">{t}</span><span>{ESC(m)}</span></div>' for t, m in c["checklist"]["itens"]) or "<p>sem falhas nem avisos</p>") + "</details>")
        if c.get("texto"):
            blocos.append(f'<details><summary>Verificação de texto idêntico</summary><pre class="md">{ESC(c["texto"]["relatorio"])}</pre></details>')
        if c["entrega"]:
            blocos.append(f'<details><summary>Resumo da entrega escrito pela skill</summary><pre class="md">{ESC(c["entrega"])}</pre></details>')
        if c["cego"] and c["sessao"]["acessos"]:
            blocos.append('<details open><summary class="bad">Acessos ao paper do grupo no log</summary>' +
                          "".join(f'<pre class="md">{ESC(a)}</pre>' for a in c["sessao"]["acessos"]) + "</details>")
        qas.append(f'<div class="panel qa" style="--c:{c["cor"]}"><div class="colhead">{ESC(c["rotulo"])}</div>{"".join(blocos)}</div>')

    # Todas as páginas
    tiras = []
    for c in cols:
        if not pronto(c):
            continue
        g = "original" if c["o"] else re.sub(r"[^a-z0-9]+", "-", c["rotulo"].lower())
        figs = "".join(f'<figure><img loading="lazy" src="{rel(p)}" alt="{ESC(c["rotulo"])}, página {i + 1}" data-grupo="{g}" data-pag="{i + 1}" data-rotulo="{ESC(c["rotulo"])}"><figcaption>{i + 1}</figcaption></figure>'
                       for i, p in enumerate(c["imgs"]))
        tiras.append(f'<div class="panel strip" style="--c:{c["cor"]}"><div class="colhead">{ESC(c["rotulo"])}<small>{c["paginas"]} páginas · clique para ampliar, ← → para navegar</small></div><div class="thumbs">{figs}</div></div>')

    return f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Comparação do Wakely</title><style>{CSS}</style></head>
<body><div class="wrap">
<header class="hero">
  <div class="eyebrow">Insper AI · teste das skills de paper</div>
  <h1>Wakely: o paper original e as versões das skills</h1>
  <p class="lede">Cada coluna é uma versão do mesmo trabalho. O original é o paper que o grupo entregou; as outras saíram das skills rodando sozinhas no Claude Code, com fontes diferentes. Clique em qualquer página para ampliar.</p>
  <div class="legend">{"".join(leg)}</div>
</header>
<nav class="toc"><a href="#numeros">Em números</a><a href="#capas">Capas</a><a href="#estrutura">Estrutura</a><a href="#chaves">Números-chave</a><a href="#resumos">Resumos</a><a href="#perguntas">Perguntas e entrega</a><a href="#paginas">Todas as páginas</a></nav>
<section id="numeros"><h2>Em números</h2><p class="sub">As barras comparam cada linha entre as versões. "Números sem fonte" conta valores do paper que não aparecem no repositório, nas respostas registradas ou (fora do teste cego) no original: cada um é um possível resultado inventado.</p>{kpi}</section>
<section id="capas"><h2>Capas</h2><p class="sub">As versões das skills usam a capa do lab no estilo de <em>Attention Is All You Need</em>.</p><div class="grid">{"".join(capas)}</div></section>
<section id="estrutura"><h2>Estrutura</h2><p class="sub">Seções de primeiro nível na ordem em que aparecem. A cor indica a seção obrigatória do padrão a que cada uma corresponde.</p><div class="slots">{slots}</div><div class="cols">{"".join(estr)}</div></section>
<section id="chaves"><h2>Números-chave do original</h2><p class="sub">Cada coluna é um número do resumo ou das tabelas do paper original; quadrado preenchido = o número aparece na versão. Passe o mouse para ver o valor.</p>{matriz or '<p class="na">Nenhuma versão concluída ainda.</p>'}</section>
<section id="resumos"><h2>Resumos</h2><p class="sub">O resumo de cada versão, como está no PDF. O padrão recomenda de 150 a 250 palavras.</p><div class="grid">{"".join(resumos)}</div></section>
<section id="perguntas"><h2>Perguntas, conflitos e entrega</h2><p class="sub">O que cada skill perguntou (e o que foi respondido), os conflitos entre paper e repositório, o checklist e o resumo que a skill entregou.</p><div class="cols">{"".join(qas)}</div></section>
<section id="paginas"><h2>Todas as páginas</h2><div>{"".join(tiras)}</div></section>
<footer>Gerado por <code>tests/comparar_versoes.py</code>. Página local com material de outros alunos: não publique sem autorização do grupo.</footer>
</div>
<div class="lb" role="dialog" aria-label="Página ampliada"><img alt=""><div class="bar2"><button class="prev">←</button><span class="txt"></span><button class="next">→</button><button class="close">Fechar</button></div></div>
<script>{JS}</script></body></html>"""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("original")
    ap.add_argument("--versao", action="append", default=[], required=True)
    ap.add_argument("--saida", required=True)
    a = ap.parse_args()
    saida = Path(a.saida).resolve()
    if (saida / "img").exists():
        shutil.rmtree(saida / "img")
    saida.mkdir(parents=True, exist_ok=True)
    original = coletar_original(a.original, saida)
    versoes = [coletar_versao(s, original, saida, a.original) for s in a.versao]
    (saida / "index.html").write_text(pagina(original, versoes, saida), encoding="utf-8")
    print(f"Página: {saida / 'index.html'}")
    for v in versoes:
        estado = "concluída" if v["pronto"] else "em andamento"
        print(f"  {v['rotulo']}: {estado}")


if __name__ == "__main__":
    main()
