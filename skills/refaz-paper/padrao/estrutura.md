# Estrutura do relatório técnico do Insper AI

> Fonte única. Edite só aqui e rode `python3 build.py` para copiar para as skills.
> As decisões e os motivos estão em `docs/contexto.md`, e os papers de referência em `docs/referencias.md`.

O padrão cobre um tipo de documento: o **relatório técnico**. É um documento público (arXiv ou site do lab), escrito para quem é de fora, que apresenta um trabalho completo.

## Ordem das seções

| # | Seção (PT / EN) | Obrigatória? | Observações |
|---|---|---|---|
| — | Capa | Sim | Veja "Capa" abaixo |
| 1 | Introdução / Introduction | Sim | Termina com **um parágrafo** de contribuições |
| 2 | Trabalhos relacionados / Related Work | Sim | Logo após a introdução |
| 3 | Método / Method | Sim | Pode ter subseções (Dados, Modelo, Protocolo, Métricas) |
| 4 | Resultados / Results | Sim | Experimentos e análise. Pode incluir a discussão |
| 5 | Limitações / Limitations | Sim | Seção própria |
| 6 | Código e dados / Code and Data | Sim | **Um parágrafo só.** Veja o modelo abaixo |
| 7 | Conclusão / Conclusion | Sim | |
| — | Contribuições dos autores / Author Contributions | Opcional | Sem número de seção |
| — | Ética e impacto / Ethics and Impact | Opcional | Sem número de seção |
| — | Referências / References | Sim | Autor-ano por padrão, ou numérico se a pessoa escolher |
| — | Apêndice / Appendix | Opcional | Hiperparâmetros, prompts, tabelas completas, exemplos |

Não há sumário.

Como reconhecer as seções (usado por `scripts/verificar_checklist.py`):
- **Título do padrão:** os da tabela, em PT ou EN; "Métodos", "Metodologia", "Conclusões" e "Methods" também valem.
- **Título equivalente** (aviso na formata, falha na refaz e na cria): "Experimentos" para Resultados; "Reprodutibilidade", "Disponibilidade" ou "Code availability" para Código e dados; "Background" ou "Estado da arte" para Trabalhos relacionados.
- **Seção combinada** (por exemplo, "Discussão, limitações e conclusão"): aviso na formata, falha na refaz e na cria.

## Capa

Montada pela classe (`\maketitle`):
- Logo do Insper AI no canto superior esquerdo e a data no canto superior direito.
- Título, autores e resumo no estilo de *Attention Is All You Need* (NeurIPS), acima das duas colunas:
  - **Título** centralizado entre um filete de 4 pt (acima) e um de 1 pt (abaixo), com subtítulo opcional.
  - **Autores** em negrito, em blocos centralizados lado a lado: `\author{Ana Souza \and Bruno Lima}`. `\AND` força uma nova linha de autores. Quem quiser afiliação ou e-mail próprio escreve dentro do bloco: `\author{Ana Souza \\ Outra Universidade \\ \texttt{ana@exemplo.com} \and ...}`.
  - **Afiliação** ("Insper AI, Insper") e **e-mail do lab** (contato@insperai.com.br, em fonte monoespaçada) centralizados abaixo dos autores.
  - **Resumo** com o título ("Resumo" ou "Abstract") centralizado em negrito e o texto justificado, recuado dos dois lados (80% da largura), sem caixa.
- Sem palavras-chave e sem link do repositório na capa. O link vai na seção "Código e dados".
- **IA nunca é autora.** Se o paper de entrada listar uma (por exemplo, "Claude (Anthropic)"), a skill remove e avisa no resumo da entrega.

## Modelo da seção "Código e dados"

O modelo segue o que os papers de referência fazem (DDPM, CLIP, LoRA, Mamba, OLMo, Mistral, DeepSeek). Em um parágrafo, a seção diz:

1. **Onde** está o código: URL do repositório e, se houver, a tag ou o commit usados nos resultados.
2. **O que** foi feito e está lá: treino, avaliação, notebooks, scripts de figuras.
3. **Dados**: de onde vêm e se estão disponíveis.
4. **Licença**, se houver.

Exemplos reais que serviram de base:

- "Our implementation is available at https://github.com/hojonathanho/diffusion." (DDPM, UC Berkeley)
- "We release our code and pre-trained model weights at https://github.com/OpenAI/CLIP." (CLIP, OpenAI)
- "Model code and pre-trained checkpoints are open-sourced at https://github.com/state-spaces/mamba." (Mamba)
- "We release OLMo alongside open training data and training and evaluation code. [...] all code and weights are released under the Apache 2.0 License." (OLMo, AI2)

Modelo em português, impessoal:

> O código deste trabalho está disponível em <URL> (versão <tag/commit>). O repositório contém <o que foi feito: o pipeline de treino, a avaliação e os notebooks que geram as figuras>. Os dados vêm de <fonte> e <estão disponíveis em <URL> | não podem ser redistribuídos por <motivo>>. O código é distribuído sob a licença <licença>.

## Ordem das seções na formata-paper

A formata **mantém a ordem e a numeração originais** das seções, figuras e tabelas. O texto cita "seção 5" e "figura 2", e ela não pode mudar o texto; reordenar quebraria essas referências. Se a ordem diferir do padrão, o checklist avisa e a diferença entra no resumo da entrega. Quem quer a ordem do padrão usa a refaz-paper.

## Seção obrigatória ausente (formata-paper)

A formata não escreve texto. Se faltar uma seção obrigatória, ela **pergunta ao usuário se deve inserir a seção e como**:
1. O usuário escreve o texto, e a skill insere exatamente o que ele escreveu.
2. A skill insere a seção com um marcador visível (`\secaofaltando{Limitações}`, uma caixa colorida no PDF).
3. A seção não é inserida, e a falta é registrada no resumo da entrega.
4. Se o conteúdo existir em outra parte do paper (por exemplo, um parágrafo "Limitações." dentro da discussão), a formata pode **promovê-lo** a `\subsection*{Limitações}`, sem mudar o texto. Subseção sem número, para não renumerar as seções que o texto cita.

Na refaz e na cria, todas as seções obrigatórias existem com o título do padrão.

## Tamanho

| Skill | Regra |
|---|---|
| `cria-paper` | Sem tamanho fixo. A skill avalia pelo conteúdo e não enche nem corta para caber num número de páginas |
| `refaz-paper` | **±10% do número de palavras do corpo** do original (sem capa, resumo, legendas, tabelas, referências nem apêndice). `scripts/contar_palavras.py` mede |
| `formata-paper` | Não mexe no texto, então o tamanho é o que resultar do novo layout |
