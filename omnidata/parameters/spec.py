from typing import Tuple, List, Dict, Optional, Union, Any, Callable, Sequence, Iterator, Iterable, Type, Set

# from .top import Industrial
# from omnidata.parameters.abstract import AbstractParameterized

from ..structure import spaces
from ..tools.abstract import AbstractTool, AbstractContext, AbstractSpaced, AbstractChangableSpace, Gizmoed
from ..tools.errors import ToolFailedError
from ..tools.kits import SpaceKit, ElasticCrafty
from ..tools.context import DynamicContext
from ..tools.kits import CraftyKit

from .abstract import AbstractModular, AbstractSubmodule, AbstractArgumentBuilder
from .parameterized import ParameterizedBase
from .building import BuilderBase


class AbstractSpecced(AbstractSpaced):
	@property
	def my_blueprint(self):
		raise NotImplementedError


	# def as_spec(self) -> 'AbstractSpec':
	# 	raise NotImplementedError


	# def _missing_spaces(self) -> Iterator[str]:
	# 	yield from ()

	pass



class AbstractSpec(AbstractChangableSpace, AbstractContext):
	def sub(self, submodule) -> 'AbstractSpec':
		raise NotImplementedError



class Spec(DynamicContext, AbstractSpec):
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



class AutoSpec(AbstractSpecced):
	_Spec = Spec

	def __init__(self, *args, blueprint=None, **kwargs):
		self._my_blueprint = blueprint
		super().__init__(*args, **kwargs) # extracts hparams and processes crafts
		self.my_blueprint = self._update_spec(blueprint)


	@property
	def my_blueprint(self):
		return self._my_blueprint
	@my_blueprint.setter
	def my_blueprint(self, blueprint):
		self._my_blueprint = blueprint


	def _update_spec(self, spec=None):
		if spec is not None:
			return spec.update_with(self)
		# if spec is None:
		# 	spec = self._Spec()
		# if '_my_blueprint' not in self.__dict__:
		# 	return spec.update_with(self)
		# return spec



class Specced(AutoSpec, ParameterizedBase, AbstractModular, SpaceKit):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs) # extracts hparams
		self._fix_missing_spaces(self.my_blueprint)
		self._create_missing_submodules(self.my_blueprint)


	def _missing_spaces(self) -> Iterator[str]:
		for gizmo, skills in self._spaces.items():
			if len(skills) == 0:
				yield gizmo
			else:
				skill = skills[0]
				if skill.is_missing():
					yield gizmo
	
	
	def _fix_missing_spaces(self, spec):
		if spec is not None:
			for gizmo in self._missing_spaces():
				try:
					space = spec.space_of(gizmo)
				except ToolFailedError:
					continue
				else:
					self.change_space_of(gizmo, space)


	def _create_missing_submodules(self, spec):
		# if spec is not None:
		for name, param in self.named_submodules(hidden=True):
			try:
				val = getattr(self, name)
			except AttributeError:
				if spec is None:
					val = param.build_with(self)
				else:
					val = param.build_with_spec(self, spec.sub(name))
			else:
				val = param.validate(val, spec=spec)
			setattr(self, name, val)

		if spec is not None:
			spec.update_with(self)


	# def check_spec(self, spec):
	# 	# for name, param in self.named_hyperparameters(hidden=True):
	# 	# 	try:
	# 	# 		val = getattr(self, name)
	# 	# 	except AttributeError:
	# 	# 		if isinstance(param, AbstractSubmodule):
	# 	# 			val = param.build_with_spec(self, spec.sub(name))
	# 	# 			setattr(self, name, val)
	# 	# 	else:
	# 	# 		val = param.validate(val)
	# 	# 		setattr(self, name, val)
	# 	raise NotImplementedError



class ArchitectBase(Specced, BuilderBase, AbstractArgumentBuilder):
	pass















