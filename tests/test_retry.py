import pytest
from common.retry import retry


def test_retry_success_after_failures():
    calls = {'n': 0}

    @retry(max_attempts=3, initial_delay=0.01, backoff=1, exceptions=(ValueError,))
    def flaky():
        calls['n'] += 1
        if calls['n'] < 2:
            raise ValueError('temporary')
        return 'ok'

    assert flaky() == 'ok'
    assert calls['n'] == 2


def test_retry_raises_after_max():
    @retry(max_attempts=2, initial_delay=0.01, backoff=1, exceptions=(ValueError,))
    def always_fail():
        raise ValueError('no')

    with pytest.raises(ValueError):
        always_fail()
