"""Create one complete Minecraft client environment for each test function."""

import pytest

from test_infrastructure import LiveMinecraftTest, load_configuration


CONFIGURATION = load_configuration()


@pytest.fixture
def live_test(request):
    """Start and stop one live test client environment."""
    with LiveMinecraftTest(CONFIGURATION, request.node.nodeid) as instance:
        yield instance
