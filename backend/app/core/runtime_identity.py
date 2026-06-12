from __future__ import annotations

import os
from datetime import datetime, timezone
from uuid import uuid4


PROCESS_STARTED_AT = datetime.now(timezone.utc)
PROCESS_STARTUP_ID = f"api_{uuid4().hex[:12]}"
PROCESS_ID = os.getpid()
