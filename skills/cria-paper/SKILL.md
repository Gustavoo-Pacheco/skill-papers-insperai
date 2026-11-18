---
name: cria-paper
description: Escreve um paper novo, do zero, já no padrão do Insper AI (relatório técnico em A4, duas colunas, capa com o logo), a partir de qualquer combinação de ideia em texto, notas ou rascunhos, resultados (CSV, tabelas, figuras, logs) e repositório de código. Antes de escrever, entrevista o usuário para cobrir o que falta e nunca inventa resultados. O tamanho sai do conteúdo. Use quando ainda não existe paper, com pedidos como "cria um paper sobre o projeto", "escreve o relatório técnico a partir do repo" ou "write a paper for Insper AI". Se já existe um paper, use refaz-paper (reescrever) ou formata-paper (só a forma).
---

# cria-paper

Escreve um paper novo no padrão do Insper AI. **Pergunta antes de escrever e não inventa resultados:** todo número do paper tem uma origem (arquivo do repo, material recebido ou resposta da pessoa).

O padrão está na pasta `padrao/` desta skill. Leia `estrutura.md`, `guia-de-estilo.md` e `ler-repositorio.md`; o roteiro da entrevista está em `referencias/entrevista.md`. Abaixo, `S=<pasta da skill>/padrao/scripts` e `T=<pasta da skill>/padrao/template`.

## Entrada

Qualquer combinação de: uma ideia em texto; notas ou rascunhos; resultados (CSV, tabelas, figuras, logs); um repositório (pasta local, URL pública, `.zip` ou, se privado, o conector do GitHub). Se a pessoa já tem um paper, sugira `refaz-paper` ou `formata-paper`.

## Passos

**0. Ambiente.** `pymupdf` e `matplotlib` instalados; pasta `<nome-do-projeto>-insperai/` com a cópia de `$T` e `figuras/logo-insperai.png`.

**1. Perguntar** (ferramenta interativa no Claude Code; chat no app), numa rodada:
- formato de saída (padrão: **os dois**);
- idioma (padrão: o do repositório ou do material);
- estilo de citação (padrão: **autor-ano**).

**2. Ler todo o material.**
- Repositório: `python3 $S/inventario_repo.py <repo> --saida <pasta>/trabalho/inventario.json`, depois README, docs, saídas dos notebooks, CSV/JSON e configs, conforme `ler-repositorio.md`.
- Anote cada resultado com a origem exata em `trabalho/fontes.md`.
- Se o repo trouxer um PDF de paper ou relatório, avise: talvez seja caso de `refaz-paper`.

**3. Mapear** em `trabalho/mapa.md` o que cada seção obrigatória de `estrutura.md` já tem e o que falta, com a fonte de cada item.

**4. Entrevistar** sobre as lacunas antes de escrever qualquer seção, seguindo `referencias/entrevista.md`:
- rodadas de até 4 perguntas, com opções;
- mostre o que encontrou e peça confirmação, em vez de perguntar do zero;
- registre perguntas e respostas em `trabalho/entrevista.md`.

**5. Escrever** no `main.tex`, na ordem de `estrutura.md` e com as regras de `guia-de-estilo.md`:
- impessoal; contribuições num parágrafo no fim da introdução; resumo de 150 a 250 palavras;
- números exatamente como na fonte; "Código e dados" em um parágrafo, com URL, commit, dados e licença.
- **O tamanho é o que o conteúdo pede.** Não encha para atingir páginas, não corte o que importa.
- Figuras do dado bruto com `plt.style.use("insperai.mplstyle")`, salvas em PDF em `figuras/`; legendas com `\legenda{Título.}{Descrição}`; tabelas em booktabs, com `\linhadestaque` no método proposto.

**6. Referências.** Só referências reais:
- as que a pessoa deu, as citadas no repositório (README, docs, comentários) ou as que você propõe e `completar_bib.py` confirma;
- `python3 $S/completar_bib.py refs.bib` completa e marca `[VERIFICAR]` o que não achar;
- chaves no formato `sobrenome2024palavra`.

**7. Compilar e verificar.**
- `bash $S/compilar.sh <pasta>`; com código 2, avise que o PDF não existe e entregue o .tex para o Overleaf.
- `python3 $S/verificar_checklist.py <pasta> --skill cria` e os itens sem (auto) de `checklist.md`.
- Confira que todo número do texto está em `trabalho/fontes.md` ou nas respostas da entrevista.
- Olhe o PDF renderizado.

**8. Entregar** a pasta e um resumo com:
- a estrutura;
- a origem de cada resultado;
- o que ficou de fora por falta de dado;
- os avisos e as referências `[VERIFICAR]`.
