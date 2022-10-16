from typing import List, Dict, Tuple, Optional, Union, Any, Hashable, Sequence, Callable, Type, Iterable, Iterator
from collections import OrderedDict
from omnibelt import unspecified_argument, agnosticmethod, extract_function_signature
from omnibelt.nodes import TreeNode, AutoTreeNode

from omnifig import Configurable

from .hyperparameters import Hyperparameter, Parameterized, hparam
from .building import Builder, MultiBuilder, AutoClassBuilder
from .machines import Machine, MachineParametrized
from .specification import Specification


class Architect(Builder, MachineParametrized, Configurable):

	
	
	pass



# class OldArchitect:
# 	class _missing_spec: pass
# 	class _unknown_spec: pass
#
# 	@agnosticmethod
# 	def settings(self, spec: Optional[Specification] = None, include_machines=True) -> Specification:
# 		def collect_children(param):
# 			if isinstance(param, Machine):
# 				builder = param.get_builder()
# 				if builder is not None:
# 					if isinstance(builder, Architect):
# 						yield from builder.settings(spec=spec, include_machines=include_machines).children()
# 					else:
# 						for k, v in builder.plan():
# 							yield k, self.Specification(v)
# 		parent = self.Specification()
# 		for key, param in self.plan_from_spec(spec):
# 			child = self.Specification(param) if not isinstance(param, Machine) or include_machines \
# 				else self.Specification()
# 			child.add_all(collect_children(param))
# 			parent.set(key, child)
# 		return parent
#
# 	@agnosticmethod
# 	def _evaluate_settings(self, settings: Specification, include_machines=True):
# 		for key, node in settings.children():
# 			val = getattr(self, key, self._unknown_spec)
# 			if node.has_payload and val is self._unknown_spec and node.payload.required:
# 				val = self._missing_spec
# 			if val.is_leaf or include_machines:
# 				yield key, val
# 			if not val.is_leaf:
# 				yield from val._evaluate_settings(node, include_machines=include_machines)
#
# 	@agnosticmethod
# 	def settings_values(self, spec: Optional[Specification] = None, include_machines=True):
# 		settings = self.settings(spec=spec, include_machines=include_machines)
# 		yield from self._evaluate_settings(settings, include_machines=include_machines)
#
# 	# @agnosticmethod
# 	# def validate_spec(self, spec: Specification):
# 	# 	raise NotImplementedError
# 	#
# 	# def update_settings(self, spec: Specification):
# 	# 	raise NotImplementedError
#
# 	@agnosticmethod
# 	def flat_settings(self, include_machines=True):
# 		return self.settings(include_machines=include_machines).flatten()
#
# 	@classmethod
# 	def create_spec(cls, data=None):
# 		data = data or {}
# 		return cls.Specification.from_raw(data)
#
# 	@agnosticmethod
# 	def _fill_spec(self, fn, spec: Optional[Specification] = None) -> Dict[str, Any]:
# 		if spec is None:
# 			return {}
# 		return extract_function_signature(fn, default_fn=lambda n: spec.get(n, self._missing_spec),
# 		                                          allow_positional=False)
#
# 	@agnosticmethod
# 	def plan_from_spec(self, spec: Optional[Specification] = None) -> Iterator[Tuple[str, Hyperparameter]]:
# 		# TODO: recurse on machine specs
# 		return self._plan(**self._fill_spec(self._plan, spec))
#
# 	@agnosticmethod
# 	def build_from_spec(self, spec: Specification, default_only=True) -> Any:
# 		# TODO: recurse on machine specs
#
# 		def get_architect(param):
# 			if isinstance(param, Machine):
# 				builder = param.get_builder()
# 				if isinstance(builder, Architect):
# 					return builder
#
# 		spec_terms = self._fill_spec(self._build, spec)
# 		kwargs = {}
# 		for key, val in spec_terms.items():
# 			param = self.get_hparam(key)
# 			builder = get_architect(param)
# 			if not val.has_payload:
#
# 				val.payload = param.default_profile if param.default_profile is not unspecified_argument else getattr(self, key)
# 			if builder is not None:
# 				val = builder.build_from_spec(val)
# 			if val.has_payload:
# 				val = val.payload
# 			kwargs[key] = val.payload if builder is None else builder.build_from_spec(val)
# 		return self._build(**kwargs)
# 		# return self._build(**self._fill_spec(self.plan, spec))
#
# 	def product_from_spec(self, spec: Specification) -> Type:
# 		# TODO: recurse on machine specs
# 		return self._product(**self._fill_spec(self._product, spec))



class ClassArchitect(MultiBuilder, Architect):
	@agnosticmethod
	def build_from_spec(self, spec: Architect.Specification) -> Any:
		if spec.is_leaf:
			return self.build(spec.payload)
		return super().build_from_spec(spec)



class AutoClassArchitect(ClassArchitect, AutoClassBuilder):
	pass



