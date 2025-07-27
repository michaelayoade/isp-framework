"""Network API Endpoints (alias).

This file simply re-exports the router defined in ``network_modular.py`` so that
other modules can import ``app.api.v1.endpoints.network`` without needing to
know the original filename. This helps us migrate from the old
``network_modular.py`` name to the simplified ``network.py`` with minimal code
changes.
"""

from .network_modular import router  # noqa: F401
