#!/usr/bin/env bash
# compilar.sh: compila <pasta-do-paper>/main.tex em PDF com Tectonic.
#
# Uso: compilar.sh <pasta-do-paper> [arquivo.tex]
#
#   1. Se `tectonic` existe (PATH ou ~/.local/bin), compila.
#   2. Se não existe, sempre tenta instalar: brew no macOS; senão, o instalador oficial em ~/.local/bin.
#   3. Se a instalação ou a compilação falhar, sai com código 2 e diz que o .tex está pronto para o Overleaf.
#      A skill repassa a mensagem. Nunca diz que o PDF existe quando ele não existe.
#
# Teste do caminho sem Tectonic: INSPERAI_SEM_TECTONIC=1 compilar.sh <pasta>
set -uo pipefail

PASTA="${1:-}"
TEX="${2:-main.tex}"
if [[ -z "$PASTA" || ! -f "$PASTA/$TEX" ]]; then
  echo "Uso: compilar.sh <pasta-do-paper> [arquivo.tex]  (não achei $PASTA/$TEX)" >&2
  exit 1
fi

overleaf() {
  echo "PDF NÃO GERADO: $1" >&2
  echo "O projeto LaTeX está pronto em: $PASTA" >&2
  echo "Para gerar o PDF no Overleaf: New Project > Upload Project (envie a pasta em .zip) e escolha o compilador XeLaTeX ou pdfLaTeX em Menu > Compiler." >&2
  exit 2
}

achar() {
  if [[ -n "${INSPERAI_SEM_TECTONIC:-}" ]]; then return 1; fi
  if command -v tectonic >/dev/null 2>&1; then TECTONIC="$(command -v tectonic)"; return 0; fi
  if [[ -x "$HOME/.local/bin/tectonic" ]]; then TECTONIC="$HOME/.local/bin/tectonic"; return 0; fi
  return 1
}

if ! achar; then
  if [[ -n "${INSPERAI_SEM_TECTONIC:-}" ]]; then overleaf "Tectonic desativado (INSPERAI_SEM_TECTONIC)."; fi
  echo "Tectonic não encontrado. Tentando instalar..." >&2
  if [[ "$(uname)" == "Darwin" ]] && command -v brew >/dev/null 2>&1; then
    brew install tectonic >&2 || true
  fi
  if ! achar; then
    mkdir -p "$HOME/.local/bin" && (
      cd "$HOME/.local/bin" &&
      curl --proto '=https' --tlsv1.2 -fsSL https://drop-sh.fullyjustified.net | sh >&2
    ) || true
  fi
  achar || overleaf "não consegui instalar o Tectonic (sem rede ou sem permissão)."
fi

cd "$PASTA" || exit 1
LOG="$(mktemp)"
if ! "$TECTONIC" -X compile --keep-logs "$TEX" >"$LOG" 2>&1; then
  grep -E "^error|^!|Undefined control|LaTeX Error" "$LOG" | head -20 >&2
  rm -f "$LOG"
  overleaf "a compilação falhou (erros acima)."
fi

BASE="${TEX%.tex}"
# Avisos que importam: glifo faltando na fonte, citação ou referência indefinida
LOGTEX="$BASE.log"
if [[ -f "$LOGTEX" ]]; then
  FALTA=$(grep -o "Missing character: There is no [^ ]* ([^)]*)" "$LOGTEX" | sort | uniq -c | sort -rn | head -10)
  [[ -n "$FALTA" ]] && echo "AVISO: caracteres sem glifo na fonte (aparecem em branco no PDF):" >&2 && echo "$FALTA" >&2
  CIT=$(grep -oE "Citation \`[^']+' (on page [0-9]+ )?undefined" "$LOGTEX" | sort -u | head -10)
  [[ -n "$CIT" ]] && echo "AVISO: citações indefinidas:" >&2 && echo "$CIT" >&2
  REF=$(grep -oE "Reference \`[^']+' (on page [0-9]+ )?undefined" "$LOGTEX" | sort -u | head -10)
  [[ -n "$REF" ]] && echo "AVISO: referências cruzadas indefinidas:" >&2 && echo "$REF" >&2
fi
rm -f "$LOG" "$BASE.aux" "$BASE.bbl" "$BASE.blg" "$BASE.out"
PAGINAS=$( (command -v pdfinfo >/dev/null && pdfinfo "$BASE.pdf" 2>/dev/null | awk '/^Pages/{print $2}') || echo "?")
echo "PDF gerado: $PASTA/$BASE.pdf (${PAGINAS:-?} páginas)"
