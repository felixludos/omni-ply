from typing import Callable, Union, Optional, Any, Iterator, Iterable, Hashable, Type, \
	Sequence, List, Tuple, Union, Mapping, Set, Dict

import inspect
import logging
from collections import UserDict
from itertools import chain

from omnibelt import unspecified_argument, filter_duplicates, extract_function_signature



prt = logging.getLogger('omniply')


