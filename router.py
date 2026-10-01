import argparse
import subprocess
import sys
import json
from prompt_toolkit import prompt as pt_prompt

def setup():
    base_url = pt_prompt("Base_Url of provider: ")
    model = pt_prompt("Model name in provider database: ")
    api_key= pt_prompt("API key of provider, if none just click enter", is_password=True)
    Tavily_api = pt_prompt("API key of Tavily (its free get it now!): ", is_password=True)

    if api_key == '':
        api_key = 'ollama'


    config = {
        "model": f"{model}",
        "base_url": f"{base_url}",
        "api_key": f"{api_key}"
    }

    with open("config.json", "w") as f:
        json.dump(config, f, indent=4)

    with open(".env", "w") as f:
        print(f"TAVILY_API_KEY={Tavily_api}", file=f)
    
    print("Config has been set if you ever need to change it run minicode --setup again!!!")

def main():
    parser = argparse.ArgumentParser(
        description="MINICODE"
    )

    parser.add_argument(
        "--setup",
        action="store_true",
        help="Run MINICODE setup"
    )

    args = parser.parse_args()

    if args.setup:
        setup()
    else:
        subprocess.run(
            [sys.executable, "main.py"]
        )


if __name__ == "__main__":
    main()