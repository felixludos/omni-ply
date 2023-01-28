from typing import Tuple, List, Dict, Optional, Union, Any, Callable, Sequence, Iterator, Iterable, Type
from collections import OrderedDict

from omnibelt.crafting import SeamlessInheritableCrafts, \
	AwareCraft, SignatureCraft, ProcessedCrafts, \
	AbstractCrafty, AbstractCraft, AbstractCrafts, AbstractRawCraft, AbstractCraftOperator, AbstractCraftsOperator
from omnibelt import operators, DecoratedOperational, operation_base, auto_operation as operation, \
	unspecified_argument, Operationalized

from ..features import Prepared

from .abstract import AbstractTool, AbstractContext, AbstractKit, SingleVendor, AbstractSpaced
from .base import CraftTool, CraftToolOperator
from .errors import MissingGizmoError, ToolFailedError



class SpacedKit(AbstractKit, AbstractSpaced):
	def space_of(self, gizmo: str) -> AbstractCrafts:
		for vendor in self.vendors(gizmo):
			try:
				return vendor.space_of(gizmo)
			except ToolFailedError:
				pass
		raise ToolFailedError(gizmo, f'No space for {gizmo!r}')



class SingleVendorSpacedKit(SingleVendor, SpacedKit):
	def space_of(self, gizmo: str):
		return self.vendor(gizmo).space_of(gizmo)



class CraftsKitOperator(SeamlessInheritableCrafts.Operator, DecoratedOperational.Operator,
                        SingleVendorSpacedKit, SingleVendor, AbstractKit, Prepared):

	def _prepare(self, *args, **kwargs):
		for tool in self.tools():
			tool.prepare(*args, **kwargs)


	@staticmethod
	def _merge_vendors(gizmo: str, main: AbstractCraft, *others: AbstractCraft) -> AbstractCraft: # N-O
		out = main.merge(others) if others else main
		return out


	def tools(self) -> Iterator[CraftToolOperator]:
		yield from self._vendors.values()


	def _process_vendors(self, crafts: List[CraftToolOperator]) -> Dict[str, AbstractCraft]: # O-N
		vendor_table = OrderedDict()
		for craft in reversed(crafts): # N-O
			for gizmo in craft.gizmos():
				vendor_table.setdefault(gizmo, []).append(craft) # N-O
		return OrderedDict([(gizmo, self._merge_vendors(gizmo, *vendors)) # N-O
		        for gizmo, vendors in vendor_table.items()])


	def __init__(self, base: 'ProcessedCrafts', instance: Any, **kwargs):
		super().__init__(base, instance, **kwargs)
		self._vendors = self._process_vendors(self._crafts)
		self._base = base # TESTING


	def get_from(self, ctx: 'AbstractContext', gizmo: str):  # O-N
		return self.vendor(gizmo).get_from(ctx, gizmo)


	def vendor(self, gizmo: str, default: Any = unspecified_argument) -> CraftToolOperator:
		try:
			return self._vendors[gizmo]
		except KeyError:
			if default is unspecified_argument:
				raise MissingGizmoError(gizmo)
			return default


	# def update(self, *others: 'CraftsKitOperator'): # N-O
	# 	self._vendors.update({
	# 		gizmo: self._merge_vendors(gizmo, *self.vendors(gizmo), *other.vendors(gizmo))
	# 		for other in others # N-O
	# 		for gizmo in other.gizmos()
	# 	})



class CraftsKit(SeamlessInheritableCrafts, DecoratedOperational, SingleVendor, AbstractKit):
	Operator = CraftsKitOperator


	def tools(self) -> Iterator[CraftTool]: # N-O
		yield from self.crafts()
		# past = set() # no duplicates
		# for tool in self._vendors.values():
		# 	if id(tool) not in past:
		# 		past.add(id(tool))
		# 		yield tool


	# def vendor(self, gizmo: str, default: Any = unspecified_argument) -> CraftToolBase:
	# 	try:
	# 		return self._vendors[gizmo]
	# 	except KeyError:
	# 		if default is unspecified_argument:
	# 			raise MissingGizmoError(gizmo)
	# 		return default


	def update(self, *others: 'CraftsKitBase'): # N-O
		for other in others:
			self._crafts.extend(other.crafts())


	# def __init__(self, owner: Type[AbstractCrafty] = None, *, history: Iterable['CraftsKitBase'] = None, **kwargs):
	# 	if history is None:
	# 		history = []
	# 	super().__init__(owner=owner, **kwargs)
	# 	self._history = history
	#
	#
	# def update(self, *others: 'CraftsKitBase'): # N-O
	# 	# self._vendors.update({
	# 	# 	gizmo: self._merge_vendors(gizmo, *self.vendors(gizmo), *other.vendors(gizmo))
	# 	# 	for other in others # N-O
	# 	# 	for gizmo in other.gizmos()
	# 	# })
	# 	self._history.extend(others)


	# def crafting(self, instance: 'AbstractCrafty') -> 'AbstractCraftOperator':
	# 	crafts = list(self.crafts())
	# 	for craft in self.crafts():
	# 		craft.crafting(instance)
	# 	op = self.as_operator(instance)
	# 	setattr(instance, '_processed_crafts', op)
	# 	return op




# class CraftsKit(DecoratedOperational, SpacedCraftsKit):
#
#
# 	@operation.prepare
# 	def send_prepare(self, instance: 'AbstractCrafty'):
# 		for tool in self.tools():
# 			tool.send_prepare(instance)
#
#
# 	@operation.space_of
# 	def send_space_of(self, instance: 'AbstractCrafty', gizmo: str):
# 		return self.vendor(gizmo).send_space_of(instance, gizmo)
#
#
# 	@operation.get_from
# 	def send_get_from(self, instance: 'AbstractCrafty', ctx: 'AbstractContext', gizmo: str):
# 		return self.vendor(gizmo).send_get_from(instance, ctx, gizmo)









