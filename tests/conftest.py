"""Shared pytest configuration and fixtures."""

import os

import pytest

from insighta_sdk.client import InsightaClient
from insighta_sdk.models import Credentials


def pytest_addoption(parser):
    parser.addoption("--live", action="store_true", default=False, help="Run live API tests")


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--live"):
        skip_live = pytest.mark.skip(reason="need --live option to run")
        for item in items:
            if "live" in item.keywords:
                item.add_marker(skip_live)


@pytest.fixture
def live_client():
    api_key = os.environ.get("INSIGHTA_DEV_API_KEY")
    if not api_key:
        pytest.skip("INSIGHTA_DEV_API_KEY not set")
    creds = Credentials(api_key=api_key, endpoint="https://dev.openapi.insighta.cloud")
    return InsightaClient(creds)
