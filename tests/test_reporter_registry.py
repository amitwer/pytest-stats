from unittest.mock import MagicMock

import pytest
from assertpy import assert_that

from pytest_stats.reporters_registry import ReportersRegistry
from pytest_stats.test_item_data import TestItemData
from pytest_stats.test_session_data import TestSessionData


def test_registering_a_reporter():
    registry = ReportersRegistry()
    mock_reporter = MagicMock()
    registry.register(reporter=mock_reporter)
    assert_that(registry._reporters).is_equal_to({mock_reporter})


def test_report_session_start_doesnt_fail_when_there_are_no_registered_reporters():
    registry = ReportersRegistry()
    registry.report_session_start(TestSessionData())
    # no assertion, as there is nothing to assert, just want to make sure no exception here


@pytest.mark.parametrize('method,param_name,data_cls', [
    ('report_test', 'test_data', TestItemData),
    ('report_session_finish', 'session_data', TestSessionData),
    ('report_session_start', 'session_data', TestSessionData),
])
def test_registry_calls_all_reporters(method, param_name, data_cls):
    data = data_cls()
    registry = ReportersRegistry()
    mock_reporter1 = MagicMock()
    mock_reporter2 = MagicMock()
    registry.register(mock_reporter1)
    registry.register(mock_reporter2)
    getattr(registry, method)(**{param_name: data})

    getattr(mock_reporter1, method).assert_called_with(**{param_name: data})
    getattr(mock_reporter2, method).assert_called_with(**{param_name: data})


def report_test_execution_status(self, test_data):
    for reporter in self._reporters:
        reporter.report_test_execution_status(test_data=test_data)


def report_test_teardown_status(self, test_data):
    for reporter in self._reporters:
        reporter.report_test_teardown_status(test_data=test_data)


def report_session_finish(self, session_data):
    for reporter in self._reporters:
        reporter.report_session_finish(session_data=session_data)
