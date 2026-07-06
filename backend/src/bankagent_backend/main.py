"""Run the mock bank backend: python -m bankagent_backend.main"""

import uvicorn


def run() -> None:
    uvicorn.run("bankagent_backend.app:create_app", factory=True, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    run()
