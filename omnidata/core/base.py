from typing import Tuple, List, Dict, Optional, Union, Any, Callable, Sequence, Iterator, Iterable


class AbstractData:
	def _title(self):
		return self.__class__.__name__


	def __str__(self):
		return self._title()


	def __repr__(self):
		return str(self)



class AbstractSource(AbstractData): # leaf
	def __getitem__(self, gizmo: str):
		return self.get_from(self, gizmo)


	def get_from(self, ctx: 'AbstractSource', gizmo: str):
		raise NotImplementedError


	def gizmos(self) -> Iterator[str]:
		raise NotImplementedError

	class SkipSourceError(KeyError):
		pass



class AbstractRouter(AbstractSource): # branch
	def sources(self) -> Iterator[AbstractSource]:
		raise NotImplementedError


	def gizmos(self) -> Iterator[str]:
		past = set()
		for source in self.sources():
			for gizmo in source.gizmos():
				if gizmo not in past:
					past.add(gizmo)
					yield gizmo


# class Guru(AbstractRouter): # fills in gizmos using the given router, and checks for cycles



class SourceBase(AbstractSource):
	def __init__(self, **kwargs):
		super().__init__(**kwargs)



class RouterBase(AbstractRouter):
	def __init__(self, *sources, **kwargs):
		super().__init__(**kwargs)
		self._sources = sources


	def sources(self) -> Iterator[AbstractSource]:
		yield from reversed(self._sources)


	def vendors(self, gizmo: str) -> Iterator[AbstractSource]:
		raise NotImplementedError


	def get_from(self, ctx: 'AbstractSource', gizmo: str):
		key = self.gizmoto(gizmo)
		for vendor in self.vendors(key):
			try:
				return vendor.get_from(ctx, key)
			except self.SkipSourceError:
				pass


	def gizmoto(self, gizmo: str) -> str: # check aliases (for getting)
		return gizmo

	def gizmofrom(self, gizmo: str) -> str: # invert aliases (for setting)
		return gizmo



class Crafty: # contains crafts (and craft sources when instantiated)
	pass


class craft: # decorator wrapping a property/method - aka craft-item
	pass


class Craft(SourceBase): # can be updated with craft items or other crafts
	pass


class CraftSource(SourceBase): # when instantiating a "Crafty", Crafts are instantiated as CraftSources
	pass


class Industrial(SourceBase): # gizmos come from crafts
	class Assembler(Router):
		pass


class Function(Industrial):
	@machine.space('output')
	def dout(self):
		return None

	@machine.space('input')
	def din(self):
		return None

	def __call__(self, inp):
		return self.Assembler(self, input=inp)['output']




