# coding: utf8

'''
SYLVA default FIMP library
'''

# import header files
if 'import dependencies' :

  import os, sys, math
  from jinja2 import Template as jinja2Template
  import sylva.glic.glic as glic

class template :

  def __init__(self, target = 'VHDL', attribute_keys = [], code_template = None):
    self.target = target
    self.attribute_keys = attribute_keys
    self.code_template = code_template

  def serialize(self) :
    return { 'target': self.target,
             'attribute_keys' : self.attribute_keys,
             'code_template' : self.code_template}

  @staticmethod
  def deserialize(json_dict) :
    return template(json_dict['target'], json_dict['attribute_keys'], json_dict['code_template'])

def integer_vhdl(max_value, min_value = 0) :
  if max_value < min_value :
    max_value, min_value = min_value, max_value
  return 'integer range {0} to {1}'.format(min_value, max_value)

if 'create VHDL code templates' :

  def create_fsm_vhdl_template() :

    attribute_keys = [
      'control',
      'state_count',
      'entity_name',
      'libraries',
      'output_type_string',
      'input_type_string' ]

    import sylva_default_fimp.vhdl.fsm

    fsm_code_template = sylva_default_fimp.vhdl.fsm.code_template

    return template('VHDL', attribute_keys, fsm_code_template)

if 'VHDL generation' :

  default_value_types = [
    ('std_logic_vector', "(others => '0')"),
    ('integer', 0) ]

  def default_value(name, default_value_types = default_value_types) :
    for d in default_value_types :
      if name.startswith(d[0]) :
        return d[1]
    return "'0'"

  import sylva_default_fimp.vhdl.counter
  def create_counter_FIMP_VHDL(actor):

    ''' Create counter FIMP in VHDL.

    This VHDL entity only depends on IEEE.std_logic_1164 package.
    '''

    attributes = {}
    attributes['libraries'] = {'IEEE' : ['std_logic_1164.all']}
    for a in dir(actor) :
      attributes[a] = getattr(actor, a)

    return jinja2Template(sylva_default_fimp.vhdl.counter.code_template).render(attributes)

  import sylva_default_fimp.vhdl.fsm
  def create_actor_control_FIMP_VHDL(actor, max_output = glic.IO):

    ''' Create actor control FSM FIMP in VHDL.

    This VHDL entity only depends on IEEE.std_logic_1164 package.
    '''
    control = actor.control
    attributes = {}
    attributes['libraries'] = {'IEEE' : ['std_logic_1164.all']}
    attributes['cycle_port'] = actor.input_ports[0]
    attributes['state_port'] = actor.output_ports[0]
    attributes['entity_name'] = actor.name
    attributes['control'] = control
    attributes['state_count'] = len(control.states)

    return jinja2Template(sylva_default_fimp.vhdl.fsm.code_template).render(attributes)

  import sylva_default_fimp.vhdl.input_selector
  def create_input_selector_FIMP_VHDL(actor,
    input_signal = glic.INPUT, io_signal = glic.IO,
    default_value_types = default_value_types,
    suffix = ''):

    def control_map_object() : pass

    ''' Create input selector FIMP in VHDL.

    This VHDL entity only depends on IEEE.std_logic_1164 package.
    '''

    attributes = {}
    attributes['libraries'] = {'IEEE' : ['std_logic_1164.all']}
    for a in dir(actor) :
      attributes[a] = getattr(actor, a)

    for o in actor.output_ports :
      o.default = default_value(o.type.name)

    attributes['INPUT'] = input_signal
    attributes['IO'] = io_signal

    return jinja2Template(sylva_default_fimp.vhdl.input_selector.code_template).render(attributes)

  import sylva_default_fimp.vhdl.output_selector
  def create_output_selector_FIMP_VHDL(actor,
    output_signal = glic.INPUT, io_signal = glic.IO,
    default_value_types = default_value_types):

    ''' Create output selector FIMP in VHDL.

    This VHDL entity only depends on IEEE.std_logic_1164 package.
    '''

    attributes = {}
    attributes['libraries'] = {'IEEE' : ['std_logic_1164.all']}
    attributes['entity_name'] = actor.name

    control_ports = [ (actor.input_ports[i].name, actor.input_ports[i].type.name)
                      for i in actor.control_port_range ]
    attributes['control_ports'] = control_ports
    control_count = len(control_ports)

    data_input_ports = []

    for i in actor.data_port_range :
      pname = actor.input_ports[i + control_count].name
      ptype = actor.input_ports[i + control_count].type.name
      pvalue = default_value(actor.input_ports[i + control_count].type.name)
      data_input_ports.append((pname, ptype, pvalue))

    attributes['data_input_ports'] = data_input_ports
    data_output_ports = [(p.name, p.type.name, default_value(p.type.name)) for p in actor.output_ports]
    attributes['data_output_ports'] = data_output_ports

    data_input_ports_count = len(data_input_ports)
    data_input_ports_range = xrange(data_input_ports_count)

    control_map = [ ( cp[0], [ (data_output_ports[j + i*data_input_ports_count], ip)
                               for j, ip in enumerate(data_input_ports) ])
                      for i, cp in enumerate(control_ports) ]
    attributes['control_map'] = control_map
    attributes['OUTPUT'] = output_signal
    attributes['IO'] = io_signal

    return jinja2Template(sylva_default_fimp.vhdl.output_selector.code_template).render(attributes)

  import sylva_default_fimp.vhdl.fimp_control
  def create_fimp_control_FIMP_VHDL(actor,
    idle_signal = glic.IDLE):

    ''' Create FIMP control FIMP in VHDL.

    This VHDL entity only depends on IEEE.std_logic_1164 package.
    '''

    attributes = {}
    attributes['libraries'] = {'IEEE' : ['std_logic_1164.all']}
    attributes['entity_name'] = actor.name

    attributes['input_ports'] = actor.input_ports
    attributes['en_port'] = actor.output_ports[0]
    attributes['IDLE'] = idle_signal

    return jinja2Template(sylva_default_fimp.vhdl.fimp_control.code_template).render(attributes)

  import sylva_default_fimp.vhdl.buffer_control
  def create_buffer_control_FIMP_VHDL(actor,
    output_signal = glic.OUTPUT, io_signal = glic.IO):

    ''' Create buffer control FIMP in VHDL.

    This VHDL entity only depends on IEEE.std_logic_1164 package.
    '''

    attributes = {}
    attributes['libraries'] = {'IEEE' : ['std_logic_1164.all']}
    attributes['entity_name'] = actor.name
    attributes['current_cycle_port'] = actor.current_cycle_port
    attributes['control_ports'] = \
      [ (control_port, actor.wr_ports[i]) for i, control_port in enumerate(actor.control_ports) ]
    # extra buffer is True
    if actor.address_ports == [] :
      attributes['address_ports'] = []
    else :
      if type(actor.address_ports[0]) is list :
        attributes['address_ports'] = [ p for ps in actor.address_ports for p in ps ]
      else :
        attributes['address_ports'] = actor.address_ports

    attributes['OUTPUT'] = output_signal
    attributes['IO'] = io_signal

    return jinja2Template(sylva_default_fimp.vhdl.buffer_control.code_template).render(attributes)

  import sylva_default_fimp.vhdl.output_buffer
  def create_output_buffer_FIMP_VHDL(actor):

    ''' Create output buffer FIMP in VHDL.

    This VHDL entity only depends on IEEE.std_logic_1164 package.
    '''

    attributes = {}
    attributes['libraries'] = {'IEEE' : ['std_logic_1164.all']}
    attributes['entity_name'] = actor.name
    attributes['buffer_size'] = actor.buffer_size
    attributes['wr_port'] = actor.wr_port
    attributes['write_address_port'] = actor.write_address_port
    attributes['read_address_port'] = actor.read_address_port
    attributes['data_input_port'] = actor.data_input_port
    attributes['data_output_port'] = actor.data_output_port
    attributes['default_data_output'] = default_value(actor.data_input_port.type.name)

    return jinja2Template(sylva_default_fimp.vhdl.output_buffer.code_template).render(attributes)

class method_collection : pass

vhdl = method_collection()
vhdl.fsm = create_actor_control_FIMP_VHDL
vhdl.counter = create_counter_FIMP_VHDL
vhdl.input_selector = create_input_selector_FIMP_VHDL
vhdl.output_selector = create_output_selector_FIMP_VHDL
vhdl.fimp_control = create_fimp_control_FIMP_VHDL
vhdl.buffer_control = create_buffer_control_FIMP_VHDL
vhdl.output_buffer = create_output_buffer_FIMP_VHDL
