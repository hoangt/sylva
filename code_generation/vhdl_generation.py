# coding: utf-8

'''Functions to generate VHDL files
'''

import os, sys, copy, warnings, random, time

from jinja2 import Template
from time import localtime, strftime

from sylva.base import sdf, fimp, sdf_schedule
from sylva.base.cgra import cgra
from sylva.base.sdf_to_hsdf import sdf_to_hsdf
from sylva.misc.plot import schedule_plot, fimp_execution_model_plot

from sylva.base.sdf import port
from sylva.code_generation import mit_license, vhdl_templates, vhdl_constants

def port_list_to_dict(port_list) :
  return dict([(p.name, p.type.name) for p in port_list])

pl2pd = port_list_to_dict

std_logic = sdf.data_type(name = 'std_logic', size = 1)

default_input_ports_list = [
  sdf.port(name ='clk', type = std_logic),
  sdf.port(name ='nrst', type = std_logic) ]

default_input_ports = pl2pd(default_input_ports_list)


'>> IMPORTANT <<'
'All empty parts will be empty string/array, not None.'

# array
def format_signals (signals = []) :
  '''Generate signal declaration part

    signals: used signals in region
      dict of string,
      e.g. { counter' : 'integer range 0 to 3' }
  '''

  result = []

  if len(signals) > 0 :
    for s_name, s_type in signals.items() :
      result.append('signal %s : %s;' % (s_name, s_type))
  return result

# array
def format_connections (connections = []) :
  '''Generate connection part

    connections
      array of dicts, keys = ['src', 'dest'], all strings (signal names)
      e.g. [ { 'src': 'counter', 'dest' : 'fsm_state_input' } ]
  '''
  result = []

  if len(connections) > 0 :
    for c in connections :
      result.append('%s <= %s;' % (c['dest'], c['src']))
  return result

# array
def format_generics (generics = vhdl_constants.global_generics) :
  '''Generate generic part

    generics:
      dict of dicts
      outter keys are the generic names
      inner keys = ['type', 'value'], all strings/integers
      e.g. { 'data_width' : { 'type': 'integer', 'value' : 8 } }
  '''

  result = []

  if len(generics.keys()) > 0 :
    for g, v in generics.items():
      result.append('%s : %s := %s;' % (g, v['type'], v['value']))

    result[-1] = result[-1][:-1]

  return result

# array
def format_ports (input_ports, output_ports) :

  '''Generate port part

    input_ports
      dict of strings
      keys are the input port name
      e.g. { 'clk' : 'std_logic' }

    output_ports
      dict of strings
      keys are the input port name
      e.g. { 'counter_output' : 'integer range 0 to 3' }
  '''

  result = []

  for k, v in input_ports.items() :
    result.append('%s : in %s;' % ( k, v ))

  for k, v in output_ports.items() :
    result.append('%s : out %s;' % ( k, v ))

  if len(result) > 0 :
    result[-1] = result[-1][:-1]

  return result

# string
def format_generic_map (generics,
  global_generics = {}, local_generics = {}) :

  '''Generate generic map part

    generics
      dict of dicts
      outter keys are the generic names
      inner keys = ['type', 'value'], all strings/integers
      e.g. { 'data_width' : { 'type': 'integer', 'value' : 8 } }

    global_generics
      dict of dicts
      outter keys are the generic names
      inner keys = ['type', 'value'], all strings/integers
      e.g. { 'data_width' : { 'type': 'integer', 'value' : 8 } }

    local_generics
      dict of dicts
      outter keys are the generic names
      inner keys = ['type', 'value'], all strings/integers
      e.g. { 'data_width' : { 'type': 'integer', 'value' : 8 } }
  '''

  result = ''

  if len(generics.keys()) > 0 :

    result = 'generic map ('

    for g_name, g_type_value in generics.items() :

      g_type = g_type_value['type']
      g_value = g_type_value['value']

      is_local = False
      if g_name in local_generics.keys() :
        if g_type == local_generics[g_name]['type'] :
          g_value = local_generics[g_name]['value']
          is_local = True
        else :
          errmsg = 'Local generics has wrong type for '
          errmsg += '\'%s\'. ' % g_name
          errmsg += 'Type should be %s ' % g_type
          errmsg += 'instead of %s.' % local_generics[g_name]['type']
          raise Exception(errmsg)

      is_global = False
      if is_local == False :
        if g_name in global_generics.keys() :
          if g_type == global_generics[g_name]['type'] :
            g_value = global_generics[g_name]['value']
            is_global = True

      if is_global == False :
        warnmsg  = 'No value is provided for %s (%s). ' % (g_name, g_type)
        warnmsg += 'Default value %s will be used.' % g_value

        warnings.warn(warnmsg)

      result += '%s => %s, ' % ( g_name, g_value )

    result = result[:-2] + ')'

  return result

# string
def format_port_map (input_ports, output_ports, function_name, fimp_index,
  default_input_ports = {'clk' : 'std_logic', 'nrst' : 'std_logic'}) :
  '''Generate port map part

   input_ports
      dict of strings
      keys are the input port name
      e.g. { 'clk' : 'std_logic' }

    output_ports
      dict of strings
      keys are the input port name
      e.g. { 'counter_output' : 'integer range 0 to 3' }

    function_name
      string

    fimp_index
      unique index among all fimps used in the system
      integer
  '''

  result = ''

  if len(input_ports.keys()) + len(output_ports.keys()) > 0 :
    prefix = '%s_%s' % (function_name, fimp_index)
    result = 'port map ('
    for p in input_ports.keys() :
      result += p + ' => %s_%s' % (prefix, p)
      result += ', '
    for p in default_input_ports.keys() :
      result += p + ' => ' + p
      result += ', '
    for p in output_ports.keys() :
      result += p + ' => %s_%s' % (prefix, p)
      result += ', '
    result = result[:-2] + ')'

  return result

# array
def format_design_units (components, fimp_lib,
  global_generics = {}, local_generics = {}) :
  '''Generate design unit instantiation part

    components
      used components
      dict of arrays
      outter keys are the entity names
      inner keys are fimp instances
      e.g. { 'fft_64' : [ fft_0, fft_1 ] }

    fimp_lib
      dict of dicts
      outter keys are the function names (entity names)
      inner keys are attributes (['generics', 'input_ports', 'output_ports'])
      e.g. { 'fft_64' :
             [ 'generics' :
               { 'data_width' :
                 { 'type' : 'integer', 'value' : 3 }
               },
               'input_ports' :
               { 're_in' : 'integer range 0 to 255,
                 'im_in' : 'integer range 0 to 255
               },
               'output_ports' :
               { 're_out' : 'integer range 0 to 255,
                 'im_out' : 'integer range 0 to 255
               }
             ]
           }

    function_name
      string

    fimp_index
      unique index among all fimps used in the system
      integer

    global_generics
      dict of dicts
      outter keys are the generic names
      inner keys = ['type', 'value'], all strings/integers
      e.g. { 'data_width' : { 'type': 'integer', 'value' : 8 } }

    local_generics
      dict of dicts
      most outter keys are the entity names
      second outter keys are the fimp index
      inner parts are the same as global_generics
  '''

  result = []
  for entity_name, fimps in components.items() :
    default_generics = fimp_lib[entity_name].generics
    input_ports = fimp_lib[entity_name].input_ports
    output_ports = fimp_lib[entity_name].output_ports

    if entity_name in local_generics :
      all_fimp_local_generics = local_generics[entity_name]
    else :
      all_fimp_local_generics = {}

    for one_fimp in fimps :
      fimp_index = one_fimp.global_index
      if fimp_index in all_fimp_local_generics.keys() :
        fimp_local_generics = all_fimp_local_generics[fimp_index]
      else :
        fimp_local_generics = {}

      generic_map = format_generic_map(
        generics = default_generics,
        global_generics = global_generics,
        local_generics = fimp_local_generics )

      port_map = format_port_map(
        input_ports = input_ports,
        output_ports = output_ports,
        function_name = entity_name,
        fimp_index = fimp_index )

      design_unit = '%s_%s: %s' \
        % ( entity_name,
            fimp_index,
            entity_name)

      result.append(design_unit)

      if generic_map != '' :
        result.append('  ' + generic_map)

      if port_map != '' :
        result.append('  ' + port_map)

      result[-1] += ';'

  return result

def merge_dict(dictA, dictB) :
  return dict(dictA.items() + dictB.items())

# array
def format_components (components, fimp_lib = {},
  template_string = vhdl_templates.component,
  default_input_ports = {'clk' : 'std_logic', 'nrst' : 'std_logic'}) :

  '''Generate component declaration part

    components
      used components
      dict of arrays
      outter keys are the entity names
      inner keys are fimp instances
      e.g. { 'fft_64' : [ fft_0, fft_1 ] }

    fimp_lib
      dict of dicts
      outter keys are the function names (entity names)
      inner keys are attributes (['generics', 'input_ports', 'output_ports'])
      e.g. { 'fft_64' :
             [ 'generics' :
               { 'data_width' :
                 { 'type' : 'integer', 'value' : 3 }
               },
               'input_ports' :
               { 're_in' : 'integer range 0 to 255,
                 'im_in' : 'integer range 0 to 255
               },
               'output_ports' :
               { 're_out' : 'integer range 0 to 255,
                 'im_out' : 'integer range 0 to 255
               }
             ]
           }

    template_string
      jinja2 template
  '''

  result = []
  template = Template(template_string)

  for entity_name, fimps in components.items() :
    default_generics = fimp_lib[entity_name].generics
    input_ports = merge_dict(default_input_ports, fimp_lib[entity_name].input_ports)
    output_ports = fimp_lib[entity_name].output_ports
    ports = format_ports(input_ports, output_ports)
    result.append(
      template.render(
        entity_name = entity_name,
        generics = format_generics(default_generics),
        ports = format_ports(input_ports, output_ports)) )

    for one_fimp in fimps :
      fimp_index = one_fimp.global_index
      fimp_type = one_fimp.type
      cfg = '  for %s_%s: %s use entity work.%s(fimp_%s);' % \
            ( entity_name, fimp_index, entity_name, entity_name, fimp_type )
      result.append(cfg)

  return result

# string
def interface( entity_name = 'no_name',
  input_ports = {},
  output_ports = {},
  libraries = {},
  generics = {},
  header = '',
  license_header = mit_license.vhdl(),
  template_string = vhdl_templates.interface,
  default_input_ports = default_input_ports) :

  template = Template(template_string)

  if type(input_ports) is list :
    input_ports_dict = pl2pd(input_ports)
  else :
    input_ports_dict = input_ports

  if type(output_ports) is list :
    output_ports_dict = pl2pd(output_ports)
  else :
    output_ports_dict = output_ports

  return template.render(
    license_header = license_header,
    header = header,
    entity_name = entity_name,
    libraries = libraries,
    generics = format_generics(generics),
    ports = format_ports( merge_dict( default_input_ports, input_ports_dict ),
      output_ports_dict ))

# string
def architecture( architecture_name = 'fimp_0',
  entity_name = 'no_name',
  signals = {},
  components = {}, fimp_lib = {},
  connections = [],
  template_string = vhdl_templates.architecture) :

  template = Template(template_string)
  return template.render( architecture_name = architecture_name,
                     entity_name = entity_name,
                     components = format_components(components, fimp_lib),
                     signals = format_signals(signals),
                     connections = format_connections(connections),
                     design_units = format_design_units(components, fimp_lib))

# 'Success' or None
def vhdl_file(interface, architectures = [],
  output_file = 'result.vhdl') :

  output_file_pointer = open(output_file, 'w')

  output_file_pointer.write( interface );
  output_file_pointer.write( '\n' );
  output_file_pointer.write( '\n' );

  for fimp in architectures :
    output_file_pointer.write( fimp );
    output_file_pointer.write( '\n' );
    output_file_pointer.write( '\n' );

  output_file_pointer.close()
  return 'Generating VHDL file {name} is successful.'.format(name = output_file)
