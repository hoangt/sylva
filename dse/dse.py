##
# \package sylva.dse
# Design Space Exploration
##

import sys
import time

from sylva.base.sylva_base import SYLVABase

__author__ = 'Shuo Li <contact@shuol.li>'
__version__ = '2017-05-26'
__license__ = 'https://opensource.org/licenses/MIT'


class solver_option(SYLVABase):

    def __init__(self, effort=0, solutions_per_schedule=0,
                 time_limit=100000, dse_engine=None):

        self.effort = effort
        self.solutions_per_schedule = solutions_per_schedule
        self.time_limit = time_limit
        self.dse_engine = dse_engine


class system_constraint(SYLVABase):

    def __init__(self,
                 tmax=sys.maxsize,
                 rmax=sys.maxsize,
                 amax=sys.maxsize,
                 emax=sys.maxsize):

        self.tmax = tmax
        self.rmax = rmax
        self.amax = amax
        self.emax = emax


class system_optimization_objective(SYLVABase):

    def __init__(self, ka=0, ke=1, kt=0, kr=0):

        self.ka = ka
        self.ke = ke
        self.kt = kt
        self.kr = kr


class system_model(SYLVABase):

    def __init__(self, name, sdfg, constraint, optimization_objective):

        self.name = name
        self.sdfg = sdfg
        self.constraint = constraint
        self.optimization_objective = optimization_objective


class design_specification(SYLVABase):

    def __init__(self, system, fimp_lib, cgra, target_architecture=['FPGA']):

        self.target_architecture = target_architecture
        self.cgra = cgra
        self.system = system
        self.fimp_lib = fimp_lib


def Solution(SYLVABase):

    def __init__(self, search_time, branches,
                 fimps, area, latency, energy, sample_interval):

        self.search_time = search_time
        self.branches = branches
        self.fimps = list(fimps)
        self.area = area
        self.latency = latency
        self.energy = energy
        self.sample_interval = sample_interval


def one_search(dse):

    start_time = time.time()

    if dse.solver.NextSolution():

        end_time = time.time()
        solution = Solution(search_time=((end_time - start_time) / 1000),
                            branches=dse.solver.Branches(),
                            fimps=len(dse.fimps),
                            area=dse.area.Value(),
                            latency=dse.latency.Value(),
                            energy=dse.energy.Value(),
                            sample_interval=dse.sample_interval.Value())

        solution.start = [int(t.Value()) for t in dse.start]
        solution.end = [int(t.Value()) for t in dse.end]
        solution.input_end = [int(t.Value()) for t in dse.input_end]
        solution.output_start = [int(t.Value()) for t in dse.output_start]
        solution.buffer_end = [int(t.Value()) for t in dse.buffer_end]
        solution.extra_buffer = [int(t.Value()) for t in dse.extra_buffer]

        solution.fimp_types = [-1 for f in dse.fimps]
        for f in dse.fimps:
            fimp_type = 0
            for var in dse.fimp_selection_variable[f.index]:
                if int(var.Value()) == 1:
                    solution.fimp_types[f.index] = fimp_type
                fimp_type = fimp_type + 1

        return Solution

    else:

        end_time = time.time()
        print('No solution found after %s branches\n' % dse.solver.Branches())
        print('  search time    : %f\n' % ((end_time - start_time) / 1000))

    return None


def search_all(design, option):

    results = []

    # prepare constraints
    tmax = design.system.constraint.tmax
    rmax = design.system.constraint.rmax
    amax = design.system.constraint.amax
    emax = design.system.constraint.emax

    # prepare optimization objectives
    KT = design.system.optimization_objective.kt
    KR = design.system.optimization_objective.kr
    KA = design.system.optimization_objective.ka
    KE = design.system.optimization_objective.ke

    # system
    sdfg = design.system

    # prepare FIMP library
    fimp_lib = design.fimp_lib

    # prepare solver options
    time_limit = option.time_limit
    solutions_per_schedule = option.solutions_per_schedule
    effort = option.effort
    dse_engine = option.dse_engine

    # create HSDF graph and schedule it

    hsdfg = sdfg.get_hsdfg()
    all_sch = all_schedules((sdf_actors, sdf_edges))
        search_schedules = int(float(effort) * len(all_sch) / 100)
        schedules = some_schedules((sdf_actors, sdf_edges), search_schedules)
        end_time = time.time()
        log += 'Done. ' + time_cost(start_time, end_time) + '\n'
        log += '%s schedules.\n' % len(schedules)
        for s in schedules:
            log += '%s \n' % s
        log.update()

    if 'search for each schedule':

        search_index = 0

        for schedule_index, one_schedule in enumerate(schedules):

            result = []

            log += 'Schedule %s: \n' % schedule_index
            critical_log.status = log.status
            log.update()

            fimps = assign_fimps(actors, one_schedule)

            log += 'Used FIMP instance space holders are generated. \n'

            for f in fimps:
                log += '\n  %s\n  Actors: %s\n' % (f, f.actors)
            log.update()

            log += 'Preparing CSOP'
            log.update()
            start_time = time.time()
            dse = dse_engine(actors, edges, fimp_lib, fimps,
                             time_limit=time_limit,
                             max_area=amax, max_energy=emax,
                             max_latency=tmax, max_sample_interval=rmax,
                             KA=KA, KE=KE, KT=KT, KR=KR)

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

            if not solutions_per_schedule:
                while keep_searching == True:
                    result.append(r)
                    search_index += 1
                    log += 'Search %s ... \n' % search_index
                    critical_log.status = log.status
                    log.update()

                    start_time = time.time()
                    keep_searching, r = one_search(dse, log)
                    end_time = time.time()

                    if not keep_searching:
                        log += 'Search failed, time limit %s seconds. \n' % (time_limit / 1000)
                        critical_log.status = log.status
                    else:
                        log += 'Done. ' + time_cost(start_time, end_time) + '\n'
                        critical_log.status = log.status

                    log.update()
            else:
                while solutions_per_schedule > 0 and keep_searching == True:

                    result.append(r)
                    search_index += 1
                    log += 'Search %s ... \n' % search_index
                    critical_log.status = log.status
                    log.update()

                    start_time = time.time()
                    keep_searching, r = one_search(dse)
                    end_time = time.time()

                    if not keep_searching:
                        log += 'Search failed, time limit %s seconds. \n' % (time_limit / 1000)
                        critical_log.status = log.status
                    else:
                        log += 'Done. ' + time_cost(start_time, end_time) + '\n'
                        critical_log.status = log.status

                    log.update()
                    solutions_per_schedule -= 1

            dse.solver.EndSearch()

            if len(result) > 0:

                for r in result:

                    if r != {}:

                        fimp_instances = []

                        for f in dse.fimps:
                            used_fimp = fimp_lib[f.name][r['fimp_types'][f.index]].clone()
                            used_fimp.index = f.index
                            used_fimp.actors = []
                            fimp_instances.append(used_fimp)

                            for a in f.actors:
                                a.assign_to(used_fimp)
                                a.fimp_index = used_fimp.index

                        for a in dse.actors:
                            i = a.index
                            a.add_schedule(
                                start=r['start'][i],
                                buffer_end=r['buffer_end'][i])
                            a.fimp.extra_buffer = r['extra_buffer'][i]

                        schedule_keys = ['start', 'input_end', 'output_start',
                                         'end', 'buffer_end', 'fimp_index']

                        r['actors'] = [a.serialize(schedule_keys, include_base_actor=True) for a in actors]
                        r['edges'] = [e.serialize() for e in edges]
                        r['fimp_instances'] = [f.serialize() for f in fimp_instances]

                        for a in actors:
                            log += 'Actor: %s\nFIMP: %s\n' % (a, a.fimp)
                            log.update()
                            log += 'Schedule:\n' + a.schedule.__str__()
                            log.update()

                    else:
                        log += 'No schedule for the following FIMP assignment:\n%s'\
                            % one_schedule
                        critical_log.status = log.status
                        log.update()

            results.append(result)

    critical_log.update()

    return results, sdfg(actors, edges)

def get_result_csv(search_result, file_name='',
                   report_items=['search time', 'fimps', 'area', 'energy',
                                 'latency', 'sample interval']):

    msg = 'index'
    for m in report_items:
        msg += ',' + m
    msg += '\n'

    index = 0
    for one_schedule_result in search_result:
        for one_solution in one_schedule_result:
            if one_solution != {}:
                msg += str(index)
                index += 1
                for key in report_items:
                    msg += ',' + str(one_solution[key])
                msg += '\n'

    if file_name == '':

        return msg

    else:

        dataf = open(file_name, 'w+')
        dataf.write(msg)
        dataf.close()
