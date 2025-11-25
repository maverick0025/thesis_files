
from __future__ import division

from twisted.internet.protocol import ServerFactory, ClientFactory, Protocol
from twisted.internet.error import ConnectionClosed
from twisted.internet.defer import Deferred

from benchlib import Client, driver, rotate_local_intf


class Client(Client):
    def __init__(self, reactor, host, portNumber):
        super(Client, self).__init__(reactor)
        self._host = host
        self._portNumber = portNumber
        self._factory = ClientFactory()


    def _request(self):
        finished = Deferred()
        factory = ClientFactory()
        factory.protocol = Protocol
        factory.clientConnectionLost = factory.clientConnectionFailed = lambda connector, reason: finished.errback(reason)
        finished.addErrback(self._filterFinished)
        self._reactor.connectTCP(self._host, self._portNumber, factory)
        finished.addCallback(self._continue)
        finished.addErrback(self._stop)


    def _filterFinished(self, reason):
        reason.trap(ConnectionClosed)


class CloseConnection(Protocol):
    def makeConnection(self, transport):
        transport.loseConnection()



def main(reactor, duration):
    concurrency = 50

    factory = ServerFactory()
    factory.protocol = CloseConnection
    port = reactor.listenTCP(0, factory,
                             interface=rotate_local_intf())

    client = Client(reactor, port.getHost().host, port.getHost().port)
    d = client.run(concurrency, duration)
    return d



if __name__ == '__main__':
    import sys
    import accepts
    driver(accepts.main, sys.argv)
