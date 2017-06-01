

__author__ = 'Shuo Li <contact@shuol.li>'
__version__ = '2014-06-12-11:47'

'''Functions to generate VHDL files
'''

import os
import copy
import warnings

from jinja2 import Template

from sylva.code_generation import vhdl_templates, vhdl_generation, mit_license

import os
import sys
import random
import time
from time import localtime, strftime

from sylva.ortools.constraint_solver import pywrapcp

from sylva.base import sdf, fimp, sdf_schedule

from sylva.base.cgra import cgra
from sylva.base.sdf_to_hsdf import sdf_to_hsdf

def get_signal_name(fimp, port):
    return '%s_%s_%s' % (fimp.base_actor.name, fimp.global_index, port.name)

def create_components(one_edge, components):
    '''Create component declarations if necessary.

      components
        dict of arrays
        keys are the function names (entity names)
        values are the fimp instances used for the function
        e.g. {'fft' : [ fft_0, fft_1, fft_2 ]}
    '''

    src_entity_name = one_edge.src_actor.base_actor.name
    dest_entity_name = one_edge.dest_actor.base_actor.name

    src_fimp = one_edge.src_actor.fimp
    dest_fimp = one_edge.dest_actor.fimp

    src_fimp_exists = False
    dest_fimp_exists = False

    if src_entity_name not in components.keys():
        components[src_entity_name] = [src_fimp]
    else:
        if src_fimp not in components[src_entity_name]:
            components[src_entity_name].append(src_fimp)
        else:
            src_fimp_exists = True

    if dest_entity_name not in components.keys():
        components[dest_entity_name] = [dest_fimp]
    else:
        if dest_fimp not in components[dest_entity_name]:
            components[dest_entity_name].append(dest_fimp)
        else:
            dest_fimp_exists = True

    return src_fimp_exists, dest_fimp_exists

def create_signals(one_edge, src_fimp_exists, dest_fimp_exists, signals):
    '''create signals

      signal name
        string
        <function name>_<fimp index>_<port name>
    '''

    src_fimp = one_edge.src_actor.fimp
    dest_fimp = one_edge.dest_actor.fimp

    if src_fimp_exists == False:
        for p in src_fimp.base_actor.input_ports \
                + src_fimp.base_actor.output_ports:
            signal_name = get_signal_name(src_fimp, p)
            signals[signal_name] = p.type.name

    if dest_fimp_exists == False:
        for p in dest_fimp.base_actor.input_ports \
                + dest_fimp.base_actor.output_ports:
            signal_name = get_signal_name(dest_fimp, p)
            signals[signal_name] = p.type.name

def create_connection(one_edge, connections):
    '''Create signal connections for one edge
    '''

    # when size is different,
    # we need to split the source port or the destination port

    # if the source port is wider: N to 1
    def n_to_one(src_port, dest_port, n, src_signal_name, dest_signal_name):

        # destination is also std_logic_vector
        if dest_port.type.name.lower().startswith('std_logic_vector'):
            return [{'dest': dest_signal_name,
                     'src': src_signal_name +
                     '( {i} * {width} - 1 downto 0)'.format(i=i, width=dest_port.type.size)}
                    for i in range(n)]
        # destination is std_logic
        else:
            return [{'dest': dest_signal_name,
                     'src': src_signal_name + '({i})'.format(i=i)}
                    for i in range(n)]

    # if the destination port is wider: 1 to N
    def one_to_n(src_port, dest_port, n, src_signal_name, dest_signal_name):

        # source is also std_logic_vector
        if src_port.type.name.lower().startswith('std_logic_vector'):
            return [{'dest': dest_signal_name +
                     '( {i} * {width} - 1 downto 0)'.format(i=i, width=src_port.type.size),
                     'src': src_signal_name}
                    for i in range(n)]
        # source is std_logic
        else:
            return [{'dest': dest_signal_name + '({i})'.format(i=i),
                     'src': src_signal_name}
                    for i in range(n)]

    src_fimp = one_edge.src_actor.fimp
    dest_fimp = one_edge.dest_actor.fimp

    src_port = one_edge.src_port
    dest_port = one_edge.dest_port

    src_signal_name = get_signal_name(src_fimp, src_port)
    dest_signal_name = get_signal_name(dest_fimp, dest_port)

    if src_port.type.size == dest_port.type.size:
        connections.append({'dest': dest_signal_name, 'src': src_signal_name})
    elif src_port.type.size > dest_port.type.size:
        connections += n_to_one(src_port, dest_port, int(src_port.type.size / dest_port.type.size), src_signal_name, dest_signal_name)
    else:
        connections += one_to_n(src_port, dest_port, int(dest_port.type.size / src_port.type.size), src_signal_name, dest_signal_name)

def connect_one_edge(one_edge, components, signals, connections):
    '''Generate necessary parts for connecting one sdf edge

      one_edge
        sdf.edge

      current_components
        current used components
        dict of arrays
        outer keys are the entity names
        inner keys are fimp instances
        e.g. { 'fft_64' : [ fft_0, fft_1 ] }

      signals
        current used components
        dict of strings
        keys are signal names
        values are signal types
        e.g. { 'counter_output' : 'integer range 0 to 3' }

      connections
        array of dicts, keys = [ 'src', 'dest' ], all strings (signal names)
        e.g. [ { 'src': 'counter', 'dest' : 'fsm_state_input' } ]
    '''

    src_fimp_exists, dest_fimp_exists = create_components(
        one_edge, components)

    create_signals(one_edge, src_fimp_exists, dest_fimp_exists, signals)

    create_connection(one_edge, connections)

def connect_global_inputs(nodes, global_inputs, exceptions={}):
    '''Connect global input ports like clock or reset

      nodes
        array of sdf nodes

      global_inputs
        dict of strings
        {port name : port type}

      exceptions
        { fimp_index : [ port names ] }
    '''

    for n in nodes:
        for p in n.input_ports:
            connect = False

            if n.fimp.index not in exceptions.keys():
                connect = True
            else:
                if p.name not in exceptions[n.fimp.index]:
                    connect = True

            if (connect == True) and (p.name in global_inputs):
                signal_name = get_signal_name(n.fimp, p)
                connections.append({'dest': signal_name, 'src': p.name})

def create_port_connections(port_connections, connections,
                            direction='input'):
    '''Create port to signal connections

      port_connections
        { 'data_in_re' : [ {'fimp' : fft_0, 'port' : data_in_re} ] }

      connections
        current established connections

      direction
        'input' or 'output'
    '''

    for top_port_name, fimp_ports in port_connections:
        if direction == 'input':
            for fimp_port in fimp_ports:
                fimp = fimp_port['fimp']
                port = fimp_port['port']
                dest_signal_name = '%s_%s_%s' \
                    % (fimp.name, fimp.index, port.name)

                connections.append({'dest': dest_signal_name, 'src': top_port_name})

        elif direction == 'output':
            for fimp_port in fimp_ports:
                fimp = fimp_port['fimp']
                port = fimp_port['port']
                src_signal_name = '%s_%s_%s' \
                    % (fimp.name, fimp.index, port.name)

                connections.append({'dest': top_port_name, 'src': src_signal_name})

def create_top_connections(input_actor_and_ports, output_actor_and_ports, connections):
    '''Create top level connections (e.g. clk or nrst) for the entire HSDF graph

      input_actor_and_ports
        e.g. [ ActorAndPort object ]

      output_actor_and_ports
        e.g. [ ActorAndPort object ]

      connections
        current established connections
    '''
    for iap in input_actor_and_ports:
        # port name format: <function name>_<fimp index>_<port name>
        func_name = iap.actor.base_actor.name
        fimp_index = 0
        port_name = iap.port.name
        signal_name = '%s_%s_%s' % (func_name, fimp_index, port_name)
        connections.append({'dest': signal_name, 'src': port_name})

    for oap in output_actor_and_ports:
        # port name format: <function name>_<fimp index>_<port name>
        func_name = oap.actor.base_actor.name
        fimp_index = 0
        port_name = oap.port.name
        signal_name = '%s_%s_%s' % (func_name, fimp_index, port_name)
        connections.append({'src': signal_name, 'dest': port_name})

def hsdf_to_vhdl(sdf_actors, sdf_edges, fimp_lib,
                 output_file='result_vhdl.vhdl',
                 entity_name='top',
                 global_generics={},
                 local_generics={},
                 input_actor_and_ports=[],
                 output_actor_and_ports=[],
                 default_input_ports={'clk': 'std_logic', 'nrst': 'std_logic'},
                 input_connections={},
                 output_ports={},
                 output_connections={},
                 global_input_connections=[],
                 global_output_connections=[],
                 used_libraries={},
                 custom_header='',
                 license_header=mit_license.vhdl()):
    ''' Generate vhdl design unit based on an HSDF graph.

      input_connections/output_connections
        { 'data_in' : [(fft_0, 'data_in_re'), (fir_0, 'data_in_re')]}

      global_input_connections/global_output_connections
        ['clk', 'nrst']
    '''

    interface = vhdl_generation.interface(entity_name=entity_name,
                                          input_ports=[ap.port for ap in input_actor_and_ports],
                                          output_ports=[ap.port for ap in output_actor_and_ports],
                                          libraries=used_libraries,
                                          generics=global_generics,
                                          header=custom_header,
                                          license_header=license_header,
                                          default_input_ports=default_input_ports)

    components = {}
    signals = {}
    connections = []

    for edge in sdf_edges:
        connect_one_edge(edge, components, signals, connections)

    create_top_connections(input_actor_and_ports, output_actor_and_ports, connections)

    create_port_connections(input_connections, connections, 'input')
    create_port_connections(output_connections, connections, 'output')

    fimps = []
    fimps.append(vhdl_generation.architecture(
        architecture_name='fimp_0',
        entity_name=entity_name,
        components=components,
        fimp_lib=fimp_lib,
        signals=signals,
        connections=connections))

    return vhdl_generation.vhdl_file(interface, fimps, output_file=output_file)

def create_empty_vhdl(sdf_actor, output_file=None, libraries={}, fimp_count=1,
                      additional_input_ports=[]):

    if output_file == None:
        output_file = sdf_actor.name + '.vhdl'

    interface = vhdl_generation.interface(entity_name=sdf_actor.name,
                                          libraries=libraries,
                                          input_ports=dict([(p.name, p.type.name) for p in (sdf_actor.input_ports + additional_input_ports)]),
                                          output_ports=dict([(p.name, p.type.name) for p in sdf_actor.output_ports]))

    architectures = [vhdl_generation.architecture(entity_name=sdf_actor.name,
                                                  architecture_name='fimp_{0}'.format(i))
                     for i in xrange(fimp_count)]

    return vhdl_generation.vhdl_file(interface, architectures, output_file)
