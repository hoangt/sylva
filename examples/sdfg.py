##
# \package sylva.examples.sdfg_example
#
# Example of SDFG creation and rendering
##

from sylva.base.sdf import Actor, Edge, Port, SDFG

__author__ = 'Shuo Li <contact@shuol.li>'
__version__ = '2017-05-19'
__license__ = 'https://opensource.org/licenses/MIT'


##
# @brief      Creates a SDFG object with four actors for demostration.
#
##
# @return     SDFG object
##
def create_sdfg():
    actor_names = ['a', 'b', 'c', 'd']

    # we will assign indexes for actors later
    a, b, c, d = [Actor(name=name) for name in actor_names]

    a_dout_b = Port(name='a_dout_b', count=4)
    a.output_ports.append(a_dout_b)

    d_dout_b = Port(name='d_dout_b', count=2)
    d.output_ports.append(d_dout_b)

    a_din_b = Port(name='a_din_b', count=2)
    d_din_b = Port(name='d_din_b', count=4)
    b.input_ports.append(a_din_b)
    b.input_ports.append(d_din_b)

    b_dout_c = Port(name='b_dout_c', count=2)
    b.output_ports.append(b_dout_c)

    b_din_c = Port(name='b_din_c', count=2)
    c.input_ports.append(b_din_c)

    Edge(a, a_dout_b, b, a_din_b)
    Edge(d, d_dout_b, b, d_din_b)
    Edge(b, b_dout_c, c, b_din_c)

    # we will assign indexes for actors by passing
    # `reassign_actor_indexes=True`
    return SDFG([a, d, b, c], reassign_actor_indexes=True)


if __name__ == '__main__':

    sdfg = create_sdfg()

    # create a dot graph from the SDFG
    dot_graph = sdfg.get_digraph()

    # render it as an svg file
    # `SDFG_example.gv` will be created
    # `SDFG_example.gv.svg` will be created
    dot_graph.format = 'svg'
    dot_graph.render('SDFG_example.gv', cleanup=False)

    # render it as a pdf file
    # `SDFG_example.gv` will be created
    # `SDFG_example.gv.pdf` will be created
    dot_graph.format = 'pdf'
    dot_graph.render('SDFG_example.gv', cleanup=False)
