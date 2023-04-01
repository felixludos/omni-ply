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

from .abstract import AbstractModular, AbstractBuilder, \
	AbstractSubmodule, AbstractArgumentBuilder, AbstractParameterized
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


	def include(self, *sources: AbstractTool):
		for source in sources:
			self._integrate_source(source)
		return super().include(*sources)


	def _integrate_source(self, source: AbstractTool):
		if isinstance(source, AbstractSpecced):
			for gizmo in source.gizmos():
				try:
					self.space_of(gizmo)
				except ToolFailedError:
					self.change_space_of(gizmo, source.space_of(gizmo))


	@property
	def size(self):
		return 1
	@property
	def indices(self):
		return [0]


	def sub(self, submodule) -> 'AbstractSpec':
		return self


	def adapt(self, overrides):
		new = self.__class__(spaces=overrides)
		new.include(self)
		return new


	def for_builder(self):
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


	# def update_with(self, other: 'AbstractSpecced'):
	# 	for gizmo in other.gizmos():
	# 		try:
	# 			space = other.space_of(gizmo)
	# 		except ToolFailedError:
	# 			continue
	# 		else:
	# 			try:
	# 				prev = self.space_of(gizmo)
	# 			except ToolFailedError:
	# 				self.change_space_of(gizmo, space)
	# 			else:
	# 				if prev is None:
	# 					self.change_space_of(gizmo, space)
	#
	# 	return self


# one of the deepest classes in the MRO (before hparam extraction and craft processing)

class PlannedBase(AbstractSpecced):
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


	def _validate_with_spec(self, spec):
		pass


	def _validate_submodules(self, spec=None):
		if spec is None:
			spec = self.my_blueprint

		# explicitly requested spaces are inferred from spec and set to self (potentially using the subs)
		# add self to spec (implicitly adds all spaces defined in self to spec) (also means space wise self is ready)
		self._validate_with_spec(spec)
		spec.include(self)

		# if sub is missing or a builder, this will instantiate it (using the sub-spec)
		for name, sub in self.named_submodules(hidden=True):
			sub.validate(self)



class PlannedSpatial(Spatial, PlannedModules): # could still be a builder
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._validate_submodules()


	def _validate_with_spec(self, spec):
		for gizmo in self._missing_spaces():
			space = spec.space_of(gizmo)
			if space is not None:
				self.change_space_of(gizmo, space)


	def _missing_spaces(self):
		for gizmo, opts in self._spaces.items():
			if not len(opts):
				yield gizmo
			elif opts[0].is_missing(gizmo):
				yield gizmo



class PlannedIndustrial(Industrial, PlannedSpatial):
	pass



class Specced(PlannedIndustrial):
	pass



class ArchitectBase(PlannedSpatial, AbstractArgumentBuilder):
	def _build_kwargs(self, product, *args, **kwargs):
		kwargs = super()._build_kwargs(product, *args, **kwargs)
		if issubclass(product, Industrial) and 'application' not in kwargs and self._application is not None:
			kwargs['application'] = self._application
		if issubclass(product, Specced) and 'blueprint' not in kwargs and self.my_blueprint is not None:
			kwargs['blueprint'] = self.my_blueprint
		return kwargs


	def _validate_with_spec(self, spec):
		for gizmo in self._missing_spaces():
			try:
				space = spec.space_of(gizmo)
			except ToolFailedError:
				pass
			else:
				if space is not None:
					self.change_space_of(gizmo, space)


	class _Plan:
		arch: 'ArchitectBase'

		def __init__(self, arch, blueprint):
			self.arch = arch
			self.spec = blueprint
			self.fixes = None


		def __enter__(self):
			fixes = []
			for gizmo in self.arch._missing_spaces():
				space = self.spec.space_of(gizmo)
				if space is not None:
					self.arch.change_space_of(gizmo, space)
					fixes.append(gizmo)
			self.fixes = fixes
			self.old_blueprint = self.arch.my_blueprint
			if isinstance(self.arch, PlannedBase):
				self.arch._my_blueprint = self.spec


		def __exit__(self, exc_type, exc_val, exc_tb):
			for gizmo in self.fixes:
				self.arch.clear_space(gizmo)
			if isinstance(self.arch, PlannedBase):
				self.arch._my_blueprint = self.old_blueprint


	def build_with_spec(self, blueprint, *args, **kwargs):
		with self._Plan(self, blueprint):
			return self.build(*args, **kwargs)


	def validate_with_spec(self, blueprint, value):
		with self._Plan(self, blueprint):
			return self.validate(value)



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












