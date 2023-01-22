from typing import Tuple, List, Dict, Optional, Union, Any, Callable, Sequence, Iterator, Iterable, Type, Set
from functools import cached_property
from omnibelt import method_propagator, OrderedSet, isiterable

from omnidata.tools.abstract import AbstractTool, Gizmoed



class CraftTool(AbstractTool): # when instantiating a "Crafty", Crafts are instantiated as CraftSources
	def __init__(self, instance: 'Crafty', base: 'Crafts', **kwargs):
		super().__init__(**kwargs)





