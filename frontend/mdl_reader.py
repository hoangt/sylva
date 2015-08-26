from pyparsing import OneOrMore, Group, nestedExpr, quotedString, Forward, Word, Keyword, alphanums
import copy

use_white_list = True

property_list = [
  'BlockType',
  'SourceBlock',
  'System',
  'Block',
  'Ports',
  'Port',
  'PortNumber',
  'SampleTime',
  'SignalType',
  'SamplingMode',
  'Inputs',
  'Operator',
  'OutDataTypeStr',
  'Name',
  'SID',
  'SrcBlock',
  'SrcPort',
  'DstBlock',
  'DstPort']

if 'hide the details' :

  class simulink_model :

    def __str__(self) :
      return 'simulink Model: {name}'.format(name = self.name)

  class simulink_system :

    def __str__(self) :
      return 'simulink system: {name}'.format(name = self.name)

  level = 0
  ParsedModel = simulink_model()

  def get_string(one_string) :
    if isinstance(one_string, str) :
      if one_string.startswith('"') :
        one_string = one_string[1:-1]
      return one_string
    else :
      return 'ERROR, value is not string but %s'\
             % one_string

  def get_list(one_list) :
    if isinstance(one_list, list) :
      if len(one_list) == 1 :
        return [ get_string(one_list[0]) ]
      else :
        return [ item for item in one_list if item != ',' ]
      return one_list
    else :
      return 'ERROR, value is not list but %s'\
             % one_list

  def get_block(one_block) :
    if isinstance(one_block, list) :
      result = {}
      for item in one_block :
        if not use_white_list or (item[0] in property_list) :
          result[ item[0] ] = get_value(item[1])
      return result
    else :
      return 'ERROR, value is not list but %s'\
              % one_block

  def get_value(one_value) :
    if isinstance(one_value, str) :
      return get_string(one_value)
    elif isinstance(one_value, list) :
      if ',' in one_value :
        return get_list(one_value)
      elif len(one_value) == 1 :
        return get_value(one_value[0])
      else :
        return get_block(one_value)
    else :
      return 'ERROR, value is not string or list but %s'\
              % one_value

  def get_model_name(value) :
    return get_value(value)

  def get_block_defaults(block_defaults) :

    return [ get_one_block(block)
             for block in block_defaults ]

  def get_one_block(block) :
    return [ (item[0], get_value(item[1]))
             for item in block[1]
               if not use_white_list or (item[0] in property_list) ]

  def get_system_block(block) :
    properties = {}
    for item in block :
      if isinstance(item[0], str) and (not use_white_list or (item[0] in property_list)) :
        if item[0] == 'System' :
          properties[item[0]] = get_system(item[1])
        else :
          properties[item[0]] = get_value(item[1])
    return properties

  def get_system(value):
    system = simulink_system()
    system.name = get_value(value[0][1])
    system.blocks = [ get_system_block(item[1])
                      for item in value
                        if item[0] == 'Block' ]
    system.lines = [ get_system_block(item[1])
                      for item in value
                        if item[0] == 'Line' ]
    return system

  def processNode(tokens):

    key, value = tokens[0].asList()
    # tokens[0] is for compensates the one additional [] level.

    global level
    global ParsedModel

    # read ParsedModel name
    if level == 0 and key == 'Name' :

      ParsedModel.name = get_model_name(value)
      level += 1

    elif level == 1 :

      # read block default parameters
      if key == 'BlockParameterDefaults' :
        ParsedModel.block_defaults = get_block_defaults(value)

      if key == 'System' :
        ParsedModel.system = get_system(value)

  key_value = Forward()

  # key
  key = Word (alphanums + '$+-_*\\.')

  # value
  value = Forward()

  off = Keyword( 'off' )
  on = Keyword( 'on' )
  string_value = quotedString
  other_value = Word (alphanums + '$+-_*\\.')
  normal_value = on | off | string_value | other_value

  block_block = nestedExpr('{', '}', content = key_value)

  list_block = nestedExpr('[', ']', content = value)

  value << (normal_value | block_block | list_block | ';' | ',')

  key_value << Group(key + value).setParseAction(processNode)

  parser = OneOrMore(key_value)

  def read_type_count(type_count) :
    type_count = type_count.lower()

    token_type = 'No type'
    token_size = 1
    token_count = 1

    port_properties = type_count.split(',')

    for p in port_properties :
      key, value = p.split('=')
      key = key.strip()
      value = value.strip()
      if key == 'type' :
        token_type = value
      elif key == 'size' :
        token_size = int(value)
      elif key == 'count' :
        token_count = int(value)
    return token_type, token_size, token_count

  def record_port(block, port_index, port_name,
    token_type, token_size, token_count, io = 'in') :

    io += 'put_ports'

    block[io][port_index] = {}
    block[io][port_index]['name'] = port_name
    block[io][port_index]['token type'] = token_type
    block[io][port_index]['token size'] = token_size
    block[io][port_index]['token count'] = token_count

    return block, port_index + 1

def read_mdl_lib_as_dict(mdl_path) :

  global ParsedModel

  p = parser.parseFile(mdl_path, True)

  if p[0][0] != 'Library' :
    print 'Input file is NOT a library (.mdl) but a %s' % p[0][0]

  lib = {}

  inport_index = 0
  outport_index = 1

  for func in ParsedModel.system.blocks :
    name = '%s/%s' % (ParsedModel.system.name, func['Name'])
    lib[ name ] = {}
    lib[ name ]['input_ports'] = {}
    lib[ name ]['output_ports'] = {}
    system = func['System']

    inport_index = 0
    outport_index = 0

    for port in system.blocks :
      if port['BlockType'] == 'Inport' :
        port_name, type_count = port['Name'].split(':')
        port_name.replace(' ', '')

        token_type, token_size, token_count \
        = read_type_count(type_count)

        lib[ name ], inport_index \
        = record_port(lib[ name ], inport_index,
            port_name, token_type, token_size, token_count,
            io = 'in')

      elif port['BlockType'] == 'Outport' :

        port_name, type_count = port['Name'].split(':')
        port_name.replace(' ', '')

        token_type, token_size, token_count \
        = read_type_count(type_count)

        lib[ name ], outport_index \
        = record_port(lib[ name ], outport_index,
            port_name, token_type, token_size, token_count,
            io = 'out')

  return lib

def read_mdl_model(mdl_path) :

  global ParsedModel
  p = parser.parseFile(mdl_path, True)

  if p[0][0] != 'Model' :
    print 'Input file is NOT a ParsedModel (.mdl) but a %s' % p[0][0]

  return copy.deepcopy(ParsedModel)
