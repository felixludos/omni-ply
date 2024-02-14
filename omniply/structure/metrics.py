# import random
from omnibelt import agnosticmethod
from . import operations


class Measure(operations.Metric):
	@staticmethod
	def difference(x, y): # should find an z such that z + y = x
		return x - y


	@agnosticmethod
	def measure(self, x, y):
		return self.difference(x, y).abs()


	@staticmethod
	def distance(x, y):
		raise NotImplementedError



class Norm(Measure):
	@staticmethod
	def magnitude(x):
		raise NotImplementedError


	@agnosticmethod
	def distance(self, x, y):
		return self.magnitude(self.difference(x, y))



class Lp(Norm):
	p = None

	@agnosticmethod
	def magnitude(self, x, dim=1):
		return x.norm(dim=dim, p=self.p)


	def __str__(self):
		return f'L{self.p}()'


class L0(Lp): p = 0
class L1(Lp): p = 1
class L2(Lp): p = 2
class Linf(Lp): p = float('inf')




