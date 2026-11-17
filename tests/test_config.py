import unittest

from xenocode.config import XenoConfig


class ConfigTests(unittest.TestCase):

    def test_default_configuration(self):
        config = XenoConfig()

        self.assertEqual(config.provider, "ollama")
        self.assertEqual(config.model, "qwen2.5-coder:7b")

    def test_planner_fallback(self):
        config = XenoConfig()

        self.assertEqual(config.planner, config.model)

    def test_custom_models(self):
        config = XenoConfig(
            architect_model="architect-model",
            reviewer_model="review-model",
        )

        self.assertEqual(config.planner, "architect-model")
        self.assertEqual(config.reviewer, "review-model")

    def test_invalid_temperature(self):
        with self.assertRaises(ValueError):
            XenoConfig(temperature=5)

    def test_invalid_context(self):
        with self.assertRaises(ValueError):
            XenoConfig(num_ctx=100)

    def test_invalid_url(self):
        with self.assertRaises(ValueError):
            XenoConfig(ollama_url="invalid-url")


if __name__ == "__main__":
    unittest.main()
