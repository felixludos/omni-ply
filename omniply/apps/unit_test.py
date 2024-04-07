from typing import Any, Mapping, Iterator
from .. import AbstractGame
from ..core import ToolKit, Context, tool
from .decisions import GadgetDecision, SimpleDecision, Controller
from .simple import DictGadget


def test_decisions():

	decision = SimpleDecision('A', [1, 2, 3])

	ctx = Controller(decision)

	assert ctx['A'] in [1, 2, 3]


def test_consideration():

	ctx = Controller(
		SimpleDecision('A', [1, 2, 3]),
		SimpleDecision('B', [4, 5]),
	)

	cases = []
	for case in ctx.consider('A', 'B'):
		# print(case['A'], case['B'])
		cases.append(case)

	assert len(cases) == 6
	assert (cases[0]['A'], cases[0]['B']) == (1, 4)
	assert (cases[1]['A'], cases[1]['B']) == (1, 5)
	assert (cases[2]['A'], cases[2]['B']) == (2, 4)
	assert (cases[3]['A'], cases[3]['B']) == (2, 5)
	assert (cases[4]['A'], cases[4]['B']) == (3, 4)
	assert (cases[5]['A'], cases[5]['B']) == (3, 5)



def test_gadget_decision():
	@tool('C')
	def from_a(A):
		return A + 100
	@tool('C')
	def from_b(B):
		return -B


	ctx = Controller(
		GadgetDecision([from_a, from_b], choice_gizmo='my_choice'),
		SimpleDecision('A', [1, 2, 3]),
		SimpleDecision('B', [4, 5]),
	)

	cases = []
	for case in ctx.consider('C'):
		cases.append(case)

	assert len(cases) == 5
	assert cases[0]['C'] == 101
	assert cases[1]['C'] == 102
	assert cases[2]['C'] == 103
	assert cases[3]['C'] == -4
	assert cases[4]['C'] == -5

	assert not ctx.is_cached('C') and not ctx.is_cached('A') and not ctx.is_cached('B')

	ctx['A'] = 10

	cases = []
	for case in ctx.consider('C'):
		cases.append(case)

	assert len(cases) == 3
	assert cases[0]['C'] == 110
	assert cases[1]['C'] == -4
	assert cases[2]['C'] == -5

	ctx['B_choice'] = 1

	assert not ctx.is_cached('B')

	cases = []
	for case in ctx.consider('C'):
		cases.append(case)

	assert len(cases) == 2
	assert cases[0]['C'] == 110
	assert cases[1]['C'] == -5




























