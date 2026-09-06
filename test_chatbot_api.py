"""
Unit & Integration Tests for LunarVision Chatbot API
"""

import sys
import unittest
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent / "backend"
sys.path.insert(0, str(backend_dir))

from services.chatbot_service import LunarChatbotService


class TestLunarChatbotService(unittest.TestCase):

    def setUp(self):
        self.service = LunarChatbotService()

    def test_01_knowledge_base_loading(self):
        self.assertIsNotNone(self.service.kb_data)
        self.assertIn("faqs", self.service.kb_data)
        self.assertIn("pipeline_steps", self.service.kb_data)
        self.assertGreater(len(self.service.kb_data["faqs"]), 5)

    def test_02_ransac_query_offline(self):
        res = self.service.process_query("What is RANSAC?", is_online=False)
        self.assertEqual(res["mode"], "offline")
        self.assertIn("RANSAC", res["answer"])
        self.assertGreaterEqual(res["confidence"], 0.90)

    def test_03_ohrc_sensor_query(self):
        res = self.service.process_query("Explain OHRC, TMC and IIRS", is_online=True)
        self.assertIn("OHRC", res["answer"])
        self.assertIn("0.25 m/pixel", res["answer"])

    def test_04_live_news_query_offline(self):
        res = self.service.process_query("What is the latest lunar news?", is_online=False)
        self.assertEqual(res["mode"], "offline")
        self.assertIn("Offline Mode", res["answer"])

    def test_05_live_news_query_online(self):
        res = self.service.process_query("What is the latest lunar news?", is_online=True)
        self.assertEqual(res["mode"], "online")
        self.assertIn("ISRO", res["answer"])
        self.assertGreater(len(res["citations"]), 0)

    def test_06_sync_knowledge(self):
        sync_res = self.service.sync_latest_knowledge()
        self.assertEqual(sync_res["sync_status"], "updated")
        self.assertIn("timestamp", sync_res)


if __name__ == "__main__":
    unittest.main()
