import os
import tempfile
import unittest
from unittest.mock import patch

from core.time_utils import (
    format_delay_seconds,
    line_event_timestamp_to_jst_iso,
    timestamp_delay_seconds,
)


class TimeUtilsTests(unittest.TestCase):
    def test_line_timestamp_and_delay(self):
        event_time = line_event_timestamp_to_jst_iso(1785226380000)
        self.assertTrue(event_time.endswith("+09:00"))
        received_time = "2026-07-28T19:50:00+09:00"
        delay = timestamp_delay_seconds(event_time, received_time)
        self.assertGreater(delay, 0)
        self.assertIn("時間", format_delay_seconds(delay))


class WebhookQueueTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.queue_path = os.path.join(self.temp_dir.name, "queue.sqlite3")
        self.env_patch = patch.dict(os.environ, {"WEBHOOK_QUEUE_PATH": self.queue_path})
        self.env_patch.start()

    def tearDown(self):
        self.env_patch.stop()
        self.temp_dir.cleanup()

    def test_queue_is_persistent_and_deduplicates(self):
        from services.webhook_queue import claim_next, enqueue_events, mark_done, queue_status_counts

        event = {
            "webhookEventId": "evt-001",
            "timestamp": 1785226380000,
            "type": "message",
            "message": {"type": "text", "text": "1"},
        }
        first = enqueue_events({"destination": "bot-1", "events": [event]})
        second = enqueue_events({"destination": "bot-1", "events": [event]})
        self.assertEqual(first, {"inserted": 1, "duplicate": 0})
        self.assertEqual(second, {"inserted": 0, "duplicate": 1})

        queued = claim_next()
        self.assertEqual(queued["event_id"], "evt-001")
        self.assertEqual(queued["event"]["message"]["text"], "1")
        self.assertTrue(queued["received_at"].endswith("+09:00"))
        mark_done("evt-001")
        self.assertEqual(queue_status_counts().get("done"), 1)


class SheetsResponseTests(unittest.TestCase):
    def test_append_response_stores_timing_and_rejects_duplicate(self):
        from services import sheets_service

        headers = sheets_service.REQUIRED_SHEETS["responses"][0]
        patient = {"patient_id": "P001", "name": "患者A"}
        with (
            patch.object(sheets_service, "get_response_severity", return_value=("低", 1)),
            patch.object(sheets_service, "update_sheet"),
            patch.object(sheets_service, "read_sheet", return_value=[headers]),
            patch.object(sheets_service, "append_sheet") as append_sheet,
        ):
            appended = sheets_service.append_response(
                patient,
                "U001",
                "DISASTER",
                "SAFE",
                "無事",
                event_timestamp="2026-07-28T17:13:00+09:00",
                received_timestamp="2026-07-28T19:50:00+09:00",
                webhook_event_id="evt-001",
                is_redelivery=True,
                delay_seconds=9420,
            )
        self.assertTrue(appended)
        saved_row = append_sheet.call_args.args[1]
        self.assertEqual(len(saved_row), 18)
        self.assertEqual(saved_row[0], "2026-07-28T17:13:00+09:00")
        self.assertEqual(saved_row[14], "2026-07-28T19:50:00+09:00")
        self.assertEqual(saved_row[15:18], ["evt-001", "TRUE", 9420])

        existing_row = [""] * 18
        existing_row[15] = "evt-001"
        with (
            patch.object(sheets_service, "get_response_severity", return_value=("低", 1)),
            patch.object(sheets_service, "update_sheet"),
            patch.object(sheets_service, "read_sheet", return_value=[headers, existing_row]),
            patch.object(sheets_service, "append_sheet") as duplicate_append,
        ):
            appended = sheets_service.append_response(
                patient, "U001", "DISASTER", "SAFE", "無事", webhook_event_id="evt-001"
            )
        self.assertFalse(appended)
        duplicate_append.assert_not_called()


class CallbackTests(unittest.TestCase):
    def test_callback_acknowledges_after_enqueue(self):
        import app as app_module

        body = {
            "destination": "bot-1",
            "events": [{"webhookEventId": "evt-quick", "type": "message"}],
        }
        with patch("routes.webhook_routes.enqueue_events", return_value={"inserted": 1, "duplicate": 0}) as enqueue:
            response = app_module.app.test_client().post("/callback", json=body)
        self.assertEqual(response.status_code, 200)
        enqueue.assert_called_once_with(body)


if __name__ == "__main__":
    unittest.main()
