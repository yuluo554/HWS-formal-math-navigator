"""`python -m hws_formal_math.viewer` 入口"""

import sys

from hws_formal_math.logging import _ensure_utf8_stdio
from hws_formal_math.viewer.main import main

if __name__ == "__main__":
    _ensure_utf8_stdio()
    sys.exit(main())
