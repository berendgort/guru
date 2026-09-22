"""Error classifier + CLI JSON envelopes."""

from __future__ import annotations

import json

from typer.testing import CliRunner

from guru.cli.main import app
from guru.core.errors import classify_error
from guru.models.forecast import Spot
from guru.search.exceptions import (
    GuruAmbiguousError,
    GuruHTTPError,
    GuruNotFoundError,
    GuruParseError,
)

runner = CliRunner()


def test_classify_error_vocabulary() -> None:
    assert classify_error(GuruNotFoundError("x")).error_type == "not_found"
    assert classify_error(GuruParseError("x")).error_type == "parse_error"
    assert classify_error(GuruHTTPError("x", status_code=503)).retryable is True
    assert classify_error(GuruHTTPError("x", status_code=404)).retryable is False
    amb = GuruAmbiguousError("a", candidates=[Spot(id=1, name="A")])
    assert classify_error(amb).error_type == "ambiguous"
    assert classify_error(ValueError("bad")).error_type == "validation_error"


def test_instruct_json() -> None:
    result = runner.invoke(app, ["instruct", "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["api_version"] == 1
    assert payload["data"]["preset"] == "WINDGURU_DEFAULT"
    assert payload["data"]["top_models"] == 3


def test_models_json() -> None:
    result = runner.invoke(app, ["models", "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert any(row["id"] == 3 for row in payload["data"])


def test_schema_forecast() -> None:
    result = runner.invoke(app, ["schema", "forecast"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert "properties" in payload["data"]["schema"]


def test_version_json() -> None:
    result = runner.invoke(app, ["version", "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["data"]["version"]
