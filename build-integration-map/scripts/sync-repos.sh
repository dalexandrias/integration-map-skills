#!/usr/bin/env bash
# Clona ou atualiza em lote os repositórios listados em repos.txt.
# Usa o git já autenticado na máquina (Git Credential Manager ou PAT no keychain).
#
#   ./sync-repos.sh ~/repos repos.txt
#
# repos.txt: uma URL por linha. Linhas vazias e comentários com # são ignorados.
#   https://dev.azure.com/minha-org/meu-projeto/_git/svc-cotacao
#   https://dev.azure.com/minha-org/meu-projeto/_git/consulta-cobertura
#
# Clone parcial e raso: traz a árvore de arquivos e baixa o conteúdo só do que for aberto.
# Em 80 repositórios isso muda o tempo de minutos para segundos por repo.

set -uo pipefail

ROOT="${1:-$HOME/repos}"
LIST="${2:-repos.txt}"
JOBS="${JOBS:-4}"

[[ -f "$LIST" ]] || { echo "lista não encontrada: $LIST" >&2; exit 1; }
mkdir -p "$ROOT"

ok=0; fail=0; failed=()

sync_one() {
  local url="$1" name
  name="$(basename "${url%.git}")"
  if [[ -d "$ROOT/$name/.git" ]]; then
    git -C "$ROOT/$name" fetch --quiet --depth 1 origin 2>/dev/null &&
    git -C "$ROOT/$name" reset --quiet --hard "@{u}" 2>/dev/null
  else
    git clone --quiet --filter=blob:none --depth 1 "$url" "$ROOT/$name" 2>/dev/null
  fi
}

while IFS= read -r line || [[ -n "$line" ]]; do
  line="${line%%#*}"
  line="$(echo "$line" | xargs || true)"
  [[ -z "$line" ]] && continue
  name="$(basename "${line%.git}")"
  if sync_one "$line"; then
    printf '  ok    %s\n' "$name"; ((ok++))
  else
    printf '  FALHA %s\n' "$name"; ((fail++)); failed+=("$name")
  fi
done < "$LIST"

echo
echo "sincronizados: $ok   falhas: $fail"
if (( fail )); then
  printf 'repositórios com falha:\n'
  printf '  - %s\n' "${failed[@]}"
  echo
  echo "Causas comuns: credencial do Azure DevOps expirada (rode 'git credential-manager"
  echo "erase' e autentique de novo), repositório renomeado, ou branch padrão sem commits."
  exit 1
fi
