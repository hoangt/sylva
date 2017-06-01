##
# \package sylva.base.fimp
# FIMP related classes
##

from sylva.base.sylva_base import SYLVABase, Actor

__author__ = 'Shuo Li <contact@shuol.li>'
__version__ = '2017-05-26'
__license__ = 'https://opensource.org/licenses/MIT'


##
# @brief      Class for FIMP cost.
##
# The function name will be provided by the FIMPSet object
##


class FIMPCost(SYLVABase):

    ##
    # \var function_name
    # The function name of this FIMP
    #
    # \var fimp_type_index
    # integer identifier of the FIMP's type, e.g `0`,
    # This is used for DSE when we want to specify
    # which FIMP type we are going to use.
    ##
    # \var width
    # FIMP width
    # in number of CGRA elements for CGRA,
    # total gate count in ASIC
    # (not used by SYLVA currently),
    # total logic element count in FPGA
    # (not used by SYLVA currently).
    ##
    # \var height
    # FIMP height
    # in number of CGRA elements for CGRA,
    # total gate count in ASIC
    # (not used by SYLVA currently),
    # total logic element count in FPGA
    # (not used by SYLVA currently).
    ##
    # \var area
    # total gate count in ASIC,
    # total logic element count in FPGA,
    # total number of CGRA element in CGRA.
    ##
    # \var energy
    # average energy consumption in nano-joule for executing once.
    # The energy unit does not matter if all FIMPs have the same energy unit.
    ##
    # \var computation_phase
    # Computation phase in the three-phase function execution model.
    # In terms of number of clock cycles.
    ##
    # \var input_phase
    # Input phase in the three-phase function execution model.
    # In terms of number of clock cycles.
    ##
    # \var output_phase
    # Output phase in the three-phase function execution model.
    # In terms of number of clock cycles.
    ##
    # \var fimp_type_name
    # The name of the current FIMP type,
    # e.g `fimp_1` when `fimp_type_index == 1`.
    # If not provided it will be `f'fimp_{fimp_type_index}'`
    ##

    ##
    # @brief      Constructs the object.
    ##
    # @param      self               The object
    # @param      function_name      \copydoc FIMPCost::function_name
    # @param      fimp_type_index    \copydoc FIMPCost::fimp_type_index
    # @param      width              \copydoc FIMPCost::width
    # @param      height             \copydoc FIMPCost::height
    # @param      area               \copydoc FIMPCost::area
    # @param      energy             \copydoc FIMPCost::energy
    # @param      computation_phase  \copydoc FIMPCost::computation_phase
    # @param      input_phase        \copydoc FIMPCost::input_phase
    # @param      output_phase       \copydoc FIMPCost::output_phase
    # @param      fimp_type_name     \copydoc FIMPCost::fimp_type_name
    ##
    def __init__(self, function_name='no_function_name', fimp_type_index=0,
                 width=0, height=0, area=0, energy=0,
                 computation_phase=1, input_phase=1, output_phase=1,
                 fimp_type_name=None):

        self.function_name = function_name
        self.fimp_type_index = fimp_type_index

        self.width = width
        self.height = height

        if width and height:
            area = width * height

        self.area = area

        self.energy = energy

        self.computation_phase = computation_phase
        self.input_phase = input_phase
        self.output_phase = output_phase

        self._fimp_type_name = fimp_type_name

    ##
    # @brief      Gets the fimp type name.
    ##
    # @param      self  The object
    ##
    # @return     The fimp type name.
    ##
    def get_fimp_type_name(self):
        if self._fimp_type_name is None:
            return f'fimp_{self.fimp_type_index}'
        else:
            return self._fimp_type_name

    ##
    # \var fimp_type_name
    # The FIMP type name
    ##
    fimp_type_name = property(get_fimp_type_name)

    ##
    # @brief      Get input end time.
    #
    # Based on the current input phase.
    ##
    # @param      self  The object
    ##
    # @return     input end time related to the start time.
    ##
    def get_input_end_time(self):
        return self.input_phase - 1

    ##
    # \var input_end_time
    ##
    # \copybrief FIMPCost::\_input\_end\_time()
    ##
    input_end_time = property(get_input_end_time)

    ##
    # @brief      Get output start time.
    #
    # Based on the current output phase and computation phase.
    ##
    # @param      self  The object
    ##
    # @return     output start time related to the start time.
    ##
    def get_output_start_time(self):
        return self.computation_phase - self.output_phase + 1

    ##
    # \var output_start_time
    ##
    # \copybrief FIMPCost::\_output\_start\_time()
    ##
    output_start_time = property(get_output_start_time)

    ##
    # @brief      Test if two FIMPCost objects are equal
    #
    # If there function name and fimp type name are equal,
    # we consider they are equal.
    ##
    # @param      self       The object
    # @param      fimp_cost  The fimp cost
    ##
    # @return     { description_of_the_return_value }
    ##
    def __eq__(self, fimp_cost):
        self_dict = self.as_dict(['fimp_type_index'])
        fimp_cost_dict = fimp_cost.as_dict(['fimp_type_index'])
        return self_dict == fimp_cost_dict

    ##
    # @brief      Get dictionary representation of this object
    ##
    # @param      self     The object
    # @param      exclude  The exclude
    ##
    # @return     dictionary object
    ##
    def as_dict(self, exclude=[]):
        result = SYLVABase.as_dict(self, [])
        if self._fimp_type_name is not None:
            result['fimp_type_name'] = result.pop('_fimp_type_name')
        return result


##
# @brief      Class for FIMPCostSet.
#
# A set of FIMPCost objects for the same function that is defined
# in the FIMPCostSet.template_actor field.
##
# A FIMPSet object is for holding a set of FIMP instances
# for the same function.
##


class FIMPCostSet(SYLVABase):

    ##
    # \var template_actor
    # A FIMPSet object is for holding a set of FIMP instances
    # with the same function name and interface defined by the
    # template_actor.
    ##
    # \var fimp_costs
    # A list of FIMPCost objects is for holding a set of FIMP costs.
    # Each FIMPCost object's `function_name` = 'template_actor.name`.
    ##
    # @brief      Constructs the object.
    ##
    # @param      self            The object
    # @param      template_actor  The function name
    # @param      fimp_costs      FIMP cost list
    # @param      otherkwargs        The other keyword arguments,
    # reserved for future usage
    # List of FIMPCost objects.
    ##
    def __init__(self, template_actor, fimp_costs=[]):

        self.template_actor = template_actor
        self.fimp_costs = fimp_costs

    ##
    # @brief      Add a FIMPCost object (one_fimp) to this FIMPSet instance.
    ##
    # @param      self      The object
    # @param      one_fimp  One FIMPCost object
    #
    # @return     Success or not
    ##
    def add(self, fimp_cost):
        if fimp_cost.function_name == self.template_actor.name:
            if fimp_cost not in self.fimp_costs:
                fimp_cost.fimp_type_index = self.fimp_costs.__len__()
                self.fimp_costs.append(fimp_cost)
                return True
        return False

    ##
    # @brief      Get the number of FIMPCost objects in this FIMPSet object
    ##
    # @param      self  The object
    ##
    # @return     The number of FIMPCost objects in this FIMPSet object
    ##
    def __len__(self):
        return len(self.fimp_costs)


##
# @brief      Class for FIMP instace.
##
# This FIMP instance is created for executing multiple HSDFG actors.
##


class FIMPInstance(SYLVABase):

    ##
    # \var function_name
    # The function name
    ##
    # \var index
    # Unique integer index of this FIMP in a deployed system,
    # e.g a CGRA fabric
    ##
    # \var actors
    # The list of HSDFG Actor objects to be hosted by this FIMP instance.
    # This attribute should be assigned explicitly.
    ##
    # \var x
    # The horizental location of the FIMP instance in a CGRA fabric.
    # Only useful for CGRA target.
    # This attribute should be assigned explicitly.
    ##
    # \var y
    # The vertical location of the FIMP instance in a CGRA fabric.
    # Only useful for CGRA target.
    # This attribute should be assigned explicitly.
    ##
    # \var cost
    # The cost of the curret FIMP instance.
    # This information is obtained from the a FIMPSet object.
    ##

    ##
    # @brief      Constructs the object.
    ##
    # @param      self           The object
    # @param      function_name  \copydoc FIMPInstance::function_name
    # @param      index          \copydoc FIMPInstance::index
    # @param      actors         \copydoc FIMPInstance::actors
    # @param      x              \copydoc FIMPInstance::x
    # @param      y              \copydoc FIMPInstance::y
    # @param      cost           \copydoc FIMPInstance::cost
    # @param      otherkwargs    The other keyword arguments,
    # reserved for future usage
    ##

    def __init__(self, function_name='', index=0, actors=[], x=-1, y=-1, cost=None):

        self.function_name = function_name

        # FIMP index in a system
        # It has to be explicitly specified after synthesis
        self.index = index

        # Actors running on this FIMP
        # It has to be explicitly add to the FIMP
        # It will not be serialized.
        self.actors = list(actors)

        # FIMP instance location on a CGRA fabric
        # They have to be explicitly add to the FIMP
        self.x = x
        self.y = y

        # FIMPCost
        self.cost = cost

        for one_actor in self.actors:
            one_actor.fimp_instance = self

    ##
    # @brief      Adds an actor to the current FIMP instance.
    #
    # This method will also dynamically assign the current FIMP instance
    # to the Actor object's `fimp` attribute.
    ##
    # @param      self       The object
    # @param      one_actor  One HSDFG Actor
    ##
    # @return     Success or not
    ##
    def add(self, actors):
        if isinstance(actors, Actor):
            actors = [actors]
        result = False
        for a in actors:
            if a not in self.actors:
                self.actors.append(a)
                a.fimp_instance = self
            result = True
        return result

    @classmethod
    def load_from_dict(cls, dict_obj):
        result = dict(dict_obj)
        actors = result.get('actors', [])
        result['actors'] = [Actor(a) for a in actors]
        fimp_cost = result.pop('cost', None)
        if fimp_cost is not None:
            result['cost'] = FIMPCost.load(fimp_cost)
        return cls(**result)


##
# @brief      Class for fimp library.
##


class FIMPLibrary(SYLVABase):

    ##
    # @brief      Constructs the object.
    ##
    # @param      self          The object
    # @param      architecture  The target architecture,
    # `ASIC`, `CGRA` or `FPGA`
    # @param      name          The name
    # @param      fimp_sets     The FIMPSet objects.
    # It is a dictionary object.
    # The keys are the function names.
    # The values are the FIMPCost object for executing that function.
    ##
    def __init__(self, architecture='ASIC',
                 name='SYLVA FIMP Library', fimp_sets={}):

        self.architecture = architecture
        self.name = name
        self.fimp_sets = fimp_sets

    ##
    # @brief      Add a FIMPCostSet of FIMPCost objcet to this FIMPLibrary. #
    #
    # @param      self  The object
    # @param      item  One FIMPCostSet or FIMPCost object
    #
    # @return     Success or not
    #
    def add(self, item):
        if isinstance(item, FIMPCost):
            if item.function_name in self.fimp_sets.keys():
                self.fimp_sets[item.function_name].add(item)
            else:
                raise ValueError(f'cannot find actor {item.function_name}')
        elif isinstance(item, FIMPCostSet):
            if item.name not in self.fimp_sets.keys():
                self.fimp_sets[item.template_actor.name] = item
            else:
                for fimp_cost in item:
                    self.add_fimp(fimp_cost)
                print(f'WARNING: Updated FIMPCostSet {item.name}.')
        return True
