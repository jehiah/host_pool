"""
A generic interface to track a list of remote hosts
to allow auto-backoff from a failed remote host.

by Jehiah Czebotar - http://github.com/jehiah/host_pool
"""
import logging
import time

__version__ = "0.1"

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
    @parameter <bool> reset_on_all_failed - reset all hosts to alive when all are marked as failed.
    @parameter <int> initial_retry_delay - seconds to delay after initial host failure. default: 30
    """
    def __init__(self, hosts, retry_failed_hosts=-1, retry_interval=-1, max_retry_interval=900, reset_on_all_failed=True, debug=True, initial_retry_delay=30):
        assert isinstance(hosts, (list, tuple))
        assert hosts, "You must provide atleast one host"
        assert isinstance(retry_failed_hosts, int)
        assert isinstance(retry_interval, int)
        assert isinstance(max_retry_interval, int)
        assert isinstance(reset_on_all_failed, bool)
        assert isinstance(debug, bool)
        assert isinstance(initial_retry_delay, int)
        
        self.hosts=hosts
        self.host_count = len(hosts)
        self.next_host = 0
        self.status = dict([[host, dict(next_retry=0, retry_count=0, retry_delay=initial_retry_delay, dead=False, host=host)] for host in hosts])
        self.retry_failed_hosts = retry_failed_hosts
        self.retry_interval = retry_interval
        self.max_retry_interval = max_retry_interval
        self.reset_on_all_failed = reset_on_all_failed
        self.initial_retry_delay = initial_retry_delay
        self.debug = debug
    
    def reset(self):
        """put all hosts back in an `alive` state"""
        for host in self.hosts:
            self.success(host)
    
    def get(self):
        """Get the next available host, implementing retry logic as appropriate
            raises `NoHostsAvailable` when all hosts are in a failed state if reset_on_all_failed == False
        """
        for i in range(self.next_host, self.next_host + self.host_count):
            index = i % self.host_count
            host = self.hosts[index]
            status = self.status[host]
            if not status['dead']:
                self.next_host = index + 1
                return host
            else:
                # have we passed the max retries for this host
                if self.retry_failed_hosts != -1 and status['retry_count'] > self.retry_failed_hosts:
                    if self.debug:
                        logging.info('passed retry_failed_hosts limit of %d for host %s (retried %d)' % (self.retry_failed_hosts, host, status['retry_count']))
                    continue
                # is it at a retry stage
                # increment the counters for when we can retry this host next
                # this will be cleared if this try is successfull. subsequeent calls 
                # for failed(host) will do nothing
                if status['next_retry'] < time.time():
                    if self.debug:
                        logging.info('host %s in failed state (after %d tries). retrying' % (host, status['retry_count']))
                    status['retry_count'] += 1
                    if self.retry_interval == -1 :
                        status['retry_delay'] = min(status['retry_delay'] * 2, self.max_retry_interval)
                    else:
                        status['retry_delay'] = self.retry_interval
                    status['next_retry'] = time.time() + status['retry_delay']
                    self.next_host = index + 1
                    return host
        
        if self.reset_on_all_failed:
            self.reset()
            index = self.next_host % self.host_count
            host = self.hosts[index]
            self.next_host = index + 1
            logging.info('all hosts are failed; returning %s' % host)
            return host
        else:
            raise NoHostsAvailable()
    
    def success(self, host):
        """mark that a host had a successful connection/request"""
        assert host in self.hosts
        status = self.status[host]
        status['dead'] = False
    
    def failed(self, host):
        """mark that a host had a failed connection/request"""
        assert host in self.hosts
        status = self.status[host]
        if not status['dead']:
            status['dead'] = True
            status['retry_count'] = 0
            if self.retry_interval == -1:
                status['retry_delay'] = self.initial_retry_delay
            else:
                status['retry_delay'] = 0
            status['next_retry'] = time.time() + status['retry_delay']
    
    def stats(self):
        """Return a dictionary with the current status of this HostPool"""
        alive = [x for x in self.status.values() if not x.get('dead')]
        dead = [x for x in self.status.values() if x.get('dead')]
        return dict(alive=alive, dead=dead, hosts=self.status.keys())
        