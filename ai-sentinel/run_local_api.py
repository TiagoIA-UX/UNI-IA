import os
import sys
from pathlib import Path

import uvicorn


ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host=os.getenv("UNI_IA_API_HOST", "127.0.0.1"),
        port=int(os.getenv("UNI_IA_API_PORT", "8000")),
        ws="none",
        http="h11",
    )