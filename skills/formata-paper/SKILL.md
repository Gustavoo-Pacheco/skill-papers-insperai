---
name: formata-paper
description: Ajusta um paper existente ao padrão do Insper AI (relatório técnico em A4, duas colunas, fonte Charter, capa com o logo, legendas e citações padronizadas) sem mudar uma palavra do texto. Use quando o usuário já tem o paper pronto (.tex/Overleaf, PDF, .docx, Google Docs ou Markdown) e quer só a forma do lab, com pedidos como "formata no padrão do Insper AI", "coloca no template do lab" ou "format this paper for Insper AI". Não use para reescrever com base no código (use refaz-paper) nem para escrever um paper do zero (use cria-paper).
---

# formata-paper

Recebe um paper pronto e devolve o mesmo paper no padrão do Insper AI. **Só muda a forma: o texto sai palavra por palavra igual ao da entrada**, e um script confere isso antes da entrega.

O padrão está na pasta `padrao/` desta skill: `estrutura.md`, `guia-de-estilo.md`, `checklist.md`, `template/` e `scripts/`. Leia `estrutura.md` e `guia-de-estilo.md` antes de começar. Os caminhos abaixo são relativos à pasta da skill (no Claude Code, é o "Base directory for this skill"). Abaixo, `S=<pasta da skill>/padrao/scripts`.

## O que pode e o que não pode

| Pode | Não pode |
|---|---|
| Aplicar a classe `insperai.cls`: capa, layout, fonte, cores, legendas | Mudar, corrigir, traduzir, resumir ou acrescentar texto |
| Trocar o estilo de citação ([3] ↔ autor-ano) e completar o `.bib` | Reordenar seções: o texto cita "seção 5" e "figura 2", e os números precisam continuar valendo |
| Promover um trecho existente a seção ("Limitações." vira subseção), sem mudar o texto | Escrever uma seção obrigatória que falta |
| Recompor uma tabela em booktabs, com as mesmas células | Mudar números, resultados ou figuras |
| Remover uma IA da lista de autores (regra do lab) e avisar | Mexer no tamanho por conta própria |

## Passos

**0. Ambiente.** Confira `python3 -c "import pymupdf"`. Se faltar: `python3 -m pip install pymupdf` (num venv, se o sistema pedir). Crie uma pasta de trabalho `<nome-do-paper>-insperai/` ao lado da entrada (no app, em `/mnt/user-data/outputs/` se existir).

**1. Perguntar** (ferramenta interativa, como AskUserQuestion, no Claude Code; no chat, no app), numa rodada só:
- Formato de saída: LaTeX, PDF ou os dois. Sem resposta: **os dois**.
- Estilo de citação: autor-ano ou numérico. Sem resposta: **autor-ano**.
- O idioma é o do paper. A formata não traduz.

**2. Ler a entrada.**
- **PDF, .docx, Markdown** (Google Docs: peça o export em .docx): `python3 $S/extrair_entrada.py <entrada> <pasta>/entrada.json`. Leia os avisos impressos.
- **.tex/Overleaf:** não passe pelo JSON. Copie o projeto para a pasta, troque `\documentclass` por `insperai` (opções `english` e `numerico` quando for o caso), passe título, autores e resumo para os comandos da capa (`\title`, `\subtitulo`, `\author{A \and B}`, `\data`, `\resumo`), troque `\caption{T. D}` por `\legenda{T.}{D}`, remova `\bibliographystyle`, `\tableofcontents` e pacotes que conflitem com a classe, e copie `template/` (classe, `.bst` e `figuras/logo-insperai.png`). Pule para o passo 5.

**3. Conferir a extração** antes de montar. Renderize a primeira página e as páginas com figuras (`pymupdf`: `page.get_pixmap(dpi=60).save(...)`) e confira no JSON:
- `meta`: título, subtítulo, autores (os com `"ia": true` saem), data;
- seções e níveis, figuras e tabelas (página e `bbox`), frações marcadas nos avisos;
- se algo estiver errado, corrija **a estrutura** no JSON (tipo de bloco, bbox, ordem), **nunca o texto**.

**4. Perguntar o que o padrão não resolve sozinho** (só se aparecer), numa rodada:
- **Seção obrigatória faltando** (lista em `estrutura.md`). Opções: (a) a pessoa escreve o texto e você insere exatamente o que ela escreveu; (b) inserir `\secaofaltando{Nome}`, uma caixa visível no PDF; (c) não inserir e registrar no resumo; (d) se o conteúdo já existe dentro de outra seção (por exemplo, um parágrafo "Limitações." na discussão), promovê-lo a `\subsection*{Limitações}` sem mudar o texto. Subseção sem número para não renumerar as seções que o texto cita.
- **Linhas da capa sem lugar no padrão** (por exemplo, link do repositório ou "Entrega final"): manter como nota da capa (`\notacapa`), mover para "Código e dados" (se existir) ou remover.
- **Tabelas de PDF:** entram como recorte vetorial do original (texto idêntico). Pergunte se quer recompostas em booktabs com `\linhadestaque`. Se sim, recomponha a partir de `linhas` no JSON, célula por célula.

**5. Montar.** `python3 $S/montar_latex.py <pasta>/entrada.json <pasta> --original <entrada.pdf> --citacao autorano|numerico` (sem `--original` para .docx e Markdown; insira as imagens do .docx a partir de `word/media/`). O script:
- copia a classe, os estilos de bibliografia e o logo;
- recorta figuras e tabelas;
- converte as citações [n] em `\citep`/`\citet`;
- monta `refs.bib` com `completar_bib.py` (arXiv, Crossref e DataCite, OpenAlex, Semantic Scholar; o que não for confirmado fica `[VERIFICAR]`);
- grava `avisos-montagem.json`.

Depois aplique as respostas do passo 4 no `main.tex`. Para um `.bib` que veio com o paper: `python3 $S/completar_bib.py refs.bib`, sem mudar as chaves.

**6. Compilar.** `bash $S/compilar.sh <pasta>`. Se sair com código 2, o PDF **não** foi gerado: repasse a mensagem (o .tex está pronto para o Overleaf) e não diga que existe PDF. Avisos de glifo faltando ou citação indefinida precisam ser resolvidos.

**7. Verificar** (obrigatório):
- `python3 $S/verificar_texto.py <entrada.pdf ou entrada.json> <pasta>/main.pdf --relatorio <pasta>/verificacao-texto.md`. Se uma IA saiu dos autores, acrescente `--ignorar <cada palavra do nome>`. Precisa terminar em **TEXTO IDÊNTICO**. Cada diferença é um erro de montagem: corrija a estrutura ou o LaTeX e rode de novo. Se sobrar alguma que você não consiga resolver, ela vai para o resumo, com o trecho.
- `python3 $S/verificar_checklist.py <pasta> --skill formata` e os itens sem (auto) de `checklist.md`.
- Olhe o PDF: capa, uma página com figura e as referências (renderize em PNG).

**8. Entregar** a pasta com `main.tex`, `refs.bib`, `figuras/` e `main.pdf` (no formato pedido; tire os arquivos de trabalho `entrada.json` e `avisos-montagem.json`, ou deixe-os se a pessoa quiser revisar). Mande um resumo curto:
- o que mudou na forma;
- os avisos (IA removida, seções faltando ou combinadas, ordem diferente do padrão, linhas da capa);
- as referências `[VERIFICAR]`;
- o resultado da verificação de texto.
