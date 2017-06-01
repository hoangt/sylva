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
__version__ = '2014-09-23-10:43'

''' Global Interconnect and Control Synthesis '''

if 'import dependencies':

    import os
    import sys
    import random
    import time
    import functools
    from time import localtime, strftime

    from sylva.ortools.constraint_solver import pywrapcp
    from sylva.base import sdf

IDLE = 0
COMPUTATION = 1
INPUT = 2
OUTPUT = 4
IO = INPUT + OUTPUT

if 'define control classes':

    class edge:

        '''
          Basic Moore FSM edge class
        '''

        def __init__(self, source=None, destination=None,
                     cycle=0):

            self.source = source
            self.destination = destination
            self.cycle = cycle
            self.__repr__ = self.__str__

        def __str__(self):
            return 'edge from %s to %s on %s' \
                % (self.source, self.destination, self.cycle)

        def serialize(self):
            return {'source': self.source.index,
                    'destination': self.destination.index,
                    'cycle': self.cycle}

        @staticmethod
        def deserialize(json_dict, states=[]):
            return edge(source=states[int(json_dict['source'])],
                        destination=states[int(json_dict['destination'])],
                        cycle=int(json_dict['cycle']))

    class state:

        '''
          Basic Moore FSM state class
        '''

        def __init__(self, index=0, output=None):

            self.index = index
            self.output = output
            self.__repr__ = self.__str__

        def __str__(self):
            return 'state: %d output: %s' % (self.index, self.output)

        def serialize(self):
            result = {'index': self.index, 'output': self.output}
            if hasattr(self, 'edges'):
                result['edges'] = [e.serialize() for e in self.edges]

            return result

        @staticmethod
        def deserialize(json_dict, states=None):
            index = int(json_dict['index'])
            output = int(json_dict['output'])

            if isinstance(states, list):
                states[index].edges = [
                    edge.deserialize(e, states) for e in json_dict['edges']]
                return None

            return state(index=index, output=output)

    class control:

        '''
          Basic Moore FSM class for FIMP or buffer control in SYLVA
        '''

        def __init__(self, states=[], edges=[], name='no name', default_state_index=0):

            self.states = states
            self.edges = edges
            self.current_cycle = 0
            self.name = name
            self.__repr__ = self.__str__

            if self.states == []:
                self.current_state = None
            else:
                self.current_state = states[0]

            self.default_state_index = default_state_index

            if default_state_index < len(states):
                self.default_state = states[default_state_index]
            else:
                self.default_state = None

            for state in self.states:
                involved_edges = [e for e in self.edges
                                  if e.source == state]
                state.edges = list(involved_edges)

        def step(self, current_cycle=None):

            if current_cycle == None:
                self.current_cycle += 1
            else:
                self.current_cycle = current_cycle

            if self.current_state != None:
                for e in self.current_state.edges:
                    if e.cycle == self.current_cycle:
                        self.current_state = e.destination
                        return True

            return False

        def __str__(self):

            result = '\n'
            result += '=' * 64 + '\n'
            result += 'Control FSM: %s \n' % self.name
            result += '=' * 64 + '\n'
            result += 'States: \n'
            for s in self.states:
                result += '  %s \n' % s
            result += '-' * 64 + '\n'
            result += 'Transactions: \n'
            for e in self.edges:
                result += '  %s \n' % e
            return result + '=' * 64 + '\n'

        def serialize(self):
            return {'states': [s.serialize() for s in self.states],
                    'edges': [e.serialize() for e in self.edges],
                    'name': self.name,
                    'default_state_index': self.default_state.index}

        @staticmethod
        def deserialize(json_dict):
            states = [state.deserialize(s) for s in json_dict['states']]
            for s in json_dict['states']:
                state.deserialize(s, states)
            edges = [e for s in states for e in s.edges]
            name = json_dict['name']
            default_state_index = int(json_dict['default_state_index'])

            result = control()
            result.name = name
            result.default_state = states[default_state_index]
            result.default_state_index = default_state_index
            result.states = states
            result.edges = edges

            return result

def get_all_edges(hsdf_edges):
    '''
      Return all edges to be presented in the final implementation
    '''

    return merge_edges(hsdf_edges)

if 'functions for merging HSDF edges':

    def merge_edges(edge_list):
        ''' Recursively merge all HSDF edges '''

        with len(edge_list) as length:

            if length > 0:
                for i in xrange(length):
                    for j in xrange(length):
                        if i != j:
                            r = merge_two_edges(edge_list[i], edge_list[j])
                            if r != None:
                                edge_list[i] = r
                                del edge_list[j]
                                return merge_edges(edge_list)

        return edge_list

    def merge_two_edges(one_edge, another_edge):
        ''' Merge two SDF edges based on their source and destination '''

        # edge : src_actor and dest_actor are actors
        # mega edge : src_actor or dest_actor is a list of actors

        if one_edge != another_edge:

            # edge, edge
            if isinstance( one_edge.src_actor, sdf.actor) \
                    and isinstance( another_edge.src_actor, sdf.actor) \
                    and isinstance( one_edge.dest_actor, sdf.actor) \
                    and isinstance(another_edge.dest_actor, sdf.actor):

                return merge_normal_edge(one_edge, another_edge)

            # mega edge, mega edge, destination is list
            if isinstance( one_edge.src_actor, sdf.actor) \
                    and isinstance( another_edge.src_actor, sdf.actor) \
                    and isinstance( one_edge.dest_actor, list) \
                    and isinstance(another_edge.dest_actor, list):

                return merge_mega_edge_dest(one_edge, another_edge)

            # mega edge, mega edge, source is list
            if isinstance( one_edge.src_actor, list) \
                    and isinstance( another_edge.src_actor, list) \
                    and isinstance( one_edge.dest_actor, sdf.actor) \
                    and isinstance(another_edge.dest_actor, sdf.actor):

                return merge_mega_edge_src(one_edge, another_edge)

            # mega edge, edge
            # source is list
            if  isinstance( one_edge.src_actor, list) \
                    and isinstance( another_edge.src_actor, sdf.actor) \
                    and isinstance( one_edge.dest_actor, sdf.actor) \
                    and isinstance(another_edge.dest_actor, sdf.actor):

                return merge_mega_edge_edge_src(one_edge, another_edge)

            # mega edge, edge
            # destination is list
            if  isinstance( one_edge.src_actor, sdf.actor) \
                    and isinstance( another_edge.src_actor, sdf.actor) \
                    and isinstance( one_edge.dest_actor, list) \
                    and isinstance(another_edge.dest_actor, sdf.actor):

                return merge_mega_edge_edge_dest(one_edge, another_edge)

            # edge, mega edge
            # source is list
            if  isinstance( one_edge.src_actor, sdf.actor) \
                    and isinstance( another_edge.src_actor, list) \
                    and isinstance( one_edge.dest_actor, sdf.actor) \
                    and isinstance(another_edge.dest_actor, sdf.actor):

                return merge_mega_edge_edge_src(another_edge, one_edge)

            # edge, mega edge
            # destination is list
            if  isinstance( one_edge.src_actor, sdf.actor) \
                    and isinstance( another_edge.src_actor, sdf.actor) \
                    and isinstance( one_edge.dest_actor, sdf.actor) \
                    and isinstance(another_edge.dest_actor, list):

                return merge_mega_edge_edge_dest(another_edge, one_edge)

        return None

    def comp_edge((actor_a, port_a), (actor_b, port_b)):
        ''' Compare two (actor, port) pair based on actor index and port index

          actor_a.index > actor_b.index => 1
          actor_a.index == actor_b.index and port_a.index > port_b.index => 1
          actor_a.index == actor_b.index and port_a.index == port_b.index => 0
          otherwise -1

        '''

        if actor_a.index > actor_b.index:
            return 1

        if actor_a.index == actor_b.index:
            if port_a.index > port_b.index:
                return 1
            elif port_a.index == port_b.index:
                return 0
            else:
                return -1

    def sorted_actor_port_list(actors, ports):

        list_to_sort = [(actors[i], ports[i]) for i in xrange(len(actors))]

        sorted_list = sorted(list_to_sort,
                             key=functools.cmp_to_key(comp_edge))

        actor_result, port_result = [], []

        for i in xrange(len(sorted_list)):
            a, p = sorted_list[i]
            actor_result.append(a)
            port_result.append(p)

        return actor_result, port_result

    def merge_mega_edge_edge_src(one_smedge, one_edge):
        '''
          Merge one mega SDF edge with one SDF edge
          with the same destination actor and port
          when the source actor and port are lists.
        '''

        if one_smedge.dest_actor \
                == one_edge.dest_actor \
                and one_smedge.dest_port \
                == one_edge.dest_port:

            result = sdf.edge()
            result.dest_actor = one_smedge.dest_actor
            result.dest_port = one_smedge.dest_port

            src_actor = one_smedge.src_actor + [one_edge.src_actor]
            src_port = one_smedge.src_port + [one_edge.src_port]

            result.src_actor, result.src_port \
                = sorted_actor_port_list(src_actor, src_port)

            return result

        return None

    def merge_mega_edge_edge_dest(one_smedge, one_edge):
        '''
          Merge one mega SDF edge with one SDF edge
          with the same source actor and port
          when the destination actor and port are lists.
        '''

        if one_smedge.src_actor \
                == one_edge.src_actor \
                and one_smedge.src_port \
                == one_edge.src_port:

            result = sdf.edge()
            result.src_actor = one_smedge.src_actor
            result.src_port = one_smedge.src_port

            dest_actor = one_smedge.dest_actor + [one_edge.dest_actor]
            dest_port = one_smedge.dest_port + [one_edge.dest_port]

            result.dest_actor, result.dest_port \
                = sorted_actor_port_list(dest_actor, dest_port)

            return result

        return None

    def merge_mega_edge_src(one_smedge, another_smedge):
        '''
          Merge two mega SDF edges
          with the same destination actor and port
          when the source actor and port are lists.
        '''

        if one_smedge.dest_actor \
                == another_smedge.dest_actor \
                and one_smedge.dest_port \
                == another_smedge.dest_port:

            result = sdf.edge()
            result.dest_actor = one_smedge.dest_actor
            result.dest_port = one_smedge.dest_port

            src_actor = one_smedge.src_actor + another_smedge.src_actor
            src_port = one_smedge.src_port + another_smedge.src_port

            list_to_sort = []
            for i in xrange(len(src_actor)):
                list_to_sort.append((src_actor[i], src_port[i]))

            sorted_list = sorted(list_to_sort,
                                 key=functools.cmp_to_key(comp_edge))

            for i in xrange(len(sorted_list)):
                (src_actor[i], src_port[i]) = sorted_list[i]

            result.src_actor = src_actor
            result.src_port = src_port

            return result

        return None

    def merge_mega_edge_dest(one_smedge, another_smedge):
        '''
          Merge two mega SDF edges
          with the same source actor and port
          when the destination actor and port are lists.
        '''

        if one_smedge.src_actor \
                == another_smedge.src_actor \
                and one_smedge.src_port \
                == another_smedge.src_port:

            result = sdf.edge()
            result.src_actor = one_smedge.src_actor
            result.src_port = one_smedge.src_port

            dest_actor = one_smedge.dest_actor + another_smedge.dest_actor
            dest_port = one_smedge.dest_port + another_smedge.dest_port

            list_to_sort = []
            for i in xrange(len(dest_actor)):
                list_to_sort.append((dest_actor[i], dest_port[i]))

            sorted_list = sorted(list_to_sort,
                                 key=functools.cmp_to_key(comp_edge))

            for i in xrange(len(sorted_list)):
                (dest_actor[i], dest_port[i]) = sorted_list[i]

            result.dest_actor = dest_actor
            result.dest_port = dest_port

            return result

        return None

    def merge_normal_edge(one_edge, another_edge):
        '''
          Merge two normal SDF edges
          based on their source and destination.
        '''

        # If two edge shares the same source actor and port,
        # merge the destination ports
        if one_edge.src_actor.index \
                == another_edge.src_actor.index \
                and one_edge.src_port.name \
                == another_edge.src_port.name:

            one_edge, another_edge \
                = swap_edges(one_edge, another_edge,
                             based_on='destination')

            result = sdf.edge()
            result.src_actor = one_edge.src_actor
            result.src_port = one_edge.src_port
            result.dest_actor = [one_edge.dest_actor,
                                 another_edge.dest_actor]
            result.dest_port = [one_edge.dest_port,
                                another_edge.dest_port]

            return result

        # If two edge shares the same destination actor and port,
        # merge the source ports
        if one_edge.dest_actor.index \
                == another_edge.dest_actor.index \
                and one_edge.dest_port.name \
                == another_edge.dest_port.name:

            one_edge, another_edge \
                = swap_edges(one_edge, another_edge,
                             based_on='source')

            result = sdf.edge()
            result.src_actor = [one_edge.src_actor,
                                another_edge.src_actor]
            result.src_port = [one_edge.src_port,
                               another_edge.src_port]
            result.dest_actor = one_edge.dest_actor
            result.dest_port = one_edge.dest_port

            return result

        return None

    def swap_edges(one_edge, another_edge, based_on):
        if based_on == 'source':
            return swap_edges_src(one_edge, another_edge)
        if based_on == 'destination':
            return swap_edges_dest(one_edge, another_edge)

    def swap_edges_dest(one_edge, another_edge):
        '''
          Swap two edges to make sure that

          1. one_edge.dest_actor < another_edge.dest_actor
          or
          2. if one_edge.dest_actor == another_edge.dest_actor
             then one_edge.dest_port < another_edge.dest_port
        '''

        # one_edge.dest_actor > another_edge.dest_actor
        # swap
        if one_edge.dest_actor.index \
                > another_edge.dest_actor.index:

            return another_edge, one_edge

        # one_edge.dest_actor == another_edge.dest_actor
        # and
        # one_edge.dest_port.index > another_edge.dest_port.index :
        # swap
        elif one_edge.dest_actor.index \
            == another_edge.dest_actor.index \
            and one_edge.dest_port.index \
                > another_edge.dest_port.index:

            return another_edge, one_edge

        # one_edge.dest_actor < another_edge.dest_actor
        # or
        # one_edge.dest_port.index < another_edge.dest_port.index
        # no touch
        else:

            return one_edge, another_edge

    def swap_edges_src(one_edge, another_edge):
        '''
          Swap two edges to make sure that

          1. one_edge.src_actor < another_edge.src_actor
          or
          2. if one_edge.src_actor == another_edge.src_actor
             then one_edge.src_port < another_edge.src_port
        '''

        # one_edge.src_actor > another_edge.src_actor
        # swap
        if one_edge.src_actor.index \
                > another_edge.src_actor.index:

            return another_edge, one_edge

        # one_edge.src_actor == another_edge.src_actor
        # and
        # one_edge.src_port.index > another_edge.src_port.index :
        # swap
        elif one_edge.src_actor.index \
            == another_edge.src_actor.index \
            and one_edge.src_port.index \
                > another_edge.src_port.index:

            return another_edge, one_edge

        # one_edge.dest_actor < another_edge.dest_actor
        # or
        # one_edge.dest_port.index < another_edge.dest_port.index
        # no touch
        else:

            return one_edge, another_edge

if 'functions for creating an ABB':

    def create_output_buffer(one_output_port, buffer_size=None):
        '''
          Create one output buffer for one output port in an HSDF actor.
        '''

        if buffer_size == None:
            buffer_size = one_output_port.count

        if one_output_port != None:
            return {'port': one_output_port,
                    'buffer_size': buffer_size}

        return None

    def create_output_buffers(one_fimp):
        '''
          Create output buffers for one FIMP instance.
          Each port has its own buffer.
          If extra_buffer = 1,
            each actor has its own buffers for all its output ports.
        '''
        # one port one buffer
        # Consider all buffers are for the first HSDF actor on the FIMP
        if one_fimp.extra_buffer == 0:
            return [[create_output_buffer(p, buffer_size=len(one_fimp.actors) * p.count)
                     for p in one_fimp.actors[0].output_ports]]
        else:
            return [[create_output_buffer(p)
                     for p in a.output_ports]
                    for a in one_fimp.actors]

    def create_actor_control(actor, INPUT=INPUT, COMPUTATION=COMPUTATION, OUTPUT=OUTPUT, IDLE=IDLE):
        ''' Create control for one HSDF actor '''

        s = actor

        # Assume the states are INPUT, COMPUTATION, OUTPUT, IDLE
        states = [state(index=i) for i in range(4)]
        edges = [edge(source=states[i - 1],
                      destination=states[i])
                 for i in range(1, 4)]

        # [input]
        # [computation]
        # [output     ]
        # if the output phase starts directly
        # first state should be INPUT + OUTPUT
        if actor.input_ports == []:
            states[0].output = COMPUTATION
        else:
            if s.output_start == 0:
                states[0].output = INPUT + OUTPUT
            else:
                states[0].output = INPUT

        #   0 1 2 3 4 5 6 7 8 9 10 11 schedule
        #   [ input  ]
        #                 [ output ]
        # 0 1 2 3 4 5 6 7 8 9 1011 12 clock cycles
        #   [ S0     ][S1][S2      ][S3]
        # if input and output phases are not overlapping
        # we have one computation state then output states
        if s.input_end < s.output_start - 1:
            states[1].output = COMPUTATION
            states[2].output = OUTPUT
            states[3].output = IDLE

            # input -> compute
            edges[0].cycle = s.input_end + 1
            # compute -> output
            edges[1].cycle = s.output_start
            # output -> idle
            edges[2].cycle = s.end + 1
            # idle -> input
            # edges.append( edge( source = states[3],
            #                     destination = states[0],
            #                     cycle = 0) )

        #   0 1 2 3 4 5 6 7 8 9 10 11 schedule
        #   [ input  ]
        #             [ output ]
        # 0 1 2 3 4 5 6 7 8 9 1011 12 clock cycles
        elif s.input_end == s.output_start - 1:

            states[1].output = OUTPUT
            states[2].output = IDLE
            del states[3]
            del edges[2]
            # input -> output
            edges[0].cycle = s.input_end + 1
            # output -> idle
            edges[1].cycle = s.end + 1
            # idle -> input
            # edges.append( edge( source = states[2],
            #                     destination = states[0],
            #                     cycle = 0) )

        #   0 1 2 3 4 5 6 7 8 9 10 11 schedule
        #   [ input  ]
        #         [ output ]
        # 0 1 2 3 4 5 6 7 8 9 1011 12 clock cycles
        else:
            states[1].output = INPUT + OUTPUT
            states[2].output = OUTPUT
            states[3].output = IDLE

            # input -> input and output
            edges[0].cycle = s.output_start
            # input and output -> output
            edges[1].cycle = s.input_end + 1
            # output -> idle
            edges[2].cycle = s.end + 1
            # idle -> input
            # edges.append( edge( source = states[3],
            #                     destination = states[0],
            #                     cycle = 0) )

        edges.append(edge(source=states[-1], destination=states[0], cycle=0))

        return control(states, edges, actor.index, default_state_index=len(states) - 1)

    def create_actor_controls(one_fimp):
        '''
          Generate all controls for all actors on this FIMP
        '''

        return [create_actor_control(a) for a in one_fimp.actors]

    def create_input_selectors(one_fimp, all_edges, actor_controls):
        '''
          Each HSDF actor has its own control (cs).
          Each input port on the FIMP has its own input selector.

          Condition =
            bitwise OR on the outputs of all the actor controls
        '''

        output_ports = one_fimp.actors[0].input_ports
        input_selector_controls = []

        for op in output_ports:

            states = []
            edges = []

            states += [state(0, None)]

            for c in actor_controls:
                for s in c.states:
                    if s.output == INPUT or s.output == IO:
                        states.append(state(len(states), c.name))
                    else:
                        states.append(state(len(states), None))
                    edges.append(edge(states[-2], states[-1], s.output))

            edges[-1].destination = states[0]
            input_selector_controls.append(control(states, edges, op.name))

        return input_selector_controls

    def create_fimp_control(one_fimp, all_edges, actor_controls):
        '''
          FIMP executes when
            bitwise OR on the outputs of all the actor controls != IDLE
        '''

        states = []
        edges = []
        states.append(state(0, IDLE))
        states.append(state(1, COMPUTATION))
        edges.append(edge(states[0], states[1], '!=%s' % IDLE))
        edges.append(edge(states[1], states[0], '==%s' % IDLE))

        return control(states, edges, one_fimp)

    def create_output_selectors(one_fimp, all_edges, actor_controls):
        '''
          Each HSDF actor has its own control (cs).
          Each output port on the FIMP has its own output selector.

          Condition =
            bitwise OR on the outputs of all the actor controls
        '''

        input_ports = one_fimp.actors[0].output_ports
        output_selector_controls = []

        for ip in input_ports:

            states = []
            edges = []

            states += [state(0, None)]

            for c in actor_controls:
                for s in c.states:
                    if s.output == OUTPUT or s.output == IO:
                        states.append(state(len(states), c.name))
                    else:
                        states.append(state(len(states), None))
                    edges.append(edge(states[-2], states[-1], s.output))

            edges[-1].destination = states[0]
            output_selector_controls.append(control(states, edges, ip.name))

        return output_selector_controls

    class abb():

        def __init__(self, one_fimp,
                     actor_controls,
                     input_selector_controls,
                     fimp_control,
                     output_buffers,
                     output_selector_controls):

            self.fimp = one_fimp
            self.actor_controls = actor_controls
            self.input_selector_controls = input_selector_controls
            self.fimp_control = fimp_control
            self.output_buffers = output_buffers
            self.output_selector_controls = output_selector_controls

    def create_abb(one_fimp, all_edges):

        # generate all controls for all actors on this FIMP
        actor_controls \
            = create_actor_controls(one_fimp)

        # generate all input selector controls for all ports on this FIMP
        input_selector_controls \
            = create_input_selectors(one_fimp, all_edges, actor_controls)

        fimp_control \
            = create_fimp_control(one_fimp, all_edges, actor_controls)

        output_buffers \
            = create_output_buffers(one_fimp)

        output_selector_controls \
            = create_output_selectors(one_fimp, all_edges, actor_controls)

        return abb(one_fimp,
                   actor_controls,
                   input_selector_controls,
                   fimp_control,
                   output_buffers,
                   output_selector_controls)
