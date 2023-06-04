from typing import Callable, Union, Optional, Any, Iterator, Iterable, Hashable, Type, \
	Sequence, List, Tuple, Union, Mapping, Set, Dict

import inspect
import logging
from collections import OrderedDict, UserDict
from itertools import chain

from omnibelt import unspecified_argument, filter_duplicates, extract_function_signature
from omnibelt.crafts import InheritableCrafty, NestableCraft, \
	AbstractCrafty, AbstractCraft, AbstractSkill



prt = logging.getLogger('omniply')


