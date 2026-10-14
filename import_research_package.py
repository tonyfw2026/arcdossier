#!/usr/bin/env python3
"""Import an ArcDossier v0.5 research package into the local SQLite database."""

import json
import os
import sys

from knowledge_base import KnowledgeBase


HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    package_dir = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "data", "research_package"))
    db_path = os.path.abspath(sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "data", "arcdossier.sqlite3"))
    result = KnowledgeBase(db_path).import_package(package_dir)
    print(json.dumps({"ok": True, "database": db_path, "package": package_dir, "imported": result}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
