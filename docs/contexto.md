# Contexto: entrevista de definição do projeto

Registro completo da entrevista que definiu o projeto, feita em **18/11/2026** com quem mantém o repositório. O `CLAUDE.md` resume este documento.

## 1. Ponto de partida

O **Insper AI** é um grupo estudantil do Insper que funciona como um laboratório de inteligência artificial. O objetivo é criar três skills do Claude que padronizem os papers do grupo, todas sobre o mesmo padrão (estrutura de seções, guia de estilo, template e checklist):

1. **Formata**: recebe um paper existente e o ajusta ao padrão, sem inventar conteúdo.
2. **Refaz**: recebe um paper e o repositório de código dele, e reescreve o paper no padrão usando o repositório como fonte.
3. **Cria**: escreve um paper novo, do zero, já no padrão.

Regras da entrevista: rodadas curtas, nada assumido sem confirmação, e opções com prós e contras quando a resposta não estava clara. Por pedido do usuário, a partir da segunda rodada as perguntas foram feitas com a ferramenta interativa do chat.

## 2. Rodadas

### Rodada 1: ambiente, formato, padrão e idioma

| Pergunta | Resposta |
|---|---|
| Onde as skills rodam? | **Nos dois**: Claude Code e app do Claude |
| Em que formato os papers saem? | **LaTeX e PDF.** A skill pergunta qual a pessoa quer e, sem resposta, gera os dois |
| O padrão do lab já existe? | **Não. Criar do zero** |
| Em que idioma? | **A skill pergunta a cada uso** |

O usuário pediu também que eu criasse o repositório público no GitHub dele.

### Rodada 2: repositório, idioma padrão, tipos e usuários

| Pergunta | Resposta |
|---|---|
| Onde está o repositório? | Não existia. "Crie ele" |
| Idioma quando a pessoa não responde | **O idioma do repositório ou do paper** |
| Tipos de paper | Relatório técnico e relatório interno. Conferência e arXiv ficaram de fora. (Na rodada 7, o interno também saiu.) |
| Quem usa | **Membros técnicos**, que sabem git e LaTeX |

### Rodada 3: nome, pasta, entrada da cria e falta de informação

| Pergunta | Resposta |
|---|---|
| Nome do repositório | **`skill-papers-insperai`**, público, em `Gustavoo-Pacheco` |
| Pasta local | **`~/Documents/InsperAI/Projetos/skill-papers-insperai`** |
| De onde a cria parte | **Qualquer combinação** de ideia, notas, resultados e repositório |
| Quando falta informação | **Perguntar antes de escrever** (descartados: marcar TODOs, esqueleto com lista) |

Daí veio o limite entre as skills: **a refaz parte de um paper que já existe, e a cria parte de um material que ainda não é paper.**

### Rodada 4: entrada, limites e citação

| Pergunta | Resposta |
|---|---|
| Formatos de entrada da formata e da refaz | **Todos**: .tex/Overleaf, PDF, .docx, Google Docs/Markdown |
| Até onde a formata mexe | **Só forma.** O texto fica palavra por palavra |
| Até onde a refaz mexe | **Pergunta a cada conflito** entre paper e repo, reorganiza seções e gera visualizações novas |
| Estilo de citação | Em vez de responder, o usuário pediu uma pesquisa: reunir os papers mais relevantes de IA e deep learning dos últimos dez anos, levantar as escolhas principais em cada dimensão, citando paper e laboratório, e juntar com a identidade visual do Insper AI. Veja a seção 3 |

### Rodada 5: escolhas de estilo, depois da pesquisa

| Pergunta | Resposta | Base apresentada |
|---|---|---|
| Citação | **A skill oferece numérico ou autor-ano. Sem resposta, usa autor-ano** | 14 dos 17 relatórios técnicos usam autor-ano |
| Layout | **Duas colunas, A4** | Gemma, Gemma 3, OLMo |
| Fonte | **Charter** | Template da DeepMind |
| Identidade visual | **Capa e cores**: logo em degradê e data na capa; links, títulos e gráficos nas cores do logo | Gemini, Gemma, Qwen, Llama 3 |

### Rodada 6: estrutura

| Pergunta | Resposta |
|---|---|
| Trabalhos relacionados | **Seção própria, logo após a introdução** |
| Seções obrigatórias além de introdução, método, resultados e conclusão | **Limitações** e **Código e dados**. Código e dados é um parágrafo sobre onde está o código e o que foi feito, baseado nos papers de referência. Contribuições e Ética ficaram opcionais |
| Relatório interno | O usuário pediu que a pergunta fosse refeita explicando os dois tipos |
| Referências | **O .bib é completado e corrigido pela skill** (arXiv, DOI, Semantic Scholar) |

### Rodada 7: interno, empacotamento, distribuição e ordem

| Pergunta | Resposta |
|---|---|
| Relatório interno | **Sai do escopo.** O padrão cobre só o relatório técnico |
| Como as skills compartilham o padrão | **Fonte única + build**: `padrao/` na raiz, copiado para cada skill por `build.py` |
| Distribuição | **Plugin + Releases**: marketplace de plugin para o Claude Code e .zip nas Releases para o app |
| Ordem de construção | **Padrão → formata → refaz → cria** |

Junto com essas respostas veio uma regra de **tamanho**: a cria não tem tamanho fixo e avalia pelo conteúdo; a refaz mantém o tamanho do original; a formata não mexe.

### Rodada 8: resultados, compilação, testes e nomes

| Pergunta | Resposta |
|---|---|
| Onde estão os resultados | CSV/JSON no repo, notebooks com saída, logs e checkpoints, e **os gráficos e tabelas do próprio paper** |
| Compilação | **Tectonic, sempre tentando instalar.** Se falhar, entrega o .tex para o Overleaf e avisa |
| Material de teste | **Os papers dos grupos baixados recentemente** (Downloads, 17/11/2026) |
| Nomes | **`formata-paper`, `refaz-paper`, `cria-paper`** |

### Rodada 9: privacidade, IA, legenda e idioma da documentação

| Pergunta | Resposta |
|---|---|
| Onde ficam os papers de teste, que são de outros alunos, num repo público | **Pasta local fora do git** (`tests/privado/`) |
| Regra sobre IA | **IA não é autora e o uso não é declarado** |
| Legenda | **"Figura 3 \| Título."**, no estilo da DeepMind |
| Idioma de SKILL.md e docs | **Português** |

### Fechamento

| Pergunta | Resposta |
|---|---|
| Licença do repo público | **MIT**, com o logo do Insper AI fora da licença |
| Paper de entrada que lista uma IA como autora | A formata e a refaz **removem e avisam** |
| Propostas: sem sumário; o mantenedor como dono do padrão, com versões x.y.z, CHANGELOG e Releases; saída em `<nome-do-paper>-insperai/` | **Confirmadas**, junto com o resumo e a estrutura de pastas |

## 3. Pesquisa de referência

**39 papers** de 2015 a 2025 (17 relatórios técnicos e 22 de conferência, pré-print ou periódico), de Google, DeepMind, OpenAI, Meta/FAIR, Anthropic, Microsoft, DeepSeek, Alibaba Qwen, Mistral, AI2, Stanford, Berkeley, CMU/Princeton e LMU/Runway. A tabela completa e a análise por dimensão estão em [`referencias.md`](referencias.md). O que mais pesou nas decisões:

- **Citação:** 14 dos 17 relatórios usam autor-ano. O numérico domina em visão computacional.
- **Layout:** 13 dos 17 relatórios usam uma coluna. Duas colunas aparecem em relatórios curtos (Gemma, OLMo, LLaMA), o tamanho dos papers dos grupos (de 5 a 17 páginas).
- **Capa com marca:** todos os 11 relatórios que a usam são de 2022 em diante (Gemini, Gemma, Llama 3, Qwen, DeepSeek, OLMo, Mistral).
- **Sumário:** só em documentos com mais de 30 páginas.
- **Código e dados:** os padrões de frase vieram de DDPM, CLIP, LoRA, Mamba, OLMo, Mistral e DeepSeek (veja `padrao/estrutura.md`).

**Identidade visual do Insper AI**, tirada de `InsperAI/Comunicação/Logos` e do site institucional:
- **Logo:** grafo formando "AI", em degradê de magenta `#B128C0` para azul `#016FD0`, com o slogan "Deep Learning, Deep Thinking".
- **Variações do logo:** Azul Cobalto `#0058B8`, Roxo Coração `#7020A8`, Roxo Noturno `#683080`, Roxo Neural `#502870`, Lavanda e Branca.
- **Site:** violeta `#8B5CF6` → índigo `#6366F1` → azul `#3B82F6`, fonte Geist Sans.

## 4. Papers de teste

Três papers de grupos do projeto final de 2026-2, todos em português e A4, cada um com o repositório correspondente:

| Caso | Autores | Repositório | Observação |
|---|---|---|---|
| Semáforos inteligentes (5 p., LaTeX) | Grupo A | repositório do grupo | O próprio paper cita resultados que não puderam ser auditados no repo, um bom teste de conflito para a refaz |
| Wakely (17 p., LaTeX) | Grupo B | repositório do grupo | |
| Gestos ao volante (14 p., HTML → PDF) | Grupo C | repositório do grupo | Lista "Claude (Anthropic)" como autor, o que testa a regra de IA |

Não havia papers dos grupos de ECG e de voz em Downloads.

## 5. Ajuste feito no scaffold

Na estrutura aprovada, `ler-repositorio.md` ficava dentro de `skills/refaz-paper/referencias/`. Mas a cria-paper também lê repositórios e, no app, cada skill é um .zip separado que não enxerga os arquivos das outras. Por isso o arquivo foi para `padrao/ler-repositorio.md`, que o build copia para as três.

## 6. Perguntas em aberto: respostas (18/11/2026)

As 13 perguntas em aberto foram respondidas em quatro rodadas interativas:

| # | Pergunta | Resposta |
|---|---|---|
| 1 | formata, seção obrigatória faltando | **Perguntar à pessoa se insere e como**: texto dela, marcador `\secaofaltando`, não inserir (registrar) ou promover um trecho existente |
| 2 | refaz, tolerância do tamanho | **±10% das palavras do corpo** (`scripts/contar_palavras.py`) |
| 3 | Cores de links e títulos | **Links em Azul Cobalto `#0058B8`, títulos pretos.** A paleta de gráficos foi validada para daltonismo (abaixo) |
| 4 | Capa: palavras-chave e link do repo | **Nenhum dos dois.** A capa leva o **e-mail do lab, contato@insperai.com.br** |
| 5 | Chaves do .bib | **Manter as do autor.** Só quando a entrada não tem chaves (PDF, .docx), `sobrenome2024palavra` |
| 6 | Guia de redação | **Impessoal**; contribuições em **um parágrafo**; resultados **como estão na fonte**; resumo com **tamanho recomendado de 150 a 250 palavras, flexível**; termos em inglês sem tradução consagrada **em itálico** |
| 7 | Repos privados no app | **Conector do GitHub ou repo público, o que tiver** (ou o .zip) |
| 8 | Testes com .tex, .docx e Markdown | **Só o PDF do Wakely** como caso real. Markdown é testado com um caso sintético (`tests/fixtures/autor-ia.md`) |
| 9 | Critério de avaliação da cria | **Só cobertura** (`tests/verificar_cobertura.py`): números-chave do original presentes e nenhum número sem fonte |
| 10 | Declaração de IA em conferência que exija | **Nunca declara** |
| 11 | Grupos de ECG e voz | Fora: os testes usam só o Wakely |
| 12 | Quem responde às perguntas das skills nos testes | **O paper original** funciona como oráculo |
| 13 | Plugin | Validado com `claude plugin validate`; a instalação real depende do push |

**Paleta dos gráficos.** As cores do logo são de uma família só e, na simulação de daltonismo (Machado et al., 2009, distância ΔE em Lab), o menor contraste entre duas séries era 6,0 sob protanopia. A paleta escolhida, `#0058B8`, `#D86FE0`, `#1E2A44`, `#A3A8B0`, tem menor ΔE de 18,7. Mais de 4 séries usam também marcadores ou tipos de linha.

## 7. Implementação e testes (18/11/2026)

Decisões tomadas durante a implementação, que não mudam nada do que foi decidido acima:

- **A formata mantém a ordem e a numeração originais.** O Wakely cita "seção 5", "seção 3.1" e "figura 2" no texto, e a formata não pode mudar o texto. Reordenar quebraria as referências. A diferença em relação à ordem do padrão vira aviso no checklist e no resumo; quem quer a ordem do padrão usa a refaz. Promover "Limitações." a seção usa `\subsection*`, sem número, pelo mesmo motivo.
- **Figuras e tabelas de PDF entram como recortes vetoriais do original** (`montar_latex.py`, com o texto fora da região apagado). O texto delas fica idêntico. Recompor uma tabela em booktabs é opcional e a skill pergunta.
- **Linhas da capa original sem lugar no padrão** (como "Entrega final" e o link do repo no Wakely) ficam numa nota da capa (`\notacapa`) até a pessoa decidir.
- **Bibliografia em português:** `insperai-autorano-pt.bst` e `insperai-numerico-pt.bst`, derivados de plainnat/unsrtnat ("e", "Em", "páginas"). Referência sem ano sai como "s.d." (em inglês, "n.d.").
- **Fontes das referências:** arXiv, Crossref e DataCite (DOI), OpenAlex e Semantic Scholar. O DBLP foi descartado porque passou a bloquear scripts com verificação anti-robô. Um resultado só é aceito com título quase idêntico (similaridade ≥ 0,92) e ano a no máximo 1 de distância; entre candidatos, vale o do mesmo ano e a versão publicada.
- **Verificação de texto** (`verificar_texto.py`): compara as palavras do original com as do PDF gerado, ignorando só a forma (citações, hifenização, números de página, frações empilhadas, texto fixo da capa) e tratando blocos que só mudaram de lugar (figuras flutuantes) como movidos.
- **Scripts que as skills usam na hora** ficam em `padrao/scripts/` (verificar_texto, verificar_checklist, contar_palavras, inventario_repo, recortar_figuras). Em `tests/` ficam só os casos, os prompts e a avaliação da cria.

Resultado no Wakely (formata, pelos scripts): texto idêntico (8.341 palavras), 14 de 19 referências confirmadas e 5 marcadas `[VERIFICAR]` (páginas web, datasets e um workshop sem DOI), checklist sem falhas e com 7 avisos (ordem, seções combinadas e títulos diferentes do padrão), e tamanho igual ao original (+0,5%).

**Capa no estilo de *Attention Is All You Need* (18/11/2026).** A pedido do mantenedor, título, autores e resumo seguem o layout do paper do Transformer (estilo NeurIPS): título centralizado entre um filete de 4 pt e um de 1 pt, autores em negrito em blocos centralizados, e o resumo com título centralizado e texto recuado. A faixa com logo e data, a fonte Charter e o e-mail do lab continuam. Os nomes dos alunos e os usuários do GitHub dos casos de teste foram retirados deste documento, porque o repositório é público.
