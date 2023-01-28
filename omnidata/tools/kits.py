from typing import Tuple, List, Dict, Optional, Union, Any, Callable, Sequence, Iterator, Iterable, Type
from collections import OrderedDict

from omnibelt.crafting import SeamlessInheritableCrafts, \
	AwareCraft, SignatureCraft, \
	AbstractCrafty, AbstractCraft, AbstractCrafts, AbstractRawCraft, AbstractCraftOperator, AbstractCraftsOperator,
from omnibelt import operators, DecoratedOperational, operation_base, auto_operation as operation, \
	unspecified_argument, Operationalized

from .abstract import AbstractTool, AbstractContext, AbstractKit, SingleVendor, AbstractSpaced
from .base import CraftToolBase
from .errors import MissingGizmoError, ToolFailedError



class SpacedKit(AbstractSpaced, AbstractKit):
	def space_of(self, gizmo: str) -> AbstractCrafts:
		for vendor in self.vendors(gizmo):
			try:
				return vendor.space_of(gizmo)
			except ToolFailedError:
				pass
		raise ToolFailedError(gizmo, f'No space for {gizmo!r}')



class CraftsKitBase(SeamlessInheritableCrafts, SingleVendor, AbstractKit):
	def __init__(self, owner: Type[AbstractCrafty], crafts: List[AbstractCraft] = None, **kwargs): # O-N
		super().__init__(**kwargs)
		self._owner = owner
		self._vendors = OrderedDict() if crafts is None else self._process_vendors(crafts)

	
	def get_from(self, ctx: 'AbstractContext', gizmo: str): # O-N
		return self.vendor(gizmo).get_from(ctx, gizmo)


	def gizmos(self) -> Iterator[str]: # O-N
		yield from reversed(self._vendors.keys())


	def tools(self) -> Iterator[CraftToolBase]: # N-O
		past = set() # no duplicates
		for tool in self._vendors.values():
			if id(tool) not in past:
				past.add(id(tool))
				yield tool


	def vendor(self, gizmo: str, default: Any = unspecified_argument) -> CraftToolBase:
		try:
			return self._vendors[gizmo]
		except KeyError:
			if default is unspecified_argument:
				raise MissingGizmoError(gizmo)
			return default


	def update(self, *others: 'CraftsKitBase'): # N-O
		self._vendors.update({
			gizmo: self._merge_vendors(gizmo, *self.vendors(gizmo), *other.vendors(gizmo))
			for other in others # N-O
			for gizmo in other.gizmos()
		})


	@staticmethod
	def _merge_vendors(gizmo: str, main: AbstractCraft, *others: AbstractCraft) -> AbstractCraft: # N-O
		return main.merge(others) if others else main


	def _process_vendors(self, crafts: List[CraftToolBase]) -> Dict[str, AbstractCraft]: # O-N
		vendor_table = OrderedDict()
		for craft in reversed(crafts): # N-O
			for gizmo in craft.gizmos():
				vendor_table.setdefault(gizmo, []).append(craft) # N-O
		return OrderedDict([(gizmo, self._merge_vendors(gizmo, *vendors)) # N-O
		        for gizmo, vendors in vendor_table.items()])



class SpacedCraftsKit(CraftsKitBase, SpacedKit):
	def space_of(self, gizmo: str):
		return self.vendor(gizmo).space_of(gizmo)



class CraftsKit(DecoratedOperational, Operationalized, SpacedCraftsKit):
	class Operator(SpacedCraftsKit.Operator):
		pass


	def crafting(self, instance: 'AbstractCrafty') -> 'AbstractCraftOperator':
		for craft in self.crafts():
			craft.crafting(instance)
		op = self.as_operator(instance)
		setattr(instance, '_processed_crafts', op)
		return op
	
	
	@operation.tools
	def send_tools(self, instance: Any):
		for tool in self.tools():
			yield tool.as_operator(instance)


	@operation.vendors
	def send_vendors(self, instance: Any, gizmo: str):
		for vendor in self.vendors(gizmo):
			yield vendor.as_operator(instance)


	@operation.vendor
	def send_vendor(self, instance: Any, gizmo: str):
		return self.vendor(gizmo).as_operator(instance)


	@operation.space_of
	def send_space_of(self, instance: 'AbstractCrafty', gizmo: str):
		return self.vendor(gizmo).send_space_of(instance, gizmo)


	@operation.get_from
	def send_get_from(self, instance: 'AbstractCrafty', ctx: 'AbstractContext', gizmo: str):
		return self.vendor(gizmo).send_get_from(instance, ctx, gizmo)









