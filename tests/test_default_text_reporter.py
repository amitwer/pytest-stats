import pytest
from assertpy import assert_that, soft_assertions

from pytest_stats.default_text_reporter import DefaultTextReporter
from pytest_stats.test_item_data import TestItemData
from pytest_stats.test_session_data import TestSessionData


# def test_me():
#     reporter = DefaultTextReporter()
#     reporter.report_test()
#     reporter.report_session_start()
#     reporter.report_session_finish()
class TestDefaultTextReporter:
    reporter: DefaultTextReporter

    @pytest.fixture(autouse=True)
    def setup(self):
        self.reporter = DefaultTextReporter()

    def test_session_start_is_storing_data(self):
        session_data = TestSessionData()
        session_data.session_id = 'session_id'
        self.reporter.report_session_start(session_data=session_data)
        assert_that(self.reporter._session_data).is_equal_to(session_data)

    def test_reported_test_is_stored(self):
        test_data = TestItemData()
        test_data.name = 'my_test'
        self.reporter.report_test(test_data=test_data)
        assert_that(self.reporter._tests).is_equal_to([test_data])

    def test_reported_multiple_tests_are_stored(self):
        test_data = []
        for name in ['test1', 'test2', 'test3']:
            td = TestItemData()
            td.name = name
            self.reporter.report_test(test_data=td)
            test_data.append(td)

        assert_that(self.reporter._tests).is_equal_to(test_data)

    def test_report_session_finished_prints_summary(self, caplog):
        session_data = TestSessionData()
        session_data.session_id = 'session_id'
        self.reporter.report_session_start(session_data=session_data)
        tests=[]
        for name in ['test1', 'test2', 'test3']:
            td = TestItemData()
            td.name = name
            self.reporter.report_test(test_data=td)
            tests.append(td)
        caplog.clear()
        self.reporter.report_session_finish(session_data=session_data)
        output = caplog.text
        with soft_assertions():
            assert_that(output).contains(str(session_data))
            for test in tests:
                assert_that(output).contains(str(test))

