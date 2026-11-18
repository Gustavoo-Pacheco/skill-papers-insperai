---
name: refaz-paper
description: Reescreve um paper existente no padrão do Insper AI usando o repositório de código do projeto como fonte do método, dos experimentos e dos resultados. Pergunta ao usuário a cada conflito entre o paper e o código, reorganiza as seções na ordem do lab, pode gerar visualizações novas e mantém o tamanho do original (±10% de palavras). Use quando o usuário tem o paper (.tex, PDF, .docx, Google Docs ou Markdown) e o repositório (pasta local, GitHub ou .zip), com pedidos como "refaz o paper com base no repo", "reescreve no padrão do lab usando o código" ou "rewrite this paper from the repo". Se só a formatação deve mudar, use formata-paper. Se ainda não existe paper, use cria-paper.
---

# refaz-paper

Recebe um paper e o repositório dele e devolve o paper reescrito no padrão do Insper AI. **O repositório é a fonte da verdade, mas nenhum conflito é resolvido sem perguntar.**

O padrão está na pasta `padrao/` desta skill. Leia `estrutura.md`, `guia-de-estilo.md` e `ler-repositorio.md` antes de começar. Caminhos relativos à pasta da skill; abaixo, `S=<pasta da skill>/padrao/scripts` e `T=<pasta da skill>/padrao/template`.

## O que pode e o que não pode

| Pode | Não pode |
|---|---|
| Reescrever o texto no estilo de `guia-de-estilo.md` (impessoal, contribuições em um parágrafo, resumo de 150 a 250 palavras) | Resolver sozinho uma divergência entre o paper e o repo |
| Reorganizar seções na ordem de `estrutura.md` e criar as obrigatórias que faltam, com conteúdo do paper e do repo | Inventar um resultado, uma referência ou um detalhe de método |
| Gerar figuras novas a partir dos dados do repo, com `insperai.mplstyle` | Fugir de ±10% das palavras do corpo do original |
| Reaproveitar figuras do original (`recortar_figuras.py`) | Declarar uso de IA ou pôr uma IA como autora |

## Passos

**0. Ambiente** como na formata: `pymupdf` instalado e uma pasta `<nome-do-paper>-insperai/` com a cópia de `$T` (`insperai.cls`, os dois `.bst`, `insperai.mplstyle`, `main.tex`, `refs.bib`) e `figuras/logo-insperai.png`.

**1. Perguntar** (ferramenta interativa no Claude Code; chat no app), numa rodada:
- formato de saída (LaTeX, PDF ou os dois; padrão: **os dois**);
- idioma (padrão: o do paper ou do repositório);
- estilo de citação (padrão: **autor-ano**);
- onde está o repositório, se não veio. Pasta local, URL pública ou `.zip`. Repositório privado: use o conector do GitHub se houver; senão, peça o `.zip`.

**2. Ler o paper.** `python3 $S/extrair_entrada.py <paper> <pasta>/trabalho/paper.json` e `python3 $S/contar_palavras.py <paper>` (meta de tamanho: esse número ±10%). Liste em `trabalho/afirmacoes.md` cada afirmação verificável: números, configurações, datasets, hiperparâmetros, com a seção de origem.

**3. Ler o repositório.** `python3 $S/inventario_repo.py <repo> --saida <pasta>/trabalho/inventario.json` e siga `ler-repositorio.md`: README, docs, saídas dos notebooks, CSV/JSON, configs. Para cada resultado, anote a origem exata (arquivo e célula ou linha) em `trabalho/fontes.md`. Não reexecute notebooks sem pedir.

**4. Comparar** cada afirmação com o repo e marcar: confirmada, divergente ou ausente do repo.
- **Divergente:** pergunte qual versão vale, mostrando os dois valores e onde cada um está. Até 4 por rodada. Registre pergunta e resposta em `trabalho/conflitos.md`.
- **Ausente do repo:** fica com o paper como fonte (prioridade 4 de `ler-repositorio.md`) e entra na lista do resumo.
- Nada que o repo tenha e o paper não tenha entra sem a pessoa saber: liste as novidades e pergunte se entram.

**5. Planejar e escrever** no `main.tex`, na ordem de `estrutura.md`:
- Introdução terminando num parágrafo de contribuições; Trabalhos relacionados; Método; Resultados; Limitações; Código e dados (um parágrafo, modelo em `estrutura.md`); Conclusão.
- Números como estão na fonte; vírgula decimal em português; termos em inglês sem tradução consagrada em itálico; siglas por extenso na primeira vez.
- Figuras: reaproveite as do original com `python3 $S/recortar_figuras.py trabalho/paper.json <paper.pdf> figuras` ou gere novas do dado bruto do repo com `plt.style.use("insperai.mplstyle")`, salvas em PDF. Legenda com `\legenda{Título.}{Descrição}`; tabelas em booktabs, com `\linhadestaque` no método proposto.

**6. Tamanho.** `python3 $S/contar_palavras.py <paper> <pasta>/main.tex` precisa dar DENTRO DA FAIXA. Ajuste o texto, não o conteúdo.

**7. Referências.** Mantenha as do original: `python3 $S/completar_bib.py --de-texto trabalho/paper.json --saida refs.bib` (ou `completar_bib.py refs.bib` se veio um `.bib`). Referência nova só se a pessoa der ou se `completar_bib.py` a confirmar.

**8. Compilar e verificar.** `bash $S/compilar.sh <pasta>` (código 2: avise que o PDF não existe e entregue o .tex para o Overleaf); `python3 $S/verificar_checklist.py <pasta> --skill refaz`, mais os itens sem (auto) de `checklist.md`; olhe o PDF renderizado.

**9. Entregar** a pasta (sem `trabalho/`, a menos que a pessoa queira) e um resumo:
- o que mudou: estrutura, seções novas, figuras novas;
- os conflitos e como foram resolvidos;
- os números que vieram só do paper;
- o tamanho (palavras antes e depois);
- os avisos e as referências `[VERIFICAR]`.
