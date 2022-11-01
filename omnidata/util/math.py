import numpy as np


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



def mixing_score(mat, dim1=1, dim2=2, eps=1e-10): # TODO: what is this?
	N1, N2 = mat.size(dim1), mat.size(dim2)
	mat = mat.abs()
	return 1 - mat.div(mat.add(eps).max(dim1, keepdim=True)[0]).sum(dim1, keepdim=True).sub(1)\
		.mean(dim2, keepdim=True).div(N1-1)


