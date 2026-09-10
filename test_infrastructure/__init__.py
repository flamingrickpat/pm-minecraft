"""Live Minecraft test infrastructure.

Code errors stop the test and retain their traceback.
Missing local programs stop collection with a clear configuration error.
Minecraft and process errors stop the current test with their log path.
"""

from .live_test import LiveMinecraftTest, load_configuration

__all__ = ["LiveMinecraftTest", "load_configuration"]
