import logging
from typing import TYPE_CHECKING, Optional, List

from pytest_stats.reporters_registry import ResultsReporter

if TYPE_CHECKING:
    from pytest_stats.test_item_data import TestItemData
    from pytest_stats.test_session_data import TestSessionData


class DefaultTextReporter(ResultsReporter):
    def __init__(self) -> None:
        self._tests: List['TestItemData'] = []
        self._session_data: Optional['TestSessionData'] = None

    def report_session_start(self, session_data: 'TestSessionData') -> None:
        logging.debug('Starting session with: %s', session_data)
        self._session_data = session_data

    def report_session_finish(self, session_data: 'TestSessionData') -> None:
        self._session_data = session_data
        self._print_report()

    def report_test(self, test_data: 'TestItemData') -> None:
        self._tests.append(test_data)

    def _print_report(self) -> None:
        logging.info("----------TEST STATS----------\r\n"
                     "Session Data\r\n %s\r\n"
                     "Tests:\r\n %s", self._session_data, '\r\n'.join([str(x) for x in self._tests])
                     )
