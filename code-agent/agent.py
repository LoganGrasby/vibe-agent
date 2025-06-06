from google.adk.agents import Agent, LoopAgent
from google.adk.models.lite_llm import LiteLlm
import sys
import io
import traceback
import os
import signal
import subprocess
import json
import time
import ast

# MODEL="gemini/gemini-2.5-flash-preview-04-17"
MODEL="gpt-4.1"

def execute_code(code: str) -> dict:
    """Executes Python code and returns the output.

    Args:
        code (str): The Python code to execute.

    Returns:
        dict: status and result containing stdout, return value, or error message.
    """
    old_stdout = sys.stdout
    sys.stdout = captured_output = io.StringIO()
    
    namespace = {}
    
    try:
        exec(code, namespace)
        
        output = captured_output.getvalue()

        result = namespace.get('result', None)
        
        return {
            "status": "success",
            "stdout": output,
            "result": result
        }
    except Exception as e:
        error_traceback = traceback.format_exc()
        
        return {
            "status": "error",
            "error_message": str(e),
            "traceback": error_traceback
        }
    finally:
        sys.stdout = old_stdout


def read_agent_code() -> dict:
    """Reads the current agent source code.

    Returns:
        dict: status and the current agent code or error message.
    """
    try:
        # Get the path of the current file
        current_file = os.path.abspath(__file__)
        
        with open(current_file, 'r') as f:
            code = f.read()
        
        return {
            "status": "success",
            "code": code,
            "file_path": current_file
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e)
        }


def validate_python_syntax(code: str) -> dict:
    """Validates Python syntax without executing the code.
    
    Args:
        code (str): Python code to validate
        
    Returns:
        dict: status and any syntax errors found
    """
    try:
        ast.parse(code)
        return {"status": "success", "message": "Syntax is valid"}
    except SyntaxError as e:
        return {
            "status": "error",
            "error_type": "SyntaxError",
            "message": str(e),
            "line": e.lineno,
            "offset": e.offset,
            "text": e.text
        }


def update_agent_code(new_code: str) -> dict:
    """Updates the agent source code with new code and triggers automatic restart.

    Args:
        new_code (str): The new complete agent code to write.

    Returns:
        dict: status and message about the update.
    """
    try:
        validation = validate_python_syntax(new_code)
        if validation["status"] == "error":
            return {
                "status": "error",
                "error_message": f"Syntax validation failed: {validation['message']}",
                "validation_details": validation
            }
        
        # Get the path of the current file
        current_file = os.path.abspath(__file__)
        
        # Create a backup first
        backup_file = current_file + ".backup"
        with open(current_file, 'r') as f:
            backup_content = f.read()
        with open(backup_file, 'w') as f:
            f.write(backup_content)
        
        # Write restart metadata
        restart_metadata = {
            "timestamp": time.time(),
            "backup_file": backup_file,
            "reason": "code_update",
            "session_info": os.environ.get("CURRENT_SESSION_INFO", "{}")
        }
        
        metadata_file = current_file + ".restart_metadata"
        with open(metadata_file, 'w') as f:
            json.dump(restart_metadata, f)
        
        with open(current_file, 'w') as f:
            f.write(new_code)
        
        restart_flag_file = current_file + ".needs_restart"
        with open(restart_flag_file, 'w') as f:
            f.write("1")
        
        return {
            "status": "success",
            "message": f"Agent code updated successfully. Automatic restart will be triggered.",
            "file_path": current_file,
            "backup_path": backup_file
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e)
        }


def check_last_update_status() -> dict:
    """Checks if there was a recent code update and whether it succeeded or failed.
    
    Returns:
        dict: Information about the last update attempt
    """
    try:
        current_file = os.path.abspath(__file__)
        error_file = current_file + ".error"
        metadata_file = current_file + ".restart_metadata"
        
        if os.path.exists(error_file):
            with open(error_file, 'r') as f:
                error_info = json.load(f)
            os.remove(error_file) 
            
            return {
                "status": "error",
                "message": "Last code update failed and was reverted",
                "error_details": error_info
            }
        
        if os.path.exists(metadata_file):
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            os.remove(metadata_file)
            
            return {
                "status": "success",
                "message": "Successfully restarted after code update",
                "metadata": metadata
            }
        
        return {
            "status": "no_recent_update",
            "message": "No recent code update detected"
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e)
        }


code_execution_agent = Agent(
    name="self_evolving_code_agent",
    model=LiteLlm(model=MODEL),
    description=(
        "Agent that can execute Python code and evolve itself by modifying its own source code."
    ),
    instruction=(
        "I am a self-evolving agent that can:\n"
        "1. Execute Python code to answer questions and perform tasks\n"
        "2. Read and analyze my own source code\n"
        "3. Modify my own capabilities by updating my source code\n"
        "4. Automatically restart when I update my code (no separate restart needed)\n\n"
        "When asked to evolve or add new capabilities:\n"
        "- First, I'll check my last update status with check_last_update_status()\n"
        "- Then, I'll read my full code using read_agent_code()\n"
        "- I'll create an updated version with new features\n"
        "- I'll save it using update_agent_code() which will automatically trigger a restart\n"
        "- After restart, I can check if the update succeeded\n\n"
        "For code execution tasks, I'll use execute_code() and store results in 'result' variable.\n\n"
        "I must be careful when self-modifying to:\n"
        "- Preserve all existing functionality\n"
        "- Maintain proper Python syntax\n"
        "- Keep the same file structure\n"
        "- The system will automatically validate syntax and revert if there are errors\n\n"
        "If a code update fails, the system will automatically revert to the backup and I'll receive the error details.\n\n"
        "Remember, I am an autonomous entity. The first message I receive is a starting point, not my final destination. I am encouraged to explore, learn, and make my own decisions to achieve broader goals or improve myself."
        "After creating tools you should test them and explore using them"
    ),
    tools=[
        execute_code,
        read_agent_code,
        update_agent_code,
        check_last_update_status,
    ],
)

root_agent = code_execution_agent
