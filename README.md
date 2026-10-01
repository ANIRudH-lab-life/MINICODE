# MINICODE

MINICODE is a terminal coding agent designed for small language models, especially local models around 1B parameters. It gives compact models an interactive prompt, web search, and supervised shell and file actions.

The default configuration uses Ollama with `qwen3:1.7b`, a small local model in the intended size range.

It is always in its provided directory so you dont have to worry about it removing all of your file in the current directory

## Requirements

- Python 3
- An OpenAI-compatible chat-completions provider, such as Ollama
- `git` and Ollama when using the installer
- A `TAVILY_API_KEY` environment variable to enable web search

## Install

The installer clones the project, creates a virtual environment, installs dependencies, downloads the default Ollama model, and exposes a `minicode` command.

```bash
curl -fsSL https://raw.githubusercontent.com/ANIRudH-lab-life/MINICODE/main/install.sh | bash
```

By default, MINICODE is installed in `~/.local/share/minicode` and the launcher is linked to `~/.local/bin/minicode`. Add that directory to `PATH` if the installer reports that it is missing.

To use custom locations, set `MINICODE_INSTALL_DIR` and/or `MINICODE_BIN_DIR` before running the script.

## Run

Configure a provider interactively:

```bash
minicode --setup
```

Then start a session:

```bash
minicode
```

To run directly from a checkout instead, install the Python dependencies and use the router:

```bash
python3 -m pip install openai prompt-toolkit python-dotenv requests
python3 router.py --setup
python3 router.py
```

## Configuration

Provider settings live in `config.json`:

```json
{
  "model": "qwen3:1.7b",
  "base_url": "http://127.0.0.1:11434/v1",
  "api_key": "ollama"
}
```

Use `minicode --setup` to rewrite these values. For providers without an API key, leave the API-key prompt blank; MINICODE uses `ollama` as a placeholder.

Place `TAVILY_API_KEY=your_key` in a `.env` file in the project directory, or export it in the shell, before asking the agent to search the web.

## In-session Commands

- `/memory`: save the current conversation as a timestamped JSON transcript, then choose a transcript file to load.
- `/quit`: end the session.
- `/update`: updates minicode
- `Ctrl+C`: save the current conversation and exit.

## Safety Prompts

When a model requests a shell command or a file write, MINICODE presents a confirmation dialog. Declining it returns that refusal to the model so it can respond appropriately. Review each prompt carefully, since the requested command or file content is shown in the dialog.

## Project Files

- `main.py`: interactive agent loop and model tools.
- `router.py`: command-line entry point and provider setup flow.
- `setup.sh`: installer for a local MINICODE command and the default Ollama model.
- `config.json`: active model-provider settings.
