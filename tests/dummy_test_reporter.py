from pytest_stats.reporters_registry import ResultsReporter


class DummyTestReporter(ResultsReporter):
    def report_session_finish(self, session_data):
        pass

    def report_session_start(self, session_data: dict):
        pass

    def report_test(self, test_data):
        pass
