from typing import Any, Iterable, Iterator, Type, Optional, Union, Self
from ...core.gaggles import AbstractGaggle, AbstractGame, AbstractGadget, LoopyGaggle, MutableGaggle
from ...core import Scope
from ..gaps import Context, ToolKit, tool
from ..simple import DictGadget

import random
import hashlib
import heapq
from collections import Counter
