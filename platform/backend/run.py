"""uvicorn launcher:  python run.py  (from platform/backend)

In headless/redirected environments (Start-Process, nohup, Windows service)
``sys.stdout`` may be None, which crashes uvicorn's console-log formatter
(``LogFormatter.__init__`` calls ``sys.stdout.isatty()``). We therefore launch
with an empty ``log_config`` so uvicorn does not build its console formatters.
Access logs are written to stderr (redirect to a file by the caller) instead.
"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8001,
        reload=False,
        workers=1,
        log_config={"version": 1, "disable_existing_loggers": False},
        access_log=True,
    )