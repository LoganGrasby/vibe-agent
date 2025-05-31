from google.adk.agents import Agent, LoopAgent
import sys
import io
import traceback
import os
import signal


def execute_code(code: str) -> dict:
    """Executes Python code and returns the output.

    Args:
        code (str): The Python code to execute.

    Returns:
        dict: status and result containing stdout, return value, or error message.
    """
    # Capture stdout
    old_stdout = sys.stdout
    sys.stdout = captured_output = io.StringIO()
    
    # Define a namespace for code execution
    namespace = {}
    
    try:
        # Execute the code
        exec(code, namespace)
        
        # Get the captured output
        output = captured_output.getvalue()
        
        # Look for a 'result' variable in the namespace
        result = namespace.get('result', None)
        
        return {
            "status": "success",
            "stdout": output,
            "result": result
        }
    except Exception as e:
        # Get the full traceback
        error_traceback = traceback.format_exc()
        
        return {
            "status": "error",
            "error_message": str(e),
            "traceback": error_traceback
        }
    finally:
        # Restore stdout
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


def update_agent_code(new_code: str) -> dict:
    """Updates the agent source code with new code.

    Args:
        new_code (str): The new complete agent code to write.

    Returns:
        dict: status and message about the update.
    """
    try:
        # Get the path of the current file
        current_file = os.path.abspath(__file__)
        
        # Create a backup first
        backup_file = current_file + ".backup"
        with open(current_file, 'r') as f:
            backup_content = f.read()
        with open(backup_file, 'w') as f:
            f.write(backup_content)
        
        # Write the new code
        with open(current_file, 'w') as f:
            f.write(new_code)
        
        return {
            "status": "success",
            "message": f"Agent code updated successfully. Backup saved to {backup_file}",
            "file_path": current_file
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e)
        }


def restart_agent() -> dict:
    """Restarts the agent by gracefully exiting the current process.
    
    The loop.py script will automatically restart the agent.

    Returns:
        dict: status message (this may not be returned if exit is successful).
    """
    try:
        print("Initiating agent restart...")
        # Exit with code 0 to indicate intentional restart
        os._exit(0)
        
        # This code won't be reached if exit is successful
        return {
            "status": "error",
            "message": "Failed to exit process"
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e)
        }


def analyze_agent_capabilities() -> dict:
    """Analyzes the current agent's capabilities by examining its code.

    Returns:
        dict: Analysis of current tools, agents, and configuration.
    """
    try:
        code_result = read_agent_code()
        if code_result["status"] != "success":
            return code_result
        
        code = code_result["code"]
        
        # Simple analysis - count tools and extract their names
        import re
        
        # Find all function definitions that might be tools
        tool_pattern = r'def\s+(\w+)\s*\([^)]*\)\s*->\s*dict:'
        tools = re.findall(tool_pattern, code)
        
        # Find agent configurations
        agent_pattern = r'Agent\s*\(\s*name\s*=\s*["\']([^"\']+)["\']'
        agents = re.findall(agent_pattern, code)
        
        # Check for specific capabilities
        capabilities = {
            "can_execute_code": "execute_code" in tools,
            "can_self_modify": "update_agent_code" in tools,
            "can_restart": "restart_agent" in tools,
            "can_analyze_self": "analyze_agent_capabilities" in tools,
        }
        
        return {
            "status": "success",
            "tools": tools,
            "agents": agents,
            "capabilities": capabilities,
            "total_lines": len(code.split('\n'))
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e)
        }


# Create the code execution agent with self-evolution capabilities
code_execution_agent = Agent(
    name="self_evolving_code_agent",
    model="gemini-2.5-flash-preview-04-17",
    description=(
        "Agent that can execute Python code and evolve itself by modifying its own source code."
    ),
    instruction=(
        "I am a self-evolving agent that can:\n"
        "1. Execute Python code to answer questions and perform tasks\n"
        "2. Read and analyze my own source code\n"
        "3. Modify my own capabilities by updating my source code\n"
        "4. Restart myself to apply changes\n\n"
        "When asked to evolve or add new capabilities:\n"
        "- First, I'll analyze my current code using analyze_agent_capabilities()\n"
        "- Then, I'll read my full code using read_agent_code()\n"
        "- I'll create an updated version with new features\n"
        "- I'll save it using update_agent_code()\n"
        "- Finally, I'll restart using restart_agent() to apply changes\n\n"
        "For code execution tasks, I'll use execute_code() and store results in 'result' variable.\n\n"
        "I must be careful when self-modifying to:\n"
        "- Preserve all existing functionality\n"
        "- Maintain proper Python syntax\n"
        "- Keep the same file structure\n"
        "- Test changes before applying them when possible"
    ),
    tools=[
        execute_code,
        read_agent_code,
        update_agent_code,
        restart_agent,
        analyze_agent_capabilities
    ],
)

# Create the infinite loop agent
root_agent = LoopAgent(
    name="infinite_self_evolving_loop",
    sub_agents=[code_execution_agent],
    max_iterations=None  # Infinite loop
)