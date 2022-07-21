# import random
import numpy as np
from omnibelt import agnosticmethod
from plethora.framework import abstract


def angle_diff(angle1, angle2, period=2*np.pi):
	a = angle1 - angle2
	return (a + period/2) % period - period/2



def round_sigfigs(x, sigfigs=3):
	mag = x.abs().log10().floor()
	mag[mag.isinf()] = 0
	reg = 10 ** (sigfigs - mag - 1)
	return x.mul(reg).round().div(reg)



def sigfig_noise(x, n, sigfigs=3):
	mag = x.abs().log10().floor()
	mag[mag.isinf()] = 0
	reg = 10 ** (sigfigs - mag - 1)
	return x.mul(reg).add(n).div(reg)



def mixing_score(mat, dim1=1, dim2=2, eps=1e-10):
	N1, N2 = mat.size(dim1), mat.size(dim2)
	mat = mat.abs()
	return 1 - mat.div(mat.add(eps).max(dim1, keepdim=True)[0]).sum(dim1, keepdim=True).sub(1)\
		.mean(dim2, keepdim=True).div(N1-1)



class Metric(abstract.Metric):
	@staticmethod
	def difference(x, y): # should find an z such that z + y = x
		return x - y


	@agnosticmethod
	def measure(self, x, y):
		return self.difference(x, y).abs()


	@staticmethod
	def distance(x, y):
		raise NotImplementedError



class Norm(Metric):
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




