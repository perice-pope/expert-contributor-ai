"""Test fixture: async function with blocking I/O."""
import asyncio
import time
import requests

async def fetch_data():
    """Async function with blocking I/O."""
    # This should trigger a warning
    time.sleep(1)
    response = requests.get("https://example.com")
    return response.text

async def read_file():
    """Async function with file I/O."""
    # This should trigger a warning
    with open("data.txt", "r") as f:
        return f.read()

async def valid_async():
    """Async function without blocking I/O."""
    await asyncio.sleep(1)
    return "ok"

def sync_function():
    """Sync function - should not trigger warnings."""
    time.sleep(1)
    return "ok"




