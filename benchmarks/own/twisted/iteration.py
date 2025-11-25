
from __future__ import division

import os,sys
# TWISTED = [relative('lib/twisted-trunk'), relative('lib/zope.interface'), relative('own/twisted')]

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../lib/twisted-trunk")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../own/twisted")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../lib/zope.interface")))
sys.path.append("/home/s265d007/Documents/projs/th/benchmarks-branch-default/lib/twisted-trunk")
sys.path.append("/home/s265d007/Documents/projs/th/benchmarks-branch-default/lib/zope.interface")
sys.path.append("/home/s265d007/Documents/projs/th/benchmarks-branch-default/own/twisted")



from benchlib import Client, driver


class Client(Client):
    def _request(self):
        self._reactor.callLater(0.0, self._continue, None)



def main(reactor, duration):
    concurrency = 10

    client = Client(reactor)
    d = client.run(concurrency, duration)
    return d



if __name__ == '__main__':
    import sys
    import iteration
    driver(iteration.main, sys.argv)
