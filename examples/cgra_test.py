##
# \package sylva.examples.cgra_test
#
# All tests for sylva.base.cgra.
##

from sylva.base.sylva_base import SYLVATest

from sylva.base.cgra import CGRA
from sylva.base.fimp import FIMPCost, FIMPInstance


__author__ = 'Shuo Li <contact@shuol.li>'
__version__ = '2017-05-17'
__license__ = 'https://opensource.org/licenses/MIT'


##
# @brief      Creates a CGRA object for demostration.
##
# It size it 4X4 and there are two FIMPInstance objects in it.
# One is `FFT` and the other is `FIR`.
##
# @return     CGRA object
##
def create_cgra():
    cgra = CGRA('CGRA', width=4, height=4)

    fft_cost = FIMPCost('FFT', width=2, height=2)
    fir_cost = FIMPCost('FIR', width=1, height=1)
    fft = FIMPInstance(name='FFT', index=0, actors=[],
                       x=1, y=1, cost=fft_cost)
    fir = FIMPInstance(name='FIR', index=1, actors=[],
                       x=3, y=1, cost=fir_cost)
    cgra.add(fft)
    cgra.add(fir)
    return cgra


if __name__ == '__main__':

    CLEAN_UP = True

    def check_reloaded(*args, **kwargs):
        SYLVATest.check_reloaded(*args, **kwargs, clean_store=CLEAN_UP)

    check_reloaded(CGRA)

    # `CGRA.svg` will be created
    create_cgra().get_svg().save()
