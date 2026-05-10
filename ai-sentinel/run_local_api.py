"""
UNI IA — Backend Launcher
Inicia o servidor FastAPI local sem WebSocket (compatível Windows)
"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
        ws="none",
        http="h11",
        log_level="info"
    )