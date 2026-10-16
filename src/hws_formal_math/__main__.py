"""包入口：python -m hws_formal_math"""

import sys

from hws_formal_math.logging import _ensure_utf8_stdio
from hws_formal_math.cli import main

if __name__ == "__main__":
    _ensure_utf8_stdio()
    sys.exit(main())
