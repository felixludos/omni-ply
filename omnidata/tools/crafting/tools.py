from typing import Tuple, List, Dict, Optional, Union, Any, Callable, Sequence, Iterator, Iterable, Type, Set
from functools import cached_property
from omnibelt import method_propagator, OrderedSet, isiterable

from ..abstract import AbstractTool, Gizmoed
from .abstract import AbstractCrafty, AbstractCraft, AbstractCrafts, AbstractRawCraft, AbstractCraftTool



class CraftTool(AbstractCraftTool): # when instantiating a "Crafty", Crafts are instantiated as CraftSources
	def __init__(self, base: AbstractCraft, instance: 'AbstractCrafty', **kwargs):
		super().__init__(**kwargs)





