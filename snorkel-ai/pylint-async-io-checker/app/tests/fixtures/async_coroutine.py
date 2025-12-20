"""Test fixture: function with @asyncio.coroutine decorator."""
import asyncio
import time

@asyncio.coroutine
def old_style_coroutine():
    """Old-style coroutine with blocking I/O."""
    # This should trigger a warning
    time.sleep(1)
    return "done"

