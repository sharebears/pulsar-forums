import forums
from core.conftest import *  # noqa: F401, F403
from core.conftest import PLUGINS, POPULATORS
from forums.test_data import ForumsPopulator

PLUGINS.append(forums)
POPULATORS.append(ForumsPopulator)
