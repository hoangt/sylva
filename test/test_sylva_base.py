from sylva.base.sylva_base import DataTokenType, Port, Actor, Edge
from sylva.base.sylva_base import DFG, SDFG
from sylva.base.sylva_base import SYLVATest, SYLVASVG
from sylva.base.sylva_base import CGRA
from sylva.base.fimp import FIMPCost, FIMPCostSet, FIMPInstance, FIMPLibrary

clean_store = True


def check_reloaded(obj):
    SYLVATest.check_reloaded(obj, clean_store)


check_reloaded(DataTokenType)
check_reloaded(Port)
check_reloaded(Actor)

din = Port('din', count=2)
a = Actor('a')
a.input_ports += [din]
b = Actor('b')
dout = Port('dout', count=1)
b.output_ports += [dout]
e = Edge(b, dout, a, din)
check_reloaded(e)

dfg = DFG([a, b])
check_reloaded(dfg)

sdfg = SDFG([a, b])
check_reloaded(sdfg)

hsdfg = sdfg.get_hsdf()
check_reloaded(hsdfg)

g = hsdfg.get_digraph()

svg = SYLVASVG()
check_reloaded(svg)


fft = Actor('fft')
fft_cost_0 = FIMPCost('fft', width=1, height=1, energy=1, fimp_type_name='fft_4')
fft_cost_1 = FIMPCost('fft', width=2, height=2, energy=4, )
check_reloaded(fft_cost_0)


ffts = FIMPCostSet(fft)
ffts.add(fft_cost_0)
ffts.add(fft_cost_1)
check_reloaded(ffts)

fft = FIMPInstance(function_name='fft',
                   index=0, actors=[], x=1, y=1, cost=fft_cost_1)
fft.add(a)
check_reloaded(fft)

flib = FIMPLibrary()
flib.add(ffts)
check_reloaded(flib)

cgra = CGRA('CGRA', width=4, height=4)

fir_cost = FIMPCost('fir', width=1, height=1)
fir = FIMPInstance(function_name='fir', index=1, actors=[],
                   x=3, y=1, cost=fir_cost)
fir.add(b.child_actors)
cgra.fimp_instances.append(fft)
cgra.fimp_instances.append(fir)
check_reloaded(cgra)
g = cgra.get_svg()
g.save()
