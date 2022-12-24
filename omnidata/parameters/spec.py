from omnibelt import agnostic, unspecified_argument

from ..features import Prepared

from .abstract import AbstractMachine
from .parameterized import ParameterizedBase
from .machines import MachineBase


# TODO: add abstract spec class



class MachineParameterized(ParameterizedBase):
	Machine = MachineBase

	@classmethod
	def register_machine(cls, name=None, _instance=None, **kwargs):
		_instance = cls.Machine(name=name, **kwargs) if _instance is None else cls.Machine.extract_from(_instance)
		if name is None:
			name = _instance.name
		return cls._register_hparam(name, _instance)

	@agnostic
	def machines(self):
		for key, val in self.named_machines():
			yield val

	@agnostic
	def named_machines(self):
		for key, val in self.named_hyperparameters():
			if isinstance(val, MachineBase):
				yield key, val



class PreparedParameterized(MachineParameterized, Prepared):
	@agnostic
	def _prepare_machine(self, name, machine, **kwargs):
		val = getattr(self, name, None)
		if isinstance(val, Prepared):
			val.prepare(**kwargs)


	@agnostic
	def _prepare(self, *args, **kwargs):
		super()._prepare(*args, **kwargs)
		for name, machine in self.named_machines():
			self._prepare_machine(name, machine)

	@agnostic
	def reset(self):
		self._prepared = False
		self.reset_hparams()





class SpecBase:
	@classmethod
	def package(cls, name, info, base, **kwargs):
		return cls(name, info, base, **kwargs)

	@classmethod
	def expand(cls, base, hidden=False, non_default=False, **kwargs):
		for key, info in base.named_hyperparameters(hidden=hidden):
			spec = cls.package(key, info, base, **kwargs)
			if non_default and spec.is_default:
				continue
			yield spec


	class NoValue(ValueError): pass

	def __init__(self, name, info, base, **kwargs):
		super().__init__(**kwargs)
		self._name = name
		self.info = info
		self.base = base

	@property
	def name(self):
		return self._name

	@property
	def is_default(self):
		return not self.info.is_cached(self.base)

	@property
	def missing(self):
		return self.value is self.NoValue

	@property
	def value(self):
		try:
			return self.info.get_value(self.base)
		except self.info.MissingValueError:
			return self.NoValue

	def _str_payload(self):
		name = self.name
		value = self.value
		payload = None if value is self.NoValue else repr(value)
		return name if payload is None else f'{name}={payload}'

	def __str__(self):
		return f'<{self._str_payload()}>'

	def __repr__(self):
		base = self.base.__name__ if isinstance(self.base, type) else self.base.__class__.__name__ + '()'
		return f'{self.__class__.__name__}<{base}>({self._str_payload()})'
		return self.__str__()



class StatusSpec(SpecBase):
	@property
	def required(self):
		return getattr(self.info, 'required', False)

	@property
	def status(self):
		return 'required' if self.required else 'optional'

	def _str_payload(self):
		name = self.name
		payload = f'{name}:[{self.status}]'
		value = self.value
		if value is not self.NoValue:
			payload += f'={repr(value)}'
		return payload



class MachineSpec(SpecBase):
	def __init__(self, name, info, base, *, parent=None, **kwargs):
		super().__init__(name, info, base, **kwargs)
		self._parent = parent

	@property
	def parent(self):
		return self._parent
	@parent.setter
	def parent(self, value):
		self._parent = value

	@property
	def name(self):
		if self._parent is None:
			return self._name
		return f'{self._parent.name}.{self._name}'

	@property
	def is_machine(self):
		return isinstance(self.info, AbstractMachine)

	@classmethod
	def expand(cls, base, include_machines=True, expand_machines=True, parent=None, **kwargs):
		for spec in super().expand(base, parent=parent, **kwargs):
			is_machine = spec.is_machine
			if include_machines or not is_machine:
				yield spec
			if is_machine and expand_machines:
				yield spec.expand_children(include_machines=include_machines,
				                           expand_machines=expand_machines, **kwargs)

	def expand_children(self, include_machines=True, expand_machines=True, **kwargs):
		value = self.value
		if value is self.NoValue:
			builder = self.info.get_builder()
			if builder is not None:
				yield from self.expand(builder, parent=self, include_machines=include_machines,
				                       expand_machines=expand_machines, **kwargs)
		else:
			yield from self.expand(value, parent=self, include_machines=include_machines,
			                       expand_machines=expand_machines, **kwargs)


class Spec(MachineSpec, StatusSpec):
	pass


class Specced(ParameterizedBase):
	Spec = Spec

	# TODO: init_from_spec and build_from_spec

	@agnostic
	def show_spec(self, **kwargs): # convenience method
		return list(self.spec(**kwargs))

	@agnostic
	def spec(self, *, hidden=False, non_default=False, **kwargs):
		yield from self.Spec.expand(self, hidden=hidden, non_default=non_default)


















