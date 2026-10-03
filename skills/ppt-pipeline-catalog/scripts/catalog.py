#!/usr/bin/env python3
"""Small SQLite catalog for the education PPT pipeline.

The database is an index and audit log. Project files and Git remain the source
of truth for slide content, style packs, and deliverables.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


SCHEMA_VERSION = 1

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS catalog_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS decks (
    deck_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    project_path TEXT NOT NULL,
    subject TEXT,
    grade TEXT,
    lesson_hours TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS styles (
    style_key TEXT PRIMARY KEY,
    style_id TEXT NOT NULL,
    name TEXT NOT NULL,
    version TEXT NOT NULL,
    status TEXT NOT NULL,
    parent_style_key TEXT,
    project_snapshot_path TEXT,
    system_path TEXT,
    content_hash TEXT,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    approved_at TEXT,
    FOREIGN KEY(parent_style_key) REFERENCES styles(style_key)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_styles_id_version
    ON styles(style_id, version);

CREATE TABLE IF NOT EXISTS deck_styles (
    deck_id TEXT NOT NULL,
    style_key TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'used',
    locked_at TEXT,
    PRIMARY KEY(deck_id, style_key),
    FOREIGN KEY(deck_id) REFERENCES decks(deck_id) ON DELETE CASCADE,
    FOREIGN KEY(style_key) REFERENCES styles(style_key) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS style_sources (
    source_id TEXT PRIMARY KEY,
    style_key TEXT NOT NULL,
    repository_url TEXT NOT NULL,
    role TEXT,
    decision TEXT,
    reusable_parts_json TEXT NOT NULL DEFAULT '[]',
    adaptation_notes_json TEXT NOT NULL DEFAULT '[]',
    checked_at TEXT,
    FOREIGN KEY(style_key) REFERENCES styles(style_key) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS style_samples (
    sample_id TEXT PRIMARY KEY,
    style_key TEXT NOT NULL,
    page_role TEXT NOT NULL,
    path TEXT NOT NULL,
    sha256 TEXT,
    approved INTEGER NOT NULL DEFAULT 0,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    FOREIGN KEY(style_key) REFERENCES styles(style_key) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS pipeline_runs (
    run_id TEXT PRIMARY KEY,
    deck_id TEXT NOT NULL,
    stage TEXT NOT NULL,
    status TEXT NOT NULL,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    message TEXT,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    FOREIGN KEY(deck_id) REFERENCES decks(deck_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_pipeline_runs_deck_stage
    ON pipeline_runs(deck_id, stage, started_at);

CREATE TABLE IF NOT EXISTS artifacts (
    artifact_id TEXT PRIMARY KEY,
    deck_id TEXT NOT NULL,
    run_id TEXT,
    kind TEXT NOT NULL,
    role TEXT,
    path TEXT NOT NULL,
    sha256 TEXT,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    FOREIGN KEY(deck_id) REFERENCES decks(deck_id) ON DELETE CASCADE,
    FOREIGN KEY(run_id) REFERENCES pipeline_runs(run_id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_artifacts_deck_kind
    ON artifacts(deck_id, kind);

CREATE TABLE IF NOT EXISTS approvals (
    approval_id TEXT PRIMARY KEY,
    deck_id TEXT NOT NULL,
    stage TEXT NOT NULL,
    status TEXT NOT NULL,
    evidence_path TEXT,
    approved_by TEXT,
    note TEXT,
    approved_at TEXT NOT NULL,
    FOREIGN KEY(deck_id) REFERENCES decks(deck_id) ON DELETE CASCADE
);
"""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def default_db_path() -> Path:
    explicit = os.environ.get("PPT_PIPELINE_CATALOG_DB")
    if explicit:
        return Path(explicit).expanduser()
    home = os.environ.get("CODEX_PPT_HOME")
    if home:
        return Path(home).expanduser() / "catalog.sqlite3"
    return Path.home() / ".codex-ppt-skill" / "catalog.sqlite3"


def connect(path: Path) -> sqlite3.Connection:
    path = path.expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 5000")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.executescript(SCHEMA)
    conn.execute(
        "INSERT INTO catalog_meta(key, value) VALUES(?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        ("schema_version", str(SCHEMA_VERSION)),
    )
    conn.commit()
    return conn


def read_json(path: Optional[str]) -> Dict[str, Any]:
    if not path:
        return {}
    return json.loads(Path(path).read_text(encoding="utf-8"))


def json_text(value: Any) -> str:
    return json.dumps(value if value is not None else {}, ensure_ascii=False, sort_keys=True)


def file_sha256(path: str) -> Optional[str]:
    candidate = Path(path).expanduser()
    if not candidate.is_file():
        return None
    digest = hashlib.sha256()
    with candidate.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require_deck(conn: sqlite3.Connection, deck_id: str) -> None:
    row = conn.execute("SELECT deck_id FROM decks WHERE deck_id = ?", (deck_id,)).fetchone()
    if row is None:
        raise SystemExit(f"unknown deck_id: {deck_id}; run upsert-deck first")


def cmd_init(args: argparse.Namespace) -> None:
    with connect(args.db):
        pass
    print(json.dumps({"database": str(args.db), "schema_version": SCHEMA_VERSION}, ensure_ascii=False))


def cmd_upsert_deck(args: argparse.Namespace) -> None:
    now = utc_now()
    metadata = read_json(args.metadata_file)
    with connect(args.db) as conn:
        conn.execute(
            """INSERT INTO decks(deck_id, title, project_path, subject, grade, lesson_hours,
               status, metadata_json, created_at, updated_at)
               VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(deck_id) DO UPDATE SET title=excluded.title,
               project_path=excluded.project_path, subject=excluded.subject,
               grade=excluded.grade, lesson_hours=excluded.lesson_hours,
               status=excluded.status, metadata_json=excluded.metadata_json,
               updated_at=excluded.updated_at""",
            (args.deck_id, args.title, str(Path(args.project_path).expanduser()), args.subject,
             args.grade, args.lesson_hours, args.status, json_text(metadata), now, now),
        )
    print(args.deck_id)


def cmd_run(args: argparse.Namespace) -> None:
    run_id = args.run_id or f"run-{uuid.uuid4().hex[:12]}"
    now = utc_now()
    with connect(args.db) as conn:
        require_deck(conn, args.deck_id)
        conn.execute(
            """INSERT INTO pipeline_runs(run_id, deck_id, stage, status, started_at,
               completed_at, message, metadata_json) VALUES(?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(run_id) DO UPDATE SET status=excluded.status,
               completed_at=excluded.completed_at, message=excluded.message,
               metadata_json=excluded.metadata_json""",
            (run_id, args.deck_id, args.stage, args.status, args.started_at or now,
             now if args.status in {"passed", "failed", "blocked", "cancelled"} else None,
             args.message, json_text(read_json(args.metadata_file))),
        )
    print(run_id)


def cmd_artifact(args: argparse.Namespace) -> None:
    with connect(args.db) as conn:
        require_deck(conn, args.deck_id)
        if args.run_id and conn.execute("SELECT 1 FROM pipeline_runs WHERE run_id = ?", (args.run_id,)).fetchone() is None:
            raise SystemExit(f"unknown run_id: {args.run_id}")
        artifact_id = args.artifact_id or f"artifact-{uuid.uuid4().hex[:12]}"
        conn.execute(
            """INSERT INTO artifacts(artifact_id, deck_id, run_id, kind, role, path,
               sha256, metadata_json, created_at) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(artifact_id) DO UPDATE SET path=excluded.path,
               sha256=excluded.sha256, metadata_json=excluded.metadata_json""",
            (artifact_id, args.deck_id, args.run_id, args.kind, args.role,
             str(Path(args.path).expanduser()), args.sha256 or file_sha256(args.path),
             json_text(read_json(args.metadata_file)), utc_now()),
        )
    print(artifact_id)


def cmd_approval(args: argparse.Namespace) -> None:
    with connect(args.db) as conn:
        require_deck(conn, args.deck_id)
        approval_id = args.approval_id or f"approval-{uuid.uuid4().hex[:12]}"
        conn.execute(
            """INSERT INTO approvals(approval_id, deck_id, stage, status, evidence_path,
               approved_by, note, approved_at) VALUES(?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(approval_id) DO UPDATE SET status=excluded.status,
               evidence_path=excluded.evidence_path, approved_by=excluded.approved_by,
               note=excluded.note, approved_at=excluded.approved_at""",
            (approval_id, args.deck_id, args.stage, args.status, args.evidence_path,
             args.approved_by, args.note, args.approved_at or utc_now()),
        )
    print(approval_id)


def cmd_register_style(args: argparse.Namespace) -> None:
    style_key = f"{args.style_id}@{args.version}"
    status = args.status
    now = utc_now()
    metadata = read_json(args.metadata_file)
    with connect(args.db) as conn:
        if args.parent_style_key:
            parent = conn.execute("SELECT 1 FROM styles WHERE style_key = ?", (args.parent_style_key,)).fetchone()
            if parent is None:
                raise SystemExit(f"unknown parent_style_key: {args.parent_style_key}")
        conn.execute(
            """INSERT INTO styles(style_key, style_id, name, version, status,
               parent_style_key, project_snapshot_path, system_path, content_hash,
               metadata_json, created_at, approved_at) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(style_key) DO UPDATE SET name=excluded.name, status=excluded.status,
               project_snapshot_path=excluded.project_snapshot_path, system_path=excluded.system_path,
               content_hash=excluded.content_hash, metadata_json=excluded.metadata_json,
               approved_at=excluded.approved_at""",
            (style_key, args.style_id, args.name, args.version, status, args.parent_style_key,
             args.project_snapshot_path, args.system_path, args.content_hash,
             json_text(metadata), now, now if status in {"verified", "approved"} else None),
        )
        for source in read_json(args.sources_file).get("sources", []):
            source_id = source.get("source_id") or f"source-{uuid.uuid4().hex[:12]}"
            conn.execute(
                """INSERT INTO style_sources(source_id, style_key, repository_url, role,
                   decision, reusable_parts_json, adaptation_notes_json, checked_at)
                   VALUES(?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(source_id) DO UPDATE SET repository_url=excluded.repository_url,
                   role=excluded.role, decision=excluded.decision,
                   reusable_parts_json=excluded.reusable_parts_json,
                   adaptation_notes_json=excluded.adaptation_notes_json,
                   checked_at=excluded.checked_at""",
                (source_id, style_key, source["repository_url"], source.get("role"),
                 source.get("decision"), json_text(source.get("reusable_parts", [])),
                 json_text(source.get("adaptation_notes", [])), source.get("checked_at")),
            )
    print(style_key)


def cmd_link_style(args: argparse.Namespace) -> None:
    with connect(args.db) as conn:
        require_deck(conn, args.deck_id)
        if conn.execute("SELECT 1 FROM styles WHERE style_key = ?", (args.style_key,)).fetchone() is None:
            raise SystemExit(f"unknown style_key: {args.style_key}")
        conn.execute(
            """INSERT INTO deck_styles(deck_id, style_key, role, locked_at) VALUES(?, ?, ?, ?)
               ON CONFLICT(deck_id, style_key) DO UPDATE SET role=excluded.role,
               locked_at=excluded.locked_at""",
            (args.deck_id, args.style_key, args.role, args.locked_at or utc_now()),
        )


def cmd_search_styles(args: argparse.Namespace) -> None:
    with connect(args.db) as conn:
        sql = "SELECT style_key, style_id, name, version, status, system_path FROM styles WHERE 1=1"
        params = []
        if args.status:
            sql += " AND status = ?"
            params.append(args.status)
        if args.query:
            sql += " AND (style_id LIKE ? OR name LIKE ?)"
            needle = f"%{args.query}%"
            params.extend([needle, needle])
        sql += " ORDER BY created_at DESC, style_id, version"
        print(json.dumps([dict(row) for row in conn.execute(sql, params).fetchall()], ensure_ascii=False, indent=2))


def cmd_export(args: argparse.Namespace) -> None:
    with connect(args.db) as conn:
        require_deck(conn, args.deck_id)
        result: Dict[str, Any] = {"deck_id": args.deck_id, "exported_at": utc_now()}
        for table in ("decks", "pipeline_runs", "artifacts", "approvals"):
            rows = conn.execute(f"SELECT * FROM {table} WHERE deck_id = ?", (args.deck_id,)).fetchall()
            result[table] = [dict(row) for row in rows]
        result["styles"] = [dict(row) for row in conn.execute(
            """SELECT s.* FROM styles s JOIN deck_styles ds ON ds.style_key=s.style_key
               WHERE ds.deck_id = ? ORDER BY s.style_id, s.version""", (args.deck_id,)
        ).fetchall()]
    output = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        destination = Path(args.out).expanduser()
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(output + "\n", encoding="utf-8")
        print(str(destination))
    else:
        print(output)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=default_db_path())
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init")

    deck = sub.add_parser("upsert-deck")
    deck.add_argument("--deck-id", required=True)
    deck.add_argument("--title", required=True)
    deck.add_argument("--project-path", required=True)
    deck.add_argument("--subject")
    deck.add_argument("--grade")
    deck.add_argument("--lesson-hours")
    deck.add_argument("--status", default="active")
    deck.add_argument("--metadata-file")

    run = sub.add_parser("run")
    run.add_argument("--run-id")
    run.add_argument("--deck-id", required=True)
    run.add_argument("--stage", required=True)
    run.add_argument("--status", required=True, choices=["pending", "running", "passed", "failed", "blocked", "cancelled"])
    run.add_argument("--started-at")
    run.add_argument("--message")
    run.add_argument("--metadata-file")

    artifact = sub.add_parser("artifact")
    artifact.add_argument("--artifact-id")
    artifact.add_argument("--deck-id", required=True)
    artifact.add_argument("--run-id")
    artifact.add_argument("--kind", required=True)
    artifact.add_argument("--role")
    artifact.add_argument("--path", required=True)
    artifact.add_argument("--sha256")
    artifact.add_argument("--metadata-file")

    approval = sub.add_parser("approval")
    approval.add_argument("--approval-id")
    approval.add_argument("--deck-id", required=True)
    approval.add_argument("--stage", required=True)
    approval.add_argument("--status", required=True, choices=["pending", "approved", "rejected", "project-only"])
    approval.add_argument("--evidence-path")
    approval.add_argument("--approved-by", default="user")
    approval.add_argument("--note")
    approval.add_argument("--approved-at")

    style = sub.add_parser("register-style")
    style.add_argument("--style-id", required=True)
    style.add_argument("--name", required=True)
    style.add_argument("--version", required=True)
    style.add_argument("--status", required=True, choices=["candidate", "locked", "verified", "approved", "project-only", "archived"])
    style.add_argument("--parent-style-key")
    style.add_argument("--project-snapshot-path")
    style.add_argument("--system-path")
    style.add_argument("--content-hash")
    style.add_argument("--metadata-file")
    style.add_argument("--sources-file")

    link = sub.add_parser("link-style")
    link.add_argument("--deck-id", required=True)
    link.add_argument("--style-key", required=True)
    link.add_argument("--role", default="used")
    link.add_argument("--locked-at")

    search = sub.add_parser("search-styles")
    search.add_argument("--query")
    search.add_argument("--status")

    export = sub.add_parser("export")
    export.add_argument("--deck-id", required=True)
    export.add_argument("--out")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    commands = {
        "init": cmd_init,
        "upsert-deck": cmd_upsert_deck,
        "run": cmd_run,
        "artifact": cmd_artifact,
        "approval": cmd_approval,
        "register-style": cmd_register_style,
        "link-style": cmd_link_style,
        "search-styles": cmd_search_styles,
        "export": cmd_export,
    }
    try:
        commands[args.command](args)
    except sqlite3.Error as exc:
        print(f"catalog sqlite error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
