#-=-=-=-=-=-=-=-=-= Imports =-=-=-=-=-=-=-=-=-#
import subprocess
import ollama
from pathlib import Path
import urllib.request
import ssl

#-=-=-=-=-=-=-=-=-= Model and venv info =-=-=-=-=-=-=-=-=-#

MODEL = "qwen3.6:35b" # Change to whatever model you're trying to prompt
SANDBOX = Path.home() / "agent_sandbox"
SANDBOX.mkdir(exist_ok=True)
DIM, RESET = "\033[2m", "\033[0m"
user_prompt = input("Enter prompt: ")
total_time = 0
#-=-=-=-=-=-=-=-=-= Tools =-=-=-=-=-=-=-=-=-#

def write_file(filename: str, content: str) -> str:
	"""
	Function to allow agent to write files
	
	filename: string, name of the file including suffix
	content: string the message or content you wish to add to the file
	"""

	# Ensure path is within sandbox to assure no spillage.
	path = (SANDBOX / filename).resolve()
	if not path.is_relative_to(SANDBOX.resolve()):
		return "Error: path is outside sandbox"
	
	path.write_text(content)
	return f"Wrote {len(content)} characters to {path}"

def read_file(filename: str) -> str:
	"""
	Function to allow the agent to read files from within the agent_sandbox directory

	filename: string, name of the file including suffix

	"""
	# Ensure path is within sandbox to assure no spillage.
	ALLOWED_EXTENSIONS = {".txt", ".py", ".md", ".html", ".js", ".css"}

	path = (SANDBOX / filename).resolve()
	if not path.is_relative_to(SANDBOX.resolve()):
		return "Error: path is outside sandbox."
	if path.suffix not in ALLOWED_EXTENSIONS:
		return f"Error: {path.suffix} files can be read."
	if not path.exists():
		return "Error: {filename} does not exist."

	return path.read_text()

def run_command(command: str) -> str:
    """
    Executes a terminal command using a bash subprocess.
    Includes safety mechanisms like timeouts to prevent hanging agents.
    
    Args:
        command (str): The shell command string to execute.
        
    Returns:
        str: The output of the command execution.
    """
    try:
        # Execute command via bash -c to support pipes and redirections if necessary.
        # We use list format for args to avoid shell injection vulnerabilities in argument passing,
        # though we still pass the command string which relies on local trust.
        result = subprocess.run(
            ['bash', '-c', command],
            capture_output=True,
            text=True,
            timeout=30  # Safety: Kill long-running processes after 30s
        )

        output_parts = []
        if result.stdout:
            output_parts.append(f"[STDOUT]\n{result.stdout}")
        if result.stderr:
            output_parts.append(f"[STDERR]\n{result.stderr}")

        stdout_content = "\n".join(output_parts)
        
        # Clean up empty output messages for readability
        if not stdout_content:
            stdout_content = "Command executed successfully (no output)."

        return f"Execution Result (Return Code: {result.returncode}):\n{stdout_content}"

    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 30 seconds."
    except Exception as e:
        return f"Fatal error during execution: {str(e)}"

def fetch_url(url: str) -> str:
    """
    Fetches content from a given URL securely.
    
    Args:
        url (str): The full HTTP/HTTPS URL to fetch.
        
    Returns:
        str: The fetched content, truncated if too large for context.
    """
    # Basic security check
    if not url.startswith(('http://', 'https://')):
        return "Error: Only http and https URLs are allowed."

    try:
        # Create an unverified SSL context for demo purposes (in production, verify certs)
        context = ssl.create_default_context()
        
        req = urllib.request.Request(url, headers={'User-Agent': 'AI-Agent/1.0'})
        
        with urllib.request.urlopen(req, timeout=15, context=context) as response:
            content = response.read().decode('utf-8', errors='ignore')
            
            # Truncate if content is too long to prevent context overflow
            MAX_CHARS = 4000
            if len(content) > MAX_CHARS:
                return f"[CONTENT TYPE: {response.headers.get('Content-Type', 'unknown')}]\n\n{content[:MAX_CHARS//2]} ... [TRUNCATED] ... {content[-MAX_CHARS//2:]}"

            return f"[CONTENT TYPE: {response.headers.get('Content-Type', 'unknown')}] \n\n{content}"
            
    except urllib.error.HTTPError as e:
        return f"HTTP Error: {e.code} - {e.reason}"
    except urllib.error.URLError as e:
        return f"URL Error: Failed to reach host. Reason: {str(e.reason)}"
    except Exception as e:
        return f"Fatal error fetching URL: {str(e)}"

def ask_user():
	"""
	Function to allow the LLM to ask the user for clarification
	or additional input, permissions, or human intervention. This will
	allow for more focused thoughts and hopefully assist in less hallucination

	"""

TOOLS = {"write_file": write_file, "read_file": read_file, "run_command": run_command, "fetch_url": fetch_url}


#-=-=-=-=-=-=-=-=-= Message =-=-=-=-=-=-=-=-=-#
messages = [{
	"role":"user",
	"content": f"{user_prompt}",
}]

#-=-=-=-=-=-=-=-=-= Logic =-=-=-=-=-=-=-=-=-#

def run_turn():
	"""
	Stream the models response showing live thinking.
	For each chunk in the stream, check if the model is thinking. 
	If it is, print the thinking out to the terminal, and add it to the message content,
	"""
	# Vars
	thinking, content, tool_calls = "", "", []
	in_thinking = False
	final = None

	# Stream of thoughts
	stream = ollama.chat(
		model=MODEL,
		messages=messages,
		tools=list(TOOLS.values()),
		think=True,
		stream=True,
		options={"num_ctx": 20000},
	)

	# Chunks within stream of thoughts
	for chunk in stream:
		if chunk.done:
			final = chunk
		msg = chunk.message
		if msg.thinking:
			if not in_thinking:
				print(f"{DIM}[thinking] ", end="")
				in_thinking = True
			print(msg.thinking, end="", flush=True)
			thinking += msg.thinking
		if msg.content:
			if in_thinking:
				print(f"{RESET}\n")
				in_thinking = False
			print(msg.content, end="", flush=True)
			content += msg.content
		if msg.tool_calls:
			tool_calls.extend(msg.tool_calls)
	if in_thinking:
		print(RESET)


	def print_metrics(final, tool_calls):
		"""Print timing stats from the last streamed chunk. Durations are in nanoseconds."""
		if final is None or not final.eval_duration:
			print("\n--- VERBOSE METRICS --- (not available)")
			return
		print("\n--- VERBOSE METRICS ---")
		if tool_calls:
			print(f"Tools requested: {', '.join(c.function.name for c in tool_calls)}")
		print(f"Total duration: {final.total_duration / 1e9:.2f}s")
		print(f"Load duration: {final.load_duration / 1e9:.2f}s")
		print(f"Prompt tokens evaluated: {final.prompt_eval_count}")
		print(f"Prompt evaluation time: {final.prompt_eval_duration / 1e9:.2f}s")
		print(f"Output tokens generated: {final.eval_count}")
		print(f"Generation time: {final.eval_duration / 1e9:.2f}s")
		print(f"Evaluation rate: {final.eval_count / final.eval_duration * 1e9:.2f} tokens/s\n")
		print(f"Done reason: {final.done_reason}")

	print_metrics(final, tool_calls)

	# Save the full turn so the model can keep its context
	entry = {"role": "assistant", "content": content, "thinking": thinking}
	if tool_calls:
		entry["tool_calls"] = tool_calls
	messages.append(entry)
	return content, tool_calls


if __name__ == "__main__":
	while True:
		content, tool_calls = run_turn()

		if not tool_calls:
			print()
			break

		for call in tool_calls:
			name, args = call.function.name, call.function.arguments
			print(f"\n-> Tool call: {name}({', '.join(args)})") # Mark progress
			func = TOOLS.get(name)
			if func:
				try:
					result = func(**args) 
					messages.append({"role": "tool", "tool_name": name, "content": result})
				except Exception as e:
					print(f"Error executing tool {name}: {e}")
					messages.append({"role": "tool", "tool_name": name, "content": f"Tool execution error: {str(e)}"})
			else:
				err_msg = f"Unknown or missing tool: {name}"
				print(f"Warning: {err_msg}")
				messages.append({"role": "tool", "tool_name": name, "content": err_msg})
