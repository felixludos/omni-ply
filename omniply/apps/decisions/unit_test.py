from typing import Any, Mapping, Iterator
import random

from ... import AbstractGame
from ...core import ToolKit, Context, tool
from .op import GadgetDecision, SimpleDecision, Combination, Controller
from ..simple import DictGadget


def test_decisions():

	decision = SimpleDecision('A', [1, 2, 3])

	for _ in range(100):
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

		assert len(cases) <= 6

	assert len(cases) == 6
	assert (cases[0]['A'], cases[0]['B']) == (1, 4)
	assert (cases[1]['A'], cases[1]['B']) == (1, 5)
	assert (cases[2]['A'], cases[2]['B']) == (2, 4)
	assert (cases[3]['A'], cases[3]['B']) == (2, 5)
	assert (cases[4]['A'], cases[4]['B']) == (3, 4)
	assert (cases[5]['A'], cases[5]['B']) == (3, 5)


def test_consider_implicit_targets():

	ctx = Controller(
		SimpleDecision('A', [1, 2, 3]),
		SimpleDecision('B', [4, 5]),
	)

	oracle = [
		(1, 4), (1, 5),
		(2, 4), (2, 5),
		(3, 4), (3, 5),
	]

	cases = []
	for case, correct in zip(ctx.consider(), oracle):
		assert (case['A'], case['B']) == correct
		cases.append(case)

		assert len(cases) <= 6

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

		assert len(cases) <= 5

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

		assert len(cases) <= 3

	assert len(cases) == 3
	assert cases[0]['C'] == 110
	assert cases[1]['C'] == -4
	assert cases[2]['C'] == -5

	ctx['B_choice'] = 1

	assert not ctx.is_cached('B')

	cases = []
	for case in ctx.consider('C'):
		cases.append(case)

		assert len(cases) <= 2

	assert len(cases) == 2
	assert cases[0]['C'] == 110
	assert cases[1]['C'] == -5



def test_consider_target():

	ctx = Controller(
		SimpleDecision('A', [1, 2, 3]),
		SimpleDecision('B', [4, 5]),
	)

	cases = []
	for case in ctx.consider('A'):
		cases.append(case)

		assert len(cases) <= 3



def test_consider_partial_target():
	# NOTE: OldController will fail this test because it's top-down, not bottom-up

	ctx = Controller(
		SimpleDecision('A', [1, 2, 3]),
		SimpleDecision('B', [4, 5]),
	)

	wait = 0
	cases = []
	for case in ctx.consider('A'):
		if wait >= 0:
			case['B'] # adds 'B' as a target
		cases.append(case)
		wait -= 1

		assert len(cases) <= 4

	assert (cases[0]['A'], cases[0]['B']) == (1, 4)
	assert (cases[1]['A'], cases[1]['B']) == (1, 5)
	assert (cases[2]['A'], cases[2]['B']) in {(2, 4), (2, 5)}
	assert (cases[3]['A'], cases[3]['B']) in {(3, 4), (3, 5)}


	wait = 1
	cases = []
	for case in ctx.consider('A'):
		if wait >= 0:
			case['B'] # adds 'B' as a target
		cases.append(case)
		wait -= 1

		assert len(cases) <= 4

	assert (cases[0]['A'], cases[0]['B']) == (1, 4)
	assert (cases[1]['A'], cases[1]['B']) == (1, 5)
	assert (cases[2]['A'], cases[2]['B']) in {(2, 4), (2, 5)}
	assert (cases[3]['A'], cases[3]['B']) in {(3, 4), (3, 5)}

	wait = 2
	cases = []
	for case in ctx.consider('A'):
		if wait >= 0:
			case['B'] # adds 'B' as a target
		cases.append(case)
		wait -= 1

		assert len(cases) <= 5

	assert (cases[0]['A'], cases[0]['B']) == (1, 4)
	assert (cases[1]['A'], cases[1]['B']) == (1, 5)
	assert (cases[2]['A'], cases[2]['B']) == (2, 4)
	assert (cases[3]['A'], cases[3]['B']) == (2, 5)
	assert (cases[4]['A'], cases[4]['B']) in {(3, 4), (3, 5)}

	wait = 2
	cases = []
	for case in ctx.consider('A'):
		if wait == 1:
			case['B'] # adds 'B' as a target
		cases.append(case)
		wait -= 1

		assert len(cases) <= 4

	assert (cases[0]['A'], cases[0]['B']) in {(1, 4), (1, 5)}
	assert (cases[1]['A'], cases[1]['B']) == (2, 4)
	assert (cases[2]['A'], cases[2]['B']) == (2, 5)
	assert (cases[3]['A'], cases[3]['B']) in {(3, 4), (3, 5)}



def test_large_decision():

	num_picks = 5
	N = 20
	K = 10

	gen = Combination(N, K, gizmo='combo', choice_gizmo='choice')

	random.seed(11)
	manual_picks = list(gen.cover(num_picks))
	assert manual_picks == [118588, 146740, 122067, 118445, 133127]

	ctx = Controller(gen)

	assert gen.count() == 184756 # 20 choose 10

	random.seed(11)
	cases = []
	auto_picks = []
	combos = []
	for case in ctx.consider(limit=5):
		combos.append(case.grab('combo'))
		assert case.is_cached('choice')
		auto_picks.append(case['choice'])
		cases.append(case)
		assert len(cases) <= 5

	assert all(len(combo) == K and min(combo) >= 0 and max(combo) <= N-1 for combo in combos)
	assert auto_picks == manual_picks
	assert auto_picks[0] != auto_picks[1]
	assert combos[0] != combos[1]






# test nested consideration - case.consider()






















