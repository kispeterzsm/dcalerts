import unittest
from unittest.mock import patch

from dcalerts.decorators import notify
from dcalerts.messages import MessageHandler, make_message, send_message
from dcalerts import utils


class MessageFormattingTests(unittest.TestCase):
    def test_make_message_formats_strings_values_callables_and_nested_lists(self):
        def dynamic():
            return ["nested", 42]

        message = make_message(["start", dynamic, None], list_item_sep="|")

        self.assertEqual(message, "start|nested|42|None")

    def test_make_message_honors_special_separator_from_utils(self):
        message = make_message(["Result:", utils.bold("ok"), utils.inline_code("x")])

        self.assertEqual(message, "Result: **ok** `x`")


class UtilsFormattingTests(unittest.TestCase):
    def assertFormatsAs(self, value, expected):
        self.assertEqual(make_message(value), expected)

    def test_markdown_helpers(self):
        cases = [
            (utils.code_block("print(1)", "py"), "```py\nprint(1)```"),
            (utils.inline_code("x"), "`x`"),
            (utils.bold("x"), "**x**"),
            (utils.italic("x"), "*x*"),
            (utils.underline("x"), "__x__"),
            (utils.strikethrough("x"), "~~x~~"),
            (utils.spoiler("x"), "||x||"),
            (utils.quote("x"), "> x"),
            (utils.block_quote("x"), ">>> x"),
            (utils.link("site", "https://example.com"), "[site](https://example.com)"),
            (utils.mention("123"), "@123"),
            (utils.channel_mention("456"), "#456"),
            (utils.role_mention("789"), "@789"),
            (utils.emoji("wave"), ":wave:"),
            (utils.header("Title", level=2), "## Title"),
        ]

        for value, expected in cases:
            with self.subTest(expected=expected):
                self.assertFormatsAs(value, expected)

    def test_create_timer_uses_relative_discord_timestamp(self):
        with patch("dcalerts.utils.time.time", return_value=1000.2):
            self.assertEqual(utils.create_timer(42), "<t:1042:R>")


class WebhookSendingTests(unittest.TestCase):
    @patch("dcalerts.messages.requests.post")
    def test_send_message_posts_formatted_payload_to_url(self, post):
        send_message("https://discord.test/webhook", ["hello", "world"], list_item_sep="\n")

        post.assert_called_once_with(
            "https://discord.test/webhook", json={"content": "hello\nworld"}
        )
        post.return_value.raise_for_status.assert_called_once_with()

    @patch("dcalerts.messages.requests.post")
    def test_send_message_accepts_settings_dict(self, post):
        send_message({"webhook": "https://discord.test/settings"}, "hello")

        post.assert_called_once_with(
            "https://discord.test/settings", json={"content": "hello"}
        )
        post.return_value.raise_for_status.assert_called_once_with()

    @patch("dcalerts.messages.requests.post")
    def test_message_handler_send_uses_default_separator(self, post):
        MessageHandler("https://discord.test/handler").send(["a", "b"])

        post.assert_called_once_with(
            "https://discord.test/handler", json={"content": "a b"}
        )
        post.return_value.raise_for_status.assert_called_once_with()


class NotifyDecoratorTests(unittest.TestCase):
    @patch("dcalerts.messages.requests.post")
    def test_notify_without_parentheses_uses_runtime_settings(self, post):
        @notify
        def work(value):
            return value * 2

        result = work(
            21,
            dcalerts_settings={
                "webhook": "https://discord.test/decorator",
                "before": "before",
                "after": ["after", "done"],
                "separator": "|",
            },
        )

        self.assertEqual(result, 42)
        self.assertEqual(post.call_count, 2)
        post.assert_any_call("https://discord.test/decorator", json={"content": "before"})
        post.assert_any_call(
            "https://discord.test/decorator", json={"content": "after|done"}
        )

    @patch("dcalerts.messages.requests.post")
    def test_notify_with_settings_sends_before_and_after(self, post):
        @notify({"webhook": "https://discord.test/decorator", "before": "before", "after": "after"})
        def work():
            return "ok"

        self.assertEqual(work(), "ok")
        self.assertEqual(post.call_count, 2)
        post.assert_any_call("https://discord.test/decorator", json={"content": "before"})
        post.assert_any_call("https://discord.test/decorator", json={"content": "after"})

    @patch("dcalerts.messages.requests.post")
    def test_notify_with_keyword_settings_sends_error_message(self, post):
        @notify(
            dcalerts_settings={
                "webhook": "https://discord.test/decorator",
                "send_error": True,
                "error_message": "failed",
            }
        )
        def work():
            raise RuntimeError("boom")

        with self.assertRaises(RuntimeError):
            work()

        post.assert_called_once_with(
            "https://discord.test/decorator",
            json={"content": "failed ```\nRuntimeError: boom```"},
        )


if __name__ == "__main__":
    unittest.main()
