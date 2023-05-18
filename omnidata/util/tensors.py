
# import torch
# from omnibelt import unspecified_argument, duplicate_instance, InitWall



class WrappedTensor():#torch.Tensor):
	@staticmethod
	def __new__(cls, src, *args, **kwargs):
		return super().__new__(cls, src)#, *args, **kwargs)


	def __init__(self, src=None, *args, **kwargs):
		# super().__init__(src, *args, **kwargs)
		pass


	def copy(self):
		copy = self.__class__.__new__(self.__class__, [])
		copy.__dict__.update(self.__dict__)
		copy.data = self.data
		return copy


	def clone(self, *args, **kwargs):
		new = self.copy()
		new.data = super().clone(*args, **kwargs)
		return new


	def to(self, *args, **kwargs):
		new = self.copy()
		new.data = super().to(*args, **kwargs)
		return new



class SpaceTensor(WrappedTensor):
	def __init__(self, src, space=None, **kwargs):
		super().__init__(src, **kwargs)
		self.space = space





