class TestSessionData:
    session_id: str
    status: str
    failed_tests: int
    collected_tests: int

    def __str__(self: 'TestSessionData') -> str:
        return f'<{self.__class__.__name__}: {str(vars(self))}>'
