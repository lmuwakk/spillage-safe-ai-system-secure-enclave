# vision.py: Image Analysis Script Explanation

This document provides a line-by-line breakdown of the `vision.py` script, which adds multimodal (image) capabilities to your Qwen agent environment.

---

## 1. Imports and Setup
```python
import os
import base64
import ollama
```
*   **Lines 12-14**: These imports bring in the necessary libraries. 
    *   `os`: Used to interact with the local file system (checking if files exist).
    *   `base64`: Used to encode the image bytes into a string format that Large Language Models (LLMs) can read.
    *   `ollama`: The Python client library used to communicate with the locally running Qwen model.

## 2. Function Definition
```python
def analyze_image(file_path: str) -> str:
```
*   **Line 19**: Defines a function named `analyze_image`. It expects one argument, `file_path` (the location of the image), and promises to return a string containing the AI's description.

## 3. File Existence Check
```python
    if not os.path.exists(file_path):
        return f"Error: Image file '{file_path}' does not exist."
```
*   **Lines 23-24**: Checks if the image actually exists on your disk before attempting to open it, preventing crashes.

## 4. Reading the Image
```python
    try:
        with open(file_path, 'rb') as img_file:
            raw_bytes = img_file.read()
    except IOError as e:
        return f"Error reading file: {str(e)}"
```
*   **Lines 28-31**: Opens the file in `'rb'` (read-binary) mode. 
*   **Line 30**: Reads the raw data of the image into memory (`raw_bytes`).
*   **Lines 32-33**: Handles any errors during reading (e.g., permission denied) and returns an error message instead of crashing the program.

## 5. Base64 Encoding
```python
    b64_string = base64.b64encode(raw_bytes).decode('utf-8')
```
*   **Line 37**: LLMs are text-based models. To send an image, we must convert its raw binary data into a readable text string using Base64 encoding. This is the standard way to transmit images in API requests or JSON payloads.

## 6. Model Selection
```python
    VISION_MODEL = "qwen2.5vl" 
```
*   **Line 41**: Defines the specific Ollama model used for vision tasks. 
*   *Note: Standard text models like `qwen3.6:35b` cannot see images. You must have a vision-language model (like `qwen2.5vl`, `llava`, or `bakllava`) pulled into your local Ollama library for this to work.*

## 7. Message Construction
```python
        messages = [
            {
                "role": "user",
                "content": "What is depicted in this image? Describe the details.",
                "images": [b64_string] 
            }
        ]
```
*   **Lines 43-50**: Formats the request as Ollama expects it.
    *   `role: user`: Identifies this message is from you.
    *   `content`: The text prompt asking the AI what to look for.
    *   `images`: A list containing your Base64 encoded string. This tells Ollama, "Treat this string as an image."

## 8. Execution and Retrieval
```python
        response = ollama.chat(model=VISION_MODEL, messages=messages, stream=False)
        return response['message']['content']
```
*   **Line 53**: Sends the request to your local AI server. `stream=False` means we wait for the full text description before returning it.
*   **Line 56**: Extracts just the text result from the response object and returns it to the user.

## 9. Error Handling
```python
    except ollama.ResponseError as e:
        return f"Error analyzing image with Ollama (Status {e.status_code}): {e.error}"
    except Exception as e:
        return f"Fatal error during image analysis: {str(e)}"
```
*   **Lines 58-61**: Catch any problems that occur during the AI communication process (like "Model not found") and return a helpful error message.

---

### Integration with your `main.py`
To use this in your agent, you would typically import it into `main.py`:
```python
from webUI.vision import analyze_image

# Inside your tool list:
def vision_tool(file_name):
    path = f"{SANDBOX}/{file_name}"
    return analyze_image(path)
```
