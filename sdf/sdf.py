# coding: utf-8

'''Synchronous Data Flow (SDF) graph model'''

import json
from math import ceil as float_ceil, log as general_log

ceil = lambda x : int(float_ceil(x))
log2 = lambda x : general_log(x, 2)

class SDFBase(object) :

  '''Base class for SDF graph in SYLVA'''

  def __str__(self) :
    return str(self.dict_value)

  def __repr__(self) :
    return self.__str__()

  @property
  def dict_value(self) :
    return {}

  @property
  def clone(self) :
    return None

  @staticmethod
  def load_from_dict(dict_value) :
    return None

class DataType(SDFBase) :

  '''
    Data type
  '''

  def __init__(self, name = 'integer range 0 to 7', size = 3) :

    '''
      name : data type name, e.g. integer range 0 to 7
      size : data type size, e.g. integer range 0 to 7 will have size of 3
    '''

    self.name = name
    self.size = size

  @property
  def dict_value(self) :
    return { 'name' : self.name, 'size' : self.size }

  @staticmethod
  def load_from_dict(dict_value) :
    return DataType( name = dict_value['name'], size = dict_value['size'] )

  @staticmethod
  def get_std_logic() :
    return DataType('std_logic', 1)

  @staticmethod
  def get_std_logic_vector(size, downto = True) :
    return DataType('std_logic', 1)

  @staticmethod
  def get_integer(max_value, min_value = None) :

    '''VHDL integer'''

    min_value = min_value or 0
    name = 'integer {0} to {1}'.format(min_value, max_value)
    size = ceil(log2(abs(max_value - min_value + 1)))

    return DataType(name, size)

class SDFPort(SDFBase) :

  '''
    IO port class for an actor
    --------------------------

    The port is either input or output.
    The IO direction (input or output) is not defined in this class.
    A port emits or receives one data token per clock cycle.

    1. name:  string, port name
    2. index: integer, port index in either input port list or output port list
    3. data_token_type: DataType, data token type of this port.
      The width of the port is defined by `type`.
    4. count: integer, number of data tokens to be transferred via this port
  '''

  def __init__(self, name, index = -1,
               data_token_type = DataType(), count = 1, actor = None) :

    self.name = name
    self.index = index
    self.data_token_type = data_token_type
    self.count = count
    self.actor = actor

  @property
  def dict_value(self) :
    return { 'name' : self.name, 'index' : self.index,
             'data_token_type' : self.data_token_type.dict_value,
             'count' : self.count }

  @property
  def clone(self) :
    return SDFPort(self.name,
                   self.index,
                   self.data_token_type,
                   self.count)

  @staticmethod
  def load_from_dict(dict_value) :
    return SDFPort(str(dict_value['name']), int(dict_value['index']),
                   DataType.load_from_dict(dict_value['data_token_type']),
                   int(dict_value['count']))

  @classmethod
  def load_from_dict_with_actors(cls, dict_value, actors = []) :
    result = cls.load_from_dict(dict_value)

    if 'actor' in dict_value.keys() :
      actor_index = int(dict_value['actor'])
      result.actor = actors[actor_index]

    return result

class SDFEdge(SDFBase) :

  '''Communication Edge'''

  def __init__(self, src_actor, src_port, dest_actor, dest_port) :

    self.src_actor = src_actor
    self.src_port = src_port

    self.dest_actor = dest_actor
    self.dest_port = dest_port

    self.src_actor.outgoing_edges.append(self)
    self.dest_actor.incoming_edges.append(self)

  @property
  def clone(self) :
    return SDFEdge( self.src_actor,  self.src_port.clone,
                    self.dest_actor, self.dest_port.clone )

  @property
  def dict_value(self) :
    return { 'src_actor'  : self.src_actor.index,
             'dest_actor' : self.dest_actor.index,
             'src_port'   : self.src_port.index,
             'dest_port'  : self.dest_port.index }

  @property
  def dict_value_with_objects(self) :
    return { 'src_actor'  : self.src_actor,
             'dest_actor' : self.dest_actor,
             'src_port'   : self.src_port,
             'dest_port'  : self.dest_port }

  @staticmethod
  def load_index_from_dict(dict_value) :
    src_actor_index  = int(dict_value['src_actor'])
    dest_actor_index = int(dict_value['dest_actor'])
    src_port_index   = int(dict_value['src_port'])
    dest_port_index  = int(dict_value['dest_port'])
    return src_actor_index, src_port_index, dest_actor_index, dest_port_index

  @classmethod
  def load_from_dict(cls, dict_value, actors) :
    src_actor_index, src_port_index, dest_actor_index, dest_port_index \
    = cls.load_index_from_dict(dict_value)

    src_actor = actors[src_actor_index]
    src_port = src_actor.output_ports[src_port_index]

    dest_actor = actors[dest_actor_index]
    dest_port = dest_actor.input_ports[dest_port_index]

    return SDFEdge(src_actor, src_port, dest_actor, dest_port)

class SDFActor(SDFBase) :

  '''
    SDF actor class
    ---------------

    An actor is assumed to be within an SDF graph.
    An actor name is the identification of its functionality.
  '''

  def __init__(self, name, index = -1, input_ports = [], output_ports = [],
    base_actor = None, outgoing_edges = None, incoming_edges = None) :

    self.name = name
    self.index = index

    self.input_ports = input_ports
    self.output_ports = output_ports

    self.base_actor = base_actor
    self.outgoing_edges = outgoing_edges or []
    self.incoming_edges = incoming_edges or []

  @property
  def clone(self) :
    return SDFActor( self.name, self.index,
                     self.input_ports, self.output_ports,
                     self.base_actor)

  @property
  def dict_value_no_base_actor(self) :

    '''
      Construct a dict object based on the SDF actor object.
      self.base_actor is ignored.
    '''

    return { 'name' : self.name, 'index' : self.index,
             'input_ports'  : [ p.dict_value for p in self.input_ports ],
             'output_ports' : [ p.dict_value for p in self.output_ports ] }

  @property
  def dict_value(self) :

    '''
      Construct a dict object based on the SDF actor object.
      If self.base_actor is not None,
      the value of key base_actor will be the index of the base actor.
    '''

    result = self.dict_value_no_base_actor
    if self.base_actor :
      result['base_actor'] = self.base_actor.index
    return result

  @staticmethod
  def load_from_dict(dict_value) :
    name  = str(dict_value['name'])
    index = int(dict_value['index'])
    input_ports   = [ SDFPort.load_from_dict(p)
                      for p in dict_value['input_ports'] ]
    output_ports  = [ SDFPort.load_from_dict(p)
                      for p in dict_value['output_ports'] ]
    return SDFActor(name, index, input_ports, output_ports)

class SDFGraph(SDFBase) :

  def __init__(self, actors, edges = None) :

    self.actors = actors
    self.edges = edges or [ e for a in actors for e in a.outgoing_edges ]

  @property
  def dict_value(self) :
    return { 'actors' : [ a.dict_value for a in self.actors ],
             'edges' : [ e.dict_value for e in self.edges ] }

  @property
  def clone(self) :

    '''This is not a deep copy'''

    return SDFGraph(self.actors, self.edges)

  @classmethod
  def load_from_dict(cls, dict_value) :

    actors, edges = [],  []

    if 'load actors' :
      actors = [ SDFActor.load_from_dict(a)
                 for a in dict_value['actors'] ]

    if 'load edges' :
      edges = [ SDFEdge.load_from_dict(e, actors)
                for e in dict_value['edges'] ]

    return SDFGraph(actors, edges)

  def dump_to_file(self, filepath, indent = 2) :
    with open(filepath, 'w+') as fp :
      fp.write(json.dumps(item, indent = 2))

  def load_from_file(self, filepath) :
    with open(filepath) as fp :
      dict_value = json.load(fp)
    self.load_from_dict(dict_value)

if __name__ == '__main__' :

  std_logic = DataType.get_std_logic()
  int32 = DataType.get_integer(31)

  clk = SDFPort('clk', 0, std_logic, 1)
  en = SDFPort('en', 1, std_logic, 1)
  din = SDFPort('din', 2, int32, 1)
  dout = SDFPort('dout', 0, int32, 1)

  fir0 = SDFActor('fir0', 0, [clk, en, din], [dout])
  fir1 = SDFActor('fir1', 1, [clk.clone, en.clone, din.clone], [dout.clone])

  connection = SDFEdge(fir0, fir0.output_ports[0], fir1, fir1.input_ports[2])

  from pprint import pprint as pp
  pp(fir0.dict_value)

  g = SDFGraph([fir0, fir1])

  print g
