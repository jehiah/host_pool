host_pool
=========

A generic interface to track a list of remote hosts
to allow auto-backoff from a failed remote host.

    pool = host_pool.HostPool(['servera','serverb'])
	endpoint = pool.get()
	pool.success(endpoint)
	endpoint = pool.get()
	pool.failed(endpoint)

