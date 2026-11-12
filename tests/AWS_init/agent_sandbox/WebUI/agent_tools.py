"""
agent_tools.py - File containing all agent tools

This file exists solely to keep tools organized and ensure that
the main.py file does not get too crowded. Notably absent is the 
`remember` function, as that will stay in the main file, or perhaps get
its own file (memory_manager.py) later.

This file contains all of the tools that the agent may use, including:
- Command execution
- Reading files (per ALLOWED_EXTENSIONS)
- Writing files 
- Image analysis 
- URL fetching for internet data
"""

#-=-=-=-=-=-=-=-=-= Imports =-=-=-=-=-=-=-=-=-#
# Standard Python Libs
import os
import subprocess
from pathlib import Path
import base64
import ssl
import urllib.request
import urllib.error

# Third Party Libs
import ollama
import trafilatura
from ddgs import DDGS

#-=-=-=-=-=-=-=-=-= Variables =-=-=-=-=-=-=-=-=-#
SANDBOX = Path.home() / "agent_sandbox" # Path for sandbox

#-=-=-=-=-=-=-=-=-= Tools =-=-=-=-=-=-=-=-=-#

# Write tool
def write_file(filename: str, content: str) -> str:
    """
    Tool to write files to the sandbox.
    Checks to ensure that files are being written inside
    the sandbox, returns an error if they are not.

    Params:
        filename (str): Name of the file relative to the sandbox
        content (str): Content of the file to be written to the sandbox
    """
    path = (SANDBOX / filename).resolve()
    if not path.is_relative_to(SANDBOX.resolve()):
        return "Error: path is outside sandbox"
    path.write_text(content)
    return f"Wrote {len(content)} characters to {path}"

# Read tool
def read_file(filename: str) -> str:
    """
    Description:
    Short `how`:
    Params:
    """
    ALLOWED_EXTENSIONS = {".txt", ".py", ".md", ".html", ".css", ".js", ".json"}
    path = (SANDBOX / filename).resolve()
    if not path.is_relative_to(SANDBOX.resolve()):
        return "Error: path is outside sandbox."
    if path.suffix not in ALLOWED_EXTENSIONS:
        return f"Error: {path.suffix} files can be read."
    if not path.exists():
        return f"Error: {filename} does not exist."
    return path.read_text()

# Command tool
def run_command(command: str) -> str:
    """
    Description:
    Short `how`:
    Params:
    """
    try:
        result = subprocess.run(
            ['bash', '-c', command],
            capture_output=True,
            text=True,
            timeout=30
        )
        output_parts = []
        if result.stdout:
            output_parts.append(f"[STDOUT]\n{result.stdout}")
        if result.stderr:
            output_parts.append(f"[STDERR]\n{result.stderr}")

        stdout_content = "\n".join(output_parts)
        
        if not stdout_content:
            stdout_content = "Command executed successfully (no output)."

        return f"Execution Result (Return Code: {result.returncode}):\n{stdout_content}"
    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 30 seconds."
    except Exception as e:
        return f"Fatal error during execution: {str(e)}"

# Web Search tool 
def fetch_url(url: str) -> str:
    """
    Description:
    Short `how`:
    Params:
    """
    if not url.startswith(('http://', 'https://')):
        return "Error: Only http and https URLs are allowed."
    try:
        context = ssl.create_default_context()
        req = urllib.request.Request(url, headers={'User-Agent': 'AI-Agent/1.0'})
        with urllib.request.urlopen(req, timeout=15, context=context) as response:
            ctype = response.headers.get('Content-Type', 'unknown')
            content = response.read().decode('utf-8', errors='ignore')

            # Pull out the readable article text instead of raw HTML
            if 'html' in ctype:
                content = trafilatura.extract(content) or content

            MAX_CHARS = 6000
            if len(content) > MAX_CHARS:
                content = content[:MAX_CHARS] + "\n...[TRUNCATED]"

            return wrap_untrusted(f"[CONTENT TYPE: {ctype}]\n\n{content}")
    except urllib.error.HTTPError as e:
        return f"HTTP Error: {e.code} - {e.reason}"
    except urllib.error.URLError as e:
        return f"URL Error: Failed to reach host. Reason: {str(e.reason)}"
    except Exception as e:
        return f"Fatal error fetching URL: {str(e)}"

# Image Analysis tool
def analyze_image(file_path: str) -> str:
    """  
    Image Analysis Tool
    This is assuming said model supports image analysis, make sure to check this 
    using `ollama show [model name]` and check for vision capabilities.

    Reads a local image file, encodes it for an LLM (Qwen),
    and returns the AI's analysis of that image. It does this
    by reading the file, encoding it to base64, and sending 
    it to the AI model via Ollama. 

    Params:
    - file_path (str): Absolute path to image file; NOT relative to the sandbox.
    """
    
    # 1. Check if the file exists to avoid runtime errors
    if not os.path.exists(file_path):
        return f"Error: Image file '{file_path}' does not exist."

    # 2. Read the image content in binary mode
    try:
        with open(file_path, 'rb') as img_file:
            raw_bytes = img_file.read()
    except IOError as e:
        return f"Error reading file: {str(e)}"

    # 3. Encode the binary data to base64 string format
    # LLMs typically communicate via text, so images must be encoded
    b64_string = base64.b64encode(raw_bytes).decode('utf-8')

    # 4. Define the model to use for visual analysis
    # Note: Ollama requires a specific Vision-capable model (e.g., qwen2.5vl, llava)
    # The standard 'qwen3.6:35b' might not support images natively in all versions.
    VISION_MODEL = "qwen3.6:35b" 

    try:
        # 5. Construct the prompt for the vision model
        messages = [
            {
                "role": "user",
                "content": "What is depicted in this image? Describe the details.",
                "images": [b64_string] # Pass the encoded string to the 'images' field
            }
        ]

        # 6. Send the request to Ollama and retrieve the response
        # timeout=60 gives enough time for larger images to process
        response = ollama.chat(model=VISION_MODEL, messages=messages, stream=False)

        # 7. Return the generated text analysis
        return response['message']['content']

    except ollama.ResponseError as e:
        return f"Error analyzing image with Ollama (Status {e.status_code}): {e.error}"
    except Exception as e:
        return f"Fatal error during image analysis: {str(e)}"

# Web Search tool
def web_search(query: str, max_results: int = 5) -> str:
    try:
        results = DDGS().text(query, max_results=int(max_results))
    except Exception as e:
        return f"Search error: {e}"
    if not results:
        return "No results found. Try different keywords."
    return "\n\n".join(
        f"[{i}] {r['title']}\n{r['href']}\n{r['body']}"
        for i, r in enumerate(results, 1)
        )
