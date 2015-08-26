from pyparsing import \
nums, alphas, alphanums, \
OneOrMore, Group, Suppress, Optional, \
quotedString, Word, Keyword, alphanums

from io import open

if 'utilities' :

  def load_command_from_file(command_file_path, encoding = 'utf-8') :
    with open(command_file_path, 'r', encoding = 'utf-8') as fp :
      cmds = []
      while True :
        one_line = fp.readline()
        if one_line :
          if one_line != '\n' and not one_line.startswith('#') :
            cmds.append(one_line[:-1]) # remove the '\n' in the end
        else :
          break
    return cmds

  class Keywords (object) :

    def __init__(self, *args, **kwarg) :
      super(Keywords, self).__init__()
      for k in args :
        value = Keyword(k)
        self.__setattr__(k, value)
        globals()[k] = self.__dict__[k]

    def __getitem__(self, key) :
      return self.__getattr__(key)

    def __setitem__(self, key, value) :
      self.__dict__[key] = value

    def __getattr__(self, key) :
      try :
        return self.__dict__[key]
      except KeyError :
        return None

    @property
    def keys(self):
      return self.__dict__.keys()

  def anyof(values, operation = '|') :
    return eval('(' + (' '+operation+' ').join(key for key in values) + ')')

if 'general tokens' :
  true = Keyword('true')
  false = Keyword('false')
  low = Keyword('low')
  mid = Keyword('mid')
  high = Keyword('high')
  full = Keyword('full')
  integer = Word(nums)

  string_value = (Word( alphas + '_./', alphanums + '_./') | quotedString)
  single_value = (low | high | mid | full | string_value | integer | quotedString | true | false)
  left_bracket = Suppress('{')
  right_bracket = Suppress('}')
  more_values = Group(left_bracket \
              + OneOrMore(single_value + Optional(Suppress(','))) \
              + right_bracket)

  value = (single_value | more_values)

if 'all commands' :
  command = Keywords(
    'synthesize',
    'set_attribute', 'set_attr',
    'define_constraint',
    'define_optimization',
    'read_hdl',
    'create_fimp_library',
    'write',
    'dump',
    'load',
    'source',
    'generate',
    'run',
    'pick_solution',
    'floorplan',
    'assign_fimps_to_cgra')

if 'set_attribute' :
  attribute= Word(alphas + '_')
  set_attribute_command = (set_attribute + attribute + value)
  set_attr_command = (set_attr + attribute + value)

if 'define_constraint' :
  constraints = Keywords('tmax', 'rmax', 'emax', 'amax')
  constraint_name = anyof(constraints.keys)
  constraint = (Suppress('-') + constraint_name + integer)
  define_constraint_command = (define_constraint + OneOrMore(constraint))

if 'define_optimization' :
  optimizations = Keywords('ka', 'ke', 'kt', 'kr')
  optimization_objective_name = anyof(optimizations.keys)
  optimization_objective = (Suppress('-') + optimization_objective_name + integer)
  define_optimization_command = (define_optimization + OneOrMore(optimization_objective))

if 'synthesis' :
  synthesis_options = Keywords(
    'to_asic', 'to_fpga', 'to_cgra','effort')
  synthesis_option = anyof(synthesis_options.keys)
  synthesize_command = (synthesize + \
    Optional(OneOrMore(Suppress('-') + synthesis_option + Optional(value))))

run_command = (run + quotedString)
read_hdl_command = (read_hdl + value)
create_fimp_library_command = create_fimp_library
write_command = (write + value + Optional(value) + Optional(Suppress('>') + value))
load_command = (load + value + Optional(Suppress('<') | Suppress('from')) + value)
dump_command = (dump + value + Optional(Suppress('>')) + value)
source_command = (source + value)
pick_solution_command = (pick_solution + integer + Optional(integer))
floorplan_command = (floorplan + Optional(integer + Optional(integer)))
assign_fimps_to_cgra_command = assign_fimps_to_cgra

if 'generate' :
  generate_outputs = Keywords('vhdl', 'verilog', 'matlab', 'hsdf_graph')
  generate_output = anyof(generate_outputs.keys)
  key_word_from = Suppress('from')
  generate_inputs = Keywords('hsdf_graph', 'sdf_graph', 'simulink')
  generate_input = anyof(generate_inputs.keys)
  generate_command = (generate + generate_output + key_word_from + generate_input +\
    Optional(Suppress('>') + value))

one_command = anyof([cmd + '_command' for cmd in command.keys])

def parse_script(file_name, encoding = 'utf-8') :
  cmd_string_list = load_command_from_file(file_name, encoding=encoding)
  cmd_list = [ one_command.parseString(cs).asList() for cs in cmd_string_list ]
  return cmd_list
