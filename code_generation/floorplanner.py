# coding = utf-8

import os
import sys
import time

from sylva.ortools.constraint_solver import pywrapcp

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

from sylva.base.fimp import fimp as FIMP
from sylva.base.cgra import cgra as CGRA
from sylva.base.sdf import sdfg as SDFG
import sylva.base.sdf as sdf
from sylva.misc.util import status_log, mkdir, to_list

class floorplanner:

    '''floorplanner for CGRA'''

    def prepare_attributes(self, CGRA, actors):

        # Create the solver
        self.solver = pywrapcp.Solver('CGRA floorplanner')

        self.cgra = CGRA
        self.actors = actors
        self.actors.sort(key=lambda a: a.index)

        self.prepare_fimp_variables()

    def prepare_fimp_variables(self):

        # prepare FIMP instances
        self.fimp_instances = []
        for a in self.actors:
            if a.fimp not in self.fimp_instances:
                self.fimp_instances.append(a.fimp)
                self.cgra.add_fimp(a.fimp)

        self.fimp_instances.sort(key=lambda i: i.index)

        fimps = range(len(self.fimp_instances))

        # FIMP size values
        self.w = [self.fimp_instances[f].width for f in fimps]
        self.h = [self.fimp_instances[f].height for f in fimps]

        # FIMP location variables
        self.x = [self.solver.IntVar(0, self.cgra.width - self.w[f],
                                     'x[%i]' % f)
                  for f in fimps]
        self.y = [self.solver.IntVar(0, self.cgra.height - self.h[f],
                                     'y[%i]' % f)
                  for f in fimps]

    def add_non_overlap_constraints(self):

        x, y, w, h = self.x, self.y, self.w, self.h
        fimps = range(len(self.fimp_instances))

        for src in fimps:
            for dest in fimps:
                if dest > src:
                    # non-overlap on x-axis
                    xn0 = self.solver.IsGreaterOrEqualVar(
                        x[src], x[dest] + w[dest])
                    xn1 = self.solver.IsGreaterOrEqualVar(
                        x[dest], x[src] + w[src])

                    # non-overlap on y-axis
                    yn0 = self.solver.IsGreaterOrEqualVar(
                        y[src], y[dest] + h[dest])
                    yn1 = self.solver.IsGreaterOrEqualVar(
                        y[dest], y[src] + h[src])

                    # non-overlap on x or y axis
                    self.solver.Add(yn0 + yn1 + xn0 + xn1 > 0)

    def add_communication_cost_constraints(self):

        # icc: individual communication cost
        self.icc = []

        # ict: individual communication time
        self.ict = []

        # rrp: required routing points
        self.rrp = []

        # communication edges
        self.edges = []

        # communication distance
        self.distance = []
        self.x_distance = []
        self.y_distance = []

        # nrp = number of routing points
        nrp_max = max(self.cgra.width / self.cgra.hop_x,
                      self.cgra.height / self.cgra.hop_y)

        for a in self.actors:
            for idx in range(len(a.next)):
                one_edge = a.next[idx]
                token = one_edge.src_port.type.size * one_edge.src_port.count
                src = a.fimp.index
                dest = one_edge.dest_actor.fimp.index

                # Assume the output port is always at the top-right actor
                src_x = self.x[src] + self.w[src] - 1
                src_y = self.y[src]

                # Assume the input port is always at the top-left actor
                dest_x = self.x[dest]
                dest_y = self.y[dest]

                # compute distance between two actors
                x_distance = abs(src_x - dest_x)
                y_distance = abs(src_y - dest_y)
                self.x_distance.append(x_distance)
                self.y_distance.append(y_distance)

                # Example:
                #
                # x_equal = True means
                #
                # [src_x]========>[rp]========>[rp]========>[rp]======>[dest_x]
                #     |< hop_x >|  |< hop_x >|  |< hop_x >|  |< r_x >|
                #     |< x_distance                 >|

                # nrp = number of routing points
                nrp = self.solver.IntVar(0, nrp_max, 'nrp')

                # remainders in x and y axes
                r_x = self.solver.IntVar(0, self.cgra.hop_x - 1, 'r_x')
                r_y = self.solver.IntVar(0, self.cgra.hop_y - 1, 'r_y')

                # x_equal : maximum step is taken on the x-axis for
                # cross-window communication
                x_equal = x_distance == nrp * self.cgra.hop_x + r_x

                # y_equal : maximum step is taken on the y-axis for
                # cross-window communication
                y_equal = y_distance == nrp * self.cgra.hop_y + r_y

                # if x_distance >= y_distance, x_equal should be true
                x_larger = x_distance >= y_distance

                # if x_distance < y_distance, y_equal should be true
                y_larger = x_distance < y_distance

                self.solver.Add(x_larger * x_equal + y_larger * y_equal == 1)

                self.rrp.append(nrp)
                self.edges.append(one_edge)

                # total communication time = nrp * (TC + TW) + TW
                total_time = nrp * (self.cgra.TC + self.cgra.TW) + self.cgra.TW
                self.ict.append(total_time)

                # communication cost = distance * token size
                distance = x_distance + y_distance
                self.distance.append(distance)
                total_cost = distance * token
                self.icc.append(total_cost)

        self.communication_cost = self.solver.Sum(self.icc)

        self.num_routing_points = self.solver.Sum(self.rrp)

    def add_area_constraints(self):
        fimps = range(len(self.fimp_instances))

        max_x = self.solver.Max([self.x[f] + self.w[f] for f in fimps])
        min_x = self.solver.Min(self.x)
        total_width = self.solver.ScalProd([max_x, min_x], [1, -1])

        # bottom = (max y + height) - min y
        max_y = self.solver.Max([self.y[f] + self.h[f] for f in fimps])
        min_y = self.solver.Min(self.y)
        total_height = self.solver.ScalProd([max_y, min_y], [1, -1])

        self.area = total_width * total_height

    def add_latency_constraints(self):
        self.latency = 0

    def __init__(self, CGRA, actors,
                 max_communication_cost=-1, max_area=-1, max_latency=-1,
                 KA=0, KC=1, KT=0, time_limit=None, log=status_log(True, True)):

        self.searching = True
        self.log = log
        self.solutions = []
        self.time_limit = time_limit

        self.prepare_attributes(CGRA, actors)

        self.add_non_overlap_constraints()

        # add area constraints if specified
        self.add_area_constraints()
        if max_area > 0:
            self.solver.Add(self.area <= max_area)

        # add communication cost constraints if specified
        self.add_communication_cost_constraints()
        if max_communication_cost > 0:
            self.solver.Add(self.communication_cost <= max_communication_cost)

        # latency constraints
        if max_latency > 0:
            self.add_latency_constraints()
        else:
            self.latency = self.solver.IntVar(0, 0, 'latency')

        objective_var = self.solver.ScalProd(
            [self.area, self.communication_cost, self.latency], [KA, KC, KT])
        # objective_var = self.communication_cost
        self.optimization = self.solver.Minimize(objective_var, 1)

        # assign values for x and y
        self.db = self.solver.Phase(self.x + self.y,
                                    self.solver.CHOOSE_FIRST_UNBOUND,
                                    self.solver.ASSIGN_MIN_VALUE)

        if self.time_limit:
            self.solver.NewSearch(self.db, self.optimization,
                                  self.solver.TimeLimit(self.time_limit))
        else:
            self.solver.NewSearch(self.db, self.optimization)

    def solve(self):
        if not self.searching:
            return None

        start = time.clock()
        if self.solver.NextSolution() == True:
            msg = 'solution {}: '.format(len(self.solutions))
            msg += 'cost = {} search time = {} sec'.format(
                self.communication_cost.Var().Value(), start)
            self.log += msg
            self.log.update()
            for f in self.fimp_instances:
                f.x = self.x[f.index].Value()
                f.y = self.y[f.index].Value()
            self.solutions.append({})
            self.solutions[-
                           1]['cost'] = int(self.communication_cost.Var().Value())
            self.solutions[-1]['search_time'] = start
            self.solutions[-1]['location'] = [(int(f.x), int(f.y))
                                              for f in self.fimp_instances]
            return True
        else:
            self.solver.EndSearch()
            self.searching = False
            return None

    def plot_solutions(self, dir_name=None, name_pattern='fp_{index}_{cost}.svg',
                       show_axis=True, compact=False):

        dir_name = dir_name or ''

        if dir_name:
            mkdir(dir_name)

        for index, solution in enumerate(self.solutions):
            for i, location in enumerate(solution['location']):
                self.cgra.fimps[i].x = location[0]
                self.cgra.fimps[i].y = location[1]
            file_name = name_pattern.format(index=index, cost=solution['cost'])
            p = self.cgra.plot(show_axis, compact)
            p.savefig(os.path.join(dir_name, file_name))
            p.close()

    def plot_best_solution(self, dir_name=None, name_pattern='fp_{index}_{cost}.svg',
                           show_axis=True, compact=False):

        dir_name = dir_name or ''

        if dir_name:
            mkdir(dir_name)

        solution = self.solutions[-1]
        for i, location in enumerate(solution['location']):
            self.cgra.fimps[i].x = location[0]
            self.cgra.fimps[i].y = location[1]
        file_name = name_pattern.format(index='', cost=solution['cost'])
        p = self.cgra.plot(show_axis, compact)
        p.savefig(os.path.join(dir_name, file_name))
        p.close()

if __name__ == '__main__':

    if 'prepare system':
        width = 10
        height = 10

        c = CGRA(width, height, hop_x=3, hop_y=3, TC=2, TW=1)
        # json.dumps(c)
        w, h, num_fimps = [2, 1, 4, 4, 1, 4, 1, 1], [2, 1, 1, 3, 1, 4, 4, 1], 8
        num_actors = 10
        fimps = range(num_fimps)
        # FIMP size values
        functions = [0, 1, 1, 2, 2, 3, 3, 3, 3, 4]
        fimp_names = [0, 1, 2, 3, 3, 3, 3, 4]

        actors = [sdf.actor(name='n_%i' % f, index=i)
                  for i, f in enumerate(functions)]
        fimp_instances = [FIMP('n_%i' % f, index=i,
                               width=w[i], height=h[i], computation_phase=i)
                          for i, f in enumerate(fimp_names)]
        c.fimps = fimp_instances
        # create sdf graph

        e_0_1 = sdf.connect(actors[0], 0, 1, actors[1], 0, 1)
        e_0_2 = sdf.connect(actors[0], 1, 1, actors[2], 0, 1)
        e_0_3 = sdf.connect(actors[0], 2, 1, actors[3], 0, 1)
        e_0_4 = sdf.connect(actors[0], 3, 1, actors[4], 0, 1)

        e_1_5 = sdf.connect(actors[1], 0, 2, actors[5], 0, 2)
        e_2_6 = sdf.connect(actors[2], 0, 2, actors[6], 0, 2)
        e_3_7 = sdf.connect(actors[3], 0, 2, actors[7], 0, 2)
        e_4_8 = sdf.connect(actors[4], 0, 2, actors[8], 0, 2)

        e_5_9 = sdf.connect(actors[5], 0, 4, actors[9], 0, 4)
        e_6_9 = sdf.connect(actors[6], 0, 4, actors[9], 0, 4)
        e_7_9 = sdf.connect(actors[7], 0, 4, actors[9], 0, 4)
        e_8_9 = sdf.connect(actors[8], 0, 4, actors[9], 0, 4)

        # map actors to fimps

        actors[0].assign_to(fimp_instances[0])

        actors[1].assign_to(fimp_instances[1])
        actors[2].assign_to(fimp_instances[1])

        actors[3].assign_to(fimp_instances[2])
        actors[4].assign_to(fimp_instances[2])

        actors[5].assign_to(fimp_instances[3])
        actors[6].assign_to(fimp_instances[4])
        actors[7].assign_to(fimp_instances[5])
        actors[8].assign_to(fimp_instances[6])

        actors[9].assign_to(fimp_instances[7])
        sdf.actor.__repr__ = sdf.actor.__str__

    fp = floorplanner(c, actors, time_limit=10000)
    while fp.solve():
        pass
    fp.plot_solutions()
