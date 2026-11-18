# Como ler o repositório

> Fonte única, usada por refaz-paper e cria-paper. Edite só aqui e rode `python3 build.py`.

## Acesso

O repositório pode chegar como:
- **Pasta local**, no Claude Code.
- **URL pública do GitHub:** `inventario_repo.py` clona com `git clone --depth 1`.
- **.zip anexado**, no app.
- **Repositório privado:** use o conector do GitHub, se estiver disponível. Senão, peça o `.zip` ou que a pessoa torne o repo público. Use o que tiver.

## Passo a passo

1. `python3 scripts/inventario_repo.py <repo> --saida trabalho/inventario.json`. O script lista README, licença, dependências, git (remote, commit, tags), CSV/JSON, notebooks (títulos e saídas com números, com o número da célula), logs, checkpoints, figuras e PDFs.
2. Leia o README e os docs inteiros. Eles dizem o que o grupo considera o resultado final.
3. Leia as saídas dos notebooks e os CSV/JSON. **Não reexecute nada sem pedir**: pode levar horas ou mudar números.
4. Anote cada resultado em `trabalho/fontes.md`: o valor, o que ele mede e a origem (`notebook.ipynb`, célula 42; `results/tabela.csv`, linha 3).
5. Repo grande: comece pelo README, pelos notebooks e pelas pastas `results/`, `outputs/`, `docs/`. Não abra checkpoints, só registre que existem.

## Onde estão os resultados

Procure, nesta ordem de confiança:

1. **CSV/JSON versionados no repo**, como `resultados/` ou `results/`. É a fonte mais confiável.
2. **Notebooks com saída** (`.ipynb`): tabelas e gráficos já executados.
3. **Logs e checkpoints** em `runs/`, `outputs/` ou `logs/`: curvas de treino e configurações.
4. **Gráficos e tabelas do próprio paper**, quando o repo não tiver o dado bruto. São fonte, mas valem menos que o repo. Se divergirem do repo, viram pergunta.

## O que extrair

- **Método:** arquitetura, hiperparâmetros (configs), dados e pré-processamento.
- **Experimentos:** quais rodaram, com quais seeds e métricas, e quais foram descartados e por quê.
- **Resultados:** os números finais, com a origem de cada um.
- **Seção "Código e dados":** URL, commit ou tag, licença (arquivo LICENSE), dados (origem e se podem ser redistribuídos) e como reproduzir (README).
