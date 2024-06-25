import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Set

if TYPE_CHECKING:
    from pytest_stats.test_session_data import TestSessionData
    from pytest_stats.test_item_data import TestItemData


class ResultsReporter(ABC):
    @abstractmethod
    def report_session_start(self, session_data: 'TestSessionData') -> None:
        pass

    @abstractmethod
    def report_session_finish(self, session_data: 'TestSessionData') -> None:
        pass

    @abstractmethod
    def report_test(self, test_data: 'TestItemData') -> None:
        pass


class ReportersRegistry:
    def __init__(self) -> None:
        self._reporters: Set[ResultsReporter] = set()

    def register(self, reporter: ResultsReporter) -> None:
        self._reporters.add(reporter)
        logging.debug('registered reporter %s', reporter)

    def report_test(self, test_data: 'TestItemData') -> None:
        for reporter in self._reporters:
            reporter.report_test(test_data=test_data)

    def report_session_start(self, session_data: 'TestSessionData') -> None:
        for reporter in self._reporters:
            reporter.report_session_start(session_data=session_data)

    def report_session_finish(self, session_data: 'TestSessionData') -> None:
        for reporter in self._reporters:
            reporter.report_session_finish(session_data=session_data)
