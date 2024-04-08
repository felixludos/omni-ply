from typing import Iterator, Any, Iterable, Mapping, Self, Union, Callable
import random, math
from omnibelt import filter_duplicates

from ...core.abstract import AbstractGadget, AbstractGaggle, AbstractGame
from ...core.genetics import AbstractGenetic, GeneticBase
from ...core.gadgets import SingleGadgetBase
from ...core.gaggles import MultiGadgetBase

from ...core import Context
