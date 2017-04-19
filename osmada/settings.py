from .base_settings import *

try:
    from .local_settings import *
except ImportError:
    import sys; sys.stderr.write('You are using default settings, See README.md if you want to override\n')
    pass
