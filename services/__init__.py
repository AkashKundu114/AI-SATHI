import os, sys
_this_dir = os.path.abspath(os.path.dirname(__file__))
_backend_services = os.path.abspath(os.path.join(_this_dir, '..', 'backend', 'services'))
if os.path.isdir(_backend_services):
    __path__.insert(0, _backend_services)
