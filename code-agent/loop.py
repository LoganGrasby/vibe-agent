import subprocess

while True:
    try:
        print("Starting agent...")
        subprocess.run(["python3", "code-agent/agent.py"], check=True)
        print("Agent finished successfully.")
    except Exception as e:
        print(e)
        # some logic to fix if this is impossible to run
        break
