#!/usr/bin/env bash
# Executa a bateria de testes automatizados (pytest).
#
# Uso:
#   ./run_tests.sh              # roda toda a suite com saida detalhada (-v -s)
#   ./run_tests.sh tests/test_auth.py        # roda apenas um arquivo
#   ./run_tests.sh -k tampering              # filtra por expressao
#
# O script:
#  - garante que esta na raiz do projeto;
#  - usa o Python da .venv quando disponivel, senao cai no python3 do sistema;
#  - instala pytest automaticamente se ainda nao estiver instalado;
#  - forca LOCAL_DB=true para nao depender de MongoDB durante os testes.

set -euo pipefail

cd "$(dirname "$0")"

if [[ -x ".venv/bin/python" ]]; then
    PY=".venv/bin/python"
else
    PY="$(command -v python3 || command -v python)"
fi

if ! "$PY" -c "import pytest" >/dev/null 2>&1; then
    echo "[run_tests] instalando pytest..."
    "$PY" -m pip install --quiet pytest
fi

export LOCAL_DB=true
unset MONGO_URI || true

if [[ $# -eq 0 ]]; then
    exec "$PY" -m pytest tests/ -v -s
else
    exec "$PY" -m pytest "$@"
fi
