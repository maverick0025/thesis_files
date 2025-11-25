
from benchlib import multidriver

import accepts, tcp, iteration, names, threads, web, pb

if __name__ == '__main__':
    multidriver(
        accepts.main, tcp.main, iteration.main, names.main, threads.main, web.main, pb.main)
