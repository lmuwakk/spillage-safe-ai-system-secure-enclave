# AI Agent Web Interface - Setup & Instructions

## 1. Environment Setup

Directories should be as follows:

`agent_sandbox/
├── WebUI
   ├── Text_Files
   │   ├── README.md
   │   ├── [any other text files you need]
   │   └── vision_explanation.md
   ├── agent_tools.py
   ├── index.html
   ├── main.py
   ├── main_backup.py
   ├── memory.json
   ├── memory_manager.py
   ├── memory_schema.json
   ├── script.js
   └── style.css`

This will require some change down the road to harden the system against attacks, such as moving most of the scripts and such *away* from the WebUI directory in order to remove direct access to the LLM from an attacker.

### Install Dependencies
Create a virtual environment (recommended) and install FastAPI, Uvicorn, Ollama, Pydantic, Python-multipart, and UWebSocket:

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install required Python packages
pip install fastapi uvicorn python-multipart ollama ws pydantic
```

### External Dependencies
This project relies on **Ollama** for local AI inference. 
1. If you don't have Ollama installed, download and install it from: https://ollama.com or use the CLI command:
   ```bash 
   curl -fsSL https://ollama.com/install.sh | sh
   ```
2. Pull the model specified in `main.py` (default: `qwen3.6:35b`) or update `MODEL` in `main.py`:
   ```bash
   ollama pull qwen3.6:35b
   ```
   *Notes: You can change `MODEL = "qwen3.6:35b"` in `main.py` to any other model available on your system (e.g., `llama3`, `mistral`, etc.) provided they are installed. 
This may cause tool errors if you do not ensure that the `tools` and `vision` tags appear on the `ollama show [model]` command.*

## 2. Running the Interface

### Start the Backend Server
Run the FastAPI application using Uvicorn. This will serve the backend API and also handle static files for the frontend if configured to do so (though standard setup requires a small tweak for production, this works perfectly for local dev and testing):

   ```bash
   uvicorn main:app --reload [options --port xxxx --host x.x.x.x]
   ```

### Accessing the Frontend
**Integrated FastAPI Static Files**
To serve the frontend automatically from FastAPI, run main.py in the CLI
   ```bash
   python main.py
   ```

## 3. Using the Interface

1. **Chat**: Type a natural language prompt in the input box and ollama and the server will handle the rest.
2. **Tools**: The backend will process tool calls (like `write_file`, `run_command`) silently and update the conversation history securely within the `agent_sandbox` directory.
3. **Logs**: The right side of the screen has an System Activity Monitor which shows the LLM's thought process as well as tool usage.

## 4. Security Notes

- **Sandboxing**: The backend restricts all file operations (`read_file`, `write_file`) to the `~/agent_sandbox` directory using strict path validation to prevent directory traversal attacks.
- **Command Execution**: `run_command` includes a 30-second timeout to prevent hanging processes. Use with caution as it executes on your local host. This will need further enhancement.
- **URL Fetching**: `fetch_url` is still a prototype without hard security guardrails. This will need security enhancement.