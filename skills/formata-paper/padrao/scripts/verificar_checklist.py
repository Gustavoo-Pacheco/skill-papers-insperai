"""verificar_checklist.py: confere os itens automáticos de padrao/checklist.md numa pasta de entrega.

Uso:
  python3 verificar_checklist.py <pasta-do-paper> --skill formata|refaz|cria [--sem-pdf]

Saída: lista em Markdown com OK, AVISO ou FALHA por item. Sai com 1 se houver FALHA.
Na formata, seção obrigatória ausente é AVISO (a pessoa escolheu como tratar); na refaz e na cria, é FALHA.
"""
import argparse
import re
import sys
from pathlib import Path

OBRIGATORIAS = [  # (nome, padrões de reconhecimento) na ordem do padrão
    ("Introdução", r"introdu[cç][aã]o|introduction"),
    ("Trabalhos relacionados", r"trabalhos relacionados|related work|estado da arte|background"),
    ("Método", r"m[ée]todos?\b|metodologia|methods?\b|approach"),
    ("Resultados", r"resultados|experimentos|results|experiments"),
    ("Limitações", r"limita[cç][oõ]es|limitations"),
    ("Código e dados", r"c[óo]digo e dados|code and data|disponibilidade|availability|reprodutibilidade|reproducibility"),
    ("Conclusão", r"conclus[aã]o|conclus[õo]es|conclusions?"),
]
NOMES_IA = re.compile(r"\b(claude|chatgpt|gpt-?\d|openai|anthropic|gemini|copilot|llama|mistral|deepseek|grok|perplexity)\b", re.I)


def sem_comentarios(tex):
    return re.sub(r"(?<!\\)%.*", "", tex)


def chaves_bib(bib):
    return set(re.findall(r"@\w+\s*\{\s*([^,\s]+)\s*,", bib))


def palavras(tex):
    t = re.sub(r"\\[a-zA-Z@]+\*?(\[[^\]]*\])?", " ", tex)
    t = re.sub(r"[{}$\\&~^_]", " ", t)
    return len(re.findall(r"[\wÀ-ÿ]+", t))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pasta")
    ap.add_argument("--skill", choices=["formata", "refaz", "cria"], required=True)
    ap.add_argument("--sem-pdf", action="store_true", help="a pessoa pediu só o .tex")
    a = ap.parse_args()
    pasta = Path(a.pasta)
    itens = []  # (status, texto)
    ok = lambda t: itens.append(("OK", t))  # noqa: E731
    aviso = lambda t: itens.append(("AVISO", t))  # noqa: E731
    falha = lambda t: itens.append(("FALHA", t))  # noqa: E731

    main_tex = pasta / "main.tex"
    if not main_tex.exists():
        print(f"FALHA: {main_tex} não existe")
        sys.exit(1)
    tex = sem_comentarios(main_tex.read_text(encoding="utf-8"))

    # Forma
    (ok if re.search(r"\\documentclass(\[[^\]]*\])?\{insperai\}", tex) else falha)("Usa a classe insperai.cls")
    (falha if "\\tableofcontents" in tex else ok)("Sem sumário")
    autor = re.search(r"\\author\{(.*?)\}\s*\n", tex, re.S)
    ia = NOMES_IA.findall(autor.group(1)) if autor else []
    (falha if ia else ok)("Nenhuma IA na lista de autores" + (f" (encontrado: {', '.join(ia)})" if ia else ""))
    for arq in ("insperai.cls", "figuras/logo-insperai.png"):
        (ok if (pasta / arq).exists() else falha)(f"{arq} está na pasta")
    caps = re.findall(r"\\caption\{", tex)
    (aviso if caps else ok)("Legendas pelo \\legenda{Título}{Descrição}" + (f" ({len(caps)} \\caption direto)" if caps else ""))
    specs = re.findall(r"\\begin\{tabular[x*]?\}(?:\{[^}]*\})?\{([^}]*)\}", tex)
    (falha if any("|" in s for s in specs) else ok)("Tabelas sem linhas verticais")
    if specs and "\\toprule" not in tex:
        aviso("Há tabular sem \\toprule (use booktabs)")

    # Seções
    titulos = [(m.start(), m.group(1), m.group(2)) for m in re.finditer(r"\\(section|subsection|secaofaltando)\*?\{([^}]*)\}", tex)]
    paragrafos = [(m.start(), m.group(1)) for m in re.finditer(r"\\paragraph\{([^}]*)\}", tex)]
    pos, usadas = [], {}
    exatos = {"Introdução": ("introdução", "introduction"), "Trabalhos relacionados": ("trabalhos relacionados", "related work"),
              "Método": ("método", "métodos", "metodologia", "method", "methods"), "Resultados": ("resultados", "results"), "Limitações": ("limitações", "limitations"),
              "Código e dados": ("código e dados", "code and data"), "Conclusão": ("conclusão", "conclusões", "conclusion", "conclusions")}
    leve = aviso if a.skill == "formata" else falha
    for nome, padrao in OBRIGATORIAS:
        sec = next(((p, cmd, t) for p, cmd, t in titulos if cmd != "secaofaltando" and re.search(padrao, t, re.I)), None)
        marcada = next((p for p, cmd, t in titulos if cmd == "secaofaltando" and re.search(padrao, t, re.I)), None)
        par = next((p for p, t in paragrafos if re.search(padrao, t, re.I)), None)
        if sec:
            titulo = re.sub(r"\s+", " ", sec[2]).strip()
            usadas.setdefault(sec[0], []).append(nome)
            if titulo.lower() in exatos[nome]:
                ok(f"Seção \"{nome}\" existe")
            else:
                leve(f"\"{nome}\" está na seção \"{titulo}\" (título diferente do padrão)")
            pos.append((sec[0], nome))
        elif marcada is not None:
            aviso(f"Seção \"{nome}\" inserida com o marcador \\secaofaltando")
            pos.append((marcada, nome))
        elif par is not None:
            leve(f"\"{nome}\" existe só como parágrafo (\\paragraph), não como seção")
            pos.append((par, nome))
        else:
            leve(f"Falta a seção obrigatória \"{nome}\"")
    for p_, nomes in usadas.items():
        if len(nomes) > 1:
            leve("Seções obrigatórias combinadas numa só: " + " + ".join(nomes) + " (o padrão pede uma seção para cada)")
    ordem = [n for _, n in sorted(pos)]
    esperada = [n for n, _ in OBRIGATORIAS if n in ordem]
    if ordem == esperada:
        ok("Seções obrigatórias na ordem do padrão")
    else:
        (aviso if a.skill == "formata" else falha)("Ordem das seções difere do padrão: " + " → ".join(ordem)
                                                  + (" (a formata mantém a ordem original porque o texto cita as seções pelo número)" if a.skill == "formata" else ""))

    cod = re.search(r"\\section\*?\{(C[óo]digo e dados|Code and Data)\}(.*?)(?=\\section|\\bibliography|\\end\{document\})", tex, re.S | re.I)
    if cod:
        pars = [p for p in re.split(r"\n\s*\n", cod.group(2).strip()) if p.strip()]
        (ok if len(pars) == 1 else (aviso if a.skill == "formata" else falha))(f"\"Código e dados\" tem {len(pars)} parágrafo(s) (o padrão pede 1)")

    resumo = re.search(r"\\resumo\{(.*?)\}\s*\n\s*\n?\\begin\{document\}", tex, re.S) or re.search(r"\\resumo\{(.*)", tex, re.S)
    if resumo:
        n = palavras(resumo.group(1)[:6000].split("\\begin{document}")[0])
        (ok if 150 <= n <= 250 else aviso)(f"Resumo com {n} palavras (recomendado: 150 a 250, flexível)")
    else:
        falha("Sem resumo (\\resumo{...})")

    # Referências
    cites = set()
    for m in re.finditer(r"\\(?:cite[tp]?|citeauthor|citeyear|nocite)\*?(?:\[[^\]]*\])*\{([^}]*)\}", tex):
        cites.update(k.strip() for k in m.group(1).split(",") if k.strip() and k.strip() != "*")
    bib = (pasta / "refs.bib").read_text(encoding="utf-8") if (pasta / "refs.bib").exists() else ""
    faltam = sorted(cites - chaves_bib(bib))
    (falha if faltam else ok)("Toda citação existe no refs.bib" + (f" (faltam: {', '.join(faltam)})" if faltam else ""))
    nver = len(re.findall(r"\[VERIFICAR\]", bib))
    (aviso if nver else ok)(f"{nver} referência(s) marcada(s) [VERIFICAR]" if nver else "Nenhuma referência [VERIFICAR]")
    estilos = {"numerico" in (re.search(r"\\documentclass\[([^\]]*)\]", tex) or [None, ""])[1]}
    if len(estilos) == 1:
        ok("Estilo de citação único (definido pela classe)")

    # Entrega
    pdf = pasta / "main.pdf"
    if not a.sem_pdf:
        (ok if pdf.exists() and pdf.stat().st_mtime >= main_tex.stat().st_mtime - 1 else falha)("main.pdf existe e está atualizado")
        log = pasta / "main.log"
        if log.exists():
            faltando = set(re.findall(r"Missing character: There is no (\S+)", log.read_text(errors="replace")))
            (aviso if faltando else ok)("Todos os caracteres têm glifo na fonte" + (f" (sem glifo: {' '.join(sorted(faltando))})" if faltando else ""))

    print(f"# Checklist automático ({a.skill}-paper): {pasta}\n")
    for st, t in itens:
        print(f"- {st}: {t}")
    nf = sum(st == "FALHA" for st, _ in itens)
    na = sum(st == "AVISO" for st, _ in itens)
    print(f"\nRESULTADO: {nf} falha(s), {na} aviso(s). Os itens sem (auto) em checklist.md são conferidos pela skill.")
    sys.exit(1 if nf else 0)


if __name__ == "__main__":
    main()
