from typing import Type
from omnidata.tools.crafting.crafting import Crafty, Crafts, craft


class Machine(Crafts):
	@classmethod
	def process_raw_crafts(cls, owner: Type['Crafty']):
		machines = []
		for base in owner.__bases__:
			if issubclass(base, MachinedBase):
				past = getattr(base, '_known_machines', None)
				if past is not None:
					machines.extend(past)
		for key, val in owner.__dict__.items():
			if isinstance(val, machine_base):
				machines.append(owner._Machine_Trigger(owner, key, val))

		raise NotImplementedError


	pass



class Machined(Crafty):
	Machine = Machine
	def __init_subclass__(cls, **kwargs):
		super().__init_subclass__(**kwargs)
		if cls.Machine is not None:
			cls._known_crafts = cls.Machine.process_raw_crafts(cls)

	pass



class machine(craft):
	Craft = Machine
	pass




