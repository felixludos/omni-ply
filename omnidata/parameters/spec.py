from typing import Tuple, List, Dict, Optional, Union, Any, Callable, Sequence, Iterator, Iterable, Type, Set

# from .top import Industrial
# from omnidata.parameters.abstract import AbstractParameterized

from omnibelt.crafts import ProcessedCrafty, IndividualCrafty, AbstractCraft, AbstractSkill, AbstractCrafty

from ..structure import spaces
from ..tools.abstract import AbstractTool, AbstractContext, AbstractSpaced, AbstractChangableSpace, Gizmoed
from ..tools.errors import ToolFailedError
from ..tools.kits import SpaceKit, ElasticCrafty
from ..tools.context import DynamicContext
from ..tools.kits import CraftyKit
from ..tools.crafts import SpaceCraft
from ..tools import Industrial, Spatial

from .abstract import AbstractModular, AbstractSubmodule, AbstractArgumentBuilder, AbstractParameterized
from .parameterized import ParameterizedBase
from .building import BuilderBase


class AbstractSpecced(AbstractSpaced):
	# @property
	# def my_blueprint(self):
	# 	raise NotImplementedError


	# def as_spec(self) -> 'AbstractSpec':
	# 	raise NotImplementedError


	# def _missing_spaces(self) -> Iterator[str]:
	# 	yield from ()

	pass



class AbstractSpec(AbstractContext, AbstractChangableSpace):
	def sub(self, submodule) -> 'AbstractSpec':
		raise NotImplementedError

	def for_builder(self):
		'''Returns the spec for a builder (usually the builder is created automatically for a submodule)'''
		raise NotImplementedError



class SpecBase(DynamicContext, AbstractSpec):
	def __init__(self, *, spaces=None, **kwargs):
		super().__init__(**kwargs)
		# self._owner = owner
		self._spaces = {}
		if spaces is not None:
			self._spaces.update(spaces)


	@property
	def size(self):
		return 1
	@property
	def indices(self):
		return [0]


	def sub(self, submodule) -> 'AbstractSpec':
		return self


	def copy(self, **kwargs):
		return self.__class__(spaces=self._spaces, **kwargs)


	def change_space_of(self, gizmo: str, space: spaces.Dim):
		self._spaces[gizmo] = space


	def gizmos(self) -> Iterator[str]:
		yield from self._spaces.keys()


	def has_gizmo(self, gizmo: str) -> bool:
		return gizmo in self._spaces


	def space_of(self, gizmo: str) -> spaces.Dim:
		if gizmo in self._spaces:
			return self._spaces[gizmo]
		return super().space_of(gizmo)


	def update_with(self, other: 'AbstractSpecced'):
		for gizmo in other.gizmos():
			try:
				space = other.space_of(gizmo)
			except ToolFailedError:
				continue
			else:
				try:
					prev = self.space_of(gizmo)
				except ToolFailedError:
					self.change_space_of(gizmo, space)
				else:
					if prev is None:
						self.change_space_of(gizmo, space)

		return self



class PlannedBase(AbstractSpecced):
	# one of the deepest classes in the MRO (before hparam extraction and craft processing)

	_Spec = None
	def __init__(self, *args, blueprint=None, **kwargs):
		if blueprint is None:
			blueprint = self._Spec() # TODO: maybe include `self`
		super().__init__(*args, **kwargs)
		self._my_blueprint = blueprint


	@property
	def my_blueprint(self):
		return self._my_blueprint



class PlannedModules(PlannedBase, AbstractModular):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._initialize_submodules()


	def _initialize_submodules(self):
		for name, sub in self.named_submodules(hidden=True):
			sub.init(self)


	def _validate_submodules(self, spec=None):
		if spec is None:
			spec = self.my_blueprint

		# explicitly requested spaces are inferred from spec and set to self (potentially using the subs)
		# add self to spec (implicitly adds all spaces defined in self to spec) (also means space wise self is ready)
		if spec is not None:
			spec.include(self)

		# if sub is missing or a builder, this will instantiate it (using the sub-spec)
		for name, sub in self.named_submodules(hidden=True):
			sub.validate(self)



class PlannedSpatial(Spatial, PlannedModules): # could still be a builder
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._validate_submodules()


	def space_of(self, gizmo: str):
		try:
			return super().space_of(gizmo)
		except ToolFailedError:
			if self.my_blueprint is not None:
				return self.my_blueprint.space_of(gizmo)



class PlannedIndustrial(Industrial, PlannedSpatial):
	pass



class Specced(PlannedIndustrial):
	pass



class ArchitectBase(PlannedSpatial):
	pass



#######################################################################################################################


# class AutoSpec(AbstractSpecced):
# 	_Spec = Spec
#
# 	def __init__(self, *args, blueprint=None, **kwargs):
# 		self._my_blueprint = blueprint
# 		super().__init__(*args, **kwargs)  # extracts hparams and processes crafts
# 		self.my_blueprint = self._update_spec(blueprint)
#
# 	@property
# 	def my_blueprint(self):
# 		return self._my_blueprint
#
# 	@my_blueprint.setter
# 	def my_blueprint(self, blueprint):
# 		self._my_blueprint = blueprint
#
# 	def _update_spec(self, spec=None):
# 		if spec is not None:
# 			return spec.update_with(self)
# # if spec is None:
# # 	spec = self._Spec()
# # if '_my_blueprint' not in self.__dict__:
# # 	return spec.update_with(self)
# # return spec
#
#
# class Specced(AutoSpec, ParameterizedBase, AbstractModular, SpaceKit):
# 	def __init__(self, *args, **kwargs):
# 		super().__init__(*args, **kwargs)  # extracts hparams
# 		self._fix_missing_spaces(self.my_blueprint)
# 		self._create_missing_submodules(self.my_blueprint)
#
# 	def _missing_spaces(self) -> Iterator[str]:
# 		for gizmo, skills in self._spaces.items():
# 			if len(skills) == 0:
# 				yield gizmo
# 			else:
# 				skill = skills[0]
# 				if skill.is_missing():
# 					yield gizmo
#
# 	def _fix_missing_spaces(self, spec):
# 		if spec is not None:
# 			for gizmo in self._missing_spaces():
# 				try:
# 					space = spec.space_of(gizmo)
# 				except ToolFailedError:
# 					continue
# 				else:
# 					self.change_space_of(gizmo, space)
#
# 	def _create_missing_submodules(self, spec):
# 		# if spec is not None:
# 		for name, param in self.named_submodules(hidden=True):
# 			try:
# 				val = getattr(self, name)
# 			except AttributeError:
# 				if spec is None:
# 					val = param.build_with(self)
# 				else:
# 					val = param.build_with_spec(self, spec.sub(name))
# 			else:
# 				val = param.validate(val, spec=spec)
# 			setattr(self, name, val)
#
# 		if spec is not None:
# 			spec.update_with(self)
#
#
# # def check_spec(self, spec):
# # 	# for name, param in self.named_hyperparameters(hidden=True):
# # 	# 	try:
# # 	# 		val = getattr(self, name)
# # 	# 	except AttributeError:
# # 	# 		if isinstance(param, AbstractSubmodule):
# # 	# 			val = param.build_with_spec(self, spec.sub(name))
# # 	# 			setattr(self, name, val)
# # 	# 	else:
# # 	# 		val = param.validate(val)
# # 	# 		setattr(self, name, val)
# # 	raise NotImplementedError
#
#
# class ArchitectBase(Specced, BuilderBase, AbstractArgumentBuilder):
# 	pass


########################################################################################################################


# class PlannedCrafty(ParamPlanned, IndividualCrafty): # comes before SpaceKit/Industrial
# 	# def _process_crafts(self):
# 	# 	for name, sub in self.named_submodules(hidden=True):
# 	# 		if sub.is_missing(self):
# 	# 			sub.setup_builder(self, spec=self.my_blueprint)
# 	# 	return super()._process_crafts()
#
# 	# def _process_skill(self, src: Type[AbstractCrafty], key: str, craft: AbstractCraft, skill: AbstractSkill):
# 	# 	super()._process_skill(src, key, craft, skill)
# 	pass
#
#
# # class PlannedBuilder(PlannedCrafty, BuilderBase):
# # 	def _integrate_spec(self, spec=None):
# # 		if spec is None:
# # 			spec = self.my_blueprint
# #
# # 		spec.node(self)  # add self to spec
# # 		for name, sub in self.named_submodules(hidden=True):
# # 			sub.setup_spec(self,
# # 			               spec=spec.sub(name))  # this should add builder/submodule to sub-spec (for space inference)
# #
# # 		for name in self._missing_spaces():  # explicitly requested spaces are inferred from spec (potentially using the subs)
# # 			self.change_space_of(name, spec.space_of(name))
# #
# # 		for name, space in self.named_spaces():
# # 			if space is None:
# # 				self.change_space_of(name, spec.space_of(name))
# #
# # 		for name, sub in self.named_submodules(hidden=True):
# # 			sub.validate(self)  # if sub is missing or a builder, this will instantiate it (using the sub-spec)
# #
# #
# # 	def space_of(self, gizmo: str) -> spaces.Dim:
# # 		try:
# # 			return super().space_of(gizmo)
# # 		except ToolFailedError:
# # 			return self.my_blueprint.space_of(gizmo)
# #
# # 	pass
#
#
#
# class PlannedBuilder(AbstractSpecced):
# 	def build(self, *args, blueprint=None, **kwargs):
# 		if blueprint is None:
# 			blueprint = self._my_blueprint
# 		return self._build(*args, blueprint=blueprint, **kwargs)
#
#
#
# class PlannedSpatial(PlannedCrafty, SpaceKit):
# 	def _coordinate_submodules(self, spec=None):
# 		if spec is None:
# 			spec = self.my_blueprint
#
# 		for name, sub in self.named_submodules(hidden=True):
# 			# this should add builder/submodule to sub-spec (for space inference)
# 			sub.setup_spec(self, spec=spec.sub(name))
#
# 		# explicitly requested spaces are inferred from spec and set to self (potentially using the subs)
# 		# add self to spec (implicitly adds all spaces defined in self to spec) (also means space wise self is ready)
# 		spec.certify(self)
#
# 		for name, sub in self.named_submodules(hidden=True):
# 			# if sub is missing or a builder, this will instantiate it (using the sub-spec)
# 			sub.validate(self)
#
#
# 	# def _fix_missing_spaces(self, spec):
# 	#
# 	# 	# find all missing spaces (in self + submodules)
# 	# 	todo = list(self._missing_spaces())
# 	#
# 	# 	# fill in missing spaces that are in blueprint
# 	#
# 	# 	# fill in remaining missing spaces using submodules
# 	#
# 	# 	# update blueprint with new spaces (and resolve conflicts)
# 	#
# 	# 	pass
#
#
#
# class CreativePlanned(PlannedSpatial):
# 	def _create_missing_submodules(self, spec):
# 		# convert submodule builders into submodules
#
# 		# send configs as needed
#
# 		# certify submodules with applications
#
# 		pass












