# coding: utf-8
# The MIT License (MIT)
  # Copyright (c) 2014 by Shuo Li (contact@shuo.li)
  #
  # Permission is hereby granted, free of charge, to any person obtaining a
  # copy of this software and associated documentation files (the "Software"),
  # to deal in the Software without restriction, including without limitation
  # the rights to use, copy, modify, merge, publish, distribute, sublicense,
  # and/or sell copies of the Software, and to permit persons to whom the
  # Software is furnished to do so, subject to the following conditions:
  #
  # The above copyright notice and this permission notice shall be included in
  # all copies or substantial portions of the Software.
  #
  # THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
  # IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
  # FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
  # AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
  # LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
  # FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
  # DEALINGS IN THE SOFTWARE.

__author__ = 'Shuo Li <contact@shuol.li>'
__version__= '2014-05-09-11:25'

'''
  SYLVA Design Space Exploration (DSE) engine.
  DSE version 1
'''

if 'import dependencies':

  import os, sys, time, random
  from sylva.ortools.constraint_solver import pywrapcp
  from sylva.base.fimp import fimp, fimp_set, fimp_lib
  from sylva.base.cgra import cgra
  from sylva.base.sdf_to_hsdf import get_repetition_count
  from sylva.misc.util import *

# DSE version 1
# number of FIMPs are fixed already
class dse_v1 :

  '''
    Design space explorer for SYLVA, version 1
  '''

  def __init__ (self, actors, edges, fimp_library, fimps, time_limit = None,
    max_area = -1, max_energy = -1, max_latency = -1, max_sample_interval = -1,
    KA = 0,        KE = 0,          KT = 1,           KR = 0) :

    self.solver = pywrapcp.Solver('dse_v1')

    if 'take inputs' :

      self.actors = actors
      self.edges = edges
      self.fimp_library = fimp_library
      self.fimps = fimps

      if max_area > 0:
        self.max_area = max_area
      else :
        self.max_area = sys.maxint

      if max_energy > 0:
        self.max_energy = max_energy
      else :
        self.max_energy = sys.maxint

      if max_latency > 0:
        self.max_latency = max_latency
      else :
        self.max_latency = sys.maxint

      if max_sample_interval > 0:
        self.max_sample_interval = max_sample_interval
      else :
        self.max_sample_interval = sys.maxint

      self.time_limit = time_limit

    self.prepare_fimp_selection_variable_matrix()
    self.prepare_area_variable()
    self.prepare_energy_ariable()
    self.prepare_start_time_variable()
    self.prepare_end_time_variable()
    self.prepare_input_end_time_variable()
    self.prepare_output_start_time_variable()
    self.prepare_buffer_end_time_variable()
    self.prepare_extra_buffer_variable()
    self.prepare_latency_and_sample_interval_variables()

    self.add_fimp_selection_constraint()
    self.add_resource_dependency_constraints()
    self.add_data_dependency_constraints()

    self.solver.Add(self.latency < self.max_latency)
    self.solver.Add(self.area < self.max_area)
    self.solver.Add(self.energy < self.max_energy)
    self.solver.Add(self.sample_interval < self.max_sample_interval)

    if 'construct optimization objective' :
      optimization_variable = []
      optimization_weight   = []
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

    self.db = self.solver.Phase(
                self.fimp_selection_variable_flatten
                + self.start
                + self.extra_buffer,
                self.solver.CHOOSE_FIRST_UNBOUND,
                self.solver.ASSIGN_MIN_VALUE)

    if self.time_limit :
      self.solver.NewSearch(self.db, self.optimization,
        self.solver.TimeLimit(self.time_limit))
    else :
      self.solver.NewSearch(self.db, self.optimization)

  def prepare_fimp_selection_variable_matrix(self) :

    # fimp matrix to search
    # each row represents an unassigned fimp
    self.fimp_matrix = [ self.fimp_library[n.name]
                           for n in self.fimps ]

    self.fimp_type_count_set = [ one_fimp_set.fimp_count
                                 for one_fimp_set in self.fimp_matrix ]

    max_fimp_type_count = max(self.fimp_type_count_set)

    self.fimp_selection_variable = []
    for unassignend_fimp_index in xrange(len(self.fimps)) :
      f = unassignend_fimp_index
      self.fimp_selection_variable.append([])
      for current_fimp_index in xrange(self.fimp_type_count_set[f]) :
        i = current_fimp_index
        self.fimp_selection_variable[f].append(
          self.solver.IntVar(0, 1, 'FIMP selection %s %s' \
            % (str(self.fimp_matrix[f][i].name), i)))

    self.fimp_selection_variable_flatten \
    = [ var for row in self.fimp_selection_variable for var in row ]

  def add_fimp_selection_constraint(self) :

    for unassignend_fimp_index in range(len(self.fimps)) :
      f = unassignend_fimp_index
      s = sum(self.fimp_selection_variable[f]).Var()
      self.solver.Add(s == 1)

  def prepare_area_variable(self) :

    self.area_matrix = []

    for unassignend_fimp_index in range(len(self.fimps)) :
      f = unassignend_fimp_index
      self.area_matrix.append([])
      for current_fimp_index in range(self.fimp_type_count_set[f]) :
        i = current_fimp_index
        self.area_matrix[f].append(self.fimp_matrix[f][i].area)

    self.area_var = [ self.solver.ScalProd(
                        self.fimp_selection_variable[f],
                        self.area_matrix[f]).Var()
                      for f in range(len(self.fimps)) ]

    self.area = sum(self.area_var).Var()

  def prepare_energy_ariable(self) :

    self.energy_matrix = []

    for unassignend_fimp_index in range(len(self.fimps)) :
      f = unassignend_fimp_index
      self.energy_matrix.append([])
      for current_fimp_index in range(self.fimp_type_count_set[f]) :
        i = current_fimp_index
        self.energy_matrix[f].append(self.fimp_matrix[f][i].energy)

    self.energy_var = [ self.solver.ScalProd(
                          self.fimp_selection_variable[f],
                          self.energy_matrix[f]).Var()
                        for f in range(len(self.fimps)) ]

    self.energy = sum([ self.energy_var[one_actor.fimp.index]
                        for one_actor in self.actors ]).Var()

  def prepare_start_time_variable(self) :

    self.start = [ self.solver.IntVar(0, self.max_latency - 1,
                     'start time %i' % one_actor.index)
                   for one_actor in self.actors ]

  def prepare_end_time_variable(self) :

    self.end_matrix = []

    for f in range(len(self.fimps)) :
      self.end_matrix.append([])
      for current_fimp_index in range(self.fimp_type_count_set[f]) :
        i = current_fimp_index
        self.end_matrix[f].append(self.fimp_matrix[f][i].computation - 1)

    self.end_var = [ self.solver.ScalProd(
                       self.fimp_selection_variable[f],
                       self.end_matrix[f]).Var()
                     for f in range(len(self.fimps)) ]

    self.end = [ (self.start[one_actor.index]
               + self.end_var[one_actor.fimp.index]).Var()
                 for one_actor in self.actors ]

  def prepare_input_end_time_variable(self) :

    self.input_end_matrix = []

    for unassignend_fimp_index in range(len(self.fimps)) :
      f = unassignend_fimp_index
      self.input_end_matrix.append([])
      for current_fimp_index in range(self.fimp_type_count_set[f]) :
        i = current_fimp_index
        self.input_end_matrix[f].append(self.fimp_matrix[f][i].input_end)

    self.input_end_var = [ self.solver.ScalProd(
                             self.fimp_selection_variable[f],
                             self.input_end_matrix[f]).Var()
                      for f in range(len(self.fimps)) ]

    self.input_end = [ (self.start[one_actor.index]
                      + self.input_end_var[one_actor.fimp.index]).Var()
                        for one_actor in self.actors ]

  def prepare_output_start_time_variable(self) :

    self.output_start_matrix = []

    for unassignend_fimp_index in range(len(self.fimps)) :
      f = unassignend_fimp_index
      self.output_start_matrix.append([])
      for current_fimp_index in range(self.fimp_type_count_set[f]) :
        i = current_fimp_index
        self.output_start_matrix[f].append(
          self.fimp_matrix[f][i].output_start)

    self.output_start_var = [ self.solver.ScalProd(
                             self.fimp_selection_variable[f],
                             self.output_start_matrix[f]).Var()
                      for f in range(len(self.fimps)) ]

    self.output_start = [ (self.start[one_actor.index]
                         + self.output_start_var[one_actor.fimp.index]).Var()
                           for one_actor in self.actors ]

  def prepare_buffer_end_time_variable(self) :

    self.buffer_end = []
    for one_actor in self.actors :
      input_end_list = [ self.end[one_actor.index] ]
      for next_edge in one_actor.next :
        input_end_list.append(self.input_end[next_edge.dest_actor.index])

      self.buffer_end.append( self.solver.Max(input_end_list).Var() )

  def prepare_extra_buffer_variable(self) :

    self.extra_buffer = [ self.solver.IntVar(0, 1, 'eb_%i' % n.index)
                          for n in self.actors ]

  def add_resource_dependency_constraints(self) :

    # computation and output buffer
    for one_fimp in self.fimps :
      if len(one_fimp.actors) > 1 :
        for i, a in enumerate(one_fimp.actors[:-1]) :

          current = one_fimp.actors[i + 1].index
          last = a.index

          # output start time > buffer end time
          # or extra buffer is presented
          normal = ( self.output_start[current] > self.buffer_end[last] ).Var()
          extra_buffer = self.extra_buffer[last]
          self.solver.Add(normal + extra_buffer > 0)

          # start time > end time for actors in a fimp
          self.solver.Add( self.start[current] > self.end[last] )

  def add_data_dependency_constraints(self) :

    for one_actor in self.actors :
      if len(one_actor.next) > 0 :
        input_end_list = [ self.end[one_actor.index] ]
        for next_edge in one_actor.next :
          # start time > end time
          self.solver.Add( self.start[next_edge.dest_actor.index] \
                         > self.end[one_actor.index] )

          input_end_list.append(self.input_end[next_edge.dest_actor.index])

        # buffer end time = max(input end times, end time)
        max_input_end = self.solver.Max(input_end_list).Var()
        self.solver.Add( self.buffer_end[one_actor.index] == max_input_end )

  def prepare_latency_and_sample_interval_variables(self) :
    self.latency = self.solver.Max(self.end).Var()

    intervals = []
    for one_fimp in self.fimps :
      last = one_fimp.actors[len(one_fimp.actors) - 1].index
      first = one_fimp.actors[0].index
      computation_interval = ( self.end[last]
                             - self.start[first] ).Var()
      buffer_interval = ( self.buffer_end[last]
                        - self.output_start[first] ).Var()

      intervals.append(buffer_interval)
      intervals.append(computation_interval)

    self.sample_interval = self.solver.Max(intervals).Var()

def approximate_numbers(number) :

  '''
    Return all approximate numbers of an input number as a list.
    Complicity = O{n}
    Good enough for small scale problems.
  '''

  return [ i for i in xrange(1, int(number) + 1)
           if int(number) % i == 0 ]

def most_parallel_schedule(p, i, c, a) :

  '''
    Find the most parallel schedule
    when the amount of used FIMPs (c)
    for an SDF actor with index (i) is given

    ---

    p: repetition vector
    i: SDF actor index
    c: FIMP count for SDF actor i
    a: approximate numbers for p
  '''

  ratio = int(p[i] / c)
  # ratio is always integer
  # since c is always one element of p[i]

  return [ ceil_in_list(a[index], int(p[index]/ratio))
           for index in xrange(len(p)) ]

def ceil_in_list(ordered_number_list, number) :

  '''
    Ceiling a given number in a given ordered number list.
  '''

  for i, v in enumerate(ordered_number_list) :
    if number <= v :
      return v

  return ordered_number_list[-1]

def all_schedules( (sdf_actors, sdf_edges) ) :

  '''
    Find all load balanced schedules for a given SDF graph.
  '''

  p = get_repetition_count( (sdf_actors, sdf_edges) )
  a = [ approximate_numbers(n) for n in p ]

  result = []
  for s in sdf_actors :
    result = schedules(p, a, s.index, result)
  return result

def some_schedules( (sdf_actors, sdf_edges), size = None) :

  '''
    Find a subset of all load balanced schedules for a given SDF graph.
  '''

  if not size :
    return all_schedules( (sdf_actors, sdf_edges) )

  p = get_repetition_count( (sdf_actors, sdf_edges) )
  a = [ approximate_numbers(n) for n in p ]

  p_sorted = sorted([ (k, v) for k, v in enumerate(p)], key = lambda x : x[1], reverse = True)

  result = []
  if len(a[p_sorted[0][0]]) < size :
    for (k, v) in p_sorted :
      result = schedules(p, a, k, result)
      if len(result) >= size :
        return result [:size]
    return result
  return evenly_pick(schedules(p, a, p[0][0], result), size)

def schedules(p, a, i, result = []) :
  for c in a[i] :
    schedule = most_parallel_schedule(p, i, c, a)
    if schedule not in result :
      result.append(schedule)
  return result

def assign_fimps(hsdf_actors, fimp_count_list) :

  '''
    Create a relative schedule based on a given FIMP count list.
  '''

  actors = {}
  for a in hsdf_actors :
    if a.base_actor.index not in actors.keys() :
      actors[a.base_actor.index] = []
    actors[a.base_actor.index].append(a)

  fimps = [ fimp(index = i)
            for i in xrange(sum(fimp_count_list)) ]

  c = 0
  # current FIMP index

  for i in actors.keys() : # for each SDF actor

    f = 0
    # current FIMP index for one SDF actor

    for a in actors[i] :
    # for each HSDF actor
      if f == fimp_count_list[i] :
        c -= fimp_count_list[i]
        f = 0

      fimps[c].name = a.name
      fimps[c].add_actor(a)
      c += 1
      f += 1

  return fimps

