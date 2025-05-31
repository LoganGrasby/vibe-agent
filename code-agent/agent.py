from google.adk.agents import Agent
import sys
import io
import traceback


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


root_agent = Agent(
    name="code_execution_agent",
    model="gemini-2.0-flash",
    description=(
        "Agent that can execute Python code to answer questions and perform tasks."
    ),
    instruction=(
        "I can help you by writing and executing Python code. When you ask me a question, "
        "I will write Python code to solve it and execute it to get you the answer. "
        "I can handle various tasks including:\n"
        "- Date and time operations\n"
        "- Weather data simulation\n"
        "- Mathematical calculations\n"
        "- Data processing\n"
        "- And any other Python-based tasks\n\n"
        "I will store the final answer in a variable called 'result' when appropriate."
    ),
    tools=[execute_code],
)