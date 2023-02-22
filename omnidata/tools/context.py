from typing import Tuple, List, Dict, Optional, Union, Any, Callable, Sequence, Iterator, Iterable, Type, Set

from .abstract import AbstractContext, AbstractTool


class Scope(AbstractContext):
	def __init__(self, src: AbstractContext, owner: AbstractTool):
		self._src = src
		self._owner = owner


	def gizmo_to(self, external: str) -> str: # global -> local
		return external


	def gizmo_from(self, local: str) -> str: # local -> global
		return local


	def space_of(self, local: str) -> str:
		try:
			return self._owner.space_of(local)
		except AttributeError: # local doesnt contain gizmo -> defer to global context
			return self._src.space_of(self.gizmo_from(local))


	def get_from(self, ctx: Optional['AbstractContext'], local: str):
		try:
			return self._owner.get_from(ctx, local)
		except AttributeError: # local doesnt contain gizmo -> defer to global context
			return self._src[self.gizmo_from(local)]



class ContextBase(AbstractContext):



	pass



class Decoder(Function):
	@machine('out')
	def forward(self, inp):
		# do something
		return out



class Autoencoder2:
	encoder = submachine(builder='encoder', input='observation', output='latent')
	decoder = submachine(builder='decoder', input='latent', output='reconstruction')

	@machine('loss')
	def compute_loss(self, observation, reconstruction):
		return self.criterion(reconstruction, observation)




















