from copy import copy
from typing import Optional, Set


class TestItemData:
    name: str
    test_start_protocol: float
    test_end_protocol: float
    test_start_setup: float
    test_end_setup: float
    test_duration_setup: float
    result_setup: str
    session_id: str
    fullname: str
    id: str
    rerun_number: str
    test_start_call: float
    test_end_call: float
    test_duration_call: float
    result_call: str
    test_start_teardown: float
    test_end_teardown: float
    test_duration_teardown: float
    result_teardown: str
    test_output: str
    marks: Set[str]
    fail_msg: Optional[str]
    stack_trace: Optional[str]

    def __str__(self: 'TestItemData') -> str:
        d = copy(vars(self))
        if 'test_output' in d:
            d.pop('test_output')
        return f'Test::{self.name}:: {d}>'

    def set_step_status(self, when: str, start: float, end: float, duration: float, outcome: str) -> None:
        setattr(self, f'test_start_{when}', start)
        setattr(self, f'test_end_{when}', end)
        setattr(self, f'test_duration_{when}', duration)
        setattr(self, f'result_{when}', outcome)
