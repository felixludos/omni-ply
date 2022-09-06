from typing import List, Dict, Tuple, Optional, Union, Any, Hashable, Sequence, Callable, Type, Iterable, Iterator
from collections import OrderedDict
from omnibelt import split_dict, unspecified_argument, agnosticmethod, OrderedSet, \
	extract_function_signature, method_wrapper

from .hyperparameters import Hyperparameter, Parameterized, hparam
from .building import get_builder, Builder, ClassBuilder, AutoClassBuilder

from omnibelt.nodes import AutoTreeNode



class Machine(Hyperparameter):
	def __init__(self, default=unspecified_argument, required=True, type=None, builder=None,
	             cache=None, ref=None, **kwargs):
		if ref is not None:
			if type is None:
				type = ref.type
			if builder is None:
				builder = ref.builder
		if cache is None:
			cache = type is not None or builder is not None
		super().__init__(default=default, required=required, cache=cache, ref=ref, **kwargs)
		self.type = type
		self.builder = builder


	class InvalidValue(Hyperparameter.InvalidValue):
		def __init__(self, name, value, base, msg=None):
			if msg is None:
				value = type(value) if isinstance(value, type) else str(value)
				msg = f'{name}: {value} (expecting an instance of {base})'
			super().__init__(name, value, msg=msg)
			self.base = base


	def get_builder(self) -> Builder:
		if self.builder is not None:
			return get_builder(self.builder) if isinstance(self.builder, str) else self.builder
		if self.type is not None and isinstance(self.type, Builder):
			return self.type



class MachineParametrized(Parameterized):
	Machine = Machine


	@agnosticmethod
	def fill_hparams(self, fn, args=(), kwargs={}):
		def defaults(n):
			if n in self._registered_hparams:
				return getattr(self, n)
			raise KeyError(n)
		return extract_function_signature(fn, args, kwargs, defaults)


	@agnosticmethod
	def _extract_hparams(self, kwargs):
		found, remaining = split_dict(kwargs, self._registered_hparams)
		for key, val in found.items():
			setattr(self, key, val)
		return remaining


	@agnosticmethod
	def register_machine(self, name=None, _instance=None, **kwargs):
		if _instance is None:
			_instance = self.Machine(name=name, **kwargs)
		return self.register_hparam(name, _instance)


	@agnosticmethod
	def machines(self):
		for key, val in self.named_machines():
			yield val


	@agnosticmethod
	def named_machines(self):
		for key, val in self.named_hyperparameters():
			if isinstance(val, Machine):
				yield key, val


	@agnosticmethod
	def full_spec(self, fmt='{}', fmt_rule='{parent}.{child}', include_machines=True):
		for key, val in self.named_hyperparameters():
			ident = fmt.format(key)
			if isinstance(val, Machine):
				builder = val.get_builder()
				if include_machines or builder is None:
					yield ident, val
				if builder is not None:
					if isinstance(builder, MachineParametrized):
						yield from builder.full_spec(fmt=fmt_rule.format(parent=ident, child='{}'), fmt_rule=fmt_rule)
					else:
						for k, v in builder.plan():
							yield fmt_rule.format(parent=ident, child=k), v
			else:
				yield ident, val



class machine(hparam):
	_registration_fn_name = 'register_machine'


# class ModifyableBuilder(Builder):
# 	@staticmethod
# 	def realize(product, *args, **kwargs):
# 		return product(*args, **kwargs)


class Architect(Builder, MachineParametrized):
	class Specification(AutoTreeNode):
		# TODO: pretty printing
		pass

	class _missing_spec: pass
	class _unknown_spec: pass

	@agnosticmethod
	def settings(self, spec: Optional[Specification] = None, include_machines=True) -> Specification:
		def collect_children(param):
			if isinstance(param, Machine):
				builder = param.get_builder()
				if builder is not None:
					if isinstance(builder, Architect):
						yield from builder.settings(spec=spec, include_machines=include_machines).children()
					else:
						for k, v in builder.plan():
							yield k, self.Specification(v)
		parent = self.Specification()
		for key, param in self.plan_from_spec(spec):
			child = self.Specification(param) if not isinstance(param, Machine) or include_machines \
				else self.Specification()
			child.add_all(collect_children(param))
			parent.set(key, child)
		return parent

	@agnosticmethod
	def _evaluate_settings(self, settings: Specification, include_machines=True):
		for key, node in settings.children():
			val = getattr(self, key, self._unknown_spec)
			if node.has_payload and val is self._unknown_spec and node.payload.required:
				val = self._missing_spec
			if val.is_leaf or include_machines:
				yield key, val
			if not val.is_leaf:
				yield from val._evaluate_settings(node, include_machines=include_machines)

	@agnosticmethod
	def settings_values(self, spec: Optional[Specification] = None, include_machines=True):
		settings = self.settings(spec=spec, include_machines=include_machines)
		yield from self._evaluate_settings(settings, include_machines=include_machines)

	@agnosticmethod
	def validate_spec(self, spec: Specification):
		raise NotImplementedError

	def update_settings(self, spec: Specification):
		raise NotImplementedError

	@agnosticmethod
	def flat_settings(self, include_machines=True):
		return self.settings(include_machines=include_machines).flatten()

	@classmethod
	def create_spec(cls, data=None):
		data = data or {}
		return cls.Specification.from_raw(data)

	@agnosticmethod
	def _fill_spec(self, fn, spec: Optional[Specification] = None) -> Dict[str, Any]:
		if spec is None:
			return {}
		return extract_function_signature(fn, default_fn=lambda n: spec.get(n, self._missing_spec),
		                                          allow_positional=False)

	@agnosticmethod
	def plan_from_spec(self, spec: Optional[Specification] = None) -> Iterator[Tuple[str, Hyperparameter]]:
		# TODO: recurse on machine specs
		return self._plan(**self._fill_spec(self._plan, spec))

	@agnosticmethod
	def build_from_spec(self, spec: Specification) -> Any:
		# TODO: recurse on machine specs

		def get_architect(key):
			setting = self.get_hparam(key)
			if isinstance(setting, Machine):
				builder = setting.get_builder()
				if isinstance(builder, Architect):
					return builder

		spec_terms = self._fill_spec(self._build, spec)
		kwargs = {}
		for key, val in spec_terms.items():
			builder = get_architect(key)
			kwargs[key] = val.payload if builder is None else builder.build_from_spec(val)
		return self._build(**kwargs)
		# return self._build(**self._fill_spec(self.plan, spec))

	def product_from_spec(self, spec: Specification) -> Type:
		# TODO: recurse on machine specs
		return self._product(**self._fill_spec(self._product, spec))



class ClassArchitect(ClassBuilder, Architect):
	@agnosticmethod
	def build_from_spec(self, spec: Architect.Specification) -> Any:
		if spec.is_leaf:
			return self.build(spec.payload)
		return super().build_from_spec(spec)



class AutoClassArchitect(ClassArchitect, AutoClassBuilder):
	pass
