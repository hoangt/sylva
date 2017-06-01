##
# \package sylva.test.sdf_test
#
# All tests for sylva.base.sdf.
##

from sylva.base.sylva_base import SYLVATest

from sylva.base.sdf import *


__author__ = 'Shuo Li <contact@shuol.li>'
__version__ = '2017-05-17'
__license__ = 'https://opensource.org/licenses/MIT'


##
# @brief      Creates an Edge object for demostration.
##
# @return     Edge object
##
def create_edge():
    Actor.reset_index()
    a = Actor('a')
    b_din_a = Port('b_din_a')
    a.input_ports.append(b_din_a)

    b = Actor('b')
    b_dout_a = Port('b_dout_a')
    b.output_ports.append(b_dout_a)

    return Edge(b, b_dout_a, a, b_din_a)


##
# @brief      Creates an Actor object for demostration.
##
# @return     Actor object
##
def create_actor():
    Actor.reset_index()
    a = Actor('a')
    b_din_a = Port('b_din_a')
    a.input_ports.append(b_din_a)
    return a


if __name__ == '__main__':

    CLEAN_UP = True

    def check_reloaded(*args, **kwargs):
        SYLVATest.check_reloaded(*args, **kwargs, clean_store=CLEAN_UP)

    # test DataTokenType
    check_reloaded(DataTokenType)

    # test Edge
    # e = create_edge()
    # check_reloaded(e)

    # # test Actor
    # a = create_actor()
    # check_reloaded(a)

    # # test SDFG
    # from sylva.examples.sdfg import create_sdfg
    # sdfg = create_sdfg()
    # print(dict(sdfg))
    # sdfg = SDFG(**dict(sdfg))
    # # check_reloaded(sdfg)

    # # test HDFG
    # hsdfg = sdfg.get_hsdf()
    # check_reloaded(hsdfg)

    # # test SDFG to graphviz
    # sdfg.get_digraph().render('SDFG_test.gv', cleanup=CLEAN_UP)

    # # test HSDFG to graphviz
    # hsdfg.get_digraph().render('HSDFG_test.gv', cleanup=CLEAN_UP)
