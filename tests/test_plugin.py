import pytest
from _pytest.config import ExitCode
from _pytest.pytester import Pytester
from assertpy import assert_that, soft_assertions

from pytest_stats.default_text_reporter import DefaultTextReporter
from tests.dummy_test_reporter import DummyTestReporter


class TestPlugin:
    _pytester: Pytester

    @pytest.fixture(autouse=True)
    def setup(self, pytester: Pytester):
        self._pytester = pytester

    def test_command_line_has_collect_stats(self):
        self._pytester.makepyfile(
            """
            def test_passing():
                pass
        """
        )
        result = self._pytester.runpytest("--collect-stats")
        result.assert_outcomes(passed=1)

    def test_all_hooks_are_registered(self, request):
        with soft_assertions():
            assert_that(self._get_hook_implementations(hooked_function='pytest_addoption', request=request)).is_length(
                1)
            assert_that(
                self._get_hook_implementations(hooked_function='pytest_runtest_protocol', request=request)).is_length(1)
            assert_that(
                self._get_hook_implementations(hooked_function='pytest_runtest_makereport', request=request)).is_length(
                1)

    @staticmethod
    def _get_hook_implementations(hooked_function, request):
        return [x for x in getattr(request.config.hook, hooked_function)._hookimpls if x.plugin_name == 'pytest_stats']

    @pytest.fixture
    def hookrecorder(self, request, pytester: pytest.Pytester):
        return pytester.make_hook_recorder(request.config.pluginmanager)

    def test_get_test_item_data_returns_the_correct_value(self):

        self._pytester.makepyfile(
            """
            from pytest_stats.pytest_stats import get_test_item_data
            from assertpy import assert_that
            def test_passing(request):
                data= get_test_item_data(item=request.node)
                assert_that(data).is_same_as(request.node.stash['test_data'])
                logging.info('assertion done!')
        """
        )
        res = self._pytester.runpytest()
        # noinspection PyUnresolvedReferences
        assert_that(str(res.stdout)).contains("assertion done!")

    def test_get_test_session_data_returns_the_correct_value(self):
        self._pytester.makepyfile(
            """
            from pytest_stats.pytest_stats import get_test_session_data
            from assertpy import assert_that
            def test_passing(request):
                data= get_test_session_data(session=request.session)
                assert_that(data).is_same_as(request.session.stash['session_data'])
                logging.info('assertion done!')
        """
        )
        res = self._pytester.runpytest()
        # noinspection PyUnresolvedReferences
        assert_that(str(res.stdout)).contains("assertion done!")
    def test_hook_for_env_is_available(self):
        self._pytester.makeconftest(
            """
            import pytest
            @pytest.hookimpl()
            def pytest_stats_env_data(session_data:dict):
                print('pytest_stats_env_data - test-output')
                session_data.wazoo = 'Test'
            """
        )
        self._pytester.makepyfile(
            """
            def test_passing():
                pass
        """
        )
        res = self._pytester.runpytest()
        # noinspection PyUnresolvedReferences
        hook_call = next(filter(lambda x: x._name == 'pytest_stats_env_data', res.reprec.calls))
        session_data = hook_call.session_data
        assert_that(session_data).has_wazoo('Test')
        assert_that(str(res.stdout)).contains("pytest_stats_env_data - test-output")

    def test_result_reporter_is_registered(self):
        self._pytester.makeconftest(
            """
            import pytest
            from tests.dummy_test_reporter import DummyTestReporter
            class MyReporter(DummyTestReporter):
                def report_session_start(session_data):
                    print(f'session_data: {session_data}')
                    pass
            
            @pytest.hookimpl()
            def pytest_stats_register_reporters(reporters:'ReportersRegistry'):
                print('registering custom reporter!')
                reporters.register(MyReporter())
            """
        )
        self._pytester.makepyfile(
            """
            def test_passing():
                pass
        """
        )
        res = self._pytester.runpytest('--log-cli-level=DEBUG')
        assert_that(str(res.stdout)).contains('registering custom reporter!')

    def test_reporter_is_called_to_store_env(self):
        self._pytester.makeconftest(
            """
        import logging
        import pytest
        from tests.dummy_test_reporter import DummyTestReporter
        class MyReporter(DummyTestReporter):
            def report_session_start(self, session_data:dict):
                print(f'called to store execution data: {session_data}')
           
        @pytest.hookimpl()
        def pytest_stats_env_data(session_data:dict):
            session_data.wazoo = 'Test'
                
        @pytest.hookimpl()
        def pytest_stats_register_reporters(reporters:'ReportersRegistry'):
            reporters.register(MyReporter())
        """
        )
        self._pytester.makepyfile(
            """
            def test_passing():
                pass
        """
        )
        res = self._pytester.runpytest('--log-cli-level=DEBUG', '--disable-default-text-reporter')
        assert_that(str(res.stdout)).contains('called to store execution data:').contains("'wazoo': 'Test'")

    def test_env_data_contains_session_id(self):
        self._pytester.makeconftest(
            """
        import pytest
        from pytest_stats.test_session_data import TestSessionData
        from tests.dummy_test_reporter import DummyTestReporter
        
        class MyReporter(DummyTestReporter):
            def report_session_start(self, session_data:TestSessionData):
                assert type(session_data) == TestSessionData
                print(f'Stats session id is: {session_data.session_id}')

        @pytest.hookimpl()
        def pytest_stats_register_reporters(reporters:'ReportersRegistry'):
            reporters.register(MyReporter())
        """
        )
        self._pytester.makepyfile(
            """
            def test_passing():
                pass
        """
        )
        res = self._pytester.runpytest()
        # noinspection PyUnresolvedReferences
        hook_call = next(filter(lambda x: x._name == 'pytest_stats_env_data', res.reprec.calls))
        session_id = hook_call.session_data.session_id
        assert_that(str(res.stdout)).contains(f"Stats session id is: {session_id}")

    def test_single_test_results_are_reported(self):
        self._pytester.makeconftest(
            """
            import pytest
            from tests.dummy_test_reporter import DummyTestReporter
            from pytest_stats.test_item_data import TestItemData
            
            class MyReporter(DummyTestReporter):
                def report_test(self, test_data:dict):
                    assert type(test_data) == TestItemData 
                    print(f'got test data: {test_data}')
                   
            @pytest.hookimpl()
            def pytest_stats_register_reporters(reporters:'ReportersRegistry'):
                reporters.register(MyReporter())
            """
        )
        self._pytester.makepyfile(
            """
            def test_passing():
                pass
        """
        )
        res = self._pytester.runpytest()
        assert_that(str(res.stdout)).contains(f"got test data:")

    def test_default_text_reporter_is_registered(self):
        self._pytester.makeconftest(
            """
            
            def pytest_sessionfinish(session: 'Session',exitstatus) -> None:
                print(f'Registered reporters: {session.stash["stats_reporters"]._reporters.pop().__class__.__name__ }')

        """)
        self._pytester.makepyfile(
            """          
            def test_passing():
                pass
        """
        )
        res = self._pytester.runpytest()
        assert_that(str(res.stdout)).contains(f"Registered reporters: {DefaultTextReporter.__name__}")

    def test_default_text_reporter_is_not_registered_when_sending_disable_text_reporter_to_pytest(self):
        self._pytester.makeconftest(
            """          
            def pytest_sessionfinish(session: 'Session',exitstatus) -> None:
                print(f'Registered reporters: {session.stash["stats_reporters"]._reporters}')
        """)
        self._pytester.makepyfile(
            """          
            def test_passing():
                pass
        """
        )
        res = self._pytester.runpytest('--disable-default-text-reporter', '--log-cli-level=DEBUG')
        assert_that(str(res.stdout)).contains("Registered reporters: set()") \
            .contains('--disable-default-text-reporter flag was used - not using default reporter')

    def test_all_mandatory_fields_are_reported_per_session(self):
        self._pytester.makeconftest(
            """ 
            import pytest
            import typing
            from assertpy import assert_that
            from tests.dummy_test_reporter import DummyTestReporter
            class MyTestReporter(DummyTestReporter):

                def report_session_finish(self, session_data):
                    assert_that(vars(session_data).keys()).is_equal_to(typing.get_type_hints(session_data).keys())
                    print('Assertion Done!')


            @pytest.hookimpl()
            def pytest_stats_register_reporters(reporters:'ReportersRegistry'):
                reporters.register(MyTestReporter())

        """)
        self._pytester.makepyfile(
            """          
            def test_passing():
                pass
        """
        )
        res = self._pytester.runpytest()
        assert_that(res.ret).is_equal_to(ExitCode.OK)
        assert_that(str(res.stdout)).contains('Assertion Done!')
    def test_all_mandatory_fields_are_reported_per_test(self):
        self._pytester.makeconftest(
            """ 
            import pytest
            import typing
            from assertpy import assert_that
            from tests.dummy_test_reporter import DummyTestReporter
            class MyTestReporter(DummyTestReporter):
            
                def report_test(self, test_data):
                    hints = {a:b for (a,b) in \
                    typing.get_type_hints(test_data).items() if type(None) not in typing.get_args(b)}
                    assert_that(vars(test_data).keys()).is_equal_to(hints.keys())
                    print('Assertion Done!')


            @pytest.hookimpl()
            def pytest_stats_register_reporters(reporters:'ReportersRegistry'):
                reporters.register(MyTestReporter())

        """)
        self._pytester.makepyfile(
            """          
            def test_passing():
                pass
        """
        )
        res = self._pytester.runpytest()
        assert_that(res.ret).is_equal_to(ExitCode.OK)
        assert_that(str(res.stdout)).contains('Assertion Done!')

    def test_logs_are_in_test_output(self):
        self._pytester.makeconftest(
            """ 
            import pytest
            import logging
            from assertpy import assert_that
            from tests.dummy_test_reporter import DummyTestReporter
            class MyTestReporter(DummyTestReporter):
                def report_test(self, test_data):
                    assert_that(test_data.test_output).contains('info log')\
                    .contains('debug log')\
                    .contains('error log')\
                    .contains('warn log')
                    print('Assertion Done!')


            @pytest.fixture(autouse=True)
            def chat():
                logging.warning('in setup')
                yield
                logging.warning('in teardown')
                
            @pytest.hookimpl()
            def pytest_stats_register_reporters(reporters:'ReportersRegistry'):
                reporters.register(MyTestReporter())

        """)
        self._pytester.makepyfile(
            """    
            import logging      
            def test_chatting():
                logging.info('info log')
                logging.error('error log')
                logging.debug('debug log')
                logging.warning('warn log')
        """
        )
        res = self._pytester.runpytest('--log-cli-level=DEBUG')
        assert_that(res.ret).is_equal_to(ExitCode.OK)
        assert_that(str(res.stdout)).contains('Assertion Done!')

    def test_all_fields_are_reported_on_test_failure(self):
        self._pytester.makeconftest(
            """ 
            import pytest
            import typing
            from assertpy import assert_that
            from tests.dummy_test_reporter import DummyTestReporter
            class MyTestReporter(DummyTestReporter):

                def report_test(self, test_data):
                    assert_that(vars(test_data).keys()).is_equal_to(typing.get_type_hints(test_data).keys())
                    print('Assertion Done!')


            @pytest.hookimpl()
            def pytest_stats_register_reporters(reporters:'ReportersRegistry'):
                reporters.register(MyTestReporter())

        """)
        self._pytester.makepyfile(
            """          
            def test_passing():
                assert False 
        """
        )
        res = self._pytester.runpytest()
        assert_that(res.ret).is_equal_to(ExitCode.TESTS_FAILED)
        assert_that(str(res.stdout)).contains('Assertion Done!')

    @pytest.mark.parametrize('test_file,expected_error_string', [
        ("""
                   import pytest
                   @pytest.fixture(autouse=True)
                   def fail_setup():
                       raise RuntimeError('Failed in fixture setup')
                   def test_passing():
                       pass
               """, "Failed in fixture setup"),
        ("""
                   import pytest
                   @pytest.fixture(autouse=True)
                   def fail_teardown():
                        yield
                        raise RuntimeError('Failed in fixture teardown')
                   def test_passing_for_teardown():
                        pass
                """, "Failed in fixture teardown"),
        ("""
            import pytest
            def test_failing():
                pytest.fail('This test is doomed')
        """, "This test is doomed")

    ],
                             ids=['fail in setup', 'fail in teardown', 'fail in test']
                             )
    def test_failure_message_is_reported(self, test_file, expected_error_string):
        self._pytester.makeconftest(
            f""" 
            import logging
            import pytest
            import typing
            from assertpy import assert_that
            from tests.dummy_test_reporter import DummyTestReporter
            class MyTestReporter(DummyTestReporter):
                def report_test(self, test_data):
                    assert_that(test_data).has_fail_msg("{expected_error_string}")
                    logging.info('Assertion Done!')


            @pytest.hookimpl()
            def pytest_stats_register_reporters(reporters:'ReportersRegistry'):
                reporters.register(MyTestReporter())

        """)
        self._pytester.makepyfile(test_file)
        res = self._pytester.runpytest('--log-cli-level=INFO')
        assert_that(str(res.stdout)).contains('Assertion Done!')

    # noinspection SpellCheckingInspection
    @pytest.mark.parametrize('test_file,expected_error_string', [
        ("raise RuntimeError('Test is failing')", 'Test is failing'),
        ("""
            def test_not_compiling():
            adsafadsfasdfd
            """, "IndentationError: expected an indented block")
    ], ids=['Throws Runtime error', 'indent error'])
    def test_collection_error_is_safe(self, test_file, expected_error_string):
        self._pytester.makeconftest(
            f""" 
            import pytest
            import typing
            from assertpy import assert_that
            from tests.dummy_test_reporter import DummyTestReporter
            class MyTestReporter(DummyTestReporter):
                def report_session_finish(self, session_data):
                    assert_that(session_data.fail_msg)\
                    .contains('{expected_error_string}')
                    
                    assert_that(session_data.stack_trace).is_not_empty()
                    print('Assertion Done!')


            @pytest.hookimpl()
            def pytest_stats_register_reporters(reporters:'ReportersRegistry'):
                reporters.register(MyTestReporter())

        """)
        self._pytester.makepyfile(test_file)
        res = self._pytester.runpytest()
        assert_that(str(res.stdout)).contains('Assertion Done!')

    def test_default_text_reporter_is_registered_when_registering_another_reporter(self):
        self._pytester.makeconftest(
            """ 
            import pytest
            from tests.dummy_test_reporter import DummyTestReporter

            @pytest.hookimpl()
            def pytest_stats_register_reporters(reporters:'ReportersRegistry'):
                reporters.register(DummyTestReporter())
                             
            def pytest_sessionfinish(session: 'Session',exitstatus) -> None:
                reporters = session.stash['stats_reporters']._reporters
                print(f'Registered reporters: {reporters}, number of reporters: {len(reporters)}')
        """)
        self._pytester.makepyfile(
            """          
            def test_passing():
                pass
        """
        )

        res = self._pytester.runpytest()
        (assert_that(str(res.stdout))
         .contains(f"<{self._full_name(DummyTestReporter)} object at")
         .contains(f"<{self._full_name(DefaultTextReporter)} object at")
         .contains('number of reporters: 2'))

    @staticmethod
    def _full_name(cls) -> str:
        return f'{cls.__module__}.{cls.__qualname__}'

    def test_marks_are_collected(self):
        self._pytester.makeconftest(
            """ 
            import logging
            import pytest
            from assertpy import assert_that
            from tests.dummy_test_reporter import DummyTestReporter
            class MyTestReporter(DummyTestReporter):
                def report_test(self, test_data):
                    assert_that(test_data.marks).is_equal_to({"simple_mark","class_mark","mark_with_kwargs(a=1)",
                    "class_mark_with_kwargs(b=aaa)", "mark_with_args(1)"})
                    logging.info('Assertion Done!')
    
    
            @pytest.hookimpl()
            def pytest_stats_register_reporters(reporters:'ReportersRegistry'):
                reporters.register(MyTestReporter())
    
        """)
        self._pytester.makepyfile(
            """
            import pytest 
            @pytest.mark.class_mark
            @pytest.mark.class_mark_with_kwargs(b='aaa')
            class TestSomething:
                @pytest.mark.simple_mark
                @pytest.mark.mark_with_kwargs(a=1)          
                @pytest.mark.mark_with_args(1)          
                def test_passing():
                    pass
                """
        )
        res = self._pytester.runpytest('--log-cli-level=INFO')
        assert_that(str(res.stdout)).contains('Assertion Done!')
