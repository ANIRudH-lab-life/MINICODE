from prompt_toolkit import prompt
from prompt_toolkit.formatted_text import HTML
import sys

def bottom_toolbar():
    return HTML("""This is a <b><style bg="beige">Toolbar</style></b>!""")

text = prompt("> ", bottom_toolbar=bottom_toolbar)
while text != 'red':
    text = prompt("> ", bottom_toolbar=bottom_toolbar)
    print(f"You said: {text}")
sys.exit()