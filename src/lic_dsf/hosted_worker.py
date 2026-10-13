"""Resource limits applied before the calculation engine loads its workbook."""
import resource
import sys
from .worker import main

if __name__ == '__main__':
    resource.setrlimit(resource.RLIMIT_CPU, (170, 175))
    resource.setrlimit(resource.RLIMIT_FSIZE, (16 * 1024 * 1024,) * 2)
    resource.setrlimit(resource.RLIMIT_NOFILE, (128, 128))
    if sys.platform == 'linux':
        resource.setrlimit(resource.RLIMIT_AS, (3 * 1024 ** 3,) * 2)
    raise SystemExit(main(sys.argv[1]))
