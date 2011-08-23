"""
this is a py.test test file
"""
import host_pool


def test_basic():
    pool = host_pool.HostPool(['a','b','c'])
    assert [pool.get(), pool.get(), pool.get(), pool.get()] == ['a', 'b', 'c', 'a']
    pool.failed('a')
    pool.failed('b')
    assert pool.get() == 'c'
    pool.success('c')
    assert pool.get() == 'c'
    assert pool.get() == 'c'
    pool.success('a')
    assert pool.get() in ['a', 'c']

def test_raise_no_hosts_available():
    pool = host_pool.HostPool(['a'])
    pool.failed('a')
    assert pool.get() == 'a'

    pool = host_pool.HostPool(['a'], reset_on_all_failed=False)
    pool.failed('a')
    try:
        pool.get()
    except host_pool.NoHostsAvailable:
        pass
    stats = pool.stats()
    assert len(stats['alive']) == 0
    assert len(stats['dead']) == 1
