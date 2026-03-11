from rich.console import Console
from rich.panel import Panel
from rich.text import Text
import json

console = Console()

def format_message_content(message):
    """Convert message content to displayable string"""
    parts = []
    tool_calls_processed = False
    
    # Handle main content
    if isinstance(message.content, str):
        parts.append(message.content)
    elif isinstance(message.content, list):
        # Handle complex content like tool calls (Anthropic format)
        for item in message.content:
            if item.get('type') == 'text':
                parts.append(item['text'])
            elif item.get('type') == 'tool_use':
                parts.append(f"\n🔧 Tool Call: {item['name']}")
                parts.append(f"   Args: {json.dumps(item['input'], indent=2)}")
                parts.append(f"   ID: {item.get('id', 'N/A')}")
                tool_calls_processed = True
    else:
        parts.append(str(message.content))
    
    # Handle tool calls attached to the message (OpenAI format) - only if not already processed
    if not tool_calls_processed and hasattr(message, 'tool_calls') and message.tool_calls:
        for tool_call in message.tool_calls:
            parts.append(f"\n🔧 Tool Call: {tool_call['name']}")
            parts.append(f"   Args: {json.dumps(tool_call['args'], indent=2)}")
            parts.append(f"   ID: {tool_call['id']}")
    
    return "\n".join(parts)


def format_messages(messages):
    """Format and display a list of messages with Rich formatting"""
    for m in messages:
        msg_type = m.__class__.__name__.replace('Message', '')
        content = format_message_content(m)

        if msg_type == 'Human':
            console.print(Panel(content, title="🧑 Human", border_style="blue"))
        elif msg_type == 'Ai':
            console.print(Panel(content, title="🤖 Assistant", border_style="green"))
        elif msg_type == 'Tool':
            console.print(Panel(content, title="🔧 Tool Output", border_style="yellow"))
        else:
            console.print(Panel(content, title=f"📝 {msg_type}", border_style="white"))


def format_message(messages):
    """Alias for format_messages for backward compatibility"""
    return format_messages(messages)


def show_prompt(prompt_text: str, title: str = "Prompt", border_style: str = "blue"):
    """
    Display a prompt with rich formatting and XML tag highlighting.
    
    Args:
        prompt_text: The prompt string to display
        title: Title for the panel (default: "Prompt")
        border_style: Border color style (default: "blue")
    """
    # Create a formatted display of the prompt
    formatted_text = Text(prompt_text)
    formatted_text.highlight_regex(r'<[^>]+>', style="bold blue")  # Highlight XML tags
    formatted_text.highlight_regex(r'##[^#\n]+', style="bold magenta")  # Highlight headers
    formatted_text.highlight_regex(r'###[^#\n]+', style="bold cyan")  # Highlight sub-headers

    # Display in a panel for better presentation
    console.print(Panel(
        formatted_text, 
        title=f"[bold green]{title}[/bold green]",
        border_style=border_style,
        padding=(1, 2)
    ))

# Windows subprocess patch for Jupyter
# This patches subprocess.Popen to avoid "UnsupportedOperation: fileno" errors
# when running in environments like Jupyter that capture stdout/stderr.
import sys
import subprocess
import os

if sys.platform == 'win32':
    # Store original Popen to avoid infinite recursion if reloaded
    if not hasattr(subprocess, '_original_Popen'):
        subprocess._original_Popen = subprocess.Popen

    class SafePopen(subprocess._original_Popen):
        def __init__(self, *args, **kwargs):
            # Check stderr
            if 'stderr' in kwargs:
                stderr = kwargs['stderr']
                # If stderr is a stream but not a valid OS handle (like Jupyter's OutStream), fileno() fails.
                # We check this and fallback to DEVNULL.
                if stderr is not None and stderr != subprocess.PIPE and stderr != subprocess.STDOUT and stderr != subprocess.DEVNULL:
                    try:
                        stderr.fileno()
                    except Exception:
                        # Fallback to DEVNULL if fileno() is not supported (e.g. Jupyter)
                        kwargs['stderr'] = subprocess.DEVNULL
            
            # Check stdout
            if 'stdout' in kwargs:
                stdout = kwargs['stdout']
                if stdout is not None and stdout != subprocess.PIPE and stdout != subprocess.DEVNULL:
                    try:
                        stdout.fileno()
                    except Exception:
                        kwargs['stdout'] = subprocess.DEVNULL
            
            # Check stdin
            if 'stdin' in kwargs:
                stdin = kwargs['stdin']
                if stdin is not None and stdin != subprocess.PIPE and stdin != subprocess.DEVNULL:
                    try:
                        stdin.fileno()
                    except Exception:
                        kwargs['stdin'] = subprocess.DEVNULL

            super().__init__(*args, **kwargs)

    subprocess.Popen = SafePopen