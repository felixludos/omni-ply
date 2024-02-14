from typing import Callable, Union, Optional, Any, Iterator, Iterable, Hashable, Type, \
	Sequence, List, Tuple, Union, Mapping, Set, Dict, TypeVar

import inspect
import logging
from functools import lru_cache
from collections import OrderedDict, UserDict, namedtuple

from itertools import chain, product

from omnibelt import agnostic, unspecified_argument, filter_duplicates, \
	extract_function_signature, args2kwargs
from omnibelt.crafts import InheritableCrafty, NestableCraft, \
	AbstractCrafty, AbstractCraft, AbstractSkill



prt = logging.getLogger('omniply')


