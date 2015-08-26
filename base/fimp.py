# coding: utf-8

'''
  Function Implementation (FIMP) and FIMP Set
'''

import json

if 'FIMP class definition' :

  class fimp (object):

    '''
      Function Implementation (FIMP) class
    '''

    def __init__( self, name = 'noName', type = 0,
      width = None, height = None, area = None, energy = None,
      computation_phase = 1, input_phase = 1, output_phase = 1, index = None,
      type_name = None) :

      '''
        Initialize a FIMP instance
        --------------------------

        1. name: string, the name of the function to be executed by this FIMP
        2. type: integer, the FIMP type index
        3. width : integer, the width of this FIMP
        4. height : integer, the height of this FIMP
        5. area: integer, the area of this FIMP
          If not provided, area = width * height.
        6. energy : integer, the energy consumption of one execution of this FIMP
        7. computation_phase: integer, the length of the computation phase
        8. input_phase: integer, the length of the input phase
        9. output_phase: integer, the length of the output phase
      '''

      self.name = name
      self.type = type
      self.type_name = type_name or 'fimp_{}'.format(self.type)

      self.width = width or 0
      self.height = height or 0

      if width and height :
        self.area = width * height
      else :
        self.area = area

      self.energy = energy or 0

      self._computation_phase = computation_phase
      self._input_phase = input_phase
      self._output_phase = output_phase

      self.computation = computation_phase
      self.input_end = input_phase - 1
      self.output_start = computation_phase - output_phase + 1

      self.actors = []
      # Actors running on this FIMP
      # It has to be explicitly add to the FIMP
      # It will not be serialized.

      # self.x, self.y = -1, -1
      # FIMP location on a fabric
      # They have to be explicitly add to the FIMP

      self.index = index
      # FIMP index in a system
      # It has to be explicitly specified after synthesis
      self.__repr__ = self.__str__

    def __setattr__(self, name, value):
      if name not in ['computation_phase', 'input_phase', 'output_phase'] :
        super(fimp, self).__setattr__(name, value)
      else :
        if name == 'computation_phase' :
          self._computation_phase = value
          self.computation = value
          self.output_start = value - self.output_phase + 1
        elif name == 'input_phase' :
          self._input_phase = value
          self.input_end = value - 1
        elif name == 'output_phase' :
          self._output_phase = value
          self.output_start = self._computation_phase - value + 1


    @property
    def computation_phase(self):
      return self._computation_phase
    @computation_phase.setter
    def computation_phase(self, value):
      self._computation_phase = value
      self.computation = value
      self.output_start = value - self.output_phase + 1

    @property
    def input_phase(self):
        return self._input_phase
    @input_phase.setter
    def input_phase(self, value):
      self._input_phase = value
      self.input_end = value - 1

    @property
    def output_phase(self):
        return self._output_phase
    @output_phase.setter
    def output_phase(self, value):
      self._output_phase = value
      self.output_start = self._computation_phase - value + 1

    def add_actor(self, one_actor) :

      '''
        Add one hsdf actor to this FIMP
        This method is invoked when actor.assign_to() method is invoked
      '''

      if one_actor not in self.actors:
        self.actors.append(one_actor)
        one_actor.fimp = self

    def __str__(self) :

      '''
        Construct human readable string of this FIMP instance.
      '''

      result = 'FIMP for {}, type {}'.format(self.name, self.type)
      result += ' type_name {}, index {}'.format(self.type_name, self.index)

      return result

    def clone(self) :

      '''
        Make a deep copy of this FIMP instance.
        Actor list is not copied.
        XY location is not copied.
      '''

      return fimp( self.name, self.type,
                   self.width, self.height, self.area,
                   self.energy, self.computation_phase,
                   self.input_phase, self.output_phase)

    def serialize(self) :

      '''
        Serialize this FIMP instance for storage.
      '''

      result = {}

      for key in dir(self) :
        if not key.startswith('__') :
          val = getattr(self, key)
          if isinstance(val, str) or isinstance(val, int) :
            result[key] = getattr(self, key)

      result['actors'] = [ a.index for a in self.actors ]

      return result

    def write_to_file(self, filename, indent = 2) :

      '''
        Store this class instance in a file.
      '''

      f = open(filename, 'w+')
      f.write(json.dumps( self.serialize(), indent = 2) )
      f.close()

if 'Modify SDF class' :

  from sdf import actor

  def assign_to(self, one_fimp) :

    '''
      Assign a FIMP instance to execute this HSDF actor.
    '''

    one_fimp.add_actor(self)

  actor.assign_to = assign_to

if 'Modify CGRA class' :

  from cgra import cgra

  def add_fimp(self, fimp) :

    '''
      Add one FIMP instance to the CGRA fabric.
      XY location may or may not to be presented in the FIMP instance.
    '''

    if fimp not in self.fimps :
      self.fimps.append(fimp)

  cgra.add_fimp = add_fimp

if 'Random FIMP generation for fimp_set' :

  import random

  def generate_random_fimps(fimp_name, num_fimps = 8,
    max_area = 0, max_width = 4, max_height = 4,
    min_area = 0, min_width = 1, min_height = 1,
    max_computation = 20, max_input = 10, max_output = 10,
    min_computation = 2,  min_input = 1,  min_output = 1,
    max_energy = 10, min_energy = 1) :

    '''
      Generate FIMP Instances for Testing
      -----------------------------------

      0. All ranges are inclusive

      1. fimp_name: string, the name of the function to be executed on the FIMP instances.
      2. num_fimps: integer, the number of FIMP instances to generate.
      3. max_width: integer, maximum width of the FIMP instances
      4. max_height: integer, maximum height of the FIMP instances
      5. min_width: integer, minimum width of the FIMP instances
      6. min_height: integer, minimum height of the FIMP instances
      7. max_computation: integer, maximum computation phase length
      8. max_input: integer, maximum input phase length
      9. max_output: integer, maximum output phase length
      10. min_computation: integer, minimum computation phase length
      11. min_input: integer, minimum input phase length
      12. min_output: integer, minimum output phase length
    '''

    # input phase can last as long as the computation phase
    if max_input > max_computation:
      max_input = max_computation

    # output phase can last as long as the computation phase
    if max_output > max_computation:
      max_output = max_computation

    fimps = []

    for x in range(num_fimps):

      computation_phase = random.randint(min_computation, max_computation)
      ratio = computation_phase/ (max_computation + min_computation)

      if (max_input > computation_phase):
        input_max = computation_phase
      else :
        input_max = max_input

      if (min_input > computation_phase):
        input_min = computation_phase
      else :
        input_min = min_input

      if (max_output > computation_phase):
        output_max = computation_phase
      else :
        output_max = max_output

      if (min_output > computation_phase):
        output_min = computation_phase
      else :
        output_min = min_output

      input_phase = random.randint(input_min, input_max)
      output_phase = random.randint(output_min, output_max)

      width = random.randint(min_width, max_width)
      width = int((ratio * (max_width + min_width) + width)/2)

      #================================================
      #                expected value + random value
      # Actual value = -----------------------------
      #                               2
      #================================================

      height = random.randint(min_height, max_height)
      height = int((ratio * (max_height + min_height) + height)/2)

      if max_area != 0 :
        area = random.randint(min_area, max_area)
        area = int((ratio * (max_area + min_area) + area)/2)
      else :
        area = width * height

      energy = random.randint(min_energy, max_energy)
      energy = int((ratio * (max_energy + min_energy) + energy)/2)

      fimps.append(
        fimp( name = fimp_name, type = x,
              area = area,
              width = width,
              height = height,
              energy = energy,
              computation_phase = computation_phase,
              input_phase = input_phase,
              output_phase = output_phase) )

    return fimps

if 'FIMP set class definition' :

  class fimp_set():

    '''
      A fimp_set instance is a dictionary instance.
      It is for holding a set of FIMP instances for one function.
    '''

    def __init__(self, name, random = False,
      num_fimps = 8,
      max_area = 0, min_area = 0,
      max_width = 4, max_height = 4,
      min_width = 1, min_height = 1,
      max_computation = 20, max_input = 10, max_output = 10,
      min_computation = 2,  min_input = 1,  min_output = 1,
      max_energy = 10, min_energy = 1) :

      '''
        Initialize a FIMP set instance
        ------------------------------

        0: The function name has to be provided when creating a FIMP set.
        1: name: string, the function name
      '''

      self.name = name
      self.set = {}
      self.generics = {}
      self.input_ports = {}
      self.output_ports = {}

      if random == True :
        fimps = generate_random_fimps( self.name, num_fimps,
                                       max_area, max_width, max_height,
                                       min_area, min_width, min_height,
                                       max_computation, max_input, max_output,
                                       min_computation,  min_input,  min_output,
                                       max_energy, min_energy )
        for f in fimps :
          self.add_fimp(f)

    def __getitem__(self, the_type) :

      '''
        Locate a FIMP instance using its type.
      '''

      return self.set[the_type]

    def add_fimp(self, one_fimp) :

      '''
        Add a FIMP instance (one_fimp) to this FIMP set instance.
      '''
      if one_fimp.actors != [] :
        if self.input_ports == {} :
          for p in one_fimp.actors[0].input_ports :
            self.input_ports[p.name] = p.type.name
          for p in one_fimp.actors[0].output_ports :
            self.output_ports[p.name] = p.type.name

      if one_fimp.type not in self.set.keys() :
        self.set[one_fimp.type] = one_fimp
      else :
        print('WARNING: FIMP with type = %s is already in this set.' % one_fimp.type)

    def serialize(self) :

      '''
        Serialize this FIMP set instance for storage.
      '''

      result = {}
      result['name'] = self.name
      result['types'] = self.set.keys()
      result['count'] = len(self.set.keys())

      for type in self.set.keys() :
        result[type] = self.set[type].serialize()

      result['generics'] = self.generics
      result['input_ports'] = self.input_ports
      result['output_ports'] = self.output_ports

      return result

    def get_fimp_count(self) : return len(self.set.keys())
    fimp_count = property(get_fimp_count, None, None, 'Number of FIMP instances in this FIMP set.')

    def write_to_file(self, filename, indent = 2) :

      '''
        Store this class instance in a file.
      '''

      f = open(filename, 'w+')
      f.write(json.dumps( self.serialize(), indent = 2) )
      f.close()

if 'FIMP library class' :

  class fimp_lib :

    '''
      FIMP library class
    '''

    def __init__(self, architecture, name = 'SYLVA FIMP Library') :

      '''
        Initialize a fimp library instance for a given architecture.
      '''

      self.architecture = architecture
      self.name = name
      self.set = {}

    def add_fimp(self, one_fimp) :

      '''
        Add one FIMP instance to this FIMP library
      '''

      if one_fimp.name not in self.set.keys() :
        self.set[one_fimp.name] = fimp_set(one_fimp.name)

      self.set[one_fimp.name].add_fimp(one_fimp)

    def add_fimp_set(self, one_fimp_set) :

      '''
        Add a FIMP set instance (one_fimp_set) to this FIMP library instance.
      '''

      if one_fimp_set.name not in self.set.keys() :
        self.set[one_fimp_set.name] = one_fimp_set
      else :
        print('WARNING: FIMP set with name = %s is already in this library.'\
              % one_fimp_set.name)

    def serialize(self) :

      '''
        Serialize this FIMP library instance for storage.
      '''

      result = {}
      result['architecture'] = self.architecture
      result['name'] = self.name
      result['functions'] = self.set.keys()
      result['count'] = len(self.set.keys())

      for function_name in self.set.keys() :
        result[function_name] = self.set[function_name].serialize()

      return result

    def write_to_file(self, filename, indent = 2) :

      '''
        Store this class instance in a file.
      '''

      f = open(filename, 'w+')
      f.write(json.dumps( self.serialize(), indent = 2) )
      f.close()

    def dump(self, filename, indent = 2) :
      self.write_to_file(filename, indent)

    def get_count(self) : return len(self.set.keys())
    function_count = property(get_count, None, None,
      'Number of FIMP set instances in this library.')

    def get_function_name_set(self) : return self.set.keys()
    function_name_set = property(get_function_name_set, None, None,
      'The set of function names of the FIMP set instances in this library.')

    def get_fimp_sets(self) : return self.set.values()
    fimp_sets = property(get_fimp_sets, None, None,
      'The set of FIMP set instances in this library.')

    def __getitem__(self, function_name) :

      if function_name.lower() not in self.set.keys() :
        raise Exception('FIMPs for function `%s` is not in this library.' % function_name)

      return self.set[function_name.lower()]

def load_fimp(fimp_dict, load_actors = False, actors = []) :

  width = 0
  height = 0

  if 'width' in fimp_dict.keys() and 'height' in fimp_dict.keys():
    width = int(fimp_dict['width'])
    height = int(fimp_dict['height'])
    area = width * height
  else :
    area = int(fimp_dict['area'])

  result = fimp(
    name = str(fimp_dict['name']),
    type = int(fimp_dict['type']),
    area = area,
    width = width,
    height = height,
    energy = int(fimp_dict['energy']),
    computation_phase = int(fimp_dict['computation_phase']),
    input_phase = int(fimp_dict['input_phase']),
    output_phase = int(fimp_dict['output_phase']))

  if 'index' in fimp_dict.keys():
    result.index = int(fimp_dict['index'])

  if 'extra_buffer' in fimp_dict.keys() :
    result.extra_buffer = int(fimp_dict['extra_buffer'])

  if load_actors == False :
    return result
  else :
    result.actors = [ actors[i] for i in fimp_dict['actors'] ]
    return result

def load_fimp_set(fimp_dict) :

  result = fimp_set(name = str(fimp_dict['name']))
  types = fimp_dict['types']
  for t in types :
    result.add_fimp(load_fimp(fimp_dict[str(t)]))
  result.generics = fimp_dict['generics']
  result.input_ports = fimp_dict['input_ports']
  result.output_ports = fimp_dict['output_ports']
  return result

def load_fimp_lib(fimp_dict) :

  architecture = str(fimp_dict['architecture'])
  name = str(fimp_dict['name'])
  functions = fimp_dict['functions']

  result = fimp_lib(architecture, name)

  for f in functions :
    result.add_fimp_set(load_fimp_set(fimp_dict[str(f)]))

  return result

def load_from_file(filename) :

  f = open(filename, 'r')
  s = f.read()
  f.close()
  d = json.loads(s)

  if 'architecture' in d.keys() :
    return load_fimp_lib(d)
  if 'types' in d.keys() :
    return load_fimp_set(d)
  if 'name' in d.keys() :
    return load_fimp(d)

  return None

