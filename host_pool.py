import logging
import random
import time

class Error(Exception):
    pass

class NoHostsAvailable(Error):
    pass

class HostPool(object):
    """
    A generic interface to track a list of remote hosts
    and call .success(host) and .failed(host) to allow 
    auto-backoff from a failed remote host.
    
    @parameter <int> retry_failed_hosts - the number of times to retry a failed host. set to -1 for indefinite retries
    @parameter <int> retry_interval - seconds between retries. set to -1 for doubling retry intervals (ie: 1, 2, 4, 8, ...)
    @parameter <int> max_retry_interval - the maximum seconds to wait between retries
    """
    def __init__(self, hosts, retry_failed_hosts=-1, retry_interval=-1, max_retry_interval=900, debug=True):
        assert isinstance(hosts, (list, tuple))
        assert hosts, "You must provide atleast one host"
        assert isinstance(retry_failed_hosts, int)
        assert isinstance(retry_interval, int)
        assert isinstance(max_retry_interval, int)
        assert isinstance(debug, bool)
        
        self.hosts=hosts
        self.host_count = len(hosts)
        self.next_host = 0
        self.status = dict([[host, dict(next_retry=0, retry_count=0, retry_delay=1, dead=False)] for host in hosts])
        self.retry_failed_hosts=retry_failed_hosts
        self.retry_interval=retry_interval
        self.max_retry_interval=max_retry_interval
        self.debug = debug
    
    def get(self):
        for i in range(self.next_host, self.next_host + self.host_count):
            index = i % self.host_count
            host = self.hosts[index]
            status = self.status[host]
            if not status['dead']:
                self.next_host = index
                return host
            else:
                # have we passed the max retries for this host
                if self.retry_failed_hosts != -1 and status['retry_count'] > self.retry_failed_hosts:
                    continue
                # is it at a retry stage
                if status['next_retry'] < time.time():
                    status['retry_count'] += 1
                    status['retry_delay'] = min(status['retry_delay'] * 2, self.max_retry_interval)
                    status['next_retry'] = time.time() + status['retry_delay']
                    self.next_host = index
                    return host
        raise NoHostsAvailable()
    
    def success(self, host):
        assert host in self.hosts
        status = self.status[host]
        status['dead'] = False
    
    def failed(self, host):
        assert host in self.hosts
        status = self.status[host]
        if not status['dead']:
            status['dead'] = True
            status['retry_count'] = 0
            status['retry_delay'] = 1
            status['next_retry'] = time.time() + status['retry_delay'] # todo: retry_interval
        
        