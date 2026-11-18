#!/usr/bin/env bash
# rodar_teste_skill.sh: roda uma skill no Claude Code sem interface, com o plugin deste repositório, sobre o caso Wakely.
#
# Uso: tests/rodar_teste_skill.sh formata|refaz|cria <pasta-de-trabalho-fora-do-repo>
#
# A pasta de trabalho precisa ficar FORA deste repositório: dentro dele, a sessão leria o CLAUDE.md de desenvolvimento.
# Usa o .venv do repositório (pymupdf, matplotlib) no PATH. As perguntas da skill são respondidas por um oráculo
# descrito em tests/prompts/<skill>.md e ficam registradas em <pasta>/perguntas.md. O log vai para <pasta>/sessao.jsonl.
set -euo pipefail
SKILL="${1:?formata|refaz|cria}"
DEST="${2:?pasta de trabalho}"
RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
PAPER="$RAIZ/tests/privado/papers/wakely.pdf"
REPO="$(cd "$RAIZ/tests/privado/repos/wakely" && pwd -P)"
ORACULO_DIR="$(mktemp -d)/oraculo"
case "$DEST" in "$RAIZ"*) echo "A pasta de trabalho precisa ficar fora do repositório." >&2; exit 1;; esac
mkdir -p "$DEST" "$ORACULO_DIR"
DEST="$(cd "$DEST" && pwd -P)"
cp "$PAPER" "$ORACULO_DIR/wakely-original.pdf"
if [[ "$SKILL" != "cria" ]]; then cp "$PAPER" "$DEST/wakely.pdf"; fi
PROMPT="$(sed -e "s#{PAPER}#$DEST/wakely.pdf#g" -e "s#{REPO}#$REPO#g" -e "s#{ORACULO}#$ORACULO_DIR/wakely-original.pdf#g" "$RAIZ/tests/prompts/$SKILL.md")"
cd "$DEST"
CLAUDE="$(command -v claude || echo "$HOME/.local/bin/claude")"
PATH="$RAIZ/.venv/bin:$PATH" "$CLAUDE" -p "$PROMPT" \
  --plugin-dir "$RAIZ" --add-dir "$REPO" --add-dir "$ORACULO_DIR" \
  --permission-mode acceptEdits --allowedTools Bash Read Write Edit Glob Grep Skill \
  --output-format stream-json --verbose > "$DEST/sessao.jsonl" 2> "$DEST/sessao.err"
echo "Fim do teste $SKILL em $DEST"
ls "$DEST"
