from typing import Tuple, List, Dict, Optional, Union, Any, Callable, Sequence, Iterator, Iterable, Type, Set

# from .top import Industrial
# from omnidata.parameters.abstract import AbstractParameterized

from ..structure import spaces
from ..tools.abstract import AbstractTool, AbstractContext, AbstractSpaced, AbstractChangableSpace, Gizmoed
from ..tools.errors import ToolFailedError
from ..tools.kits import CraftyKit

from .abstract import AbstractModular, AbstractSubmodule
from .parameterized import ParameterizedBase


class AbstractSpecced(AbstractSpaced):
	@property
	def my_blueprint(self):
		raise NotImplementedError


	# def as_spec(self) -> 'AbstractSpec':
	# 	raise NotImplementedError


	# def _missing_spaces(self) -> Iterator[str]:
	# 	yield from ()

	pass



class AbstractSpec(Gizmoed, AbstractChangableSpace, AbstractContext):
	def sub(self, submodule) -> 'AbstractSpec':
		raise NotImplementedError

	@property
	def size(self):
		return 1
	@property
	def indices(self):
		return [0]



class Spec(AbstractSpec):
	def __init__(self, *, spaces=None, **kwargs):
		super().__init__(**kwargs)
		# self._owner = owner
		self._spaces = {}
		if spaces is not None:
			self._spaces.update(spaces)


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
		return self._spaces[gizmo]


	def update_with(self, other: 'AbstractSpecced'):
		for gizmo in self.gizmos():
			try:
				space = self.space_of(gizmo)
			except ToolFailedError:
				continue
			self.change_space_of(gizmo, space)

		return self



class Specced(ParameterizedBase, AbstractModular, AbstractSpecced, AbstractTool):
	_Spec = Spec
	_my_blueprint = None

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs) # extracts hparams
		self.my_blueprint = self._update_spec(self.my_blueprint)
		self._fix_missing_spaces(self.my_blueprint)
		self._create_missing_submodules(self.my_blueprint)


	@property
	def my_blueprint(self):
		return self._my_blueprint
	@my_blueprint.setter
	def my_blueprint(self, blueprint):
		self._my_blueprint = blueprint


	def _update_spec(self, spec=None):
		if spec is None:
			spec = self._Spec()
		return spec.update_with(self)


	def _fix_missing_spaces(self, spec):
		pass


	def _create_missing_submodules(self, spec):
		for name, param in self.named_submodules(hidden=True):
			try:
				val = getattr(self, name)
			except AttributeError:
				val = param.build_with_spec(self, spec.sub(name))
			else:
				val = param.validate(val)
			setattr(self, name, val)


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

















