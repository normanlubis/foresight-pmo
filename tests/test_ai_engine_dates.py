import json
import unittest
from datetime import timedelta
from unittest.mock import patch

from ai_engine import ai_predict_timeline
from mock_data import CURRENT_DATE, SPRINT_LENGTH_DAYS


class TimelineDateTests(unittest.TestCase):
    def test_predicted_date_is_derived_from_sprints_remaining(self):
        mock_response = json.dumps({
            "predicted_date": "2030-01-01",
            "confidence_p50": "2030-01-01",
            "confidence_p95": "2030-01-01",
            "sprints_remaining": 4,
            "avg_velocity": 10.0,
            "trend": "stable",
            "on_track": True,
            "risk_level": "medium",
            "key_risks": [],
            "recommendations": [],
            "narrative": ""
        })

        with patch("ai_engine._chat", return_value=mock_response):
            result = ai_predict_timeline({}, [], {})

        expected = (CURRENT_DATE + timedelta(days=4 * SPRINT_LENGTH_DAYS)).strftime("%Y-%m-%d")
        self.assertEqual(result["predicted_date"], expected)


if __name__ == "__main__":
    unittest.main()
