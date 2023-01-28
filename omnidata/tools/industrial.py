

from .abstract import AbstractKit



class Industrial(AbstractKit): # gizmos come from crafts
	class Assembler(AbstractKit):
		pass



# class Guru(AbstractRouter): # fills in gizmos using the given router, and checks for cycles



class Function(Industrial):
	@space('output')
	def dout(self):
		return None

	@space('input')
	def din(self):
		return None

	def __call__(self, inp):
		return self.Assembler(self, input=inp)['output']














