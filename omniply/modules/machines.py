from typing import Type, Union, Any, Optional, Callable, Sequence, Iterable, Iterator, Tuple, List, Dict, NamedTuple
from collections import OrderedDict
from omnibelt import smartproperty, unspecified_argument
# from omnibelt.tricks import nested_method_decorator
from omnibelt.collectors import method_propagator, universal_propagator, AbstractCollector, AbstractCollectorTrigger




class Container(OrderedDict): # contains gizmos
	class MissingKey(KeyError):
		pass
	
	
	def _find_missing(self, key):
		raise self.MissingKey(key)


	def __getitem__(self, item):
		try:
			return super().__getitem__(item)
		except KeyError:
			return self._find_missing(item)


	def __str__(self):
		entries = ', '.join(self.keys())
		return f'{self.__class__.__name__}({entries})'


	def __repr__(self):
		return str(self)


class AbstractDepot:
	pass


class Depot(Container): # contains machines
	def __init__(self, *sources, **kwargs):
		super().__init__(**kwargs)
		self._sources = sources


	def _load_missing(self, key):
		if key in self._gizmos:
			return self._gizmos[key].get_from(self, key)
		return self.source[key]
	
	
	def _find_missing(self, key):
		if key in self._gizmos:
			self[key] = self._gizmos[key].get_from(self, key)
			return self[key]
		if self._gizmos is not None:
			self[key] = self._load_missing(key) # load and cache
			return self[key]
		return super()._find_missing(key)



class machine_base(method_propagator):
	def gizmos(self):
		yield from self._keys


class AbstractMachine:
	def gizmos(self):
		raise NotImplementedError



class AbstractMachineTrigger:
	pass



class _Machine_Trigger(AbstractMachineTrigger):
	def __init__(self, owner, key, base):
		self.owner = owner
		self.key = key
		self.base = base



class MachineBase(AbstractMachine):
	_known_machines_type = list

	@classmethod
	def process_machine_triggers(cls, owner: Type['MachinedBase']):
		machines = []
		for base in owner.__bases__:
			if issubclass(base, MachinedBase):
				past = getattr(base, '_known_machines', None)
				if past is not None:
					machines.extend(past)
		for key, val in owner.__dict__.items():
			if isinstance(val, machine_base):
				machines.append(owner._Machine_Trigger(owner, key, val))

		known = set()
		used = cls._known_machines_type()
		for trigger in reversed(machines):
			gizmos = list(cls.extract_gizmos_from_trigger(trigger))
			if all(g in known for g in gizmos):
				continue
			known.update(gizmos)
			used.append(trigger)
		return used


	@staticmethod
	def extract_gizmos_from_trigger(trigger: 'AbstractMachineTrigger'):
		yield from trigger.val.gizmos()
		
		
	def gizmos(self):
		yield from self.extract_gizmos_from_trigger(self.trigger)


	_known_machines_gizmos_type = OrderedDict

	@classmethod
	def process_gizmos(cls, source, triggers):
		table = cls._known_machines_gizmos_type()
		for trigger in triggers:
			machine = cls(source, trigger)
			for gizmo in machine.gizmos():
				table[gizmo] = machine
		return table


	def __init__(self, source, trigger: 'AbstractMachineTrigger', **kwargs):
		super().__init__(**kwargs)
		self.source = source
		self.trigger = trigger



class MachinedBase:
	Machine = MachineBase
	_Machine_Trigger = _Machine_Trigger
	Depot = Depot

	_known_gizmos = None
	_known_machine_triggers = None
	def __init_subclass__(cls, **kwargs):
		super().__init_subclass__(**kwargs)
		if cls.Machine is not None:
			cls._known_machine_triggers = cls.Machine.process_machine_triggers(cls)


	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		if self.Machine is not None:
			self._known_gizmos = self.Machine.process_gizmos(self, self._known_machine_triggers)


	def create_depot(self, *args, **kwargs):
		return self.Depot(self._known_gizmos, *args, **kwargs)



























