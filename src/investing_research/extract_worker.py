"""Private PDF parser process; invoked by sources.extract_source, never by an agent."""
import json
from pathlib import Path
import sys


def main():
    source, output, engine, receipt = sys.argv[1:]
    # POSIX limits supplement the parent's portable timeout and process-tree RSS cap.
    try:
        import resource
        resource.setrlimit(resource.RLIMIT_CPU, (120, 120))
        resource.setrlimit(resource.RLIMIT_FSIZE, (20 * 1024**2, 20 * 1024**2))
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    except (ImportError, OSError, ValueError):
        pass
    # -I ignores PYTHONPATH and local startup modules. Add only our installed package root.
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from investing_research.sources import _extract_local, SourceError
    try:
        result = _extract_local(Path(source), Path(output), engine=engine)
        payload = {"ok": True, "result": result}
    except Exception as exc:
        payload = {"ok": False, "error": str(exc) if isinstance(exc, SourceError)
                   else type(exc).__name__}
    Path(receipt).write_text(json.dumps(payload))


if __name__ == "__main__":
    main()
