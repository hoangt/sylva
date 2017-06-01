##
# \package sylva.base.cgra
# Simple CGRA class definition
##

from sylva.base.fimp import *
from sylva.base.sylva_base import SYLVABase, SYLVAList, SYLVASVG

__author__ = 'Shuo Li <contact@shuol.li>'
__version__ = '2017-05-18'
__license__ = 'https://opensource.org/licenses/MIT'


##
# @brief      Class for CGRA
#
##


class CGRA(SYLVABase):

    ##
    # \var name
    # The name of this CGRA.
    #
    # \var width
    # CRGA fabric width in number of CGRA elements
    ##
    # \var height
    # CRGA fabric height in number of CGRA elements
    ##
    # \var hop_x
    # ((Window width - 1) / 2) for sliding window communication scheme
    # in number of CGRA elements.
    ##
    # \var hop_y
    # ((Window height - 1) / 2) for sliding window communication scheme
    # in number of CGRA elements.
    ##
    # \var TC
    # cross-window communication time in clock cycles
    ##
    # \var TW
    # intra-window communication time in clock cycles
    ##
    # \var fimp_instances
    # FIMP instances mapped on this CGRA
    ##
    #

    ##
    # @brief      Constructs the object.
    ##
    # @param      self            The object
    # @param      name            \copydoc CGRA::name
    # @param      width           \copydoc CGRA::width
    # @param      height          \copydoc CGRA::height
    # @param      hop_x           \copydoc CGRA::hop_x
    # @param      hop_y           \copydoc CGRA::hop_y
    # @param      TC              \copydoc CGRA::TC
    # @param      TW              \copydoc CGRA::TW
    # @param      fimp_instances  \copydoc CGRA::fimp_instances
    # @param      otherkwargs     The other keyword arguments,
    # reserved for future usage
    ##
    def __init__(self, name='CGRA',
                 width=1, height=1,
                 hop_x=1, hop_y=1,
                 TC=1, TW=1,
                 fimp_instances=[], **otherkwargs):

        self.width = width
        self.height = height
        self.hop_x = hop_x
        self.hop_y = hop_y
        self.TC = TC
        self.TW = TW
        self.fimp_instances = fimp_instances

        SYLVABase.__init__(self, **SYLVABase._args(locals(), globals()))

        self.fimp_instances = SYLVAList(self.fimp_instances)

    ##
    # @brief      Adds a FIMPInstance to this CGRA
    ##
    # @param      self           The object
    # @param      fimp_instance  The FIMP object
    ##
    def add(self, fimp_instance):
        if fimp_instance not in self.fimp_instances:
            self.fimp_instances.append(fimp_instance)

    def get_usage(self):
        usage = []
        for x in range(self.width):
            usage.append([])
            for y in range(self.height):
                usage[-1].append([])

        for fimp_instance in self.fimp_instances:
            x = fimp_instance.x
            y = fimp_instance.y
            for w in range(fimp_instance.width):
                for h in range(fimp_instance.height):
                    usage[x + w][y + h] += [fimp_instance.name]
        return usage

    def get_svg(self, name='CGRA', padding=2):

        svg = SYLVASVG(name)
        grids = svg.add_grid(rows=self.height, cols=self.width, label_pos=True)
        for f in self.fimp_instances:
            w_unit = grids[0][0].width
            h_unit = grids[0][0].height
            w = f.cost.width * w_unit - 2 * padding
            h = f.cost.height * h_unit - 2 * padding
            x = f.x * w_unit + padding
            y = f.y * h_unit + padding
            svg.add_rect(x=x, y=y, width=w, height=h,
                         label=f.function_name, fill='gray',
                         text_color='red', text_stroke='blue')
        return svg
