import asyncio
import uuid
from typing import Optional
import os
import sys
from pathlib import Path
import textwrap
import json
import time
import subprocess
import traceback

from google.genai import types
from google.adk.runners import Runner, RunConfig
from google.adk.sessions import DatabaseSessionService, Session
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService

DB_BASE_PATH = Path(os.getenv("DB_PATH", "~/.sessions")).expanduser()
APP_NAME = "self-evolving-agent"
TENANT_ID = "default"
AGENT_FILE = "agent.py"

def sanitize_id(val: str) -> str:
    "Return a string that is safe to be used as an ADK app / user id."
    cleaned = "".join(ch if ch.isalnum() else "_" for ch in val)
    if not cleaned:
        return "empty_id"
    if not cleaned[0].isalpha():
        cleaned = f"a{cleaned}"
    return cleaned

def get_session_service(tenant: str) -> DatabaseSessionService:
    p = DB_BASE_PATH / "sessions" / f"{sanitize_id(tenant)}_sessions.sqlite"
    p.parent.mkdir(parents=True, exist_ok=True)
    return DatabaseSessionService(db_url=f"sqlite:///{p}")

def check_and_handle_restart_flag():
    """Check if agent code needs restart and handle it."""
    agent_path = Path(AGENT_FILE).absolute()
    restart_flag = agent_path.with_suffix(agent_path.suffix + ".needs_restart")
    
    if restart_flag.exists():
        restart_flag.unlink() 
        return True
    return False

def test_agent_import():
    """Test if the agent module can be imported without errors."""
    try:
        # Try to import in a subprocess to avoid polluting current process
        result = subprocess.run(
            [sys.executable, "-c", f"import {AGENT_FILE.replace('.py', '')}"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode != 0:
            return False, result.stderr
        return True, None
    except Exception as e:
        return False, str(e)

def revert_agent_code():
    """Revert agent code to backup and save error information."""
    agent_path = Path(AGENT_FILE).absolute()
    backup_path = agent_path.with_suffix(agent_path.suffix + ".backup")
    error_path = agent_path.with_suffix(agent_path.suffix + ".error")
    
    if backup_path.exists():
        error_info = {
            "timestamp": time.time(),
            "error": "Code import failed after update",
            "traceback": traceback.format_exc()
        }
        
        backup_content = backup_path.read_text()
        agent_path.write_text(backup_content)
        
        success, error = test_agent_import()
        if success:
            with open(error_path, 'w') as f:
                json.dump(error_info, f)
            print("[Recovery] Successfully reverted to backup code")
        else:
            print(f"[CRITICAL] Backup code also fails to import: {error}")
            sys.exit(1)

# Test initial agent import
print("[Startup] Testing agent import...")
success, error = test_agent_import()
if not success:
    print(f"[Startup] Agent import failed: {error}")
    print("[Startup] Attempting to revert to backup...")
    revert_agent_code()

# Import the agent after validation
try:
    from agent import root_agent
except Exception as e:
    print(f"[CRITICAL] Failed to import agent even after recovery: {e}")
    sys.exit(1)

async def invoke_agent(
    runner: Runner,
    session_service: DatabaseSessionService,
    user_id: str,
    session_id: str,
    message: str
):
    """Manually invoke the self-evolving agent with a message using a specific session."""
    
    current_session = await session_service.get_session(app_name=APP_NAME, user_id=user_id, session_id=session_id)
    if current_session is None:
        print(f"Warning: Session {session_id} not found for user {user_id}. Creating it.", file=sys.stderr)
        current_session = await session_service.create_session(app_name=APP_NAME, user_id=user_id, session_id=session_id)
        if current_session is None:
             raise Exception(f"Failed to create or retrieve session {session_id}")

    user_message = types.Content(role="user", parts=[types.Part(text=message)])
    run_cfg = RunConfig()
    
    full_response = ""
    tool_responses = []
    
    print(f"\n[Agent Processing in session {session_id}] Task: {message}\n")
    
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=user_message,
        run_config=run_cfg,
    ):
        if event.content and event.content.parts:
            part = event.content.parts[0]
            if hasattr(part, "text") and part.text is not None:
                print(part.text, end="", flush=True)
                full_response += part.text
        
        if event.get_function_responses():
            for tool_resp in event.get_function_responses():
                tool_responses.append({
                    "name": tool_resp.name,
                    "response": tool_resp.response
                })
                print(f"\n\n[Tool '{tool_resp.name}' called in session {session_id}]")
                response_str = str(tool_resp.response)
                print(textwrap.indent(response_str, "  "))
                print("")
    
    print("\n" + "="*50 + "\n")
    
    return {
        "session_id": session_id,
        "response": full_response,
        "tool_calls": tool_responses
    }

async def main_loop():
    """Main function to run the agent with automatic restart on code updates."""
    
    session_info = os.environ.get("RESUME_SESSION_INFO")
    if session_info:
        session_data = json.loads(session_info)
        user_id = session_data["user_id"]
        current_session_id = session_data["session_id"]
        message_counter = session_data.get("message_counter", 0)
        current_task = "Check your last update status and continue with the task"
        print(f"[Restart] Resuming session {current_session_id} after code update")
    else:
        user_id = sanitize_id(f"user_{TENANT_ID}")
        current_session_id = None
        message_counter = 0
        current_task = "Check your status and then update yourself to have an internet search tool"
    
    session_service = get_session_service(TENANT_ID)
    artifact_service = InMemoryArtifactService()
    memory_service = InMemoryMemoryService()
    
    runner = Runner(
        app_name=APP_NAME,
        agent=root_agent,
        artifact_service=artifact_service,
        session_service=session_service,
        memory_service=memory_service,
    )

    SESSION_MESSAGE_LIMIT = 10
    restart_requested = False

    try:
        while True:
            if check_and_handle_restart_flag():
                restart_requested = True
                break
            
            if current_session_id is None:
                current_session_id = str(uuid.uuid4())
                existing_session = await session_service.get_session(app_name=APP_NAME, user_id=user_id, session_id=current_session_id)
                if existing_session is None:
                    await session_service.create_session(app_name=APP_NAME, user_id=user_id, session_id=current_session_id)
                    print(f"[Session Management] Created new session: {current_session_id}")
                else:
                    print(f"[Session Management] Reusing existing session: {current_session_id}")

            try:
                print(f"\n{'='*60}")
                print(f"INVOKING WITH (Session: {current_session_id}, Msg #: {message_counter + 1}): {current_task}")
                print('='*60 + "\n")
                
                os.environ["CURRENT_SESSION_INFO"] = json.dumps({
                    "user_id": user_id,
                    "session_id": current_session_id,
                    "message_counter": message_counter
                })
                
                result = await invoke_agent(
                    runner, 
                    session_service, 
                    user_id, 
                    current_session_id,
                    current_task
                )
                message_counter += 1
                
                if check_and_handle_restart_flag():
                    restart_requested = True
                    break

                if message_counter % SESSION_MESSAGE_LIMIT == 0:
                    print(f"\n[Session Management] Reached {SESSION_MESSAGE_LIMIT} messages in session {current_session_id}.")
                    current_session_id = str(uuid.uuid4())
                    await session_service.create_session(app_name=APP_NAME, user_id=user_id, session_id=current_session_id)
                    print(f"[Session Management] ---- Switched to new session {current_session_id} ----\n")
                    message_counter = 0

                print("\nWaiting before next iteration...")
                await asyncio.sleep(2)

            except KeyboardInterrupt:
                print("\n[User requested exit. Shutting down...]")
                break
            except Exception as e:
                print(f"\nError in main loop iteration: {e}")
                traceback.print_exc()
                print("Attempting to continue loop after 5 seconds...")
                await asyncio.sleep(5)
                
    finally:
        print("\n[Main loop finished]")
        
        if restart_requested:
            print("[Restart] Initiating automatic restart...")
            resume_info = {
                "user_id": user_id,
                "session_id": current_session_id,
                "message_counter": message_counter
            }
            
            env = os.environ.copy()
            env["RESUME_SESSION_INFO"] = json.dumps(resume_info)
            
            subprocess.Popen([sys.executable, __file__], env=env)
            sys.exit(0)


if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("GEMINI_API_KEY"):
        print("ERROR: Environment variable OPENAI_API_KEY or GEMINI_API_KEY not set.", file=sys.stderr)
        print("Please set the appropriate API key for the model you intend to use.", file=sys.stderr)
        sys.exit(1)
    
    asyncio.run(main_loop())