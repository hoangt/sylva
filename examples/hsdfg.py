##
# \package sylva.examples.hsdfg_example
#
# Example of HSDFG creation and rendering.
# It used the same SDFG from sylva.examples.sdfg
##

from sylva.examples.sdfg import create_sdfg

__author__ = 'Shuo Li <contact@shuol.li>'
__version__ = '2017-05-18'
__license__ = 'https://opensource.org/licenses/MIT'


if __name__ == '__main__':

    hsdfg = create_sdfg().get_hsdf()

    # create a dot graph from the HSDFG
    dot_graph = hsdfg.get_digraph()

    # render it as an svg file
    # `HSDFG_example.gv` will be created
    # `HSDFG_example.gv.svg` will be created
    dot_graph.format = 'svg'
    dot_graph.render('HSDFG_example.gv', cleanup=False)

    # render it as a pdf file
    # `HSDFG_example.gv` will be created
    # `HSDFG_example.gv.pdf` will be created
    dot_graph.format = 'pdf'
    dot_graph.render('HSDFG_example.gv', cleanup=False)
