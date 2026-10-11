from pathlib import Path

import yaml


def test_daily_workflow_has_uae_schedule_and_manual_dispatch():
    workflow = yaml.safe_load(Path(".github/workflows/daily-amazon-research.yml").read_text())
    triggers = workflow[True]
    assert triggers["schedule"][0]["cron"] == "0 5 * * *"
    assert "workflow_dispatch" in triggers
    assert workflow["concurrency"]["cancel-in-progress"] is False

