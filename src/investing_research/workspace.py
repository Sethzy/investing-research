"""Atomic local records and content-addressed evidence, without a database service."""

import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from filelock import FileLock

from .contracts import Company, Settings


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def digest(value) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()
    ).hexdigest()


def read_json(path: Path, default=None):
    return json.loads(path.read_text()) if path.exists() else default


def write_json(path: Path, value) -> None:
    atomic_text(path, json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


def atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".write-", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


class Workspace:
    def __init__(self, root: Path):
        self.root = root.expanduser().resolve()
        self.settings_path = self.root / "config/local.json"

    def lock(self):
        (self.root / "state").mkdir(parents=True, exist_ok=True)
        return FileLock(self.root / "state/workspace.lock", timeout=0)

    def settings(self) -> Settings:
        if not self.settings_path.exists():
            raise ValueError("Workspace is not initialized. Run invest init first.")
        return Settings.model_validate(read_json(self.settings_path))

    def company(self, company_id: str) -> Company:
        for company in self.settings().companies:
            if company.id == company_id:
                return company
        raise ValueError(f"Unknown company {company_id}; use watch-add with a company JSON file.")

    def relative(self, path: Path) -> str:
        return str(path.resolve().relative_to(self.root))

    def inside(self, path: str) -> Path:
        resolved = (self.root / path).resolve()
        if not resolved.is_relative_to(self.root):
            raise ValueError("Path must remain inside the workspace")
        return resolved

    def captures(self) -> dict:
        return {p.stem: read_json(p) for p in (self.root / "state/captures").glob("*.json")}

    def capture_record(self, record: dict) -> tuple[dict, bool]:
        # Identity is content plus original source URL, not retrieval time or engagement.
        identity = {"url": record["url"], "sha256": record["sha256"]}
        capture_id = digest(identity)
        path = self.root / "state/captures" / f"{capture_id}.json"
        if path.exists():
            return read_json(path), False
        captured = {**record, "id": capture_id, "first_seen": now()}
        write_json(path, captured)
        return captured, True

    def capture_x(self, post: dict) -> tuple[dict, bool]:
        content = {
            k: post.get(k)
            for k in (
                "id",
                "url",
                "text",
                "author",
                "published_at",
                "completeness",
                "article",
                "conversation",
            )
        }
        sha = digest(content)
        path = self.root / "data/sources/x" / f"{sha}.json"
        if not path.exists():
            write_json(path, content)
        return self.capture_record(
            {
                "url": post["url"],
                "sha256": sha,
                "files": [self.relative(path)],
                "kind": "x",
                "title": f"X post by {post.get('author', 'unknown')}",
                "text": post.get("text", ""),
                "published_at": post.get("published_at"),
                "completeness": post.get("completeness", "partial"),
                "retrieved_at": now(),
            }
        )

    def record_source(self, source: dict) -> tuple[dict, bool]:
        record = dict(source)
        files = record.get("files", [])
        if isinstance(files, dict):
            files = list(files.values())
        record["files"] = [self.relative(Path(p)) if Path(p).is_absolute() else str(p) for p in files]
        if "extraction" in record:
            record["extraction"] = dict(record["extraction"])
            if "files" in record["extraction"]:
                record["extraction"]["files"] = {
                    k: self.relative(Path(v)) if Path(v).is_absolute() else v
                    for k, v in record["extraction"]["files"].items()
                }
        return self.capture_record(record)
