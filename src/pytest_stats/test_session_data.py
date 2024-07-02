from typing import Optional


class TestSessionData:
    session_id: str
    xdist_worker_id: Optional[str]
    status: str
    failed_tests: int
    collected_tests: int
    start_time: float
    end_time: float

    def __str__(self: 'TestSessionData') -> str:
        return f'<{self.__class__.__name__}: {str(vars(self))}>'
