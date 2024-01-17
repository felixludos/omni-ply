

try:
	from graphviz import Digraph

except ImportError:
	pass




def signature_graph(kit, name='unknown'):

	g = Digraph(name, filename=f'{name}.gv')

	for sig in kit.signatures():
		for inp in sig.inputs:
			g.edge(inp, sig.output)
		for meta in sig.meta:
			g.edge(meta, sig.output, style='dashed')
			g.node(meta, shape='box')

	return g














