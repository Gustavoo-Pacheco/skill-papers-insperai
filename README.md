# skill-papers-insperai

Três skills do Claude para padronizar os papers do **Insper AI**, o grupo estudantil e laboratório de inteligência artificial do Insper.

| Skill | Quando usar |
|---|---|
| `formata-paper` | Você já tem o paper e só quer que ele siga o padrão do lab. O texto não muda |
| `refaz-paper` | Você tem o paper e o repositório de código, e quer o paper reescrito no padrão usando o repo como fonte |
| `cria-paper` | Ainda não existe paper. Você tem uma ideia, notas, resultados ou um repositório |

As três seguem o mesmo padrão, definido em [`padrao/`](padrao/): relatório técnico em A4, duas colunas, fonte Charter, capa com o logo do lab e citações em autor-ano ou numéricas.

> **Status:** v0.1.0, em teste. A formata foi verificada de ponta a ponta num paper real (texto idêntico ao original); a refaz e a cria estão em teste.

## Instalação

### Claude Code

```
/plugin marketplace add Gustavoo-Pacheco/skill-papers-insperai
/plugin install skill-papers-insperai@insperai
```

### App do Claude (web/desktop)

1. Baixe `formata-paper.zip`, `refaz-paper.zip` e `cria-paper.zip` da [última Release](https://github.com/Gustavoo-Pacheco/skill-papers-insperai/releases).
2. Em **Configurações → Capacidades → Skills**, envie cada `.zip`.

## Como usar

Peça em linguagem natural. Por exemplo:

- "Formata este paper no padrão do Insper AI" (anexe .tex, PDF, .docx ou Markdown).
- "Refaz o paper do projeto usando o repositório" (anexe ou aponte o paper e o repo).
- "Cria um paper sobre o projeto X a partir deste repositório e destas notas".

A skill pergunta o formato de saída (LaTeX, PDF ou os dois), o idioma e o estilo de citação. A saída fica numa pasta `<nome-do-paper>-insperai/` com `main.tex`, `refs.bib`, `figuras/` e `main.pdf`.

### Requisitos

- Python 3.10+ com `pymupdf` (e `matplotlib` para a refaz e a cria): `python3 -m pip install -r requirements.txt`. A skill instala se faltar.
- [Tectonic](https://tectonic-typesetting.github.io) para gerar o PDF. A skill tenta instalar sozinha (`brew install tectonic` no macOS); sem ele, entrega o .tex pronto para o Overleaf.
- Acesso à internet para completar as referências (arXiv, Crossref, DataCite, OpenAlex, Semantic Scholar). Sem rede, as referências ficam marcadas `[VERIFICAR]`.

## Para quem desenvolve

- **Contexto e decisões:** [`CLAUDE.md`](CLAUDE.md) e [`docs/contexto.md`](docs/contexto.md).
- **Edição do padrão:** o padrão só é editado em `padrao/`. Depois rode `python3 build.py` para copiá-lo para as skills e gerar `dist/`.
- **Testes:** `python3 build.py --check`, `claude plugin validate .` e os casos de [`tests/casos.md`](tests/casos.md): scripts no paper Wakely e as skills rodando sem interface (`tests/rodar_teste_skill.sh`).

## Licença

MIT. O logo do Insper AI não está coberto pela licença (veja [`LICENSE`](LICENSE)).
