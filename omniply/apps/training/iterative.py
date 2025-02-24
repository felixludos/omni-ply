from .imports import *
from .abstract import AbstractEvent, AbstractEngine
from omnibelt import AbstractStaged



class Event(AutoStaged, AbstractEvent):
	pass



class EngineBase(Event, AbstractEngine):
	def __init__(self, events: Mapping[[str, AbstractEvent]] = None, env: Mapping[str, AbstractGadget] = None,
				 **kwargs):
		if events is None: events = {}
		if env is None: env = {}
		super().__init__(**kwargs)
		self._events = events
		self._env = env


	def gadgetry(self):
		yield from self._env.values()
		yield from self._events.values()


	def loop(self) -> Iterator[AbstractGame]:
		raise NotImplementedError


	def run(self):
		for _ in self.loop(): pass












