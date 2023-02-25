

from .crafts import MachineCraft, ContextedCraft, SpacedCraft, OptionalCraft, DefaultCraft, LoggingCraft, \
	TensorCraft, SizeCraft, IndexCraft, SampleCraft, IndexSampleCraft, SpaceCraft, \
	MaterialedCrafty, AssessibleCrafty, SignaturedCrafty
from .context import SizedContext, ScopedContext, SimpleContext, ScopeBase, Cached



class machine(MachineCraft, ContextedCraft, SpacedCraft):
	optional = OptionalCraft
	default = DefaultCraft


class indicator(machine, LoggingCraft):
	pass


class material(TensorCraft, ContextedCraft, SpacedCraft):
	get_from_size = SizeCraft
	get_from_indices = IndexCraft
	get_next_sample = SampleCraft
	get_sample_from_index = IndexSampleCraft


class space(SpaceCraft):
	pass



class Context(Cached, SizedContext, SimpleContext):
	def __init__(self, *args, tools=None, **kwargs):
		super().__init__(**kwargs)
		if tools is not None:
			for tool in tools:
				self.add_tool(tool)



class Guru(Context):
	def __init__(self, *tools, **kwargs):
		super().__init__(tools=tools, **kwargs)


class Industrial(MaterialedCrafty, SignaturedCrafty, AssessibleCrafty):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._process_crafts()


