from typing import Tuple, List, Dict, Optional, Union, Any, Callable, Sequence, Iterator, Iterable, Type, Set
from functools import cached_property
from omnibelt import method_propagator, OrderedSet, isiterable

from .abstract import AbstractCraft



class craft(AbstractCraft):
	pass



# class nestable_craft(AbstractCraft):
# 	def emit_craft_contents(self) -> Iterator[AbstractCraft]:
# 		crafts = []
# 		current = self
# 		while isinstance(current, AbstractCraft):
# 			crafts.append(current)
# 			current = current._fn
#
# 		for craft in crafts:
# 			craft._fn = current
# 			yield craft




	# Craft = None
	# def package_craft_item(self, owner: Type['Crafty'], key: str):
	# 	return self.Craft.package(owner, key, self)



class A:
	@machine.space('observation')
	@material.get_from('samples')
	@cached_property
	def get_observation(self):
		return 100




