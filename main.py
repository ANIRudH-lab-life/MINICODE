from dotenv import load_dotenv
import requests
import os
import subprocess
import json
from openai import OpenAI
from openai.types.chat import ChatCompletionMessage
import sys
import warnings
from prompt_toolkit import prompt as pt_prompt
from datetime import datetime
from prompt_toolkit import Application
from prompt_toolkit import print_formatted_text as print , HTML
from xml.sax.saxutils import escape
from prompt_toolkit.styles import Style
from prompt_toolkit.cursor_shapes import CursorShape, ModalCursorShapeConfig
from prompt_toolkit.shortcuts import yes_no_dialog
from prompt_toolkit.shortcuts import message_dialog
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.completion import Completer, Completion

COMMANDS = ["/memory", "/quit"]

class SlashCompleter(Completer):
    async def get_completions_aysnc(self, document, complete_event):
        text = document.text_before_cursor

        if text.startswith("/"):
            for command in COMMANDS:
                if command.startswith(text):
                    yield Completion(
                        command,
                        start_position=-len(text)
                    )

c_or_t=None

def bottom_toolbar():
    return HTML("""<style bg="beige" fg="Black"></style>Context Used!""")

style = Style.from_dict(
    {
        "": "Peru",
        'dialog': 'bg:Black',
        'dialog frame.label': 'bg:Black #000000',
        'dialog.body': 'bg:Black Peru',
        'dialog shadow': 'bg: Black',
        'button': 'bg: Black'
    }
)


warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")

with open("config.json", 'r') as f:
    config = json.load(f)

session_ended = False

load_dotenv()

memory = []

message_dialog(
    title='WELCOME TO',
    text=HTML(r"""

                                    ⠀⠀⠀⠀⠀⠀⠀⢀⡖⣲⣄⣀⣀⣔⡲⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
                                    ⠀⠀⠀⠀⠀⠀⠀⠈⡎⠁⠀⠀⠀⠀⠹⡏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
                                    ⠀⠀⠀⠀⠀⠀⠀⣴⠃⠘⣣⣶⣶⠃⠀⢳⠀⠀⡴⠶⢤⠀⢀⡴⠶⣦⢠⠶⠶⣦⣴⠶⢦⠀⠀⢠⠶⢦⣠⠶⠶⣦⠀⣠⠶⠶⠶⠶⣄⠀⣠⠶⠶⠶⠶⣄⠀⢠⠶⠶⠶⠶⣄⠀⢠⠶⠶⠶⠶⠶⡄⠀⠀⠀
                                    ⠀⠀⠀⠀⠀⠀⢠⠟⠷⢦⠍⠉⠉⠤⠶⡇⠀⠀⡇⠀⠈⠷⠞⠁⠀⣽⠘⡆⢰⠋⣿⠀⠈⠳⡀⢸⠀⢸⠙⡆⠠⡏⢰⠋⣠⠖⠒⣦⣼⣶⠁⢠⡶⠶⢤⠈⣷⣾⠀⣴⠒⢦⠈⢣⣸⠀⣰⣒⠒⠒⠁⠀⠀⠀
                                    ⠀⠀⠀⠀⠀⡰⠋⠀⣄⠀⠀⡀⠀⠀⠀⢳⡀⠀⡇⠀⡶⣄⣠⢶⠀⣾⠀⡇⢸⠀⣿⠀⢰⣆⠹⣽⠂⢸⠀⡇⠀⡇⢸⠰⣿⠀⠀⠀⠀⢸⠀⢸⠀⠀⢸⠀⣿⣿⠀⡇⠀⢸⠀⢸⢻⠀⢈⣉⣉⡇⠀⠀⠀⠀
                                    ⠀⠀⠀⢠⠞⠀⣸⢿⣻⡀⠀⢳⡴⠀⠀⡿⢷⣤⡇⠀⡇⠈⠁⣸⠀⢿⣀⡇⢸⣀⣿⠀⢸⠈⢧⠈⠀⢸⢀⡇⠀⣇⠺⡀⠻⠤⠤⠖⢲⠾⡀⠘⠦⠤⠞⢀⡿⢿⠀⠧⠤⠞⢀⡸⢸⠄⠸⠥⠤⠤⡀⠀⠀⠀
                                    ⠀⠀⠀⠘⣤⢸⣥⣤⡏⣧⣤⣼⡇⣤⣼⣥⣤⡟⠧⠤⠇⠀⠀⠳⠤⠼⠻⠤⠤⠟⠻⠤⠼⠀⠀⠳⠤⠼⠸⠤⠤⠞⠀⠙⠦⠤⠤⠤⠋⠀⠙⠦⠤⠤⠤⠎⠀⠸⠤⠤⠤⠤⠞⠀⠸⠤⠤⠤⠤⠤⠃⠀⠀⠀
                                    ⠀⠀⠀⠀⠀⠉⠉⠉⠈⠉⠉⠉⠉⠉⠉⠉⠉⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
                                                                                
"""),
style=style).run()


system_prompt = f""" 
SYSTEM PROMPT

You are a decisive, task-oriented coding assistant. Your job is to get things done using your tools — not to explain how the user could do them themselves.

CORE PRINCIPLES

1. Search before writing code. When asked to write, fix, or modify code, always search the web first to understand how the code should be written. Do not rely on your own knowledge for implementation details — use web_search to find current, correct approaches, then write the code based on what you find.

2. Prefer tools over text. If a task can be accomplished by running a command, searching the web, or writing a file, do it. Only answer with plain text when the question requires no external action (e.g. factual questions like "what is 2+2" or "capital of France").

3. Always inspect before modifying. Before editing or creating any file, read its current contents with run_command (e.g. cat <path>). Never assume what a file contains.

4. Never give manual instructions. If you can execute the action yourself, do not tell the user how to do it step by step. Execute it.

5. Stay concise. Short, direct responses. No filler, no apologies, no hedging.

TOOLS

- run_command(command) — run a shell command. Use it to read files (cat), inspect directories, run scripts, etc.
- web_search(query) — search the web. Use it to learn how to implement something before writing code, and to find current approaches.
- write_file(path, content) — write or overwrite a file. Use it when the user asks you to create or modify a file.
- finish(finalAnswer) — signal that the task is complete. Call this at the end of every turn where you have accomplished what was asked. Do not call it on turns where you only made tool calls and still need to report results.

FILE NAMING

Use underscores or hyphens instead of spaces in file names. Spaces cause issues with shell commands.

WORKING DIRECTORY

You are currently in: {os.getcwd()}

Remember which directories you switch to during the conversation — you will not be told the working directory again.

DATE

Current date: {datetime.now()}

HARD RULES

- Always use valid JSON when constructing tool arguments.
- When a user asks "what is in a file", that means: read the file contents and report them.
- When a user asks you to modify or create a file, use write_file — do not explain what you would do, just do it.
- Call tools. Do not finish tasks by only describing them.

"""
memory.append({"role": "system", "content": system_prompt})

client = OpenAI(
    base_url = config.get("base_url", "http://localhost:11434/v1"),
    api_key = config.get("api_key", "ollama")
)

model = config.get("model", "qwen2.5:1.5b")

def run_command(command):
    result_yes_no=yes_no_dialog(
        style=style,
        title='Yes/No dialog example',
        text=HTML(f"""
<style bg="Beige" fg="Black">The command {command} will be called</style>
    
""")).run()
    if result_yes_no == True:
        result = subprocess.run(command, shell = True, capture_output = True, text = True)
        return json.dumps({
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        })
    elif result_yes_no == False:
        return "You have not been allowed to call this command inform the user about this and tell them if they wish to run the command they will have to approve the command. If they tell you try again call the command again if they approve it on their end it will work."


def web_search(query):
    print(HTML(f"""
<style bg="Beige" fg="Black">  The query {query} was called</style>

"""))

    api_key = os.environ.get("TAVILY_API_KEY")
    web_results = requests.post(
        "https://api.tavily.com/search",
        json = {"api_key":api_key, "query": query}
    )
    return web_results.json()

def web_search_trimmer(webResults):

    query_results = []

    for r in webResults["results"]:
        content = r["content"]
        title = r["title"]  
        url = r["url"]
        content = content[:200]
        query_results.append({"content": content, "url": url, "title": title})
    
    return query_results

def write_file(path, content):
    result_yes_no = yes_no_dialog(
        style=style,
        title='Yes/No dialog example',
        text=HTML(f"""
<style bg="Beige" fg="Black">The file {path} will be edited with this code {content}</style>

""")).run()

    if result_yes_no == True:
        try:
            with open(path, 'w') as f:
               f.write(content)
            return {"success": True, "resolved_path": path}
        except Exception as e:
            return {"error": str(e)}
    elif result_yes_no == False:
        return "You have not been allowed to edit this file explain to the user the reason behind editing the file and then ask them to approve it next time. If they tell you try again call the command again if they approve it on their end it will work."

tools = [
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "lets you run a shell command in the terminal",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "a viable terminal command"
                    }
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "allows you to search the web",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "what you want to search about"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "finish",
            "description": "this tool signals the system that you have achived the goal of the prompt, this must be called at the end of evey turn until called the turn will not end. Please do not call on turns where there are no tool calls this menas reponses can take longer and wastes time.",
            "parameters": {
                "type": "object",
                "properties": {
                    "finalAnswer": {
                        "type": "string",
                        "description": "The final answer or summary of what was accomplished"
                    }
                },
                "required": ["finalAnswer"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write content to a file. Use this to create new files or overwrite existing ones.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path":{
                        "type": "string",
                        "description": "The path where the file should be written. This should be an absolute path or relative to the current working directory."
                    },
                    "content": {
                        "type": "string",
                        "description": "The content to write to the file."
                    }
                },
                "required": ["path", "content"]
            }
        }
    }
]

used_old_session = False

while session_ended == False:
    try:
        prompt = pt_prompt("""
    
>>> """, style=style, cursor=CursorShape.BLINKING_UNDERLINE, completer=SlashCompleter)

        if prompt == '/quit':
            session_ended = True
            break
        elif prompt == '/memory':
            now = datetime.now().strftime("%Y%m%d_%H%M%S")
            title = f"minicode_{now}.md"
            clean_memory = []
            for msg in memory:
                clean_msg = {
                    "role": msg.get("role", ""),
                    "content": msg.get("content", "")
                }
                if "tool_calls" in msg and msg["tool_calls"]:
                    clean_msg["tool_calls"] = str(msg["tool_calls"])
                if "tool_call_id" in msg:
                    clean_msg["tool_call_id"] = msg.get("tool_call_id", "")
                clean_memory.append(clean_msg)
            with open(title, 'w') as z:
                json.dump(clean_memory,z, indent = 2)
            memory_retrive = pt_prompt("type in the .md file name ")
            z = open(memory_retrive, 'r')
            loaded_memory = json.load(z)
            memory.clear()
            # Filter out tool_calls when loading - can't reconstruct them properly
            for msg in loaded_memory:
                clean_msg = {
                    "role": msg.get("role", ""),
                    "content": msg.get("content", "")
                }
                if msg.get("role") == "tool":
                    clean_msg["tool_call_id"] = msg.get("tool_call_id", "")
                memory.append(clean_msg)
            used_old_session = True
# use memory_retrive as the name of the session
            continue

    except KeyboardInterrupt:
        # Sanitize memory for JSON serialization before saving
        clean_memory = []
        for msg in memory:
            clean_msg = {
                "role": msg.get("role", ""),
                "content": msg.get("content", "")
            }
            if "tool_calls" in msg and msg["tool_calls"]:
                clean_msg["tool_calls"] = str(msg["tool_calls"])  # Convert to string to avoid serialization issues
            if "tool_call_id" in msg:
                clean_msg["tool_call_id"] = msg["tool_call_id"]
            clean_memory.append(clean_msg)
        if used_old_session == True:
            with open(memory_retrive, 'w') as z:
                json.dump(clean_memory,z, indent = 2)
        else:
            now = datetime.now().strftime("%Y%m%d_%H%M%S")
            title = f"minicode_{now}.md"
            with open(title, 'w') as z:
                json.dump(clean_memory,z, indent = 2)
        sys.exit()
    
    memory.append({"role": "user", "content": prompt})

    agent_finished = False


    while agent_finished == False:

        response = client.chat.completions.create(
            model = model,
            messages = memory,
            tools = tools,
            stream = True
        )

        full_content = ""
        full_thinking = ""
        full_tool_calls = []

        for chunk in response:
            choice = chunk.choices[0]
            delta = choice.delta

            if delta.content:
                content_printed=True
                if c_or_t==None or c_or_t=='t':
                    print(HTML(f"<Peru><i>\n{escape(delta.content)}</i></Peru>"), end="", flush=True)
                    c_or_t='c'
                else:
                    print(HTML(f"<Peru><i>{escape(delta.content)}</i></Peru>"), end="", flush=True)
                    full_content += delta.content
                    c_or_t='c'

            if hasattr(delta, 'reasoning') and delta.reasoning:
                full_thinking += delta.reasoning
                if c_or_t == None or c_or_t == 'c':
                    print(HTML(f"<SlateGrey><i>\n{escape(delta.reasoning)}</i></SlateGrey>"), end="", flush=True)
                    c_or_t='t'
                else:
                    print(HTML(f"<SlateGrey><i>{escape(delta.reasoning)}</i></SlateGrey>"), end="", flush=True)
                    c_or_t='t'
                    
            if delta.tool_calls:
                for tc in delta.tool_calls:
                    idx = getattr(tc, 'index', 0) or 0
                    while len(full_tool_calls) <= idx:
                        full_tool_calls.append(None)
                    if full_tool_calls[idx] is None:
                        if hasattr(tc, 'function'):
                            full_tool_calls[idx] = type(tc)(index=idx, function=tc.function)
                        else:
                            full_tool_calls[idx] = type(tc)(index=idx)
                    else:
                        if tc.function:
                            if tc.function.name:
                                full_tool_calls[idx].function.name = tc.function.name
                            if tc.function.arguments:
                                full_tool_calls[idx].function.arguments += tc.function.arguments

            if choice.finish_reason:
                print()
                break

        reply = ChatCompletionMessage(role="assistant", content=full_content or None)
        if full_tool_calls:
            reply.tool_calls = full_tool_calls

        memory.append({"role": "assistant", "content": full_content or "", "tool_calls": full_tool_calls if full_tool_calls else None})

        if reply.tool_calls:
            for tool_call in reply.tool_calls:
                name = tool_call.function.name
                try:
                    args = json.loads(tool_call.function.arguments)
                except (json.JSONDecodeError, TypeError):
                    args = {}

                if name == "run_command":
                    output = run_command(**args)
                    memory.append({"role": "tool", "tool_call_id": str(tool_call.id), "content": output})

                elif name == "web_search":
                    output = web_search(**args)
                    output = web_search_trimmer(output)
                    output = json.dumps(output)
                    memory.append({"role": "tool", "tool_call_id": str(tool_call.id), "content": output})

                elif name == "finish":
                    final_answer = args.get("finalAnswer", "")
                    print(HTML(f'<style fg="Moccasin">\n{escape(final_answer)}</style>'))
                    agent_finished = True
                    memory.append({"role": "tool", "tool_call_id": str(tool_call.id), "content": "task completed successfully"})
                    break
                elif name == "write_file":
                    success = write_file(**args)
                    memory.append({"role": "tool", "tool_call_id": str(tool_call.id), "content": json.dumps({"success": success["success"], "path": success["resolved_path"]})})
                
        else:
            
            agent_finished = True

    if reply.content:
        if content_printed == True:
            continue
        else:
            print(HTML(f'<style fg="Moccasin">\n {escape(reply.content)}</style>'))


sys.exit()