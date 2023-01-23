from typing import Tuple, List, Dict, Optional, Union, Any, Callable, Sequence, Iterator, Iterable, Type
from collections import OrderedDict

# from omnibelt import AbstractOperator, AbstractOperational
from omnibelt.crafting import ProcessedCrafts, SeamlessCrafts, InheritableCrafts, \
	AwareCraft, SignatureCraft, \
	AbstractCrafty, AbstractCraft, AbstractCrafts, AbstractRawCraft, AbstractCraftOperator
from omnibelt import operators, AbstractOperator, AbstractOperational

from .abstract import AbstractTool, AbstractContext, AbstractKit, SingleVendor, AbstractSpaced
from .errors import MissingGizmoError



class CraftsKit(InheritableCrafts, SeamlessCrafts, AbstractKit, SingleVendor):

	class Operator(operators.SimpleOperator, operators.UniversalOperator, AbstractKit, AbstractSpaced):
		def space_of(self, gizmo: str):
			return self._base.craft_space_of(self._instance, gizmo)


		def get_from(self, ctx: 'AbstractContext', gizmo: str):  # O-N
			return self._base.craft_get_from(self._instance, ctx, gizmo)


	def craft_space_of(self, instance: 'AbstractCrafty', gizmo: str):
		return self._vendors[gizmo].crafted_space_of(instance)


	def craft_get_from(self, instance: 'AbstractCrafty', ctx: 'AbstractContext', gizmo: str):
		return self._vendors[gizmo].crafted_get_from(instance, ctx, gizmo)


	def __init__(self, owner: Type[AbstractCrafty], crafts: List[AbstractCraft] = None, **kwargs): # O-N
		super().__init__(**kwargs)
		self._owner = owner
		self._vendors = OrderedDict() if crafts is None else self._process_vendors(crafts)


	def _create_operator(self, instance, owner, operations=None):
		if operations is None:
			operations = dict(self._operation_aliases())
		return self.Operator(self, instance, aliases=operations)


	def get_from(self, ctx: 'AbstractContext', gizmo: str): # O-N
		if gizmo in self._vendors:
			return self._vendors[gizmo].get_from(ctx, gizmo)
		raise MissingGizmoError(gizmo)


	def gizmos(self) -> Iterator[str]: # O-N
		yield from reversed(self._vendors.keys())


	def tools(self) -> Iterator[AbstractCraft]: # N-O
		yield from self._vendors.values()


	def vendor(self, gizmo: str, default: Any = None):
		return self._vendors.get(gizmo, default)


	def update(self, *others: 'CraftsKit'): # N-O
		self._vendors.update({
			gizmo: self._merge_vendors(gizmo, *self.vendors(gizmo), *other.vendors(gizmo))
			for other in others # N-O
			for gizmo in other.gizmos()
		})


	@staticmethod
	def _merge_vendors(gizmo: str, main: AbstractCraft, *others: AbstractCraft) -> AbstractCraft: # N-O
		return main.merge(gizmo, others) if others else main


	def _process_vendors(self, crafts: List[AbstractCraft]) -> Dict[str, AbstractCraft]: # O-N
		vendor_table = OrderedDict()
		for craft in reversed(crafts): # N-O
			for gizmo in craft.gizmos():
				vendor_table.setdefault(gizmo, []).append(craft) # N-O
		return OrderedDict([(gizmo, self._merge_vendors(gizmo, *vendors)) # N-O
		        for gizmo, vendors in vendor_table.items()])



class CraftTool(SignatureCraft, AwareCraft, AbstractTool):
	def gizmos(self) -> Iterator[str]:
		yield from self._gizmos


	class _ExtractionFailedError(ValueError):
		pass


	def _extract_signature_term(self, term):
		if isinstance(term, str):
			return (term,)
		elif isinstance(term, Iterable):
			return tuple(term)
		else:
			raise self._ExtractionFailedError(f'invalid gizmo: {term!r}')


	def _extract_signature(self, terms: Tuple[Union[str, Iterable[str]]]):
		past = set()
		signature = []
		for term in terms:
			targets = self._extract_signature_term(term)
			if any(t in past for t in targets):
				raise self._ExtractionFailedError(f'{term!r} is used more than once')
			signature.append(targets)
			past.update(targets)
		return signature


	def __init__(self, owner: Type[AbstractCrafty], key: str, raw: AbstractRawCraft, *,
	             signature=None, gizmos=None, **kwargs):
		super().__init__(owner, key, raw, **kwargs)

		try:
			if signature is None:
				signature = self._extract_signature(self._raw._args)
			if gizmos is None:
				gizmos = [target for targets in signature for target in targets]
		except self._ExtractionFailedError as e:
			raise ValueError(f'{owner.__name__}.{key}: {e}') from e

		self._vendors = {}
		self._signature = signature
		self._gizmos = gizmos


	def merge(self, gizmo, others: Iterable['SignatureCrafts']) -> 'SignatureCrafts':  # N-O
		self._vendors.setdefault(gizmo).extend(others)


# class ReferenceCraft(SignatureCraft):
# 	pass


# class CallableCraft(AbstractCraft):
# 	def craft(self, instance: AbstractCrafty, gizmo: str, command: str, context: AbstractKit):
# 		raise NotImplementedError


class DescriptorCraft(AbstractCraft):
	CraftTool: AbstractCraftOperator = None


	def _create_tool(self, instance: AbstractCrafty, owner: Type[AbstractCrafty]) -> AbstractCraftOperator:
		return self.CraftTool(self, instance)


	def __get__(self, instance: AbstractCrafty, owner: Type[AbstractCrafty]) -> AbstractCraftOperator:
		return self._create_tool(instance, owner)


	def craft(self, instance: AbstractCrafty, command: str, args: Tuple, kwargs: Dict):
		raise NotImplementedError


####################


class MachineCraft(SignatureCraft, SeamlessCraft):
	pass


class MaterialCraft(SignatureCraft, SeamlessCraft):
	def __init__(self, owner: Type[AbstractCrafty], key: str, raw: AbstractRawCraft, *,
	             signature=None, gizmos=None, **kwargs):
		super().__init__(owner, key, raw, signature=signature, gizmos=gizmos, **kwargs)
		self._getter = getattr(self._raw, '_method_name', None)

	pass


class SpaceCraft(SignatureCraft, PropertyCraft, SeamlessCraft):
	pass


class IndicatorCraft(MachineCraft):
	pass


############################################################################################################



class SkippableTool(AbstractTool):
	class SkipTool(ValueError):
		pass



class ToolBase(SkippableTool, AbstractTool):
	def __init__(self, **kwargs):
		super().__init__(**kwargs)



class KitBase(SkippableTool, AbstractKit):
	def __init__(self, *tools, aliases=None, **kwargs):
		if aliases is None:
			aliases = {}
		super().__init__(**kwargs)
		self._aliases = aliases
		self._reverse_aliases = {v: k for k, v in reversed(aliases.items())}
		self._tools = tools
		self._vendors = {}
		for tool in self.tools():
			for gizmo in tool.gizmos():
				self._vendors.setdefault(gizmo, []).append(tool)


	def tools(self) -> Iterator[AbstractTool]:
		yield from reversed(self._tools)


	def vendors(self, gizmo: str) -> Iterator[AbstractTool]:
		yield from self._vendors.get(gizmo, ())


	def get_from(self, ctx: 'AbstractTool', gizmo: str):
		key = self.gizmoto(gizmo)
		for vendor in self.vendors(key):
			try:
				return vendor.get_from(ctx, key)
			except self.SkipTool:
				pass
		raise self.MissingGizmo(gizmo)


	def gizmoto(self, gizmo: str) -> str: # check aliases (for getting)
		return self._aliases.get(gizmo, gizmo)


	def gizmofrom(self, gizmo: str) -> str: # invert aliases (for setting)
		return self._reverse_aliases.get(gizmo, gizmo)



################################################################################


class Industrial(AbstractKit): # gizmos come from crafts
	class Assembler(AbstractKit):
		pass

# class Guru(AbstractRouter): # fills in gizmos using the given router, and checks for cycles



class Function(Industrial):
	@space('output')
	def dout(self):
		return None

	@space('input')
	def din(self):
		return None

	def __call__(self, inp):
		return self.Assembler(self, input=inp)['output']




