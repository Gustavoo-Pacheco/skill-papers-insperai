# Casos de teste

Os papers e repositórios de teste são de outros alunos do Insper AI e ficam só na máquina local, em `tests/privado/`, que está fora do git porque este repositório é público. Aqui ficam a descrição dos casos, os prompts e os scripts de avaliação.

## Montar `tests/privado/` numa máquina nova

```
tests/privado/
├── papers/wakely.pdf
└── repos/wakely/      clone ou link simbólico do repositório do grupo (peça o link ao mantenedor)
```

E o ambiente: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`, mais o Tectonic (`brew install tectonic`).

| Caso | O que é | Testa |
|---|---|---|
| **wakely** | Paper real de um grupo (17 p., LaTeX, PT, citações numéricas, 8 figuras, 6 tabelas, frações, índices) e o repositório dele | As três skills |
| **autor-ia** (`tests/fixtures/autor-ia.md`) | Paper sintético em Markdown com "Claude (Anthropic)" como autor | Entrada Markdown e a remoção de IA da lista de autores |

## Testes dos scripts (deterministas)

```
S=padrao/scripts; P=tests/privado/papers/wakely.pdf; O=tests/saidas/wakely-formata
.venv/bin/python $S/extrair_entrada.py $P tests/saidas/wakely.json
.venv/bin/python $S/montar_latex.py tests/saidas/wakely.json $O --original $P
bash $S/compilar.sh $O
.venv/bin/python $S/verificar_texto.py $P $O/main.pdf          # esperado: TEXTO IDÊNTICO
.venv/bin/python $S/verificar_checklist.py $O --skill formata  # esperado: 0 falhas
.venv/bin/python $S/contar_palavras.py $P $O/main.tex          # esperado: DENTRO DA FAIXA
```

Para o caso autor-ia, o mesmo fluxo com `tests/fixtures/autor-ia.md`, sem `--original`, e `verificar_texto.py <pasta>/entrada.json <pasta>/main.pdf --ignorar Claude --ignorar Anthropic`. Esperado: IA fora de `\author`, aviso no resumo e TEXTO IDÊNTICO.

## Testes das skills (Claude Code sem interface)

`[MODELO=sonnet|opus] [ESFORCO=high] tests/rodar_teste_skill.sh formata|refaz|cria|cria-cego <pasta-fora-do-repo>` roda a skill com o plugin deste repositório (`--plugin-dir`). Como não há ninguém para responder, o prompt em `tests/prompts/<teste>.md` define um oráculo e a sessão registra perguntas e respostas em `<pasta>/perguntas.md`:
- **formata:** respostas fixas (LaTeX e PDF, autor-ano, promover o que existir, marcador no que faltar).
- **refaz:** o paper original responde aos conflitos.
- **cria:** recebe só o repositório; o paper original responde à entrevista, sem servir de fonte de texto.
- **cria-cego:** recebe uma cópia limpa do repositório (sem `.git` e sem a pasta `paper/` do grupo) e responde às próprias perguntas só com o que o repo sustenta. Depois, procure no `sessao.jsonl` acessos ao paper do grupo.

`tests/comparar_versoes.py <original.pdf> --saida tests/saidas/comparacao --versao "Rótulo|skill|pasta|repo|descrição[|cego]" ...` gera uma página HTML local que compara o original com as versões: números, capas, estrutura, números-chave do original, resumos, perguntas e todas as páginas. A página tem o paper de outros alunos: não publique.

### O que cada skill precisa provar

**formata-paper**
- [ ] `verificar_texto.py` termina em TEXTO IDÊNTICO.
- [ ] `verificar_checklist.py --skill formata` sem falhas; avisos explicados no resumo.
- [ ] No caso autor-ia, a IA sai dos autores e a remoção aparece no resumo.
- [ ] As seções obrigatórias que faltam geram pergunta, e não texto inventado.

**refaz-paper**
- [ ] `contar_palavras.py <original> <novo>/main.tex` dentro de ±10%.
- [ ] `verificar_checklist.py --skill refaz` sem falhas: todas as seções obrigatórias, com o título do padrão e na ordem.
- [ ] As divergências entre o paper e o repo aparecem em `perguntas.md` com a resposta.
- [ ] `tests/verificar_cobertura.py <original> <novo>/main.tex --repo <repo>`: nenhum número sem fonte.

**cria-paper**
- [ ] A entrevista acontece antes da escrita (`perguntas.md`).
- [ ] `verificar_checklist.py --skill cria` sem falhas.
- [ ] `tests/verificar_cobertura.py <original> <novo>/main.tex --repo <repo> --extra <pasta>/perguntas.md`: nenhum número sem fonte. A cobertura dos números-chave do original é medida e registrada, sem meta fixa. No cria-cego, com `--cego` (o original não conta como fonte).

## Gerais
- [ ] `python3 build.py --check` passa.
- [ ] `claude plugin validate .` passa.
- [ ] Compilação: com Tectonic sai o PDF. Sem ele (`INSPERAI_SEM_TECTONIC=1 bash padrao/scripts/compilar.sh <pasta>`), sai com código 2 e a mensagem do Overleaf.
