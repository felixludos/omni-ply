

from .crafts import MachineCraft, ContextedCraft, SpacedCraft, OptionalCraft, DefaultCraft, LoggingCraft, \
	TensorCraft, SizeCraft, IndexCraft, SampleCraft, IndexSampleCraft, SpaceCraft
from .kits import MaterialedCrafty, AssessibleCrafty, SignaturedCrafty, RelabeledKit
from .context import SizedContext, ScopedContext, DynamicContext, ScopeBase, Cached



class machine(ContextedCraft, MachineCraft, SpacedCraft):
	class Skill(MachineCraft.Skill, SpacedCraft.Skill):
		pass

	optional = OptionalCraft
	default = DefaultCraft



class indicator(machine, LoggingCraft):
	class Skill(machine.Skill, LoggingCraft.Skill):
		pass



class material(ContextedCraft, TensorCraft, SpacedCraft):
	class Skill(TensorCraft.Skill, SpacedCraft.Skill):
		pass

	from_size = SizeCraft
	from_indices = IndexCraft
	next_sample = SampleCraft
	sample_from_index = IndexSampleCraft



class space(SpaceCraft):
	pass



class Context(Cached, SizedContext, DynamicContext):
	def __init__(self, *args, tools=None, **kwargs):
		super().__init__(**kwargs)
		if tools is not None:
			for tool in tools:
				self.add_tool(tool)



class Guru(Context):
	def __init__(self, *tools, **kwargs):
		super().__init__(tools=tools, **kwargs)



class Industrial(MaterialedCrafty, SignaturedCrafty, RelabeledKit, AssessibleCrafty):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._process_crafts()


