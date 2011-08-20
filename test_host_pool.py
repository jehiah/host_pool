"""
this is a py.test test file
"""
import host_pool


def test_basic():
    pool = host_pool.HostPool(['a','b','c'])
    pool.failed('a')
    pool.failed('b')
    assert pool.get() == 'c'
    pool.success('c')
    assert pool.get() == 'c'
    assert pool.get() == 'c'
    pool.success('a')
    assert pool.get() in ['a', 'c']
