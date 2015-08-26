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
__version__= '2014-09-23-10:41'

'''
  Design Space Exploration.
'''

# import header files
if 'import dependencies' :

  import os, sys, random, time
  from time import localtime, strftime

  from sylva.ortools.constraint_solver import pywrapcp

  import sylva.base.sdf as sdf
  from sylva.base.sdf import sdfg
  import sylva.base.fimp as fimp
  import sylva.base.sdf_schedule as sdf_schedule

  from sylva.base.cgra import cgra
  from sylva.base.sdf_to_hsdf import sdf_to_hsdf
  from sylva.misc.util import status_log
  from sylva.misc.plot import schedule_plot, fimp_execution_model_plot
  from sylva.dse.dse_engine_v1 import dse_v1, all_schedules, some_schedules, assign_fimps

def time_cost(start_time, end_time) :
  return 'Time cost: %f seconds.' % ((end_time - start_time)/1000)

class solver_option :

  def __init__(self,
    effort = 0,
    solutions_per_schedule = 0,
    time_limit = 100000,
    dse_engine = dse_v1) :

    self.effort = effort
    self.solutions_per_schedule = solutions_per_schedule
    self.time_limit = time_limit
    self.dse_engine = dse_engine

class system_constraint :

  def __init__(self,
    tmax = sys.maxint,
    rmax = sys.maxint,
    amax = sys.maxint,
    emax = sys.maxint) :

    self.tmax = sys.maxint if tmax == 0 else tmax
    self.rmax = sys.maxint if rmax == 0 else rmax
    self.amax = sys.maxint if amax == 0 else amax
    self.emax = sys.maxint if emax == 0 else emax

sc = system_constraint

class system_optimization_objective :

  def __init__(self,
    ka = 0,
    ke = 1,
    kt = 0,
    kr = 0) :

    self.ka = ka
    self.ke = ke
    self.kt = kt
    self.kr = kr

soo = system_optimization_objective

class system_model :

  def __init__(self, name = 'one system model',
    actors = [], edges = [],
    constraint = sc(),
    optimization_objective = soo()) :

    self.name = name
    self.actors = actors
    self.edges = edges
    self.constraint = constraint
    self.optimization_objective = optimization_objective

  def serialize(self) :
    result = {}
    result['name'] = self.name
    temp = sdf.serialize_sdf_graph(self.actors, self.edges)
    result['actors'] = temp['actors']
    result['edges'] = temp['edges']
    result['constraint'] = self.constraint.__dict__
    result['optimization_objective'] = self.optimization_objective.__dict__
    return result

class design_specification :

  def __init__(self,
    target_architecture = ['FPGA'],
    system = system_model([], [], sc(), soo()),
    fimp_lib = fimp.fimp_lib('FPGA', 'FPGA FIMP Library'),
    cgra = cgra(width = 7, height = 2, hop_x = 3, hop_y = 3, TC = 2, TW = 1)) :

    self.target_architecture = target_architecture
    self.cgra = cgra
    self.system = system
    self.fimp_lib = fimp_lib

  def serialize(self) :
    return {
      'target_architecture' : self.target_architecture,
      'cgra' : self.cgra.__dict__,
      'fimp_lib' : self.fimp_lib.serialize(),
      'system' : self.system.serialize() }

def one_search(dse, log) :

  '''
  Perform one search.

  Returns

  1. if a solution is found (True or False)
  2. the solution
  3. the search log
  '''

  result = {}
  performance = {}

  start_time = time.time()

  if dse.solver.NextSolution() :

    end_time = time.time()

    log += 'Found one solution after %s branches\n' \
         % dse.solver.Branches()
    log += '  search time    : %f\n' % ((end_time -  start_time)/1000)
    log += '  FIMPs          : %s\n' % len(dse.fimps)
    log += '  area           : %s\n' % dse.area.Value()
    log += '  latency        : %s\n' % dse.latency.Value()
    log += '  energy         : %s\n' % dse.energy.Value()
    log += '  sample interval: %s' % dse.sample_interval.Value()
    log.update()

    result['start']        = [ int(t.Value()) for t in dse.start ]
    result['end']          = [ int(t.Value()) for t in dse.end ]
    result['input_end']    = [ int(t.Value()) for t in dse.input_end ]
    result['output_start'] = [ int(t.Value()) for t in dse.output_start ]
    result['buffer_end']   = [ int(t.Value()) for t in dse.buffer_end ]
    result['extra_buffer'] = [ int(t.Value()) for t in dse.extra_buffer ]

    result['fimp_types']   = [ -1 for f in dse.fimps]

    result['search time']     = (end_time -  start_time)/1000
    result['fimps']           = len(dse.fimps)
    result['area']            = dse.area.Value()
    result['latency']         = dse.latency.Value()
    result['energy']          = dse.energy.Value()
    result['sample interval'] = dse.sample_interval.Value()

    for f in dse.fimps :
      fimp_type = 0
      for var in dse.fimp_selection_variable[f.index] :
        if int(var.Value()) == 1 :
          result['fimp_types'][f.index] = fimp_type
        fimp_type = fimp_type + 1

    return True, result#, log

  else :

    end_time = time.time()
    log += 'No solution found after %s branches\n' \
         % dse.solver.Branches()
    log += '  search time    : %f\n' % ((end_time -  start_time)/1000)
    log.update()

  return False, result#, log

def search_all(design, option, log = status_log(),
  critical_log = status_log()):

  results = []

  if 'prepare constraints and optimization objectives':

    if 'prepare constraints' :

      tmax = design.system.constraint.tmax
      rmax = design.system.constraint.rmax
      amax = design.system.constraint.amax
      emax = design.system.constraint.emax

      log += 'Constraints: \n'
      log += 'Maximum latency (T_{max}) is %s\n' % tmax
      log += 'Maximum sample interval (R_{max}) is %s\n' % rmax
      log += 'Maximum area (A_{max}) is %s\n' % amax
      log += 'Maximum energy consumption (E_{max}) is %s\n' % emax
      log.update()

    if 'prepare optimization objectives' :

      KT = design.system.optimization_objective.kt
      KR = design.system.optimization_objective.kr
      KA = design.system.optimization_objective.ka
      KE = design.system.optimization_objective.ke

      log += 'Optimization objectives: \n'
      log += 'KA = %s\n' % KA
      log += 'KE = %s\n' % KE
      log += 'KT = %s\n' % KT
      log += 'KR = %s\n' % KR
      log.update()

  if 'prepare system SDF graph' :

    sdf_actors = design.system.actors
    sdf_edges = design.system.edges

  # prepare CGRA
  cgra = design.cgra

  # prepare FIMP library
  fimp_lib = design.fimp_lib

  if 'prepare solver options' :

    time_limit = option.time_limit
    solutions_per_schedule = option.solutions_per_schedule
    effort = option.effort
    dse_engine = option.dse_engine

  if 'create HSDF graph and schedule it':

    log += 'Converting system SDF graph to HSDF graph ... \n'
    start_time = time.time()
    (actors, edges) = sdf_to_hsdf( (sdf_actors, sdf_edges) )
    end_time = time.time()
    log += 'Done. ' + time_cost(start_time, end_time) + '\n'
    log += '%s actors, %s edges.' % (len(actors), len(edges))
    log.update()
    log += 'Generating load balanced SDF schedule ...\n'
    start_time = time.time()
    all_sch = all_schedules( (sdf_actors, sdf_edges) )
    search_schedules = int(float(effort)*len(all_sch)/100)
    schedules = some_schedules( (sdf_actors, sdf_edges), search_schedules)
    end_time = time.time()
    log += 'Done. ' + time_cost(start_time, end_time) + '\n'
    log += '%s schedules.\n' % len(schedules)
    for s in schedules :
      log += '%s \n' % s
    log.update()

  if 'search for each schedule' :

    search_index = 0

    for schedule_index, one_schedule in enumerate(schedules) :

      result = []

      log += 'Schedule %s: \n' % schedule_index
      critical_log.status = log.status
      log.update()

      fimps = assign_fimps(actors, one_schedule)

      log += 'Used FIMP instance space holders are generated. \n'

      for f in fimps :
        log += '\n  %s\n  Actors: %s\n' % (f, f.actors)
      log.update()

      log += 'Preparing CSOP'
      log.update()
      start_time = time.time()
      dse = dse_engine(actors, edges, fimp_lib, fimps,
        time_limit = time_limit,
        max_area = amax, max_energy = emax,
        max_latency = tmax, max_sample_interval = rmax,
        KA = KA, KE = KE, KT = KT, KR = KR)

      end_time = time.time()
      log += 'Done. ' + time_cost(start_time, end_time)
      log.update()

      log += 'Search %s ... \n' % search_index
      critical_log.status = log.status
      log.update()
      start_time = time.time()
      keep_searching, r = one_search(dse, log)
      end_time = time.time()
      log += ('Search %s is done. ' % search_index) \
           + time_cost(start_time, end_time) + '\n'
      critical_log.status = log.status
      log.update()

      if not solutions_per_schedule :
        while keep_searching == True :
          result.append(r)
          search_index += 1
          log += 'Search %s ... \n' % search_index
          critical_log.status = log.status
          log.update()

          start_time = time.time()
          keep_searching, r = one_search(dse, log)
          end_time = time.time()

          if not keep_searching:
            log += 'Search failed, time limit %s seconds. \n' % (time_limit/1000)
            critical_log.status = log.status
          else :
            log += 'Done. ' + time_cost(start_time, end_time) + '\n'
            critical_log.status = log.status

          log.update()
      else :
        while solutions_per_schedule > 0 and keep_searching == True :

          result.append(r)
          search_index += 1
          log += 'Search %s ... \n' % search_index
          critical_log.status = log.status
          log.update()

          start_time = time.time()
          keep_searching, r = one_search(dse)
          end_time = time.time()

          if not keep_searching:
            log += 'Search failed, time limit %s seconds. \n' % (time_limit/1000)
            critical_log.status = log.status
          else :
            log += 'Done. ' + time_cost(start_time, end_time) + '\n'
            critical_log.status = log.status

          log.update()
          solutions_per_schedule -= 1

      dse.solver.EndSearch()

      if len(result) > 0 :

        for r in result :

          if r != {} :

            fimp_instances = []

            for f in dse.fimps :
              used_fimp = fimp_lib[ f.name ][ r['fimp_types'][f.index] ].clone()
              used_fimp.index = f.index
              used_fimp.actors = []
              fimp_instances.append(used_fimp)

              for a in f.actors :
                a.assign_to(used_fimp)
                a.fimp_index = used_fimp.index

            for a in dse.actors:
              i = a.index
              a.add_schedule(
                start = r['start'][i],
                buffer_end = r['buffer_end'][i])
              a.fimp.extra_buffer = r['extra_buffer'][i]

            schedule_keys = [ 'start', 'input_end', 'output_start',
                              'end', 'buffer_end', 'fimp_index']

            r['actors'] = [ a.serialize(schedule_keys, include_base_actor = True) for a in actors ]
            r['edges'] = [ e.serialize() for e in edges ]
            r['fimp_instances'] = [ f.serialize() for f in fimp_instances ]

            for a in actors :
              log += 'Actor: %s\nFIMP: %s\n' % (a, a.fimp)
              log.update()
              log += 'Schedule:\n' + a.schedule.__str__()
              log.update()

          else :
            log += 'No schedule for the following FIMP assignment:\n%s'\
                 % one_schedule
            critical_log.status = log.status
            log.update()

      results.append(result)

  critical_log.update()

  return results, sdfg(actors, edges)

def get_result_csv(search_result, file_name = '',
  report_items = [ 'search time', 'fimps', 'area', 'energy',
                   'latency', 'sample interval' ]) :

  msg = 'index'
  for m in report_items :
    msg += ',' + m
  msg += '\n'

  index = 0
  for one_schedule_result in search_result :
    for one_solution in one_schedule_result :
      if one_solution != {} :
        msg += str(index)
        index += 1
        for key in report_items :
          msg += ',' + str(one_solution[key])
        msg += '\n'

  if file_name == '' :

    return msg

  else :

    dataf = open(file_name, 'w+')
    dataf.write(msg)
    dataf.close()
