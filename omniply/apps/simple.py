from typing import Any, Iterator, Callable, Optional
from collections import UserDict
from omnibelt import filter_duplicates

from ..core import AbstractGig
from ..core.gadgets import GadgetBase



class DictGadget(GadgetBase):
	def __init__(self, *srcs: dict, **data):
		super().__init__()
		self.data = {**data}
		self._srcs = srcs


	def __delitem__(self, key):
		raise NotImplementedError


	def __getitem__(self, item):
		if item in self.data:
			return self.data[item]
		for src in self._srcs:
			if item in src:
				return src[item]
		raise KeyError(f'Key not found: {item}')


	def gizmos(self) -> Iterator[str]:
		yield from filter_duplicates(self.data.keys(), *map(lambda x: x.keys(), self._srcs))


	def grab_from(self, ctx: 'AbstractGig', gizmo: str) -> Any:
		return self[gizmo]



















