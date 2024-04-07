from .op import tool, ToolKit, Context, Scope, Selection


def test_tool():
	"""
	This function tests the functionality of the 'tool' decorator and the 'gizmos' method.

	The 'tool' decorator is used to define two functions, 'f' and 'g', with 'a' and 'b' as their respective gizmos.
	The 'gizmos' method is then used to check if the gizmo of the function 'g' is correctly set to 'b'.
	"""

	@tool('a')  # The 'tool' decorator is used to define a function 'f' with 'a' as its gizmo.
	def f(x):
		"""
		This function takes an integer as input and returns the integer incremented by 1.

		Args:
			x (int): The input integer.

		Returns:
			int: The input integer incremented by 1.
		"""
		return x + 1

	assert f(1) == 2  # Asserts that the function 'f' correctly increments its input by 1.

	@tool('b')  # The 'tool' decorator is used to define a function 'g' with 'b' as its gizmo.
	def g(x, y, z):
		"""
		This function takes three integers as input and returns their sum.

		Args:
			x (int): The first input integer.
			y (int): The second input integer.
			z (int): The third input integer.

		Returns:
			int: The sum of the input integers.
		"""
		return x + y + z

	# Asserts that the gizmo of the function 'g' is correctly set to 'b'.
	assert list(g.gizmos()) == ['b'], f'gizmos: {list(g.gizmos())}'


def test_context():
	"""
	This function tests the functionality of the 'tool' decorator, the 'Context' class, and the 'include' method.

	The 'tool' decorator is used to define three functions, 'f', 'g', and 'f2', with 'y', 'z', and 'y' as their respective gizmos.
	The 'Context' class is used to create a context with the functions 'f' and 'g'.
	The 'include' method is then used to add the function 'f2' to the context.

	The function asserts that the context correctly maps 'x' to 'y' and that it updates correctly when the context's cache is cleared and 'f2' is included.
	"""

	@tool('y')  # The 'tool' decorator is used to define a function 'f' with 'y' as its gizmo.
	def f(x):
		"""
		This function takes an integer as input and returns the integer incremented by 1.

		Args:
			x (int): The input integer.

		Returns:
			int: The input integer incremented by 1.
		"""
		return x + 1

	@tool('z')  # The 'tool' decorator is used to define a function 'g' with 'z' as its gizmo.
	def g(x, y):
		"""
		This function takes two integers as input and returns their sum.

		Args:
			x (int): The first input integer.
			y (int): The second input integer.

		Returns:
			int: The sum of the input integers.
		"""
		return x + y

	@tool('y')  # The 'tool' decorator is used to define a function 'f2' with 'y' as its gizmo.
	def f2(y):
		"""
		This function takes an integer as input and returns the integer negated.

		Args:
			y (int): The input integer.

		Returns:
			int: The input integer negated.
		"""
		return -y

	ctx = Context(f, g)  # The 'Context' class is used to create a context with the functions 'f' and 'g'.

	ctx['x'] = 1  # The context maps 'x' to 'y'.
	assert ctx['y'] == 2  # Asserts that the context correctly maps 'x' to 'y'.

	ctx.clear_cache()  # The context's cache is cleared.
	ctx.include(f2)  # The function 'f2' is added to the context.

	ctx['x'] = 1  # The context maps 'x' to 'y'.
	assert ctx['y'] == -2  # Asserts that the context correctly maps 'x' to 'y' after 'f2' is included.


def _future_test_gizmo_dashes(): # this test is for the dash-gizmos
	"""
	This function tests the functionality of the 'tool' decorator, the 'gizmos' method, and the 'Context' class with gizmos that contain dashes.

	The 'tool' decorator is used to define a function 'f' with 'a-1' as its gizmo.
	The 'gizmos' method is then used to check if the gizmo of the function 'f' is correctly set to 'a_1'.
	The 'Context' class is used to create a context with the function 'f'.
	The function asserts that the context correctly maps 'a-1' to 1 and that it correctly identifies 'a-1' and 'a_1' as cached gizmos.
	"""

	@tool('a-1')  # The 'tool' decorator is used to define a function 'f' with 'a-1' as its gizmo.
	def f():
		"""
		This function returns the integer 1.

		Returns:
			int: The integer 1.
		"""
		return 1

	# Asserts that the gizmo of the function 'f' is correctly set to 'a_1'.
	assert list(f.gizmos()) == ['a_1'], f'gizmos: {list(f.gizmos())}'

	ctx = Context(f)  # The 'Context' class is used to create a context with the function 'f'.

	# Asserts that the context correctly maps 'a-1' to 1 and that it correctly identifies 'a-1' and 'a_1' as cached gizmos.
	assert ctx['a-1'] == 1, f'ctx["a-1"]: {ctx["a-1"]}'
	assert ctx.is_cached('a-1'), f'is_cached("a-1"): {ctx.is_cached("a-1")}'
	assert ctx.is_cached('a_1'), f'is_cached("a_1"): {ctx.is_cached("a_1")}'
	assert ctx['a_1'] == 1, f'ctx["a_1"]: {ctx["a_1"]}'


class _Kit1(ToolKit):
	"""
	The _Kit1 class is a subclass of ToolKit. It provides methods to handle gizmos 'y', 'z', and 'w'.
	"""

	@tool('y')  # The 'tool' decorator is used to define a function 'f' with 'y' as its gizmo.
	@staticmethod
	def f(x):
		"""
		This static method takes an integer as input and returns the integer incremented by 1.

		Args:
			x (int): The input integer.

		Returns:
			int: The input integer incremented by 1.
		"""
		return x + 1

	@tool('z')  # The 'tool' decorator is used to define a function 'g' with 'z' as its gizmo.
	def g(self, x, y):
		"""
		This method takes two integers as input and returns their sum.

		Args:
			x (int): The first input integer.
			y (int): The second input integer.

		Returns:
			int: The sum of the input integers.
		"""
		return x + y

	@tool('w')  # The 'tool' decorator is used to define a function 'h' with 'w' as its gizmo.
	@classmethod
	def h(cls, z):
		"""
		This class method takes an integer as input and returns the integer incremented by 2.

		Args:
			z (int): The input integer.

		Returns:
			int: The input integer incremented by 2.
		"""
		return z + 2

def test_crafty_kit():
	"""
	This function tests the functionality of the '_Kit1' class, the 'Context' class, and the 'clear_cache' method.

	The '_Kit1' class is instantiated and its methods 'f', 'g', and 'h' are tested.
	The 'Context' class is used to create a context with the '_Kit1' instance.
	The 'clear_cache' method is then used to clear the context's cache.

	The function asserts that the '_Kit1' instance correctly increments its input by 1 for method 'f', correctly sums its inputs for method 'g', and correctly increments its input by 2 for method 'h'.
	It also asserts that the context correctly maps 'x' to 'y', 'z', and 'w', and that it updates correctly when the context's cache is cleared.
	"""

	# Asserts that the 'f' method of the '_Kit1' class correctly increments its input by 1.
	assert _Kit1.f(1) == 2
	# Asserts that the 'h' method of the '_Kit1' class correctly increments its input by 2.
	assert _Kit1.h(1) == 3

	# The '_Kit1' class is instantiated.
	kit = _Kit1()
	# Asserts that the 'f' method of the '_Kit1' instance correctly increments its input by 1.
	assert kit.f(1) == 2
	# Asserts that the 'g' method of the '_Kit1' instance correctly sums its inputs.
	assert kit.g(1, 2) == 3
	# Asserts that the 'h' method of the '_Kit1' instance correctly increments its input by 2.
	assert kit.h(1) == 3

	# The 'Context' class is used to create a context with the '_Kit1' instance.
	ctx = Context(kit)

	# Asserts that the context correctly identifies the gizmos of the '_Kit1' instance.
	assert list(ctx.gizmos()) == ['y', 'z', 'w']

	# The context maps 'x' to 'y'.
	ctx['x'] = 1
	# Asserts that the context correctly maps 'x' to 'y'.
	assert ctx['y'] == 2
	# The context maps 'y' to 3.
	ctx['y'] = 3
	# Asserts that the context correctly maps 'y' to 3.
	assert ctx['y'] == 3
	# Asserts that the context correctly maps 'z' to 4.
	assert ctx['z'] == 4
	# Asserts that the context correctly maps 'w' to 6.
	assert ctx['w'] == 6

	# The context's cache is cleared.
	ctx.clear_cache()
	# The context maps 'x' to 10.
	ctx['x'] = 10
	# Asserts that the context correctly maps 'z' to 21 after the cache is cleared.
	assert ctx['z'] == 21
	# Asserts that the context correctly maps 'w' to 23 after the cache is cleared.
	assert ctx['w'] == 23

class _Kit2(_Kit1):  # Inherits all tools from the parent class by default
	"""
	The _Kit2 class is a subclass of _Kit1. It provides methods to handle gizmos 'y', 'z', and 'x'.
	It also includes a method to check the results of other methods.

	Attributes:
		_sign (int): A multiplier used in the get_x method. Defaults to 1.
	"""

	def __init__(self, sign=1):
		"""
		Initializes a new instance of the _Kit2 class.

		Args:
			sign (int): A multiplier used in the get_x method. Defaults to 1.
		"""
		super().__init__()
		self._sign = sign

	@tool('y')  # The 'tool' decorator is used to define a function 'change_y' with 'y' as its gizmo.
	def change_y(self, y):  # "Refinement" - chaining the tool implicitly
		"""
		This method takes an integer as input and returns the integer incremented by 10.

		Args:
			y (int): The input integer.

		Returns:
			int: The input integer incremented by 10.
		"""
		return y + 10

	@tool('x')  # The 'tool' decorator is used to define a function 'get_x' with 'x' as its gizmo.
	def get_x(self):
		"""
		This method returns the product of 100 and the _sign attribute.

		Returns:
			int: The product of 100 and the _sign attribute.
		"""
		return 100 * self._sign  # Freely use object attributes

	def check(self):  # Freely calling tools as methods
		"""
		This method returns the sum of the results of the 'f' method called with 9, the 'h' method called with 8, and the 'f' method called with 19.

		Returns:
			int: The sum of the results of the 'f' method called with 9, the 'h' method called with 8, and the 'f' method called with 19.
		"""
		return self.f(9) + type(self).h(8) + type(self).f(19)  # 40

	@tool('z')  # The 'tool' decorator is used to define a function 'g' with 'z' as its gizmo.
	def g(self, x):  # Overriding a tool (this will be registered, rather than the super method)
		"""
		This method takes an integer as input and returns the sum of the integer and itself.

		Args:
			x (int): The input integer.

		Returns:
			int: The sum of the input integer and itself.
		"""
		# Use with caution - it's recommended to use clear naming for the function
		return super().g(x, x)  # Super method can be called as usual

def test_crafty_kit_inheritance():
	"""
	This function tests the functionality of the '_Kit2' class, the 'Context' class, and the 'clear_cache' method.

	The '_Kit2' class is instantiated and its methods 'f', 'g', 'h', 'check', 'get_x', and 'change_y' are tested.
	The 'Context' class is used to create a context with the '_Kit2' instance.
	The 'clear_cache' method is then used to clear the context's cache.

	The function asserts that the '_Kit2' instance correctly increments its input by 1 for method 'f', correctly sums its input for method 'g', correctly increments its input by 2 for method 'h', correctly checks the results of other methods for method 'check', correctly gets the product of 100 and the _sign attribute for method 'get_x', and correctly increments its input by 10 for method 'change_y'.
	It also asserts that the context correctly maps 'x' to 'y', 'z', 'w', and 'x', and that it updates correctly when the context's cache is cleared and a new tool is included.
	"""

	# Asserts that the 'f' method of the '_Kit2' class correctly increments its input by 1.
	assert _Kit2.f(1) == 2
	# Asserts that the 'h' method of the '_Kit2' class correctly increments its input by 2.
	assert _Kit2.h(1) == 3

	# The '_Kit2' class is instantiated.
	kit = _Kit2()
	# Asserts that the 'f' method of the '_Kit2' instance correctly increments its input by 1.
	assert kit.f(1) == 2
	# Asserts that the 'g' method of the '_Kit2' instance correctly sums its input.
	assert kit.g(2) == 4
	# Asserts that the 'h' method of the '_Kit2' instance correctly increments its input by 2.
	assert kit.h(1) == 3
	# Asserts that the 'check' method of the '_Kit2' instance correctly checks the results of other methods.
	assert kit.check() == 40
	# Asserts that the 'get_x' method of the '_Kit2' instance correctly gets the product of 100 and the _sign attribute.
	assert kit.get_x() == 100
	# Asserts that the 'change_y' method of the '_Kit2' instance correctly increments its input by 10.
	assert kit.change_y(1) == 11

	# The 'Context' class is used to create a context with the '_Kit2' instance.
	ctx = Context(kit)

	# Asserts that the context correctly identifies the gizmos of the '_Kit2' instance.
	assert list(ctx.gizmos()) == ['y', 'z', 'w', 'x']

	# The context maps 'x' to 'y'.
	ctx['x'] = 100
	# Asserts that the context correctly maps 'x' to 'y'.
	assert ctx['y'] == 111
	# Asserts that the context correctly maps 'z' to 'w'.
	assert ctx['z'] == 200
	# Asserts that the context correctly maps 'w' to 'x'.
	assert ctx['w'] == 202

	# The context's cache is cleared.
	ctx.clear_cache()

	# A new tool is defined and included in the context.
	new_z = tool('z')(lambda: 1000)
	ctx.include(new_z)

	# Asserts that 'x' is not in the context's cache.
	assert 'x' not in ctx.cached()
	# Asserts that the context correctly maps 'y' to 'a'.
	assert ctx['y'] == 111
	# Asserts that 'x' is in the context's cache.
	assert 'x' in ctx.cached()
	# Asserts that the context correctly maps 'x' to 'y'.
	assert ctx['x'] == 100

	# Asserts that the context correctly maps 'z' to 'w' after the new tool is included.
	assert ctx['z'] == 1000
	# Asserts that the context correctly maps 'w' to 'x' after the new tool is included.
	assert ctx['w'] == 1002


class _Kit3(ToolKit):
	"""
	The _Kit3 class is a subclass of ToolKit. It provides methods to handle gizmos 'a', 'b', 'c', and 'd'.
	"""

	@tool('b')  # The 'tool' decorator is used to define a function 'f' with 'b' as its gizmo.
	@tool('a')  # The 'tool' decorator is used to define a function 'f' with 'a' as its gizmo.
	def f(self):
		"""
		This method returns the integer 1.

		Returns:
			int: The integer 1.
		"""
		return 1

	@tool('c')  # The 'tool' decorator is used to define a function 'g' with 'c' as its gizmo.
	@tool('b')  # The 'tool' decorator is used to define a function 'g' with 'b' as its gizmo.
	def g(self):
		"""
		This method returns the integer 2.

		Returns:
			int: The integer 2.
		"""
		return 2

	@tool('d')  # The 'tool' decorator is used to define a function 'h' with 'd' as its gizmo.
	@tool('c')  # The 'tool' decorator is used to define a function 'h' with 'c' as its gizmo.
	def h(self, b):
		"""
		This method takes an integer as input and returns the integer incremented by 10.

		Args:
			b (int): The input integer.

		Returns:
			int: The input integer incremented by 10.
		"""
		return b + 10



def test_nested_tools():
	"""
	This function tests the functionality of the '_Kit3' class and the 'Context' class.

	The '_Kit3' class is instantiated and a context is created with the '_Kit3' instance as its tool kit.
	The function asserts that the gizmos of the '_Kit3' instance are correctly identified and that the context correctly maps 'x' to 'y', 'z', 'w', and 'x'.
	"""

	# The '_Kit3' class is instantiated.
	kit = _Kit3()

	# Asserts that the gizmos of the '_Kit3' instance are correctly identified.
	assert list(kit.gizmos()) == ['a', 'b', 'c', 'd']

	# The 'Context' class is used to create a context with the '_Kit3' instance.
	ctx = Context(kit)

	# Asserts that the context correctly maps 'd' to 11.
	assert ctx['d'] == 11
	# Asserts that the context correctly maps 'c' to 2.
	assert ctx['c'] == 2
	# Asserts that the context correctly maps 'b' to 1.
	assert ctx['b'] == 1
	# Asserts that the context correctly maps 'a' to 1.
	assert ctx['a'] == 1


def test_scope():
	"""
	This function tests the functionality of the 'Scope' class and the 'Context' class with a '_Kit1' instance.

	The '_Kit1' class is instantiated and a scope is created with the '_Kit1' instance as its tool kit and a gizmo mapping from 'y' to 'a'.
	A context is then created with the scope as its tool kit.
	The function asserts that the gizmos of the scope are correctly identified and that the context correctly maps 'x' to 'a'.
	A new context is then created with a new scope as its tool kit, which has a gizmo mapping from 'y' to 'a' and 'x' to 'b'.
	The function asserts that the gizmos of the new scope are correctly identified and that the new context correctly maps 'b' to 'a' and 'z' to 'c'.
	"""

	# The '_Kit1' class is instantiated.
	kit = _Kit1()

	# The 'Scope' class is used to create a scope with the '_Kit1' instance and a gizmo mapping from 'y' to 'a'.
	scope = Scope(kit, gap={'y': 'a'})

	# Asserts that the gizmos of the scope are correctly identified.
	assert list(scope.gizmos()) == ['a', 'z', 'w']

	# The 'Context' class is used to create a context with the scope.
	ctx = Context(scope)

	# Asserts that the gizmos of the context are correctly identified.
	assert list(ctx.gizmos()) == ['a', 'z', 'w']

	# The context maps 'x' to 'y'.
	ctx['x'] = 1
	# Asserts that the context correctly maps 'x' to 'a'.
	assert ctx['a'] == 2

	# The 'Context' class is used to create a new context with a new scope, which has a gizmo mapping from 'y' to 'a' and 'x' to 'b'.
	ctx = Context(Scope(kit, gap={'y': 'a', 'x': 'b'}))

	# Asserts that the gizmos of the new scope are correctly identified.
	assert list(ctx.gizmos()) == ['a', 'z', 'w']

	# The context maps 'b' to 'x'.
	ctx['b'] = 1
	# Asserts that the context correctly maps 'b' to 'a'.
	assert ctx['a'] == 2
	# Asserts that the context correctly maps 'z' to 'c'.
	assert ctx['z'] == 3


def test_selection():
	"""
	This function tests the functionality of the 'Selection' class, the 'Context' class, and the '_Kit1' instance.

	The '_Kit1' class is instantiated and a selection is created with the '_Kit1' instance as its tool kit and a gizmo mapping from 'y' to 'a'.
	A context is then created with the selection as its tool kit.
	The function asserts that the gizmos of the selection are correctly identified and that the context correctly maps 'x' to 'y'.
	"""

	# The '_Kit1' class is instantiated.
	kit = _Kit1()

	# The 'Selection' class is used to create a selection with the '_Kit1' instance and a gizmo mapping from 'y' to 'a'.
	scope = Selection(kit, gap=['y'])

	# Asserts that the gizmos of the selection are correctly identified.
	assert list(scope.gizmos()) == ['y']

	# The 'Context' class is used to create a context with the selection.
	ctx = Context(scope)

	# Asserts that the gizmos of the context are correctly identified.
	assert list(ctx.gizmos()) == ['y']

	# The context maps 'x' to 'y'.
	ctx['x'] = 1

	# Asserts that the context correctly maps 'x' to 'y'.
	assert list(ctx.gizmos()) == ['x', 'y']

	# Asserts that the context correctly maps 'y' to 2.
	assert ctx['y'] == 2


def test_gate_cache():
	"""
	This function tests the functionality of the 'tool' decorator, the 'Context' class, the 'Scope' class, and the '_Kit1' instance.

	The 'tool' decorator is used to define two functions, 'f' and 'g', with 'a' and 'x' as their respective gizmos.
	The 'Context' class is used to create a context with the functions 'f' and 'g'.
	The 'Scope' class is used to create a scope with the functions 'f' and 'g' and a gizmo mapping from 'a' to 'b'.
	The 'clear_cache' method is then used to clear the context's cache.

	The function asserts that the context correctly maps 'x' to 'y' and 'z', and that it updates correctly when the context's cache is cleared.
	"""

	counter = 0

	@tool('a')  # The 'tool' decorator is used to define a function 'f' with 'a' as its gizmo.
	def f():
		"""
		This function increments a counter and returns 1.

		Returns:
			int: The integer 1.
		"""
		nonlocal counter
		counter += 1
		return 1

	ctx = Context(f)  # The 'Context' class is used to create a context with the function 'f'.

	assert ctx['a'] == 1  # Asserts that the context correctly maps 'a' to 1.
	assert counter == 1  # Asserts that the counter is correctly incremented.
	assert 'a' in ctx.data  # Asserts that 'a' is in the context's data.
	assert ctx['a'] == 1  # Asserts that the context correctly maps 'a' to 1.
	assert counter == 1  # Asserts that the counter is not incremented.

	ctx = Context(Scope(f, gap={'a': 'b'}))  # The 'Scope' class is used to create a scope with the function 'f' and a gizmo mapping from 'a' to 'b'.

	assert not ctx.gives('a')  # Asserts that 'a' is not grabable from the context.
	assert ctx.gives('b')  # Asserts that 'b' is grabable from the context.
	assert ctx['b'] == 1  # Asserts that the context correctly maps 'b' to 1.
	assert counter == 2  # Asserts that the counter is correctly incremented.
	assert 'b' in ctx.data  # Asserts that 'b' is in the context's data.
	assert ctx['b'] == 1  # Asserts that the context correctly maps 'b' to 1.
	assert counter == 2  # Asserts that the counter is not incremented.

	ctx.clear_cache()  # The context's cache is cleared.

	assert ctx['b'] == 1  # Asserts that the context correctly maps 'b' to 1.
	assert counter == 3  # Asserts that the counter is correctly incremented.

	@tool('x')  # The 'tool' decorator is used to define a function 'g' with 'x' as its gizmo.
	def g(a):
		"""
		This function takes an integer as input and returns the product of the integer and 10.

		Args:
			a (int): The input integer.

		Returns:
			int: The product of the input integer and 10.
		"""
		return 10 * a

	ctx = Context(Scope(f, g, gap={'a': 'b'}))  # The 'Scope' class is used to create a scope with the functions 'f' and 'g' and a gizmo mapping from 'a' to 'b'.

	assert list(ctx.gizmos()) == ['b', 'x']  # Asserts that the gizmos of the context are correctly identified.

	assert ctx['x'] == 10  # Asserts that the context correctly maps 'x' to 10.
	assert counter == 4  # Asserts that the counter is correctly incremented.
	assert 'x' in ctx.data  # Asserts that 'x' is in the context's data.
	assert 'b' not in ctx.data  # Asserts that 'b' is not in the context's data.
	assert 'a' not in ctx.data  # Asserts that 'a' is not in the context's data.

	assert ctx.is_cached('x')  # Asserts that 'x' is cached in the context.
	assert ctx.is_cached('b')  # Asserts that 'b' is cached in the context.

	assert ctx['b'] == 1  # Asserts that the context correctly maps 'b' to 1.
	assert counter == 4  # Asserts that the counter is not incremented.

	ctx.clear_cache()  # The context's cache is cleared.

	assert ctx['b'] == 1  # Asserts that the context correctly maps 'b' to 1.
	assert counter == 5  # Asserts that the counter is correctly incremented.

	ctx.clear_cache()  # The context's cache is cleared.

	ctx['b'] = 2  # The context maps 'b' to 2.
	assert ctx['x'] == 20  # Asserts that the context correctly maps 'x' to 20.
	assert counter == 5  # Asserts that the counter is not incremented.

	ctx = Context(Scope(f, g))  # The 'Scope' class is used to create a scope with the functions 'f' and 'g'.

	assert list(ctx.gizmos()) == ['a', 'x']  # Asserts that the gizmos of the context are correctly identified.

	assert ctx['x'] == 10  # Asserts that the context correctly maps 'x' to 10.
	assert counter == 6  # Asserts that the counter is correctly incremented.
	assert 'x' in ctx.data  # Asserts that 'x' is in the context's data.
	assert 'a' not in ctx.data  # Asserts that 'a' is not in the context's data.
	assert ctx['a'] == 1  # Asserts that the context correctly maps 'a' to 1.
	assert counter == 6  # Asserts that the counter is not incremented.

	ctx.clear_cache()  # The context's cache is cleared.

	assert ctx['a'] == 1  # Asserts that the context correctly maps 'a' to 1.
	assert counter == 7  # Asserts that the counter is correctly incremented.

	ctx.clear_cache()  # The context's cache is cleared.

	ctx['a'] = 2  # The context maps 'a' to 2.
	assert ctx['x'] == 20  # Asserts that the context correctly maps 'x' to 20.
	assert counter == 7  # Asserts that the counter is not incremented.



def test_simple_mimo():

	_fuel = 1

	@tool('x', 'y')
	def f(a, b):
		nonlocal _fuel
		if _fuel == 0:
			raise Exception('No fuel')
		_fuel -= 1
		return a + b, a * b

	ctx = Context(f)
	ctx['a'] = 2
	ctx['b'] = 3

	assert ctx['x'] == 5
	assert ctx.is_cached('x')
	assert not ctx.is_cached('y')
	assert ctx['y'] == 6
	assert ctx.is_cached('x')
	assert ctx.is_cached('y')
	assert ctx['x'] == 5


	@tool('x', 'y')
	def g(a):
		return {'x': a + 1, 'y': a + 2}

	@tool('a')
	def h():
		return 1

	ctx = Context(g, h)

	assert ctx['x'] == 2
	assert ctx.is_cached('x')
	assert not ctx.is_cached('y')
	assert ctx['y'] == 3
	assert ctx.is_cached('x')
	assert ctx.is_cached('y')


def test_simple_purge():

	@tool('x')
	def g(a):
		return a + 1

	@tool('a')
	def h():
		return 1

	ctx = Context(g, h)

	assert ctx['x'] == 2
	assert ctx.is_cached('a') and ctx.is_cached('x')
	ctx.purge('a')
	assert not ctx.is_cached('a') and not ctx.is_cached('x')

	assert ctx['x'] == 2
	assert ctx.is_cached('a') and ctx.is_cached('x')
	ctx['a'] = 10
	assert ctx.is_cached('a') and not ctx.is_cached('x')
	assert ctx['x'] == 11
	assert ctx.is_cached('x')

	# mimo

	@tool('x', 'y')
	def f(a):
		return a + 1, a + 2

	ctx = Context(f, h)

	assert ctx['x'] == 2
	assert ctx.is_cached('a') and ctx.is_cached('x') and not ctx.is_cached('y')

	ctx['a'] = 10
	assert ctx.is_cached('a') and not ctx.is_cached('x') and not ctx.is_cached('y')
	assert ctx['y'] == 12
	assert ctx.is_cached('a') and not ctx.is_cached('x') and ctx.is_cached('y')



def test_genetics():
	kit = _Kit3()

	genome = next(kit.genes('a'))

	assert genome.name == 'a'
	assert genome.parents == ()
	assert genome.siblings is None

	genomes = list(kit.genes('c'))

	assert len(genomes) == 2
	assert genomes[1].name == 'c'
	assert genomes[1].parents == ('b',)
	assert genomes[1].siblings is None

	genome = next(kit.genes('d'))

	assert genome.name == 'd'
	assert genome.parents == ('b',)
	assert genome.siblings is None


	@tool('x', 'y')
	def f(a):
		return a + 1, a + 2

	genome = next(f.genes('x'))

	assert genome.name == 'x'
	assert genome.parents == ('a',)
	assert genome.siblings == (None, 'y')

	genome = next(f.genes('y'))

	assert genome.name == 'y'
	assert genome.parents == ('a',)
	assert genome.siblings == ('x', None)
	assert genome.endpoint == f._fn
	assert genome.source == f



def test_parents():
	class MyKit(ToolKit):
		@tool.from_context('a', 'b')
		def f(self, ctx):
			return ctx['x'] * ctx['y'], ctx['y']
		@f.parents
		def _f_parents(self):
			return 'x', 'y'

	kit = MyKit()

	genome = next(kit.genes('a'))

	assert genome.name == 'a'
	assert genome.parents == ('x', 'y')
	assert genome.siblings == (None, 'b')

	ctx = Context(kit)

	ctx['x'] = 10
	ctx['y'] = 20

	assert ctx['a'] == 200
	assert not ctx.is_cached('b')
	assert ctx['b'] == 20















