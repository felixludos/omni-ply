from typing import Any, Iterable, Iterator, Type, Optional, Union, Self, Dict, List, Mapping
from ...core.gaggles import AbstractGaggle, AbstractGame, AbstractGadget, LoopyGaggle, MutableGaggle
# from ...core import Scope
from ...gears.mechanics import AbstractMechanics
from ..gaps import Context, ToolKit, tool, DictGadget
from omnibelt import JSONABLE
from omnibelt.staging import AbstractStaged, Staged, AutoStaged, AbstractSetup

import random
import hashlib
import heapq
import math
from collections import Counter
