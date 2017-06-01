##
# \package sylva.dse.dse_engine
#
# Design Space Exploration (DSE) Engine
##


import sys

from ortools.constraint_solver import pywrapcp

from sylva.base.sylva_base import SYLVABase
from sylva.base.fimp import FIMPLibrary, FIMPSet, FIMPCost, FIMPInstance
from sylva.base.cgra import CGRA
from sylva.base.sdf import SDFG, HSDFG


__author__ = 'Shuo Li <contact@shuol.li>'
__version__ = '2017-05-19'
__license__ = 'https://opensource.org/licenses/MIT'


##
# @brief      Class for DSEEngine
##
class DSEEngine(SYLVABase):

    ##
    # \var solver
    # The constraint programming solver in Ortools.
    # Check <https://developers.google.com/optimization/> for more information.
    # last checked 2017-05-19.
    ##
    # \var hsdfg
    # The HSDFG object.
    # It has all the HSDFG actors and edges to be used for CSOP generation.
    ##
    # \var fimp_library
    # The FIMPLibrary.
    # It has all the FIMPCost objects to be used for CSOP generation.
    ##
    # \var fimp_instances
    # The list of FIMPInstance objects.
    # It has all the FIMPInstance objects to be used for CSOP generation.

    ##
    # @brief      Constructs the object.
    ##
    # @param      self                 The object
    # @param      hsdfg                \copydoc DSEEngine::hsdfg
    # @param      fimp_library         \copydoc DSEEngine::fimp_library
    # @param      fimp_instances       \copydoc DSEEngine::fimp_instances
    # @param      time_limit           The time limit for solver
    # @param      max_area             The maximum area
    # @param      max_energy           The maximum energy
    # @param      max_latency          The maximum latency
    # @param      max_sample_interval  The maximum sample interval
    # @param      KA                   Weight factor for area
    # @param      KE                   Weight factor for energy
    # @param      KT                   Weight factor for latency
    # @param      KR                   Weight factor for sample interval
    ##
    def __init__(self, hsdfg, fimp_library, fimp_instances,
                 time_limit=0,
                 max_area=0, max_energy=0, max_latency=0,
                 max_sample_interval=0,
                 KA=0, KE=0, KT=1, KR=0):

        self.solver = pywrapcp.Solver('SYLVA DSE')

        # take inputs
        self.hsdfg = hsdfg
        self.fimp_library = fimp_library
        self.fimp_instances = fimp_instances

        if max_area <= 0:
            max_area = sys.maxsize

        if max_energy <= 0:
            max_energy = sys.maxsize

        if max_latency <= 0:
            max_latency = sys.maxsize

        if max_sample_interval <= 0:
            max_sample_interval = sys.maxsize

        self.max_area = max_area
        self.max_energy = sys.maxsize
        self.max_latency = sys.maxsize
        self.max_sample_interval = sys.maxsize

        self.time_limit = time_limit

        # prepare variables
        self.prepare_fimp_selection_variable()
        self.prepare_area_variable()
        self.prepare_energy_ariable()
        self.prepare_start_time_variable()
        self.prepare_end_time_variable()
        self.prepare_input_end_time_variable()
        self.prepare_output_start_time_variable()
        self.prepare_buffer_end_time_variable()
        self.prepare_extra_buffer_variable()
        self.prepare_latency_and_sample_interval_variables()

        # create constraints
        self.add_fimp_selection_constraint()
        self.add_resource_dependency_constraints()
        self.add_data_dependency_constraints()

        self.solver.Add(self.latency < self.max_latency)
        self.solver.Add(self.area < self.max_area)
        self.solver.Add(self.energy < self.max_energy)
        self.solver.Add(self.sample_interval < self.max_sample_interval)

        # prepare optimization objective

        search_variables = self.fimp_selection_variable_flatten
        search_variables += self.start
        search_variables += self.extra_buffer

        self.db = self.solver.Phase(search_variables,
                                    self.solver.CHOOSE_FIRST_UNBOUND,
                                    self.solver.ASSIGN_MIN_VALUE)

        if self.time_limit:
            self.solver.NewSearch(self.db, self.optimization,
                                  self.solver.TimeLimit(self.time_limit))
        else:
            self.solver.NewSearch(self.db, self.optimization)

    ##
    # @brief      Prepare optimization objective
    ##
    # @param      self  The object
    # @param      KA    Weight factor for area
    # @param      KE    Weight factor for energy
    # @param      KT    Weight factor for latency
    # @param      KR    Weight factor for sample interval
    ##
    def prepare_optimization_objective(self, KA, KE, KT, KR):
        optimization_variable = []
        optimization_weight = []
        if KA > 0:
            optimization_variable.append(self.area)
            optimization_weight.append(KA)
        if KE > 0:
            optimization_variable.append(self.energy)
            optimization_weight.append(KE)
        if KT > 0:
            optimization_variable.append(self.latency)
            optimization_weight.append(KT)
        if KR > 0:
            optimization_variable.append(self.sample_interval)
            optimization_weight.append(KR)

        optimization_obj = self.solver.ScalProd(
            optimization_variable,
            optimization_weight)

        self.optimization = self.solver.Minimize(optimization_obj, 1)

    ##
    # @brief      Preoare FIMP selection variable
    ##
    # @param      self  The object
    ##
    # @return     { description_of_the_return_value }
    ##
    def prepare_fimp_selection_variable(self):

        # FIMP assignment search varable
        # It is a matrix.
        # Each row represents a FIMPInstance with unassigned FIMP type
        self.fimp_matrix = [self.fimp_library[n.function_name]
                            for n in self.fimp_instances]

        self.fimp_type_count_set = [one_fimp_set.fimp_count
                                    for one_fimp_set in self.fimp_matrix]

        max_fimp_type_count = max(self.fimp_type_count_set)

        self.fimp_selection_variable = []
        for unassignend_fimp_index in range(len(self.fimps)):
            f = unassignend_fimp_index
            self.fimp_selection_variable.append([])
            for current_fimp_index in range(self.fimp_type_count_set[f]):
                i = current_fimp_index
                self.fimp_selection_variable[f].append(
                    self.solver.IntVar(0, 1, 'FIMP selection %s %s'
                                       % (str(self.fimp_matrix[f][i].name), i)))

        self.fimp_selection_variable_flatten \
            = [var for row in self.fimp_selection_variable for var in row]

    def add_fimp_selection_constraint(self):

        for unassignend_fimp_index in range(len(self.fimps)):
            f = unassignend_fimp_index
            s = sum(self.fimp_selection_variable[f]).Var()
            self.solver.Add(s == 1)

    def prepare_area_variable(self):

        self.area_matrix = []

        for unassignend_fimp_index in range(len(self.fimps)):
            f = unassignend_fimp_index
            self.area_matrix.append([])
            for current_fimp_index in range(self.fimp_type_count_set[f]):
                i = current_fimp_index
                self.area_matrix[f].append(self.fimp_matrix[f][i].area)

        self.area_var = [self.solver.ScalProd(
            self.fimp_selection_variable[f],
            self.area_matrix[f]).Var()
            for f in range(len(self.fimps))]

        self.area = sum(self.area_var).Var()

    def prepare_energy_ariable(self):

        self.energy_matrix = []

        for unassignend_fimp_index in range(len(self.fimps)):
            f = unassignend_fimp_index
            self.energy_matrix.append([])
            for current_fimp_index in range(self.fimp_type_count_set[f]):
                i = current_fimp_index
                self.energy_matrix[f].append(self.fimp_matrix[f][i].energy)

        self.energy_var = [self.solver.ScalProd(
            self.fimp_selection_variable[f],
            self.energy_matrix[f]).Var()
            for f in range(len(self.fimps))]

        self.energy = sum([self.energy_var[one_actor.fimp.index]
                           for one_actor in self.actors]).Var()

    def prepare_start_time_variable(self):

        self.start = [self.solver.IntVar(0, self.max_latency - 1,
                                         'start time %i' % one_actor.index)
                      for one_actor in self.actors]

    def prepare_end_time_variable(self):

        self.end_matrix = []

        for f in range(len(self.fimps)):
            self.end_matrix.append([])
            for current_fimp_index in range(self.fimp_type_count_set[f]):
                i = current_fimp_index
                self.end_matrix[f].append(self.fimp_matrix[f][i].computation - 1)

        self.end_var = [self.solver.ScalProd(
            self.fimp_selection_variable[f],
            self.end_matrix[f]).Var()
            for f in range(len(self.fimps))]

        self.end = [(self.start[one_actor.index]
                     + self.end_var[one_actor.fimp.index]).Var()
                    for one_actor in self.actors]

    def prepare_input_end_time_variable(self):

        self.input_end_matrix = []

        for unassignend_fimp_index in range(len(self.fimps)):
            f = unassignend_fimp_index
            self.input_end_matrix.append([])
            for current_fimp_index in range(self.fimp_type_count_set[f]):
                i = current_fimp_index
                self.input_end_matrix[f].append(self.fimp_matrix[f][i].input_end)

        self.input_end_var = [self.solver.ScalProd(
            self.fimp_selection_variable[f],
            self.input_end_matrix[f]).Var()
            for f in range(len(self.fimps))]

        self.input_end = [(self.start[one_actor.index]
                           + self.input_end_var[one_actor.fimp.index]).Var()
                          for one_actor in self.actors]

    def prepare_output_start_time_variable(self):

        self.output_start_matrix = []

        for unassignend_fimp_index in range(len(self.fimps)):
            f = unassignend_fimp_index
            self.output_start_matrix.append([])
            for current_fimp_index in range(self.fimp_type_count_set[f]):
                i = current_fimp_index
                self.output_start_matrix[f].append(
                    self.fimp_matrix[f][i].output_start)

        self.output_start_var = [self.solver.ScalProd(
            self.fimp_selection_variable[f],
            self.output_start_matrix[f]).Var()
            for f in range(len(self.fimps))]

        self.output_start = [(self.start[one_actor.index]
                              + self.output_start_var[one_actor.fimp.index]).Var()
                             for one_actor in self.actors]

    def prepare_buffer_end_time_variable(self):

        self.buffer_end = []
        for one_actor in self.actors:
            input_end_list = [self.end[one_actor.index]]
            for next_edge in one_actor.next:
                input_end_list.append(self.input_end[next_edge.dest_actor.index])

            self.buffer_end.append(self.solver.Max(input_end_list).Var())

    def prepare_extra_buffer_variable(self):

        self.extra_buffer = [self.solver.IntVar(0, 1, 'eb_%i' % n.index)
                             for n in self.actors]

    def add_resource_dependency_constraints(self):

        # computation and output buffer
        for one_fimp in self.fimps:
            if len(one_fimp.actors) > 1:
                for i, a in enumerate(one_fimp.actors[:-1]):

                    current = one_fimp.actors[i + 1].index
                    last = a.index

                    # output start time > buffer end time
                    # or extra buffer is presented
                    normal = (self.output_start[current] > self.buffer_end[last]).Var()
                    extra_buffer = self.extra_buffer[last]
                    self.solver.Add(normal + extra_buffer > 0)

                    # start time > end time for actors in a fimp
                    self.solver.Add(self.start[current] > self.end[last])

    def add_data_dependency_constraints(self):

        for one_actor in self.actors:
            if len(one_actor.next) > 0:
                input_end_list = [self.end[one_actor.index]]
                for next_edge in one_actor.next:
                    # start time > end time
                    self.solver.Add(self.start[next_edge.dest_actor.index]
                                    > self.end[one_actor.index])

                    input_end_list.append(self.input_end[next_edge.dest_actor.index])

                # buffer end time = max(input end times, end time)
                max_input_end = self.solver.Max(input_end_list).Var()
                self.solver.Add(self.buffer_end[one_actor.index] == max_input_end)

    def prepare_latency_and_sample_interval_variables(self):
        self.latency = self.solver.Max(self.end).Var()

        intervals = []
        for one_fimp in self.fimps:
            last = one_fimp.actors[-1].index
            first = one_fimp.actors[0].index
            computation_interval = (self.end[last] - self.start[first]).Var()
            buffer_interval = (self.buffer_end[last] - self.output_start[first]).Var()

            intervals.append(buffer_interval)
            intervals.append(computation_interval)

        self.sample_interval = self.solver.Max(intervals).Var()


def all_schedules(self):

    # Calculate the factor of n
    # e.g. factor(4) = [1, 2, 4], factor(10) = [1, 2, 5]
    def _factor(n):
        return [i for i in range(1, n + 1) if n % i == 0]

    ##
    # @brief      Ceil a list
    ##
    # Example:
    # ceil([1, 2, 3, 4], 4) => 4
    # ceil([1, 2, 3, 4], 3) => 3
    # ceil([1, 2, 3, 4], 2) => 3
    # ceil([1, 2, 3, 5], 2) => 4
    ##
    # @param      list_obj  The list object
    # @param      number    The number
    ##
    # @return     { description_of_the_return_value }
    ##
    def _ceil(list_obj, number):
        for v in list_obj:
            if number <= v:
                return v
        return list_obj[-1]

    repetition_vector = self.repetition_vector
    possible_fimp_counts = [_factor(n) for n in repetition_vector]

    result = []

    for actor in self.actor:
        for fimp_count in possible_fimp_counts[actor.index]:
            # Maximum numbef of FIMPInstance objects
            # over
            # current deployed FIMPInstance objects
            #
            # This ratio should be kept for all the SDFG Actors otherwise
            # some of the FIMPInstance objects will be wasted.
            ratio = int(repetition_vector[actor.index] / fimp_count)
            schedule = []

            for a in self.actors:
                fimp_count = int(repetition_vector[a.index] / ratio)
                fimp_count = _ceil(possible_fimp_counts[a.index], fimp_count)
                schedule.append(fimp_count)

            if schedule not in result:
                result.append(schedule)

        return result

    return result

# def some_schedules((sdf_actors, sdf_edges), size=None):
#     '''
#       Find a subset of all load balanced schedules for a given SDF graph.
#     '''

#     if not size:
#         return all_schedules((sdf_actors, sdf_edges))

#     p = get_repetition_count((sdf_actors, sdf_edges))
#     a = [approximate_numbers(n) for n in p]

#     p_sorted = sorted([(k, v) for k, v in enumerate(p)], key=lambda x: x[1], reverse=True)

#     result = []
#     if len(a[p_sorted[0][0]]) < size:
#         for (k, v) in p_sorted:
#             result = schedules(p, a, k, result)
#             if len(result) >= size:
#                 return result[:size]
#         return result
#     return evenly_pick(schedules(p, a, p[0][0], result), size)


# def assign_fimps(hsdf_actors, fimp_count_list):
#     '''
#       Create a relative schedule based on a given FIMP count list.
#     '''

#     actors = {}
#     for a in hsdf_actors:
#         if a.base_actor.index not in actors.keys():
#             actors[a.base_actor.index] = []
#         actors[a.base_actor.index].append(a)

#     fimps = [fimp(index=i)
#              for i in xrange(sum(fimp_count_list))]

#     c = 0
#     # current FIMP index

#     for i in actors.keys():  # for each SDF actor

#         f = 0
#         # current FIMP index for one SDF actor

#         for a in actors[i]:
#             # for each HSDF actor
#             if f == fimp_count_list[i]:
#                 c -= fimp_count_list[i]
#                 f = 0

#             fimps[c].name = a.name
#             fimps[c].add_actor(a)
#             c += 1
#             f += 1

#     return fimps
