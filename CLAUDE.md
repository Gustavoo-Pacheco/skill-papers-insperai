# skill-papers-insperai

## Objetivo
Três skills do Claude que padronizam os papers do **Insper AI**, o grupo estudantil e laboratório de IA do Insper, todas sobre um único "padrão do lab": estrutura de seções, guia de estilo, template LaTeX, checklist e scripts. Os usuários são membros técnicos (sabem git e LaTeX), no Claude Code e no app do Claude.

## As três skills

| Skill | Recebe | Entrega | Limite |
|---|---|---|---|
| `formata-paper` | Paper (.tex, PDF, .docx, Docs, Markdown) | O mesmo paper no padrão | Só forma. Texto idêntico, conferido por `verificar_texto.py`. Mantém a ordem e a numeração originais |
| `refaz-paper` | Paper + repositório | Paper reescrito com o repo como fonte | Pergunta a cada conflito. Reorganiza na ordem do padrão, pode gerar figuras. ±10% das palavras |
| `cria-paper` | Ideia, notas, resultados e/ou repo, sem paper | Paper novo | Entrevista antes de escrever, não inventa resultados, tamanho pelo conteúdo |

As três perguntam o formato (padrão: LaTeX e PDF), o idioma (padrão: o da entrada) e o estilo de citação (padrão: autor-ano).

## Estrutura

```
padrao/            FONTE ÚNICA: estrutura.md, guia-de-estilo.md, checklist.md, ler-repositorio.md
  template/        insperai.cls, .bst em PT, insperai.mplstyle, main.tex, logo
  scripts/         extrair_entrada → montar_latex → completar_bib → compilar.sh → verificar_texto / verificar_checklist;
                   contar_palavras, inventario_repo, recortar_figuras
skills/<nome>/     SKILL.md (+ referencias/) e padrao/ GERADO pelo build: nunca edite as cópias
build.py           copia padrao/ para as skills e gera dist/*.zip; --check verifica as cópias
tests/             casos.md, prompts/ e rodar_teste_skill.sh (skills sem interface), fixtures/, verificar_cobertura.py;
                   tests/privado/ (fora do git) guarda o paper e o repo do Wakely; tests/saidas/ (fora do git)
docs/              contexto.md (entrevista e decisões) e referencias.md (análise dos 39 papers)
.claude-plugin/    o repo é ao mesmo tempo plugin e marketplace do Claude Code
```

## Decisões principais (detalhes e motivos em [docs/contexto.md](docs/contexto.md))
- **Só relatório técnico.** A4, duas colunas, Charter 10 pt, sem sumário, legenda "Figura N | **Título.** Descrição".
- **Capa:** logo + "Insper AI" e data; título, autores e resumo no estilo de *Attention Is All You Need*: título centralizado entre filetes (4 pt e 1 pt), autores em negrito em blocos centralizados (`\and`; `\AND` quebra a linha), afiliação e e-mail do lab (contato@insperai.com.br) abaixo, e o resumo com título centralizado e texto recuado (80% da largura). Sem palavras-chave e sem link do repo.
- **Cores:** links em Azul Cobalto `#0058B8`, títulos pretos; gráficos com a paleta validada para daltonismo (`#0058B8`, `#D86FE0`, `#1E2A44`, `#A3A8B0`).
- **Seções:** Introdução (termina num parágrafo de contribuições) → Trabalhos relacionados → Método → Resultados → Limitações → Código e dados (um parágrafo) → Conclusão.
- **Redação:** impessoal; resultados como na fonte; resumo recomendado de 150 a 250 palavras; termos em inglês em itálico.
- **Referências:** chaves do autor mantidas; `completar_bib.py` confirma por arXiv, Crossref/DataCite, OpenAlex e Semantic Scholar; o resto fica `[VERIFICAR]`.
- **IA:** nunca é autora (a skill remove e avisa) e o uso nunca é declarado.
- **Compilação:** Tectonic, sempre tentando instalar; sem ele, código 2 e o .tex pronto para o Overleaf.
- **Distribuição:** marketplace de plugin (Claude Code) e .zip nas Releases (app). As cópias geradas entram no git.

## Convenções
- Documentação, SKILL.md e guias em **português**. Os papers saem no idioma escolhido.
- Edite o padrão só em `padrao/` e rode `python3 build.py` (e `--check`) antes de commitar.
- Versões x.y.z, com `CHANGELOG.md` e uma Release com `dist/*.zip`.
- Repo público, MIT; o logo não está coberto. **Nada de `tests/privado/` nem `tests/saidas/` vai para o git.**
- Não faça commit nem push sem o mantenedor pedir.

## Como testar
Veja [tests/casos.md](tests/casos.md): scripts deterministas no Wakely e no caso sintético autor-ia, e as três skills rodando sem interface com `tests/rodar_teste_skill.sh`.

## Em aberto
- Tectonic no sandbox do app ainda não foi testado (sem ele, a skill entrega o .tex para o Overleaf).
- Instalação real do plugin pelo marketplace depende do push.
