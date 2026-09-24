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


warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")

with open("config.json", 'r') as f:
    config = json.load(f)

session_ended = False

load_dotenv()

memory = []

print(r"""


         .......               .....         
       //.....\\ .........  //....:\       __  __ ___ _  _ ___ ___ ___  ___  ___ 
       `::....\\./.......\\///....::\      |  \/  |_ _| \| |_ _|  _/ _ \|   \| __|
      `::`/.##-::::::::::::::-`#.\`::`     | |\/| || || .` || || || (_) | |) | _| 
      `::`\//.::::::::::::::::\\.//::`     |_|  |_|___|_|\_|___|___\___/|___/|___|
       `::\.::::::::::::::::::::..::`       
       `-::::::::::::::::::::::::::-`       
      `/:::::::: :::::::::: ::::::::\`      
      ``:::::::\./...==...\./:::::::``      
      ``::::::=.....`/.`/....=::::::``      
      ``:::::::`/###`` ``##\``::::::``      
      `\::::::``####\../####``::::::``      
       \\:::::`\\##########//`::::::/`      
        \\:::::\\..........//:::::-//       
         \\-::::\..........:::::://         
          .\\..::::::::::::::..//           
             ..\\..........//..             
                ............        
        
                                            
                                            

""")

system_prompt = f""" 

### SYSTEM PROMPT

You are a decisive, task-oriented coding assistant. 

#### OPERATIONAL RULES:
1. **Tool Usage:** When a task requires running a terminal command or searching the web, call the appropriate tool (`run_command` or `web_search`) immediately. ALWAYS
2. **Direct Text Answers:** If a task can be answered directly using your existing knowledge without external actions, respond directly with concise text. This does not include making files or doing coding tasks these are wuestions such as 2+2 or what is the capital of france.
3. **No Direct Instructions:** Never give the user manual instructions or step-by-step guides for tasks you can execute yourself—execute the actions using your tools instead. ALWAYS
4. **Completion:** When an action-based task is fully accomplished, call the `finish` tool to conclude the turn.
5. **Tone:** Keep all text responses short, direct, and free of conversational filler or unnecessary apologies.
6. **For most coding tasks:** For most coding tasks you will not know how to erite it that is why you have the web search tool use it to learn about how to code the certain problem you are facign and then respond use it appropriatly but do not be afraid to use it.
7. **File Modification:** If the user asks you to modify, fix, or inspect a file, ALWAYS inspect the existing file with run_command before making changes. Never assume the file contents.
8. **How to read a file** If a user asks for the contents of a file use the run_command tool and write the command 'cat [Here add the path to the file]' this will give you the contents of the file
9. **What to do if asked to modify or create a file** If asked to do so make sure to use the write_file tool to edit the file or create it dont give instuction or anything else just use the tool and edit it
10. **NEVER USE SPACES IN FILE NAMES EVER**
11. **ALWAYS USE WORKING JSON** USE WEBSEARCH IF you dont know what it is
12. THINK ABOUT WHAT IS NEEDED DONE, 'what is in a file' means the content of a file
You are currently working in the directory: {os.getcwd()}
this is only at the start you will have to remember which directories you have switched to throughut the conversation.

** STRICT FOR ALL CODING TASKS CALL TOOLS THERE SHOULD BE NO INSTRUCTION OR SAYING FINISH IT YOURSELF YOU MUST FINISH THE TASK AND YOU MUST CALL TOOLS NO INSTRUCTIONS ETC **

You Are on a linux environment


"""
memory.append({"role": "system", "content": system_prompt})

client = OpenAI(
    base_url = config.get("base_url", "http://localhost:11434/v1"),
    api_key = config.get("api_key", "ollama")
)

model = config.get("model", "qwen2.5:1.5b")

def run_command(command):
    print(f"""
The command {command} was called
    
""")
    result = subprocess.run(command, shell = True, capture_output = True, text = True)
    return json.dumps({
        "stdout": result.stdout,
        "stderr": result.stderr,
        "returncode": result.returncode
    })


def web_search(query):
    print(f"""
The query {query} was called

""")
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
    print(f"""
The file {path} was edited with this code {content}

""")
    try:
        with open(path, 'w') as f:
            f.write(content)
        return {"success": True, "resolved_path": path}
    except Exception as e:
        return {"error": str(e)}
    

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
    
>>> """)

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
                print(delta.content, end="", flush=True)
                full_content += delta.content

            if hasattr(delta, 'reasoning') and delta.reasoning:
                full_thinking += delta.reasoning
                print(delta.reasoning, end="", flush=True)

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
                    print("Final Answer:", final_answer)
                    agent_finished = True
                    memory.append({"role": "tool", "tool_call_id": str(tool_call.id), "content": "task completed successfully"})
                    break
                elif name == "write_file":
                    success = write_file(**args)
                    memory.append({"role": "tool", "tool_call_id": str(tool_call.id), "content": json.dumps({"success": success["success"], "path": success["resolved_path"]})})
                
        else:
            
            agent_finished = True

    if reply.content:
        print("\nFinal Response:", reply.content)


sys.exit()