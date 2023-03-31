from typing import Tuple, List, Dict, Optional, Union, Any, Callable, Sequence, Iterator, Iterable, Type, Set

from omnibelt import method_decorator, agnostic, unspecified_argument, filter_duplicates
from omnibelt.crafts import AbstractCraft, AbstractCrafty, NestableCraft, SkilledCraft, IndividualCrafty, HiddenCrafty

from ..features import Prepared
from ..structure import spaces

from .abstract import AbstractSpaced, Loggable, AbstractAssessible, AbstractKit, SingleVendor, AbstractTool, \
	AbstractChangableSpace, AbstractDynamicKit
from .errors import ToolFailedError, MissingGizmoError
from .crafts import ToolCraft, OptionalCraft, DefaultCraft, LabelCraft, SpaceCraft, InitCraft, ReplaceableCraft
from .assessments import AbstractSignature, Signatured


class DynamicKit(AbstractDynamicKit):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._added_tools = []


	def include(self, *tools: AbstractTool) -> 'AbstractDynamicKit':
		self._added_tools.extend(tools)
		return self


	def tools(self) -> Iterator['AbstractTool']:
		yield from getattr(self, '_added_tools', [])



class SpacedTool(AbstractTool, AbstractSpaced):
	def space_of(self, gizmo: str) -> spaces.Dim:
		for tool in self.vendors(gizmo):
			try:
				if isinstance(tool, AbstractSpaced):
					return tool.space_of(gizmo)
			except ToolFailedError:
				pass
		raise self._ToolFailedError(f'No tool for {gizmo} in {self}')



class SpaceKit(IndividualCrafty, AbstractChangableSpace): # processes `space` decorators
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._spaces = {}


	def clear_space(self, gizmo: str) -> bool:
		if gizmo in self._spaces:
			self._spaces[gizmo][0].clear_space(gizmo)


	def gizmos(self) -> Iterator[str]:
		yield from self._spaces.keys()


	def _process_skill(self, src: Type[AbstractCrafty], key: str, craft: AbstractCraft, skill: LabelCraft.Skill):
		super()._process_skill(src, key, craft, skill)
		if isinstance(skill, SpaceCraft.Skill):
			self._spaces.setdefault(skill.label, []).append(skill)


	def space_of(self, gizmo: str):
		if gizmo in self._spaces:
			return self._spaces[gizmo][0].space_of(gizmo)
		# return self._tools[gizmo].space_of(gizmo)
		return super().space_of(gizmo)


	def _default_space_of(self, gizmo: str):
		raise NotImplementedError # TODO

	
	# def gizmos(self) -> Iterator[str]:
	# 	yield from filter_duplicates(super().gizmos(), self._spaces.keys())


	def change_space_of(self, gizmo: str, space: spaces.Dim):
		if gizmo in self._spaces:
			self._spaces[gizmo][0].change_space_of(gizmo, space)
		else:
			super().change_space_of(gizmo, space)

	
	# def gizmos(self) -> Iterator[str]:
	# 	yield from filter_duplicates(super().gizmos(), self._spaces.keys())



class ValidatedCrafty(IndividualCrafty):
	@staticmethod
	def validate_label(label):
		return label



class RelabeledCrafty(IndividualCrafty):
	'''Relabel inherited crafts'''
	_inherited_tool_relabels = None
	def __init_subclass__(cls, replace=None, **kwargs): # {old_label: new_label}
		if replace is None:
			replace = {}
		super().__init_subclass__(**kwargs)
		# past = {}
		# for parent in cls.__bases__:
		# 	if issubclass(parent, RelabeledKit) and parent._inherited_tool_relabels is not None:
		# 		past.update(parent._inherited_tool_relabels)
		# replace.update(past)
		cls._inherited_tool_relabels = replace


	@agnostic
	def _emit_all_craft_items(self, *, remaining: Iterator[Type['InheritableCrafty']] = None,
	                          start : Type['InheritableCrafty'] = None, owner : Type['InheritableCrafty'] = None,
	                          **kwargs) -> Iterator[Tuple[Type[AbstractCrafty], str, AbstractCraft]]: # N-O
		live = start is None # make sure replacements only happen once
		cls = self if isinstance(self, type) else type(self)
		if start is None:
			start = cls

		for loc, key, craft in super()._emit_all_craft_items(remaining=remaining, start=start, owner=owner, **kwargs):
			if loc is start:
				yield loc, key, craft
			elif live and len(start._inherited_tool_relabels) and isinstance(craft, ReplaceableCraft):
				# if issubclass(loc, RelabeledKit):
				# 	craft = craft.replace(loc._inherited_tool_relabels)
				fix = craft.replace(start._inherited_tool_relabels)
				yield loc, key, fix
			else:
				yield loc, key, craft



class ElasticCrafty(ValidatedCrafty):
	'''Relabel instance crafts'''
	_application = None

	def __init__(self, *args, application=None, **kwargs):
		if application is None:
			application = {}
		super().__init__(*args, **kwargs)
		self._application = application

	@agnostic
	def validate_label(self, label):
		if self._application is None:
			return label
		return self._application.get(label, label)



class CraftyKit(SpaceKit, SpacedTool, AbstractKit):
	class _SkillTool(AbstractTool): # collects all skills (of the whole mro) of one gizmo
		def __init__(self, label: str, **kwargs):
			super().__init__(**kwargs)
			self._label = label
			self._standard = []
			self._optionals = []
			self._defaults = []


		def add(self, skill: ToolCraft.Skill):
			if isinstance(skill, OptionalCraft.Skill):
				self._optionals.append(skill)
			elif isinstance(skill, DefaultCraft.Skill):
				self._defaults.append(skill)
			else:
				self._standard.append(skill)


		def tool_history(self):
			yield from self._standard
			yield from self._optionals
			yield from self._defaults


		def tool(self):
			return next(self.tool_history())


		def tools(self): # by default, only uses the newest tool in the class hierarchy
			yield self.tool()


	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._tool_skills = {}


	def _process_skill(self, src: Type[AbstractCrafty], key: str, craft: AbstractCraft, skill: LabelCraft.Skill):
		super()._process_skill(src, key, craft, skill)
		if isinstance(skill, ToolCraft.Skill):
			if skill.label not in self._tool_skills:
				self._tool_skills[skill.label] = self._SkillTool(skill.label)
			self._tool_skills[skill.label].add(skill)


	def has_gizmo(self, gizmo: str) -> bool:
		return gizmo in self._tool_skills


	def vendors(self, gizmo: str):
		# gizmo = self.validate_label(gizmo)
		if gizmo not in self._tool_skills:
			raise MissingGizmoError(gizmo)
		yield from self._tool_skills[gizmo].tools()


	def tools(self) -> Iterator['AbstractTool']:
		for skill in self._tool_skills.values():
			yield from skill.tools()


	def gizmos(self) -> Iterator[str]:
		yield from filter_duplicates(self._spaces.keys(), super(SpaceKit, self).gizmos())



class MaterialedCrafty(CraftyKit, Prepared): # allows materials to be initialized when prepared
	def _prepare(self, *args, **kwargs):
		super()._prepare(*args, **kwargs)

		materials = {}
		for gizmo, tool in self._tool_skills.items():
			if isinstance(tool, self._SkillTool):
				skill = tool.tool()
				if isinstance(skill, InitCraft.Skill):
					materials[gizmo] = skill.init(self)
		self._tool_skills.update(materials)



class SignaturedCrafty(CraftyKit, Signatured):
	@agnostic
	def signatures(self, owner = None) -> Iterator['AbstractSignature']:
		outputs = set()
		if isinstance(self, type):
			self: Type['SignaturedCrafty']
			for loc, key, craft in self._emit_all_craft_items():
				if isinstance(craft, Signatured):
					for signature in craft.signatures(self):
						if signature.output not in outputs:
							outputs.add(signature.output)
							yield signature
		else:
			for tool in self.tools():
				if isinstance(tool, Signatured):
					yield from tool.signatures(self)



class AssessibleCrafty(CraftyKit, AbstractAssessible):
	@classmethod
	def assess_static(cls, assessment):
		super().assess_static(assessment)
		for owner, key, craft in cls._emit_all_craft_items():
			if isinstance(craft, AbstractAssessible):
				assessment.add_edge(cls, craft, name=key, loc=owner)
				assessment.expand(craft)


	def assess(self, assessment):
		super().assess(assessment)
		for tool in self.tools():
			if isinstance(tool, AbstractAssessible):
				assessment.add_edge(self, tool)
				assessment.expand(tool)













