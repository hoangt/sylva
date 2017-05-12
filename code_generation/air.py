# coding: utf-8
# The MIT License (MIT)
# Copyright (c) 2017 by Shuo Li (contact@shuo.li)
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
__version__ = '2015-08-16-21:02'

''' ABB to SDF Actor Conversion '''

import math
import sylva.glic.glic as glic
import sylva.base.sdf as sdf
import sylva.base.fimp as fimp
from sylva.code_generation.vhdl_types import \
    integer as integer_DataTokenType, std_logic
from sylva.code_generation.hsdf_to_vhdl import *
import sylva.code_generation.sylva_fimp_lib as sflib

# All ABBs use the same type of counter.


def counter_actor(fimp_instance, sample_interval, default_name='sylva_counter'):

    current_cycle_port = sdf.port(
        name='current_cycle',
        type=integer_DataTokenType(sample_interval))

    output_ports = [current_cycle_port]

    name = '_'.join([default_name, str(sample_interval)])

    base_actor = sdf.actor(name=name, output_ports=output_ports)
    result = sdf.actor(name=name,
                       output_ports=output_ports, base_actor=base_actor)

    result.current_cycle_port = current_cycle_port
    result.max_output = sample_interval

    return result

# Each ABB uses its own type of FSM


def actor_fsm_actor(control, sample_interval, max_output=glic.IO,
                    default_name='sylva_actor_control_fsm'):

    current_cycle_port = sdf.port(name='current_cycle', index=0, type=integer_DataTokenType(sample_interval))
    control_port = sdf.port(name='control_output', index=0, type=integer_DataTokenType(max_output))

    input_ports = [current_cycle_port]
    output_ports = [control_port]

    name = default_name + '_' + str(control.name)

    base_actor = sdf.actor(name=name, input_ports=input_ports, output_ports=output_ports)
    result = sdf.actor(name=name, input_ports=input_ports, output_ports=output_ports, base_actor=base_actor)

    result.control = control
    result.control_port = control_port
    result.current_cycle_port = current_cycle_port

    return result


def get_control_ports(name_prefix, max_output, fimp_instance):

    control_ports = [get_one_control_port(name_prefix, max_output, index=actor.index)
                     for actor in fimp_instance.actors]
    return control_ports, xrange(len(control_ports))


def get_one_control_port(name_prefix, max_output, index=0):

    return sdf.port(name='_'.join([name_prefix, str(index)]), index=index, type=integer_DataTokenType(max_output))


class BassObject:

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()


class ControlMap(BassObject):

    def __init__(self, output_port, conditions):
        self.output_port = output_port
        self.conditions = conditions


class PortMapCondition(BassObject):

    def __init__(self, control_port, valid_values, input_port):
        self.control_port = control_port
        self.valid_values = valid_values
        self.input_port = input_port


class PortAndActions(BassObject):

    def __init__(self, port, actions):
        self.port = port
        self.actions = actions


class AddressPortAction(BassObject):

    def __init__(self, cycle, address):
        self.cycle = cycle
        self.address = address


class ActorAndPort(BassObject):

    def __init__(self, actor, port):
        self.actor = actor
        self.port = port

# Each ABB has its own input selector type
# sylva_input_selector_N, N = FIMP index


def input_selector_actor(fimp_instance, sample_interval, max_output=glic.IO, default_name='sylva_input_selector'):

    input_ports = []
    output_ports = []

    name = default_name + '_' + str(fimp_instance.index)

    control_ports, control_port_range \
        = get_control_ports('control_input', max_output, fimp_instance)

    data_input_ports = []
    for a in fimp_instance.actors:
        for p in a.input_ports:
            data_input_port_name = '_'.join([p.name, str(a.index), str(p.index)])
            data_input_port = sdf.port(name=data_input_port_name, type=p.type)
            data_input_port.actor = a
            p.top_port = data_input_port
            data_input_ports.append(data_input_port)

    current_cycle_port = sdf.port(
        name='current_cycle', index=0, type=integer_DataTokenType(sample_interval))

    data_output_ports = [sdf.port(name='_'.join([p.name, str(fimp_instance.index)]), type=p.type)
                         for p in fimp_instance.actors[0].input_ports]

    read_address_ports = {}
    # assume actors are sorted based on their start time
    # increasing
    for a in fimp_instance.actors:

        input_start_time = a.start
        input_end_time = a.input_end

        for p in a.previous:
            cycles_step = output_data_structure(p.src_actor)[1][p.src_port.index]

            source_fimp = p.src_actor.fimp
            source_actor = p.src_actor
            source_port = p.src_port
            extra_buffer = p.src_actor.fimp.extra_buffer == 1
            source_actor_count = len(p.src_actor.fimp.actors)

            if extra_buffer == True:
                addres_port_type = integer_DataTokenType(source_port.count)
                address_port_name = '_'.join(['read_address',
                                              str(source_fimp.index),
                                              str(source_actor.index),
                                              str(source_port.index)])

            else:
                addres_port_type = \
                    integer_DataTokenType(source_port.count * source_actor_count)
                address_port_name = '_'.join(['read_address',
                                              str(source_fimp.index),
                                              'shared',
                                              str(source_port.index)])

            if address_port_name not in read_address_ports.keys():
                address_port = sdf.port(name=address_port_name, type=addres_port_type)
                address_port.extra_buffer = extra_buffer
                address_port.actions = []
                address_port.source_fimp = source_fimp
                address_port.source_port = source_port
                if extra_buffer == True:
                    address_port.source_actor = source_actor
                read_address_ports[address_port_name] = address_port

            actions = read_address_ports[address_port_name].actions
            previous_actions = len(actions)

            if extra_buffer == True:
                address_offset = previous_actions * p.dest_port.count
                actions += [AddressPortAction(
                    cycle=input_start_time + token_index * cycles_step,
                    address=address_offset + token_index)
                    for token_index in xrange(p.dest_port.count)]
            else:
                actor_index = p.src_actor.abb.fimp.actors.index(p.src_actor)
                address_offset = actor_index * p.src_port.count + previous_actions * p.dest_port.count
                actions += [AddressPortAction(
                    cycle=input_start_time + token_index * cycles_step,
                    address=address_offset + token_index)
                    for token_index in xrange(p.dest_port.count)]

    read_address_ports = read_address_ports.values()
    input_ports = control_ports + data_input_ports + [current_cycle_port]
    output_ports = data_output_ports + read_address_ports

    base_actor = sdf.actor(name=name, input_ports=input_ports, output_ports=output_ports)

    result = sdf.actor(name=name, input_ports=input_ports, output_ports=output_ports, base_actor=base_actor)
    result.control_ports = control_ports
    result.data_input_ports = data_input_ports
    result.data_output_ports = data_output_ports
    result.read_address_ports = read_address_ports
    result.current_cycle_port = current_cycle_port

    result.control_map = [
        ControlMap(output_port=data_output_port,
                   conditions=[
                       PortMapCondition(control_port=c,
                                        valid_values=[glic.INPUT, glic.IO],
                                        input_port=data_input_ports[j + i*len(data_output_ports)])
                       for i, c in enumerate(control_ports)
                       for j, __ in enumerate(data_output_ports)])
        for data_output_port in data_output_ports]

    return result

# Each ABB has its own output selector type
# sylva_output_selector_N, N = FIMP index


def output_selector_actor(fimp_instance, max_output=glic.IO,
                          default_name='sylva_output_selector'):

    control_ports, control_port_range \
        = get_control_ports('control_input', max_output, fimp_instance)

    data_ports = [sdf.port(name='_'.join([p.name, str(fimp_instance.index)]), type=p.type)
                  for p in fimp_instance.actors[0].output_ports]
    data_port_range = xrange(len(data_ports))

    input_ports = control_ports + data_ports

    output_ports = []
    for a in fimp_instance.actors:
        for p in a.output_ports:
            output_ports.append(sdf.port(name='_'.join([p.name, str(a.index), str(p.index)]), type=p.type))
            output_ports[-1].actor_index = a.index

    name = default_name + '_' + str(fimp_instance.index)

    base_actor = sdf.actor(name=name, input_ports=input_ports, output_ports=output_ports)

    result = sdf.actor(name=name, input_ports=input_ports, output_ports=output_ports, base_actor=base_actor)
    result.control_port_range = control_port_range
    result.data_port_range = data_port_range
    return result


# Each ABB has its own FIMP control type
# since the number of HSDF actors are different
# name = sylva_fimp_control_FIMPIndex
def fimp_control_actor(controls, fimp_instance,
                       max_output=glic.IO, default_name='sylva_fimp_control',
                       fimp_enable_signal_name='en',
                       input=glic.INPUT,
                       output=glic.OUTPUT,
                       inout=glic.IO,
                       computation=glic.COMPUTATION,
                       idle=glic.IDLE):

    input_ports, __ \
        = get_control_ports('control_input', max_output, fimp_instance)

    output_ports = [sdf.port(name=fimp_enable_signal_name, index=0,
                             type=std_logic)]
    name = '_'.join([default_name, str(fimp_instance.index)])

    base_actor = sdf.actor(name=name, input_ports=input_ports, output_ports=output_ports)
    return sdf.actor(name=name, input_ports=input_ports, output_ports=output_ports, base_actor=base_actor)

# output_cycles, cycles_per_data_token


def output_data_structure(actor):
    output_cycles = actor.end - actor.output_start + 1
    cycles_per_data_token = [int(math.ceil(float(output_cycles)/p.count)) for p in actor.output_ports]
    return output_cycles, cycles_per_data_token

# Each ABB has its own buffer control type
# since the number of HSDF actors are different
# name = Name_FIMPIndex_HSDFActorIndex
# One controller controls all the buffers


def buffer_control_actor(controls, fimp_instance, max_cycle,
                         max_output=glic.IO,
                         default_name='sylva_buffer_control',
                         read_write_signal='wr', extra_buffer=True):

    control_ports, control_port_range = \
        get_control_ports('control_input', max_output, fimp_instance)

    current_cycle_port = sdf.port(name='current_cycle', index=0, type=integer_DataTokenType(max_cycle))

    wr_ports = [sdf.port(name='_'.join([read_write_signal, str(actor.index)]), index=i, type=std_logic)
                for i, actor in enumerate(fimp_instance.actors)]

    address_ports = []
    __, cycles_per_data_token = output_data_structure(fimp_instance.actors[0])

    if extra_buffer == True:
        # each actor has its own output buffers
        for actor in fimp_instance.actors:
            address_ports.append([])
            # each output port has one output buffer
            for port_index, port in enumerate(actor.output_ports):
                address_ports[-1].append(
                    sdf.port(name='_'.join(['write_address', str(actor.index), str(port.index)]),
                             type=integer_DataTokenType(port.count)))
                address_ports[-1][-1].actions = [
                    (actor.output_start + token_index * cycles_per_data_token[port_index], token_index)
                    for token_index in xrange(port.count)]
    else:
        actor_count = len(fimp_instance.actors)
        # all output ports of all actors share one output buffer
        for port_index, port in enumerate(fimp_instance.actors[0].output_ports):
            address_ports.append(
                sdf.port(name='_'.join(['write_address', 'shared', str(port.index)]),
                         type=integer_DataTokenType(port.count * actor_count)))
            address_ports[-1].actions = []
            token_index = 0
            for actor_index, actor in enumerate(fimp_instance.actors):
                for __ in xrange(port.count):
                    action = (actor.output_start + token_index * cycles_per_data_token[port_index],
                              token_index)
                    token_index += 1
                    address_ports[-1].actions.append(action)

    input_ports = control_ports + [current_cycle_port]
    output_ports = wr_ports + address_ports

    name = '_'.join([default_name, str(fimp_instance.index)])
    base_actor = sdf.actor(
        name=name,
        input_ports=input_ports,
        output_ports=output_ports)
    result = sdf.actor(
        name=name,
        input_ports=input_ports,
        output_ports=output_ports,
        base_actor=base_actor)
    result.control_ports = control_ports
    result.current_cycle_port = current_cycle_port
    result.wr_ports = wr_ports
    result.address_ports = address_ports

    return result


def fimp_actor(fimp_instance, fimp_enable_signal_name='en'):
    name = fimp_instance.actors[0].base_actor.name
    index = fimp_instance.index

    data_input_ports = fimp_instance.actors[0].base_actor.input_ports
    en_port = sdf.port(name=fimp_enable_signal_name, index=0, type=std_logic)

    input_ports = data_input_ports + [en_port]
    output_ports = fimp_instance.actors[0].base_actor.output_ports

    base_actor = sdf.actor(name=name, input_ports=input_ports, output_ports=output_ports)
    result = sdf.actor(name=name, input_ports=input_ports, output_ports=output_ports, base_actor=base_actor,
                       index=fimp_instance.index)
    result.en_port = en_port
    result.fimp_type = fimp_instance.type
    return result


def buffer_actors(fimp_instance,
                  default_name='sylva_output_buffer',
                  read_write_signal='wr'):

    fimp_index = str(fimp_instance.index)
    extra_buffer = fimp_instance.extra_buffer == 1

    result = []
    if extra_buffer == True:
        # each actor has its own output buffers
        for actor in fimp_instance.actors:
            result.append([])
            actor_index = actor.index
            # each output port has one output buffer
            for port in actor.output_ports:
                name = '_'.join([default_name, str(fimp_index), str(actor_index), str(port.index)])
                wr_port = sdf.port(name='_'.join([read_write_signal, str(actor.index), str(port.index)]),
                                   index=0, type=std_logic)
                write_address_port = sdf.port(
                    name='_'.join(['write_address', str(actor_index), str(port.index)]),
                    type=integer_DataTokenType(port.count))
                read_address_port = sdf.port(
                    name='_'.join(['read_address', str(fimp_instance.index), str(actor_index), str(port.index)]),
                    type=integer_DataTokenType(port.count))
                data_input_port = sdf.port(
                    name='_'.join([port.name]),
                    type=port.type)
                data_output_port = sdf.port(
                    name='_'.join([port.name, str(actor.index)]),
                    type=port.type)
                input_ports = [wr_port, write_address_port, read_address_port, data_input_port]
                output_ports = [data_output_port]
                port.top_port = data_output_port
                base_actor = sdf.actor(name=name, input_ports=input_ports, output_ports=output_ports)
                one_buffer = sdf.actor(name=name, input_ports=input_ports, output_ports=output_ports,
                                       base_actor=base_actor)
                one_buffer.buffer_size = port.count
                one_buffer.wr_port = wr_port
                one_buffer.write_address_port = write_address_port
                one_buffer.read_address_port = read_address_port
                one_buffer.data_input_port = data_input_port
                one_buffer.data_output_port = data_output_port
                result[-1].append(one_buffer)

    else:  # extra_buffer = False

        actor_count = len(fimp_instance.actors)
        for port in fimp_instance.actors[0].output_ports:
            name = '_'.join([default_name, str(fimp_index), 'shared', str(port.index)])
            wr_port = sdf.port(name='_'.join([read_write_signal, 'shared', str(port.index)]),
                               index=0, type=std_logic)
            write_address_port = sdf.port(
                name='_'.join(['write_address', 'shared', str(port.index)]),
                type=integer_DataTokenType(port.count * actor_count))
            read_address_port = sdf.port(
                name='_'.join(['read_address', str(fimp_instance.index), 'shared', str(port.index)]),
                type=integer_DataTokenType(port.count * actor_count))
            data_input_port = sdf.port(
                name='_'.join([port.name]),
                type=port.type)
            data_output_port = sdf.port(
                name='_'.join([port.name, 'shared']),
                type=port.type)
            input_ports = [wr_port, write_address_port, read_address_port, data_input_port]
            output_ports = [data_output_port]
            for a in fimp_instance.actors:
                for p in a.output_ports:
                    if p.name == port.name:
                        p.top_port = data_output_port
            base_actor = sdf.actor(name=name, input_ports=input_ports, output_ports=output_ports)
            one_buffer = sdf.actor(name=name, input_ports=input_ports, output_ports=output_ports,
                                   base_actor=base_actor)
            one_buffer.buffer_size = port.count * len(fimp_instance.actors)
            one_buffer.wr_port = wr_port
            one_buffer.write_address_port = write_address_port
            one_buffer.read_address_port = read_address_port
            one_buffer.data_input_port = data_input_port
            one_buffer.data_output_port = data_output_port

            result.append(one_buffer)

    return result


def create_abb_hsdf(one_abb, sample_interval):

    one_abb.abb_counter_actor = counter_actor(one_abb.fimp, sample_interval)
    one_abb.abb_control_fsm_actors = [
        actor_fsm_actor(control, sample_interval) for control in one_abb.actor_controls]
    if one_abb.fimp.actors[0].input_ports != []:
        one_abb.abb_input_selector_actor = input_selector_actor(one_abb.fimp, sample_interval)
    if one_abb.fimp.actors[0].output_ports != []:
        one_abb.abb_output_selector_actor = output_selector_actor(one_abb.fimp)
        one_abb.abb_output_buffer_actors = buffer_actors(one_abb.fimp)
        one_abb.abb_buffer_control_actor = buffer_control_actor(
            one_abb.actor_controls, one_abb.fimp, sample_interval,
            extra_buffer=one_abb.fimp.extra_buffer == 1)
    one_abb.abb_fimp_control_actor = fimp_control_actor(
        one_abb.actor_controls, one_abb.fimp)
    one_abb.abb_fimp_actor = fimp_actor(one_abb.fimp)

    one_abb.hsdf_actors = [one_abb.abb_counter_actor]
    one_abb.hsdf_actors += one_abb.abb_control_fsm_actors
    one_abb.hsdf_actors.append(one_abb.abb_fimp_control_actor)
    one_abb.hsdf_actors.append(one_abb.abb_fimp_actor)

    if one_abb.fimp.actors[0].input_ports != []:
        one_abb.hsdf_actors.append(one_abb.abb_input_selector_actor)
    if one_abb.fimp.actors[0].output_ports != []:
        one_abb.hsdf_actors.append(one_abb.abb_output_selector_actor)
        one_abb.hsdf_actors.append(one_abb.abb_buffer_control_actor)
        if one_abb.fimp.extra_buffer == 1:
            one_abb.hsdf_actors += [
                a for b in one_abb.abb_output_buffer_actors for a in b]
        else:
            one_abb.hsdf_actors += [
                a for a in one_abb.abb_output_buffer_actors]

    for a in one_abb.hsdf_actors:
        global_index = 0
        a.assign_to(fimp.fimp(name=a.base_actor.name))
        a.fimp.global_index = global_index
        global_index += 1
        a.fimp.base_actor = a.base_actor

    one_abb.abb_fimp_actor.fimp.type = one_abb.fimp.type

    # counter to fsms
    one_abb.edges_counter_to_fsm = [sdf.edge(src_actor=one_abb.abb_counter_actor,
                                             src_port=one_abb.abb_counter_actor.current_cycle_port,
                                             dest_actor=a, dest_port=a.current_cycle_port)
                                    for a in one_abb.abb_control_fsm_actors]

    one_abb.hsdf_edges = list(one_abb.edges_counter_to_fsm)

    # fsms to fimp control
    one_abb.edges_fsm_to_fimp_control = \
        [sdf.edge(src_actor=a,
                  src_port=a.output_ports[0],
                  dest_actor=one_abb.abb_fimp_control_actor,
                  dest_port=one_abb.abb_fimp_control_actor.input_ports[i])
         for i, a in enumerate(one_abb.abb_control_fsm_actors)]
    one_abb.hsdf_edges += one_abb.edges_fsm_to_fimp_control

    # fimp control to fimp
    one_abb.edge_fimp_control_to_fimp = \
        sdf.edge(src_actor=one_abb.abb_fimp_control_actor,
                 src_port=one_abb.abb_fimp_control_actor.output_ports[0],
                 dest_actor=one_abb.abb_fimp_actor,
                 dest_port=one_abb.abb_fimp_actor.en_port)
    one_abb.hsdf_edges.append(one_abb.edge_fimp_control_to_fimp)

    # fsms to input selector
    if one_abb.fimp.actors[0].input_ports != []:
        one_abb.edges_fsm_to_input_selector = [sdf.edge(src_actor=a,
                                                        src_port=a.output_ports[0],
                                                        dest_actor=one_abb.abb_input_selector_actor,
                                                        dest_port=one_abb.abb_input_selector_actor.input_ports[i])
                                               for i, a in enumerate(one_abb.abb_control_fsm_actors)]
        one_abb.hsdf_edges += one_abb.edges_fsm_to_input_selector
        # counter to output buffer control
        one_abb.edge_counter_to_input_selector = sdf.edge(
            src_actor=one_abb.abb_counter_actor,
            src_port=one_abb.abb_counter_actor.output_ports[0],
            dest_actor=one_abb.abb_input_selector_actor,
            dest_port=one_abb.abb_input_selector_actor.current_cycle_port)
        one_abb.hsdf_edges.append(one_abb.edge_counter_to_input_selector)

    if one_abb.fimp.actors[0].output_ports != []:

        # counter to output buffer control
        one_abb.edge_counter_to_output_buffer = sdf.edge(
            src_actor=one_abb.abb_counter_actor,
            src_port=one_abb.abb_counter_actor.output_ports[0],
            dest_actor=one_abb.abb_buffer_control_actor,
            dest_port=one_abb.abb_buffer_control_actor.current_cycle_port)
        one_abb.hsdf_edges.append(one_abb.edge_counter_to_output_buffer)

        # fsms to output selector
        one_abb.edges_fsm_to_output_selector = [sdf.edge(src_actor=a,
                                                         src_port=a.output_ports[0],
                                                         dest_actor=one_abb.abb_output_selector_actor,
                                                         dest_port=one_abb.abb_output_selector_actor.input_ports[i])
                                                for i, a in enumerate(one_abb.abb_control_fsm_actors)]
        one_abb.hsdf_edges += one_abb.edges_fsm_to_output_selector

        # fsms to output buffers
        one_abb.edges_fsm_to_output_buffer_controls = \
            [sdf.edge(src_actor=a,
                      src_port=a.output_ports[0],
                      dest_actor=one_abb.abb_buffer_control_actor,
                      dest_port=one_abb.abb_buffer_control_actor.input_ports[i])
             for i, a in enumerate(one_abb.abb_control_fsm_actors)]
        one_abb.hsdf_edges += one_abb.edges_fsm_to_output_buffer_controls

        # output buffer control to output buffers
        # wr
        if one_abb.fimp.extra_buffer == 1:
            one_abb.edges_output_buffer_controls_to_output_buffers_wr = \
                [sdf.edge(src_actor=one_abb.abb_buffer_control_actor,
                          src_port=one_abb.abb_buffer_control_actor.wr_ports[i],
                          dest_actor=one_buffer_actor,
                          dest_port=one_buffer_actor.wr_port)
                 for buffer_set in one_abb.abb_output_buffer_actors
                 for i, one_buffer_actor in enumerate(buffer_set)]
        else:
            one_abb.edges_output_buffer_controls_to_output_buffers_wr = \
                [sdf.edge(src_actor=one_abb.abb_buffer_control_actor,
                          src_port=one_abb.abb_buffer_control_actor.wr_ports[i],
                          dest_actor=one_buffer_actor,
                          dest_port=one_buffer_actor.wr_port)
                 for i, one_buffer_actor in enumerate(one_abb.abb_output_buffer_actors)]
        one_abb.hsdf_edges += one_abb.edges_output_buffer_controls_to_output_buffers_wr

        # output buffer control to output buffers
        # address
        if one_abb.fimp.extra_buffer == 1:
            one_abb.edges_output_buffer_controls_to_output_buffers_address = \
                [sdf.edge(src_actor=one_abb.abb_buffer_control_actor,
                          src_port=one_abb.abb_buffer_control_actor.address_ports[actor_index][port_index],
                          dest_actor=one_buffer_actor,
                          dest_port=one_buffer_actor.write_address_port)
                 for actor_index, actor in enumerate(one_abb.fimp.actors)
                 for port_index, __ in enumerate(actor.output_ports)]
        else:
            one_abb.edges_output_buffer_controls_to_output_buffers_address = \
                [sdf.edge(src_actor=one_abb.abb_buffer_control_actor,
                          src_port=one_abb.abb_buffer_control_actor.address_ports[port_index],
                          dest_actor=one_buffer_actor,
                          dest_port=one_buffer_actor.write_address_port)
                 for port_index, __ in enumerate(one_abb.fimp.actors[0].output_ports)]
        one_abb.hsdf_edges += one_abb.edges_output_buffer_controls_to_output_buffers_address

        # fimp to output_buffers
        if one_abb.fimp.extra_buffer == 1:
            one_abb.edges_fimp_to_output_buffers = \
                [sdf.edge(src_actor=one_abb.abb_fimp_actor,
                          src_port=one_abb.abb_fimp_actor.output_ports[i],
                          dest_actor=one_buffer_actor,
                          dest_port=one_buffer_actor.data_input_port)
                 for buffer_set in one_abb.abb_output_buffer_actors
                 for i, one_buffer_actor in enumerate(buffer_set)]
        else:
            one_abb.edges_fimp_to_output_buffers = \
                [sdf.edge(src_actor=one_abb.abb_fimp_actor,
                          src_port=one_abb.abb_fimp_actor.output_ports[i],
                          dest_actor=one_buffer_actor,
                          dest_port=one_buffer_actor.data_input_port)
                 for i, one_buffer_actor in enumerate(one_abb.abb_output_buffer_actors)]

        one_abb.hsdf_edges += one_abb.edges_fimp_to_output_buffers

    return one_abb


def abb_to_vhdl(one_abb, sample_interval, sylva_lib):

    entity_name = '_'.join([one_abb.fimp.name, str(one_abb.fimp.index)])
    input_ports, output_ports = [], []
    input_actor_and_ports, output_actor_and_ports = [], []

    if hasattr(one_abb, 'abb_input_selector_actor'):

        # input data ports
        data_input_ports = one_abb.abb_input_selector_actor.data_input_ports
        input_actor_and_ports += [
            ActorAndPort(actor=one_abb.abb_input_selector_actor,
                         port=p)
            for p in data_input_ports]
        one_abb.data_input_ports = data_input_ports

        # read address ports output
        read_address_output_ports = one_abb.abb_input_selector_actor.read_address_ports
        output_actor_and_ports += [
            ActorAndPort(actor=one_abb.abb_input_selector_actor,
                         port=p)
            for p in read_address_output_ports]
        one_abb.read_address_output_ports = read_address_output_ports

        input_ports += data_input_ports
        output_ports += read_address_output_ports

    if hasattr(one_abb, 'abb_output_buffer_actors'):

        # output data ports
        data_output_ports = [a.data_output_port for a in one_abb.abb_output_buffer_actors]
        output_actor_and_ports += [ActorAndPort(actor=a, port=a.data_output_port)
                                   for a in one_abb.abb_output_buffer_actors]
        one_abb.data_output_ports = data_output_ports

        # read address ports input
        read_address_input_ports = [a.read_address_port for a in one_abb.abb_output_buffer_actors]
        input_actor_and_ports += [ActorAndPort(actor=a, port=a.read_address_port)
                                  for a in one_abb.abb_output_buffer_actors]
        one_abb.read_address_input_ports = read_address_input_ports

        input_ports += read_address_input_ports
        output_ports += data_output_ports

    status = hsdf_to_vhdl(one_abb.hsdf_actors, one_abb.hsdf_edges, sylva_lib,
                          entity_name=entity_name,
                          used_libraries={'IEEE': ['std_logic_1164.all'], 'WORK': ['all']},
                          output_file=entity_name + '.vhdl',
                          input_actor_and_ports=input_actor_and_ports,
                          output_actor_and_ports=output_actor_and_ports)

    top_input_ports = [p.port for p in input_actor_and_ports]
    top_output_ports = [p.port for p in output_actor_and_ports]
    base_actor = sdf.actor(name=entity_name, index=one_abb.fimp.index,
                           input_ports=top_input_ports, output_ports=top_output_ports)
    one_abb.top_actor = sdf.actor(name=entity_name, index=one_abb.fimp.index,
                                  input_ports=top_input_ports, output_ports=top_output_ports,
                                  base_actor=base_actor)

    one_abb.top_actor.assign_to(fimp.fimp(name=entity_name, index=one_abb.fimp.index))
    one_abb.top_actor.fimp.base_actor = base_actor
    one_abb.top_actor.fimp.global_index = one_abb.fimp.index

    return status


def air_to_vhdl(air, sample_interval, fimp_lib, output_dir, top_module_name):

    cwd = os.getcwd()
    os.chdir(output_dir)

    for function_name in fimp_lib.function_name_set:
        for key, value in fimp_lib[function_name].set.items():
            value.code_template = 'entity {{entity_name}} is end;'

    for one_abb in air:

        for a in one_abb.fimp.actors:
            a.abb = one_abb
        one_abb.fimp.abb = one_abb
        sylva_lib = fimp.fimp_lib('FPGA')
        create_abb_hsdf(one_abb, sample_interval)

        if 'create temporal fimp lib':

            if 'create counter':

                sylva_lib.add_fimp(one_abb.abb_counter_actor.fimp)
                if os.path.isfile(one_abb.abb_counter_actor.fimp.name + '.vhdl') == False:
                    with open(one_abb.abb_counter_actor.fimp.name + '.vhdl', 'w') as fp:
                        fp.write(sflib.vhdl.counter(one_abb.abb_counter_actor))

            if 'create control fsms':
                for a in one_abb.abb_control_fsm_actors:
                    sylva_lib.add_fimp(a.fimp)
                    with open(a.name + '.vhdl', 'w') as fp:
                        fp.write(sflib.vhdl.fsm(a))

            if 'create fimp control':
                sylva_lib.add_fimp(one_abb.abb_fimp_control_actor.fimp)
                with open(one_abb.abb_fimp_control_actor.name + '.vhdl', 'w') as fp:
                    fp.write(sflib.vhdl.fimp_control(one_abb.abb_fimp_control_actor))

            if 'create input selector':
                if one_abb.fimp.actors[0].input_ports != []:
                    sylva_lib.add_fimp(one_abb.abb_input_selector_actor.fimp)
                    with open(one_abb.abb_input_selector_actor.name + '.vhdl', 'w') as fp:
                        fp.write(sflib.vhdl.input_selector(one_abb.abb_input_selector_actor))

            if 'create output selector':
                if one_abb.fimp.actors[0].output_ports != []:
                    sylva_lib.add_fimp(one_abb.abb_output_selector_actor.fimp)
                    with open(one_abb.abb_output_selector_actor.name + '.vhdl', 'w') as fp:
                        fp.write(sflib.vhdl.output_selector(one_abb.abb_output_selector_actor))

            if 'create buffer control':
                if one_abb.fimp.actors[0].output_ports != []:
                    sylva_lib.add_fimp(one_abb.abb_buffer_control_actor.fimp)
                    with open(one_abb.abb_buffer_control_actor.name + '.vhdl', 'w') as fp:
                        fp.write(sflib.vhdl.buffer_control(one_abb.abb_buffer_control_actor))

            if 'create output buffer':
                if one_abb.fimp.actors[0].output_ports != []:
                    for b in one_abb.abb_output_buffer_actors:
                        sylva_lib.add_fimp(b.fimp)
                        with open(b.name + '.vhdl', 'w') as fp:
                            fp.write(sflib.vhdl.output_buffer(b))

            if 'copy fimp from lib':
                fs = fimp_lib[one_abb.fimp.actors[0].base_actor.name]
                fs.input_ports['en'] = 'std_logic'
                sylva_lib.add_fimp_set(fs)
                create_empty_vhdl(one_abb.fimp.actors[0],
                                  libraries={'IEEE': ['std_logic_1164.all'], 'WORK': ['all']},
                                  fimp_count=one_abb.fimp.type + 1,
                                  additional_input_ports=[sdf.port(name='en', type=std_logic)])

        __ = abb_to_vhdl(one_abb, sample_interval, sylva_lib)

    top_actors = [one_abb.top_actor for one_abb in air]
    top_edges = []

    for one_abb in air:

        # for each actor that requires the output data from this actor
        # we need to connect the data_output_ports and the read_address_ports
        data_edges = [sdf.edge(
            src_actor=p.src_actor.abb.top_actor,
            src_port=p.src_port.top_port,
            dest_actor=one_abb.top_actor,
            dest_port=p.dest_port.top_port)
            for a in one_abb.fimp.actors
            for p in a.previous]

        top_edges += data_edges

        if len(data_edges) > 0:
            address_edges = [sdf.edge(
                src_actor=address_port.source_fimp.abb.top_actor,
                src_port=[p for p in address_port.source_fimp.abb.read_address_input_ports
                          if p.name == address_port.name][0],
                dest_actor=one_abb.top_actor,
                dest_port=address_port)
                for address_port in one_abb.abb_input_selector_actor.read_address_ports]
            top_edges += address_edges

    temp_lib = fimp.fimp_lib(architecture='VHDL', name='temporal lib for top module')
    for a in top_actors:
        temp_lib.add_fimp(a.fimp)

    hsdf_to_vhdl(top_actors, top_edges, temp_lib,
                 entity_name=top_module_name,
                 used_libraries={'IEEE': ['std_logic_1164.all'], 'WORK': ['all']},
                 output_file=top_module_name + '.vhdl')

    os.chdir(cwd)
