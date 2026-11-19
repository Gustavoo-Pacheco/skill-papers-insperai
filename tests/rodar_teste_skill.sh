#!/usr/bin/env bash
# rodar_teste_skill.sh: roda uma skill no Claude Code sem interface, com o plugin deste repositório, sobre o caso Wakely.
#
# Uso: [MODELO=sonnet|opus] [ESFORCO=low|medium|high|xhigh|max] tests/rodar_teste_skill.sh <teste> <pasta-de-trabalho-fora-do-repo>
#
# Testes (prompt em tests/prompts/<teste>.md):
#   formata    o paper original na pasta; respostas fixas às perguntas
#   refaz      o paper original na pasta e o repo; o paper responde aos conflitos
#   cria       só o repo; o paper original responde à entrevista (oráculo), sem servir de fonte de texto
#   cria-cego  só o repo, sem oráculo: a sessão responde às próprias perguntas com o que o repo sustenta.
#              Recebe uma cópia limpa (git archive do HEAD, sem .git e sem a pasta paper/ do grupo).
#
# A pasta de trabalho precisa ficar FORA deste repositório: dentro dele, a sessão leria o CLAUDE.md de desenvolvimento.
# Usa o .venv do repositório (pymupdf, matplotlib) no PATH. Perguntas e respostas ficam em <pasta>/perguntas.md
# e o log da sessão em <pasta>/sessao.jsonl.
set -euo pipefail
TESTE="${1:?formata|refaz|cria|cria-cego}"
DEST="${2:?pasta de trabalho}"
RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
PAPER="$RAIZ/tests/privado/papers/wakely.pdf"
REPO="$(cd "$RAIZ/tests/privado/repos/wakely" && pwd -P)"
[[ -f "$RAIZ/tests/prompts/$TESTE.md" ]] || { echo "Teste desconhecido: $TESTE" >&2; exit 1; }
case "$DEST" in "$RAIZ"*) echo "A pasta de trabalho precisa ficar fora do repositório." >&2; exit 1;; esac
mkdir -p "$DEST"
DEST="$(cd "$DEST" && pwd -P)"

EXTRA=()
ORACULO=""
GIT_URL=""
GIT_COMMIT=""
case "$TESTE" in
  formata|refaz) cp "$PAPER" "$DEST/wakely.pdf" ;;
  cria) ORACULO_DIR="$(mktemp -d)/oraculo"; mkdir -p "$ORACULO_DIR"
        ORACULO="$ORACULO_DIR/wakely-original.pdf"; cp "$PAPER" "$ORACULO"; EXTRA+=(--add-dir "$ORACULO_DIR") ;;
  *) # cria-cego: cópia limpa do repo, sem o paper do grupo nem o histórico do git (onde o paper também está)
     GIT_URL="$(git -C "$REPO" remote get-url origin)"; GIT_COMMIT="$(git -C "$REPO" rev-parse --short HEAD)"
     LIMPO="$(mktemp -d)/$(basename "$REPO")"; mkdir -p "$LIMPO"
     git -C "$REPO" archive HEAD | tar -x -C "$LIMPO"
     rm -rf "$LIMPO/paper"
     REPO="$LIMPO"; echo "Repo limpo: $LIMPO" ;;
esac
if [[ -n "${MODELO:-}" ]]; then EXTRA+=(--model "$MODELO"); fi
if [[ -n "${ESFORCO:-}" ]]; then EXTRA+=(--effort "$ESFORCO"); fi

PROMPT="$(sed -e "s#{PAPER}#$DEST/wakely.pdf#g" -e "s#{REPO}#$REPO#g" -e "s#{ORACULO}#$ORACULO#g" -e "s#{GIT_URL}#$GIT_URL#g" -e "s#{GIT_COMMIT}#$GIT_COMMIT#g" "$RAIZ/tests/prompts/$TESTE.md")"
cd "$DEST"
CLAUDE="$(command -v claude || echo "$HOME/.local/bin/claude")"
PATH="$RAIZ/.venv/bin:$PATH" "$CLAUDE" -p "$PROMPT" \
  --plugin-dir "$RAIZ" --add-dir "$REPO" ${EXTRA[@]+"${EXTRA[@]}"} \
  --permission-mode acceptEdits --allowedTools Bash Read Write Edit Glob Grep Skill \
  --output-format stream-json --verbose > "$DEST/sessao.jsonl" 2> "$DEST/sessao.err"
echo "Fim do teste $TESTE em $DEST"
ls "$DEST"
