#!/usr/bin/env python3

import json
import os
import re
import tempfile
import unittest

from knowledge_base import KnowledgeBase


HERE = os.path.dirname(os.path.abspath(__file__))
PACKAGE = os.path.join(HERE, "data", "research_package")


class KnowledgeBaseTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp.name, "test.sqlite3")
        self.kb = KnowledgeBase(self.db_path, PACKAGE)

    def tearDown(self):
        self.temp.cleanup()

    def test_import_is_complete_and_idempotent(self):
        self.assertEqual(self.kb.stats()["projects"], 28)
        self.assertEqual(self.kb.stats()["tokens"], 27)

    def test_all_public_research_is_english(self):
        with open(os.path.join(PACKAGE, "arc_projects.json"), encoding="utf-8") as handle:
            projects = json.load(handle)["projects"]
        self.assertEqual(len(projects), 28)
        for project in projects:
            public_research = {
                "summary": project.get("summary_en"),
                "modules": project.get("seven_modules"),
                "risks": project.get("risks"),
            }
            self.assertEqual(len(public_research["modules"] or {}), 7, project["project_id"])
            self.assertIsNone(re.search(r"[\u3400-\u9fff]", json.dumps(public_research, ensure_ascii=False)),
                              project["project_id"])
        self.kb.import_package(PACKAGE)
        self.assertEqual(self.kb.stats()["projects"], 28)
        self.assertEqual(self.kb.stats()["tokens"], 27)

    def test_contract_name_website_and_x_resolve_same_project(self):
        queries = [
            "0xeCe5cA8bf9220718E5727754026757512212cb3c",
            "Argus",
            "https://argus.world/docs",
        ]
        self.assertEqual({self.kb.resolve(query)["match"]["projectId"] for query in queries}, {"arc-03"})
        self.assertEqual(self.kb.resolve("@arcat_meme")["match"]["projectId"], "arc-24")
        self.assertEqual(self.kb.resolve("https://twitter.com/arcat_meme")["match"]["projectId"], "arc-24")

    def test_duplicate_symbol_returns_candidates(self):
        result = self.kb.resolve("DUKE")
        self.assertIsNone(result["match"])
        self.assertEqual(len(result["candidates"]), 2)
        self.assertEqual(len({item["contractAddress"].lower() for item in result["candidates"]}), 2)

    def test_untrusted_url_does_not_match(self):
        for query in ("file:///etc/passwd", "http://127.0.0.1/private", "javascript:alert(1)"):
            result = self.kb.resolve(query)
            self.assertIsNone(result["match"])

    def test_market_cache_and_stale_fallback(self):
        calls = []

        def live(address):
            calls.append(address)
            return ({"priceUsd": 1.25, "volume24hUsd": 50.0, "liquidityUsd": 100.0,
                     "dataSource": "test", "updatedAt": "2026-10-14T00:00:00Z", "pairs": []}, [])

        first = self.kb.market("arc-03", fresh=True, fetcher=live)
        self.assertEqual(first["status"], "live")
        second = self.kb.market("arc-03", fetcher=lambda _: self.fail("fresh cache should avoid a request"))
        self.assertEqual(second["status"], "cached")
        stale = self.kb.market("arc-03", fresh=True, fetcher=lambda _: (None, ["offline"]))
        self.assertEqual(stale["status"], "stale")
        self.assertEqual(len(calls), 1)


if __name__ == "__main__":
    unittest.main()
