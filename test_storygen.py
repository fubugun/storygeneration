import unittest

from storygen import StoryRequest, StoryService, build_messages, check_story, demo_generate


class StoryGeneratorTests(unittest.TestCase):
    def setUp(self):
        self.request = StoryRequest.from_form(
            "雨夜，旧车站，机器人，重逢",
            "陈安",
            "年轻机械修理师",
            "沉默、善良",
            "寻找朋友",
            "科幻",
            "温暖",
            600,
        )

    def test_prompt_contains_story_order(self):
        messages = build_messages(self.request)
        self.assertIn("旧车站", messages[1]["content"])
        self.assertIn("年轻机械修理师", messages[1]["content"])

    def test_demo_story_passes_quality_check(self):
        story = demo_generate(self.request)
        report = check_story(story, self.request)
        self.assertEqual(report["关键词覆盖率"], "100%")
        self.assertTrue(report["通过质检"])

    def test_missing_keyword_is_reported(self):
        report = check_story("陈安是一名年轻机械修理师。最后，他回家了。", self.request)
        self.assertFalse(report["通过质检"])
        self.assertTrue(any("遗漏关键词" in item for item in report["问题"]))

    def test_identity_conflict_is_reported(self):
        request = StoryRequest.from_form(
            "雨夜，机器人",
            "陈安",
            "人类机械修理师",
            "沉默、善良",
            "修好机器人",
            "科幻",
            "温暖",
            100,
        )
        story = "雨夜里，机器人陈安走进车站。然而，他终于修好了自己。"
        report = check_story(story, request)
        self.assertFalse(report["通过质检"])
        self.assertIn("人类主角被写成机器人", report["角色冲突"])

    def test_service_runs_in_demo_mode(self):
        service = StoryService()
        story, report, attempts = service.generate(self.request)
        self.assertIn("陈安", story)
        self.assertTrue(report["通过质检"])
        self.assertEqual(attempts, 1)


if __name__ == "__main__":
    unittest.main()

