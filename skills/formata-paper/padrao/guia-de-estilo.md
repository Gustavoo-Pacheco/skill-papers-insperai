# Guia de estilo do Insper AI

> Fonte única. Edite só aqui e rode `python3 build.py`.
> As decisões e os motivos estão em `docs/contexto.md`.

## Layout

| Item | Regra | Referência |
|---|---|---|
| Papel | A4 | Google DeepMind, DeepSeek, Qwen, OLMo |
| Colunas | Duas. Figuras e tabelas largas usam a largura toda (`figure*`, `table*`) | Gemma, Gemma 3, OLMo |
| Fonte do corpo | Charter (XCharter), 10 pt | Template da DeepMind: Gemini, Gemma, Chinchilla |
| Sumário | Não há | Nenhum relatório em duas colunas da coleção usa |
| Legenda | "Figura 3 \| **Título em negrito.** Descrição" (macro `\legenda{Título}{Descrição}`) | Template da DeepMind |
| Tabelas | booktabs, sem linhas verticais. A linha do método proposto pode ter fundo azul claro (`\linhadestaque`) | Todos os 39. OLMo e Qwen destacam a linha |

## Cores

As cores foram amostradas do logo e das variações oficiais (`InsperAI/Comunicação/Logos`):

| Uso | Cor | Hex |
|---|---|---|
| Links e citações | Azul Cobalto | `#0058B8` |
| Títulos de seção | Preto | `#000000` |
| Capa | Logo em degradê (magenta `#B128C0` → azul `#016FD0`) | Arquivo `template/logo-insperai.png` |
| Destaque de linha em tabela | Azul Cobalto a 10% | `insperCobalto!10` |

### Paleta dos gráficos (`template/insperai.mplstyle`)

| Ordem | Cor | Hex | Uso sugerido |
|---|---|---|---|
| 1 | Azul Cobalto | `#0058B8` | Método proposto |
| 2 | Magenta médio | `#D86FE0` | Principal comparação (derivado do magenta do logo) |
| 3 | Azul-noite | `#1E2A44` | Baseline |
| 4 | Cinza | `#A3A8B0` | Referência ou ablação |

Validada para daltonismo com simulação de Machado et al. (2009). O menor ΔE entre duas cores é 18,7 (protanopia); com as cores originais do logo, era 6,0. **Com mais de quatro séries, diferencie também por marcador ou tipo de linha.** Não use as duas pontas do logo (`#016FD0` e `#B128C0`) como par de séries: sob protanopia, elas quase se confundem (ΔE 11).

## Citações e referências

- A skill pergunta: **autor-ano** (Silva et al., 2024) ou **numérico** [12]. Sem resposta, usa **autor-ano**.
- As referências chegam num `.bib`. `scripts/completar_bib.py` valida, completa e corrige as entradas pelo arXiv, DOI (Crossref) ou Semantic Scholar. O que não for encontrado recebe `note = {[VERIFICAR]}` e entra no resumo da entrega.
- **As chaves do .bib são as do autor.** A skill não renomeia. Só quando a entrada não tem chaves (PDF ou .docx) a skill cria uma no formato `sobrenome2024palavra`.

## Redação

| Item | Regra |
|---|---|
| Pessoa verbal | **Impessoal**: "propõe-se", "o modelo foi treinado", "os resultados mostram". Na formata, o texto não muda |
| Tempo verbal | Presente para o que o paper faz e mostra ("a seção 3 apresenta"). Passado para o que foi feito nos experimentos ("o modelo foi treinado") |
| Contribuições | **Um parágrafo** no fim da introdução, sem lista |
| Resumo | **Recomendado de 150 a 250 palavras**, flexível conforme o conteúdo. A mediana dos 39 papers de referência é 203. Um resumo maior precisa se justificar pela quantidade de resultados |
| Resultados numéricos | **Como estão na fonte** (repositório ou paper). Não acrescentar nem remover desvio, intervalo ou casas decimais |
| Termos em inglês num texto em português | **Em itálico** quando não há tradução consagrada (*fine-tuning*, *baseline*, *dataset*). Quando há, traduzir ("conjunto de validação", "rede neural") |
| Siglas | Por extenso na primeira vez, com a sigla entre parênteses |

## Idioma

- Cada paper sai no idioma que a pessoa escolher. Sem resposta, sai no idioma do repositório ou do paper de entrada.
- Português: "Figura", "Tabela", "Resumo", com vírgula decimal (18,44 s).
- Inglês: "Figure", "Table", "Abstract", com ponto decimal (18.44 s).

## Uso de IA

- IA nunca entra como autora. Se o paper de entrada listar uma, a skill remove e avisa.
- O uso de IA nunca é declarado no paper, qualquer que seja o destino.
