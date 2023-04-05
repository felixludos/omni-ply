

from .crafts import MachineCraft, ContextedCraft, SpacedCraft, OptionalCraft, DefaultCraft, LoggingCraft, \
	TensorCraft, SizeCraft, IndexCraft, SampleCraft, IndexSampleCraft, SpaceCraft, \
	TransformedSpaceCraft, SignatureCraft
from .kits import MaterialedCrafty, AssessibleCrafty, SignaturedCrafty, RelabeledCrafty, ElasticCrafty, SpaceKit
from .context import SizedContext, DynamicContext, ScopeBase, Cached, SeededContext, ScopedContext

from .assessments import SimpleSignature


class machine(ContextedCraft, MachineCraft, SpacedCraft):
	@classmethod
	def is_derivative(cls, obj):
		return isinstance(obj._base, machine)
	
	
	class Skill(MachineCraft.Skill, SpacedCraft.Skill):
		pass

	optional = OptionalCraft
	default = DefaultCraft



class indicator(machine, LoggingCraft):
	class Skill(machine.Skill, LoggingCraft.Skill):
		pass



class material(ContextedCraft, TensorCraft, SpacedCraft):
	@classmethod
	def is_derivative(cls, obj):
		return isinstance(obj._base, cls.from_size) or isinstance(obj._base, cls.from_indices) \
			or isinstance(obj._base, cls.next_sample) or isinstance(obj._base, cls.sample_from_index)
	
	
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
			self.include(*tools)



class Guru(Context):
	def __init__(self, *tools, **kwargs):
		super().__init__(tools=tools, **kwargs)



class Spatial(ElasticCrafty, RelabeledCrafty, SpaceKit):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._process_crafts()



class Industrial(Spatial, MaterialedCrafty, SignaturedCrafty, AssessibleCrafty):
	pass



class Signature(SimpleSignature):
	pass


# class Elastic(ElasticCrafty):






