#!/usr/bin/env python3
"""Ingest knowledge base files into the database for RAG retrieval."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

KNOWLEDGE_ROOT = Path("knowledge")
SUPPORTED_SUFFIXES = {".md", ".json", ".txt"}


def chunk_text(text: str, max_chars: int = 800) -> list[str]:
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    current = ""
    for para in paragraphs:
        if len(current) + len(para) + 2 <= max_chars:
            current = f"{current}\n\n{para}".strip()
        else:
            if current:
                chunks.append(current)
            current = para
    if current:
        chunks.append(current)
    return chunks


def infer_authority(path: Path) -> str | None:
    parts = path.parts
    if "authorities" in parts:
        idx = parts.index("authorities")
        if idx + 1 < len(parts):
            return parts[idx + 1]
    return None


def collect_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES:
            files.append(path)
    return sorted(files)


def build_records(root: Path) -> list[dict]:
    records: list[dict] = []
    for path in collect_files(root):
        text = path.read_text(encoding="utf-8")
        authority = infer_authority(path)
        rel = str(path.relative_to(root)).replace("\\", "/")
        for i, chunk in enumerate(chunk_text(text)):
            records.append(
                {
                    "source_path": rel,
                    "authority": authority,
                    "chunk_index": i,
                    "chunk_text": chunk,
                    "content_hash": hashlib.sha256(chunk.encode()).hexdigest()[:16],
                    "metadata": {"filename": path.name, "suffix": path.suffix},
                }
            )
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest knowledge files for RAG")
    parser.add_argument("--root", type=Path, default=KNOWLEDGE_ROOT)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/knowledge_chunks.jsonl"),
        help="Write chunked records to JSONL (DB insert wired in RAG MCP)",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not args.root.exists():
        raise SystemExit(f"Knowledge root not found: {args.root}")

    records = build_records(args.root)
    print(f"Collected {len(records)} chunks from {args.root}")

    if args.dry_run:
        for rec in records[:3]:
            print(json.dumps(rec, ensure_ascii=False)[:200], "…")
        return

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
