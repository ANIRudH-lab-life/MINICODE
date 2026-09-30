#!/usr/bin/env bash

set -euo pipefail

readonly REPOSITORY_URL="https://github.com/ANIRudH-lab-life/MINICODE.git"
readonly MODEL_NAME="qwen3:1.7b"

data_dir="${XDG_DATA_HOME:-$HOME/.local/share}"
install_dir="${MINICODE_INSTALL_DIR:-$data_dir/minicode}"
bin_dir="${MINICODE_BIN_DIR:-$HOME/.local/bin}"

fail() {
    printf 'setup.sh: %s\n' "$*" >&2
    exit 1
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
    printf 'Install MINICODE and the qwen3:1.7b Ollama model.\n'
    printf 'MINICODE_INSTALL_DIR and MINICODE_BIN_DIR may override the default paths.\n'
    exit 0
fi

[[ $# -eq 0 ]] || fail "unexpected argument: $1"
command -v git >/dev/null 2>&1 || fail "git is required"
command -v python3 >/dev/null 2>&1 || fail "python3 is required"
command -v ollama >/dev/null 2>&1 || fail "Ollama is required: https://ollama.com"

if [[ -d "$install_dir/.git" ]]; then
    printf 'Updating MINICODE in %s\n' "$install_dir"
    git -C "$install_dir" pull --ff-only
elif [[ -e "$install_dir" ]]; then
    fail "$install_dir exists but is not a git checkout"
else
    mkdir -p "$(dirname "$install_dir")"
    printf 'Cloning MINICODE into %s\n' "$install_dir"
    git clone "$REPOSITORY_URL" "$install_dir"
fi

printf 'Creating Python environment\n'
python3 -m venv "$install_dir/.venv"
"$install_dir/.venv/bin/python" -m pip install --upgrade pip
"$install_dir/.venv/bin/python" -m pip install \
    'openai>=1.0.0' \
    'prompt-toolkit>=3.0.0' \
    'python-dotenv>=1.0.0' \
    'requests>=2.0.0'

printf 'Downloading Ollama model %s\n' "$MODEL_NAME"
ollama pull "$MODEL_NAME"

mkdir -p "$bin_dir"
launcher="$install_dir/.minicode-launcher"
cat > "$launcher" <<EOF
#!/usr/bin/env bash
set -euo pipefail
cd "$install_dir"
exec "$install_dir/.venv/bin/python" router.py "\$@"
EOF
chmod +x "$launcher"
ln -sfn "$launcher" "$bin_dir/minicode"

printf '\nMINICODE is installed. Run: minicode\n'
case ":$PATH:" in
    *":$bin_dir:"*) ;;
    *) printf 'Add %s to your PATH, then open a new shell.\n' "$bin_dir" ;;
esac
