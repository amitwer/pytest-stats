import logging
import os
import traceback
import uuid
from datetime import datetime
from typing import Optional, TYPE_CHECKING, List, Union, Any, Set

import pytest
from _pytest.config import PytestPluginManager, ExitCode, Config

from pytest_stats.default_text_reporter import DefaultTextReporter
from pytest_stats.reporters_registry import ReportersRegistry
from pytest_stats.test_item_data import TestItemData
from pytest_stats.test_session_data import TestSessionData

TEST_DATA_KEY = 'test_data'

if TYPE_CHECKING:
    from _pytest.config.argparsing import Parser
    from _pytest.mark import Mark
    from _pytest.nodes import Item, Collector
    from _pytest.reports import TestReport, CollectReport
    from _pytest.runner import CallInfo
    from _pytest.main import Session


def pytest_configure(config: 'Config') -> None:
    config.addinivalue_line("markers", "cool_marker: this one is for cool tests.")
    config.addinivalue_line(
        "markers", "mark_with(arg, arg2): this marker takes arguments."
    )
    registry = ReportersRegistry()
    config.stash['reporters'] = registry  # type: ignore[index]
    config.hook.pytest_stats_register_reporters(reporters=registry)


@pytest.hookimpl
def pytest_addhooks(pluginmanager: 'PytestPluginManager') -> None:
    from . import hooks  # pylint: disable=import-outside-toplevel
    pluginmanager.add_hookspecs(hooks)


# noinspection PyUnusedLocal
def _create_mark_string(m: 'Mark') -> str:
    if not m.args and not m.kwargs:
        return m.name
    args = [str(arg) for arg in m.args]
    kwargs = [f'{key}={str(val)}' for (key, val) in m.kwargs.items()]
    return f'{m.name}({", ".join(args + kwargs)})'


def _get_marks(item: 'Item') -> Set[str]:
    markers = [_create_mark_string(m) for m in item.iter_markers()]
    return set(markers)


# noinspection PyUnusedLocal
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_protocol(  # type: ignore[return]
        item: 'Item', nextitem: "Optional[Item]"  # pylint:disable=unused-argument
) -> Optional[object]:
    # noinspection PyTypeChecker
    test_data = get_test_item_data(item)
    # noinspection PyTypeChecker
    item.stash[TEST_DATA_KEY] = test_data  # type: ignore[index]
    test_data.session_id = _session_id(item.config)
    test_data.name = item.name
    test_data.marks = _get_marks(item)
    test_data.test_start_protocol = datetime.timestamp(datetime.now())
    yield
    test_data.test_end_protocol = datetime.timestamp(datetime.now())
    reporters(item.session).report_test(test_data=test_data)


def get_test_item_data(item: 'Item') -> TestItemData:
    return item.stash.get(TEST_DATA_KEY, TestItemData())  # type: ignore[arg-type]


# noinspection PyUnusedLocal
def pytest_addoption(parser: "Parser", pluginmanager: "PytestPluginManager") -> None:  # pylint:disable=unused-argument
    parser.addoption('--collect-stats', action='store_true', dest='collect_stats')
    parser.addoption('--disable-default-text-reporter', action='store_false', dest='use_default_text_reporter')


def _report_session_start(session: 'Session') -> None:
    session_data: TestSessionData = get_test_session_data(session=session)
    session_data.session_id = _session_id(session.config)
    session_data.xdist_worker_id = os.getenv('PYTEST_XDIST_WORKER', None)
    session_data.fail_msg = None
    session_data.stack_trace = None
    session_data.start_time = datetime.timestamp(datetime.now())
    reporters(session).report_session_start(session_data=session_data)


def reporters(session: 'Session') -> ReportersRegistry:
    return session.stash['stats_reporters']  # type: ignore[index]


def pytest_sessionstart(session: 'Session') -> None:
    session_data = TestSessionData()
    # noinspection PyTypeChecker
    session.stash['session_data'] = session_data  # type: ignore[index]
    reporters_registry = ReportersRegistry()
    session.config.hook.pytest_stats_env_data(session_data=session_data)
    _init_reporters(reporters_registry, session)
    _report_session_start(session)


def pytest_sessionfinish(session: 'Session', exitstatus: int) -> None:
    # noinspection PyTypeChecker
    session_data: TestSessionData = get_test_session_data(session)
    session_data.status = ExitCode(exitstatus).name
    session_data.collected_tests = session.testscollected
    session_data.failed_tests = session.testsfailed
    session_data.end_time = datetime.timestamp(datetime.now())
    reporters(session).report_session_finish(session_data=session_data)


def get_test_session_data(session: 'Session') -> TestSessionData:
    return session.stash['session_data']  # type: ignore[index]


def _init_reporters(reporters_registry: ReportersRegistry, session: 'Session') -> None:
    session.stash['stats_reporters'] = reporters_registry  # type: ignore[index]
    session.config.hook.pytest_stats_register_reporters(reporters=reporters_registry)
    if session.config.option.use_default_text_reporter:
        reporters_registry.register(DefaultTextReporter())
    else:
        logging.debug('--disable-default-text-reporter flag was used - not using default reporter')


@pytest.hookimpl
def pytest_load_initial_conftests(early_config: "Config", parser: "Parser", args: List[str]) -> None:
    session_id = str(uuid.uuid4())
    if early_config.pluginmanager.has_plugin('xdist'):
        parsed_args = parser.parse(args=args)
        if 'testrunuid' in parsed_args and parsed_args.testrunuid is not None:
            session_id = parsed_args.testrunuid
        else:
            args.append(f'--testrunuid={session_id}')
    # noinspection PyTypeChecker
    early_config.stash['stats_session_id'] = session_id  # type: ignore[index]


def _session_id(config: 'Config') -> str:
    if hasattr(config, 'workerinput'):
        return config.workerinput["testrunuid"]
    return config.stash['stats_session_id']  # type: ignore[index]


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item: "Item", call: "CallInfo[None]") -> Optional["TestReport"]:  # type: ignore[misc]
    output = yield
    test_state = output.get_result()
    # noinspection PyTypeChecker
    test_data: TestItemData = item.stash[TEST_DATA_KEY]  # type: ignore[index]
    test_data.set_step_status(
        when=call.when,
        start=call.start,
        end=call.stop,
        duration=call.duration,
        outcome=test_state.outcome)

    if test_state.when == 'setup':
        rerun_number = item.execution_count - 1 if hasattr(item, 'execution_count') else 0
        test_data.fullname = item.nodeid
        test_data.id = f'{item.nodeid}-{rerun_number}'
        test_data.rerun_number = rerun_number

    elif test_state.when == 'teardown':
        test_data.test_output = str(test_state.sections)


# noinspection PyUnusedLocal
def pytest_exception_interact(
        node: Union["Item", "Collector"],
        call: "CallInfo[Any]",
        report: Union["CollectReport", "TestReport"],  # pylint:disable=unused-argument
) -> None:
    if call.excinfo is None:
        return
    if call.when == 'collect':
        logging.debug('Got exception during collection, reporting error in session')
        session_data = get_test_session_data(session=node.session)
        session_data.fail_msg = str(call.excinfo.value)
        session_data.stack_trace = '\n'.join(traceback.format_tb(call.excinfo.tb))
    else:
        logging.debug('Collecting exception information for test')
        # noinspection PyTypeChecker
        test_data = node.stash[TEST_DATA_KEY]  # type: ignore[index]
        test_data.fail_msg = str(call.excinfo.value)
        test_data.stack_trace = '\n'.join(traceback.format_tb(call.excinfo.tb))
