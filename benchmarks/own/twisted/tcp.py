"""
This benchmarks runs a trivial Twisted TCP echo server and a client pumps as
much data to it as it can in a fixed period of time.

The size of the string passed to each write call may play a significant
factor in the performance of this benchmark.
"""

from __future__ import division

import os,sys
# TWISTED = [relative('lib/twisted-trunk'), relative('lib/zope.interface'), relative('own/twisted')]

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../lib/twisted-trunk")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../own/twisted")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../lib/zope.interface")))

sys.path.append("/home/s265d007/Documents/projs/th/benchmarks-branch-default/lib/twisted-trunk")
sys.path.append("/home/s265d007/Documents/projs/th/benchmarks-branch-default/own/twisted")
sys.path.append("/home/s265d007/Documents/projs/th/benchmarks-branch-default/lib/zope.interface")


from twisted.internet.defer import Deferred
from twisted.internet.protocol import ServerFactory, ClientCreator, Protocol
from twisted.protocols.wire import Echo

from benchlib import driver, rotate_local_intf


class Counter(Protocol):
    count = 0

    def dataReceived(self, bytes):
        self.count += len(bytes)



class Client(object):
    _finished = None

    def __init__(self, reactor, host, port, server):
        self._reactor = reactor
        self._host = host
        self._port = port
        self._server = server


    def run(self, duration, chunkSize):
        self._duration = duration
        self._bytes = b'x' * chunkSize
        # Set up a connection
        cc = ClientCreator(self._reactor, Counter)
        d = cc.connectTCP(self._host, self._port)
        d.addCallback(self._connected)
        return d


    def _connected(self, client):
        self._client = client
        self._stopCall = self._reactor.callLater(self._duration, self._stop)
        client.transport.registerProducer(self, False)
        self._finished = Deferred()
        return self._finished


    def _stop(self):
        self.stopProducing()
        self._client.transport.unregisterProducer()
        self._finish(self._client.count)


    def _finish(self, value):
        if self._finished is not None:
            finished = self._finished
            self._finished = None
            finished.callback(value)


    def resumeProducing(self):
        self._client.transport.write(self._bytes)


    def stopProducing(self):
        self._client.transport.loseConnection()
        self._server.stopListening()

    def connectionLost(self, reason):
        self._finish(reason)


 
def main(reactor, duration):
    chunkSize = 16384

    server = ServerFactory()
    server.protocol = Echo
    serverPort = reactor.listenTCP(0, server,
                                   interface=rotate_local_intf())
    client = Client(reactor, serverPort.getHost().host,
                             serverPort.getHost().port, serverPort)
    d = client.run(duration, chunkSize)
    return d


if __name__ == '__main__':
    import sys
    import tcp
    driver(tcp.main, sys.argv)
