import typing

import pytest

from pytest_stats.reporters_registry import ReportersRegistry

if typing.TYPE_CHECKING:
    from pytest_stats.test_session_data import TestSessionData


# noinspection PyUnusedLocal
@pytest.hookspec()
def pytest_stats_env_data(session_data: 'TestSessionData') -> None:  # pylint:disable=unused-argument
    """called on session start to get the environment details """


# noinspection PyUnusedLocal
@pytest.hookspec()
def pytest_stats_register_reporters(reporters: 'ReportersRegistry') -> None:  # pylint:disable=unused-argument
    """called on session start to get the environment details """
