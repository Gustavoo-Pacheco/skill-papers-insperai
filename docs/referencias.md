# Papers de referência e análise das escolhas

Coleção de 39 papers de IA e deep learning (2015 a 2025) usada para definir o padrão do lab. Os PDFs não estão neste repositório, porque a licença do arXiv não permite redistribuí-los. Para baixar, use os ids do arXiv da tabela abaixo. Na máquina de quem mantém o projeto, eles ficam em `~/Documents/InsperAI/Estudos e referências/Artigos/Padrão de papers - referências/pdfs/`.

A extração foi automática (PyMuPDF): colunas, papel, fonte, estilo de citação, sumário, seções e tamanho. Depois conferi as capas e as páginas internas visualmente. Em PDFs sem índice embutido, as seções foram lidas do texto, então pode haver pequenas imprecisões.

## Os papers

Tipo: **R** = relatório técnico, **C** = conferência, **P** = pré-print, **J** = periódico.

| # | Paper | Laboratório | Ano | Onde saiu | Tipo | arXiv |
|---|---|---|---|---|---|---|
| 1 | Deep Residual Learning (ResNet) | Microsoft Research | 2015 | CVPR 2016 | C | 1512.03385 |
| 2 | Attention Is All You Need (Transformer) | Google Brain / Google Research | 2017 | NeurIPS 2017 | C | 1706.03762 |
| 3 | Proximal Policy Optimization (PPO) | OpenAI | 2017 | arXiv | P | 1707.06347 |
| 4 | BERT | Google AI Language | 2018 | NAACL 2019 | C | 1810.04805 |
| 5 | Exploring the Limits of Transfer Learning (T5) | Google | 2019 | JMLR 2020 | J | 1910.10683 |
| 6 | Scaling Laws for Neural Language Models | OpenAI | 2020 | arXiv | P | 2001.08361 |
| 7 | Retrieval-Augmented Generation (RAG) | Facebook AI Research | 2020 | NeurIPS 2020 | C | 2005.11401 |
| 8 | Language Models are Few-Shot Learners (GPT-3) | OpenAI | 2020 | NeurIPS 2020 | C | 2005.14165 |
| 9 | Denoising Diffusion Probabilistic Models (DDPM) | UC Berkeley | 2020 | NeurIPS 2020 | C | 2006.11239 |
| 10 | An Image is Worth 16x16 Words (ViT) | Google Research, Brain Team | 2020 | ICLR 2021 | C | 2010.11929 |
| 11 | Learning Transferable Visual Models (CLIP) | OpenAI | 2021 | ICML 2021 | C | 2103.00020 |
| 12 | LoRA | Microsoft | 2021 | ICLR 2022 | C | 2106.09685 |
| 13 | On the Opportunities and Risks of Foundation Models | Stanford CRFM | 2021 | arXiv | R | 2108.07258 |
| 14 | Masked Autoencoders (MAE) | Meta FAIR | 2021 | CVPR 2022 | C | 2111.06377 |
| 15 | Latent Diffusion Models (Stable Diffusion) | LMU Munich & Runway | 2021 | CVPR 2022 | C | 2112.10752 |
| 16 | Chain-of-Thought Prompting | Google Research, Brain Team | 2022 | NeurIPS 2022 | C | 2201.11903 |
| 17 | InstructGPT | OpenAI | 2022 | NeurIPS 2022 | C | 2203.02155 |
| 18 | Training Compute-Optimal LLMs (Chinchilla) | DeepMind | 2022 | NeurIPS 2022 | C | 2203.15556 |
| 19 | Helpful and Harmless Assistant with RLHF | Anthropic | 2022 | arXiv | R | 2204.05862 |
| 20 | FlashAttention | Stanford | 2022 | NeurIPS 2022 | C | 2205.14135 |
| 21 | Whisper | OpenAI | 2022 | ICML 2023 | C | 2212.04356 |
| 22 | Constitutional AI | Anthropic | 2022 | arXiv | R | 2212.08073 |
| 23 | LLaMA | Meta AI | 2023 | arXiv | R | 2302.13971 |
| 24 | GPT-4 Technical Report | OpenAI | 2023 | arXiv | R | 2303.08774 |
| 25 | Segment Anything (SAM) | Meta AI (FAIR) | 2023 | ICCV 2023 | C | 2304.02643 |
| 26 | Direct Preference Optimization (DPO) | Stanford | 2023 | NeurIPS 2023 | C | 2305.18290 |
| 27 | Llama 2 | Meta | 2023 | arXiv | R | 2307.09288 |
| 28 | Mistral 7B | Mistral AI | 2023 | arXiv | R | 2310.06825 |
| 29 | Mamba | CMU & Princeton | 2023 | COLM 2024 | C | 2312.00752 |
| 30 | Gemini | Google | 2023 | arXiv | R | 2312.11805 |
| 31 | OLMo | Allen Institute for AI | 2024 | ACL 2024 | R | 2402.00838 |
| 32 | Gemma | Google DeepMind | 2024 | arXiv | R | 2403.08295 |
| 33 | Phi-3 Technical Report | Microsoft | 2024 | arXiv | R | 2404.14219 |
| 34 | The Llama 3 Herd of Models | Meta | 2024 | arXiv | R | 2407.21783 |
| 35 | Qwen2.5 Technical Report | Alibaba (Qwen) | 2024 | arXiv | R | 2412.15115 |
| 36 | DeepSeek-V3 Technical Report | DeepSeek | 2024 | arXiv | R | 2412.19437 |
| 37 | DeepSeek-R1 | DeepSeek | 2025 | Nature 2025 | R | 2501.12948 |
| 38 | Gemma 3 Technical Report | Google DeepMind | 2025 | arXiv | R | 2503.19786 |
| 39 | Qwen3 Technical Report | Alibaba (Qwen) | 2025 | arXiv | R | 2505.09388 |

São 17 relatórios técnicos, que é o tipo que o lab vai produzir, e 22 papers de conferência, pré-print ou periódico.

## Escolhas e o que os labs fazem

### 1. Estilo de citação

| Opção | Total | Nos 17 relatórios | Quem usa |
|---|---|---|---|
| **Autor-ano**: (Silva et al., 2024) | 24 | 14 | **Relatórios:** Gemini e Gemma/Gemma 3 (Google DeepMind), Llama/Llama 2/Llama 3 (Meta), DeepSeek-V3/R1 (DeepSeek), Qwen2.5/Qwen3 (Alibaba), OLMo (AI2), Constitutional AI e HH-RLHF (Anthropic), Foundation Models (Stanford CRFM). **Conferência:** BERT (Google AI Language), ViT e CoT (Google Brain), CLIP, InstructGPT e Whisper (OpenAI), LoRA (Microsoft), Chinchilla (DeepMind), Mamba (CMU & Princeton), T5 (Google) |
| **Numérico**: [12] | 11 | 2 | **Relatórios:** GPT-4 (OpenAI), Mistral 7B (Mistral AI). **Conferência:** ResNet (Microsoft Research), Transformer (Google Brain), RAG (FAIR), DDPM (UC Berkeley), MAE e SAM (Meta FAIR), Latent Diffusion (LMU & Runway), FlashAttention e DPO (Stanford) |
| **Alfabético**: [KMH+20] | 4 | 1 | PPO, Scaling Laws e GPT-3 (OpenAI), Phi-3 (Microsoft) |

O numérico domina em visão computacional (CVPR/ICCV) e o autor-ano domina em NLP/LLMs e nos relatórios técnicos.

### 2. Colunas

| Opção | Total | Nos relatórios | Quem usa (relatórios) |
|---|---|---|---|
| **Uma coluna** | 28 | 13 | GPT-4 (OpenAI), Llama 2 e Llama 3 (Meta), Gemini (Google), DeepSeek-V3/R1, Qwen2.5/Qwen3, Phi-3 (Microsoft), Mistral 7B, Anthropic (2), Foundation Models (Stanford) |
| **Duas colunas** | 11 | 4 | LLaMA (Meta AI), OLMo (AI2), Gemma e Gemma 3 (Google DeepMind) |

As duas colunas aparecem quase só em formatos de conferência (CVPR, ICML, ACL) e em relatórios curtos, com menos de 25 páginas.

### 3. Tamanho do papel

- **Letter (EUA):** 26 papers, entre eles 7 relatórios (OpenAI, Anthropic, Meta, Microsoft, Mistral).
- **A4:** 12 papers, entre eles 9 relatórios (Google DeepMind, DeepSeek, Qwen, OLMo, LLaMA).
- Entre os relatórios de 2024 e 2025, a maioria é A4.

### 4. Fonte do corpo

| Fonte | Total | Quem usa |
|---|---|---|
| **Times** | 23 | Praticamente todos os templates de conferência (NeurIPS, ICML, CVPR, ICLR), GPT-4, Anthropic, LLaMA, Mistral, OLMo |
| **Palatino** | 5 | Llama 2 (Meta), DeepSeek-V3/R1, Qwen2.5/Qwen3. **Todos relatórios** |
| **Computer/Latin Modern** (padrão do LaTeX) | 5 | PPO (OpenAI), T5 (Google), FlashAttention (Stanford), Phi-3 (Microsoft), Llama 3 (Meta) |
| **Charter** | 4 | Chinchilla, Gemini, Gemma e Gemma 3. É o template da DeepMind |
| **Libertine** | 2 | Foundation Models (Stanford), Mamba |

O corpo tem de 10 a 11 pt em todos. Os relatórios com identidade própria escolhem fontes fora do Times, como Palatino ou Charter, para se diferenciar dos templates de conferência.

### 5. Capa / primeira página

| Opção | Quem usa |
|---|---|
| **Clássica acadêmica**: título centralizado, autores e afiliações, sem logo | 28 papers, incluindo GPT-4 (OpenAI), Anthropic, LLaMA/Llama 2 (Meta), Phi-3 (Microsoft) e todos os de conferência |
| **Com marca do lab**: logo no topo, data, título alinhado à esquerda, abstract destacado | Chinchilla (DeepMind), Gemini, Gemma e Gemma 3 (Google DeepMind), Llama 3 (Meta, abstract em caixa cinza com data e site), Qwen2.5/Qwen3 (logo, data e links de HF/ModelScope/GitHub), DeepSeek-V3/R1 (logo), OLMo (logo no título), Mistral 7B (logo grande) |

Desde 2023, a capa com marca virou o padrão dos relatórios técnicos da indústria: todos os 11 que a usam são de 2022 em diante.

Outros elementos de capa:
- **Figura de abertura na página 1:** ResNet, DDPM, LoRA, MAE, Latent Diffusion, CoT, SAM, Qwen2.5, DeepSeek-V3.
- **Data na capa:** Gemma, Gemma 3, Qwen2.5, Qwen3, Llama 3, FlashAttention.

### 6. Sumário impresso

Seis papers têm sumário, todos com mais de 30 páginas: Scaling Laws e GPT-3 (OpenAI), Foundation Models (Stanford CRFM), HH-RLHF (Anthropic), Llama 2 (Meta) e DeepSeek-V3 (DeepSeek). Os relatórios com menos de 30 páginas não usam.

### 7. Estrutura de seções

**Esqueleto típico de relatório técnico** (Gemini, Gemma, Llama 3, DeepSeek-V3, Qwen2.5/3, Phi-3):

> Introdução → Visão geral/Arquitetura → Dados e Pré-treino → Pós-treino → Avaliação/Resultados → Segurança/Responsabilidade → Discussão e Conclusão (com limitações) → Contribuições/Autores → Referências → Apêndice

**Esqueleto típico de conferência** (ResNet, ViT, MAE, DPO, LoRA):

> Introdução → Trabalhos relacionados → Método → Experimentos → Discussão/Conclusão → Referências → Apêndice

**Onde fica a seção "Trabalhos relacionados":**

| Posição | Quem |
|---|---|
| Logo após a introdução | ResNet, BERT, ViT, MAE, Latent Diffusion, InstructGPT, Chinchilla, DPO |
| No fim, antes da conclusão | Scaling Laws, GPT-3, CLIP e Whisper (OpenAI), RAG (FAIR), DDPM, LoRA, CoT, Constitutional AI, LLaMA, Llama 2, Llama 3 |
| No apêndice | FlashAttention, Mamba, DeepSeek-R1 |
| Sem seção própria (o contexto fica na introdução) | GPT-4, Gemini, Gemma, Gemma 3, Qwen2.5, Qwen3, DeepSeek-V3, Mistral, Phi-3, OLMo, HH-RLHF, SAM, T5, Transformer e PPO (usam "Background") |

**Seções opcionais e quem as usa:**

| Seção | Quem usa |
|---|---|
| **Limitações** (própria ou no título da conclusão) | GPT-3, CLIP, Whisper e GPT-4 (OpenAI), Latent Diffusion, FlashAttention, InstructGPT, Llama 2, OLMo, DeepSeek-V3, DeepSeek-R1, Phi-3 ("Weakness") |
| **Impacto, segurança e ética** | GPT-3, CLIP, GPT-4 (Risks & mitigations), Latent Diffusion, LLaMA (viés e pegada de carbono), SAM (RAI analysis), Llama 2 (Safety), Gemini (Responsible Deployment), Gemma 3, Phi-3 (Safety), DeepSeek-R1 (Ethics and Safety Statement) |
| **Contribuições / lista de autores** (seção própria) | Constitutional AI (Anthropic), GPT-4, Llama 2, Llama 3, Gemini, Gemma, DeepSeek-V3, DeepSeek-R1, Qwen2.5, Qwen3, Phi-3 |
| **Model, system ou data card** | Chinchilla, GPT-4 (System Card), SAM, Llama 2, Gemini |
| **Apêndice** | Quase todos. Nos relatórios, o apêndice guarda hiperparâmetros, prompts, tabelas completas e exemplos |
| **Link para código, pesos ou dados** | A maioria. Nos relatórios de modelos abertos (Llama, Gemma, Qwen, DeepSeek, OLMo), fica na capa ou na introdução |

### 8. Tamanho

| Tipo | Páginas até as referências (mediana) | Faixa |
|---|---|---|
| Conferência | 10 | 8 a 17 (T5 tem 57) |
| Relatório técnico | 30 | 7 (Mistral) a 160 (Foundation Models) |

O abstract tem mediana de 203 palavras, e metade dos papers fica entre 138 e 233.

### 9. Detalhes visuais

- **Legenda de figura:** "Figure 3 | **Título em negrito.** Descrição" é a marca do template da DeepMind (Chinchilla, Gemini, Gemma, Gemma 3). Os demais usam "Figure 3: Descrição".
- **Links e citações coloridos:** Gemini, Gemma, Gemma 3, Qwen2.5, Qwen3, Llama 3 e OLMo usam azul. OpenAI e Anthropic usam preto.
- **Cabeçalho corrido com o título do relatório:** Gemini, Gemma, Gemma 3.
- **Tabelas sem linhas verticais (booktabs):** é o padrão em todos. OLMo e Qwen destacam a linha do próprio modelo com fundo colorido.

## Identidade visual do Insper AI

As fontes são `InsperAI/Comunicação/Logos` e o site institucional (`Site/site-institucional`: `Main/Logos` e `src/app/globals.css`).

- **Logo:** um grafo de nós formando "AI", em degradê de **magenta `#B128C0` para azul `#016FD0`**. A versão completa traz "Insper AI" e o slogan "Deep Learning, Deep Thinking".
- **Variações do logo:** Azul Cobalto `#0058B8`, Roxo Coração `#7020A8`, Roxo Neural `#502870`, Roxo Noturno `#683080`, Lavanda (clara) e Branca. As cores foram amostradas dos PNGs.
- **Site:** tema escuro (`#09090B`), destaque em degradê violeta `#8B5CF6` → índigo `#6366F1` → azul `#3B82F6`, fonte **Geist Sans**.
- A paleta azul de `Projetos/Olimpiedas-dos-trainees-1/identidade-visual.md` é específica daquele evento e não é a identidade geral do lab.
