import re, os.path, imp
from sylva.base.fimp import fimp as FIMP, fimp_lib as FIMP_Lib, fimp_set as FIMP_Set
from sylva.misc.util import to_list

class VHDL(object) :

  def __init__(self, file_path) :
    self.file_path = file_path
    self.clean_vhdl_source(file_path)
    self.get_file_info()
    self.get_fimps()

  def __str__(self) :
    return str(self.fimps)

  def clean_vhdl_source(self, file_path) :

    # read source file
    with open(file_path, 'r') as fp :
      source_code = fp.read().lower()

    # eliminate comments, extra \n and whitespace
    source_code = re.sub(r'\s*-{2}.*', '', source_code)
    source_code = re.sub(r'\n+', '\n', source_code)
    source_code = re.sub(r'\s+\n', '\n', source_code)
    source_code = re.sub(r'\s\s+', ' ', source_code)

    self.vhdl_src = source_code

  def get_file_info(self) :

    source_code = self.vhdl_src
    entity_name, generics, input_ports, output_ports = '', {}, {}, {}

    if 'find entity name' :
      entity_re = r'entity[\s\n]+(?P<entity_name>\w+)[\s\n]+is[\s\n]+'
      m = re.search(entity_re, source_code)
      if m :
        entity_name = m.group('entity_name')

    if 'find generics' and entity_name :
      g0_re = r'generic[\n\s]*\(([\n\s]*' + \
              r'(?P<generic_content>.+))\)[\n\s]*;[\n\s]*port'
      g1_re = r'generic[\n\s]*\(([\n\s]*' + \
              r'(?P<generic_content>.+))\)[\n\s]*;[\n\s]*end[\n\s]+%s' % \
                entity_name

      g0_m = re.search(g0_re, source_code, flags = re.S)
      g1_m = re.search(g1_re, source_code, flags = re.S)

      if g0_m != None :
        generic_content = re.sub(r'\s*$', '', g0_m.group('generic_content'))
      elif g1_m != None :
        generic_content = re.sub(r'\s*$', '', g1_m.group('generic_content'))
      else :
        generic_content = None

      if generic_content != None :
        one_generic_re = r'[\n\s]*(?P<generic_name>\w+)[\n\s]+:[\n\s]+' + \
                         r'(?P<generic_type>[^:]+)[\n\s]+:=[\n\s]+' + \
                         r'(?P<default_value>[^;]+)'
        generic_matches = re.finditer(one_generic_re, generic_content)
        generics = { gm.group('generic_name') : {
                       'type' : gm.group('generic_type'),
                       'value' : gm.group('default_value')}
                      for gm in generic_matches }

    if 'find ports' and entity_name :
      port_re = r'port[\n\s]*\([\n\s]*(?P<ports>.+)\)[\n\s]*;' + \
                r'[\n\s]*end[\n\s]+%s' % entity_name
      port_m = re.search(port_re, source_code, flags = re.S)

      if port_m != None :
        port_content = port_m.group('ports')

        one_port_re = r'[\n\s]*(?P<port_name>\w+)[\n\s]+:[\n\s]+' + \
                      r'(?P<port_direction>((in)|(out)))[\n\s]+' + \
                      r'(?P<port_type>[^;]+)'

        port_matches = re.finditer(one_port_re, port_content, flags = re.S)

        for m in port_matches :
          if m.group('port_direction') == 'in' :
            input_ports[m.group('port_name')] = m.group('port_type')
          else :
            output_ports[m.group('port_name')] = m.group('port_type')

    self.entity_name = entity_name
    self.generics = generics
    self.input_ports = input_ports
    self.output_ports = output_ports

  def get_fimps(self) :

    source_code = self.vhdl_src
    self.fimps = {}

    arch_re = r'(?<=architecture)\s+' + \
              r'(?P<arch_name>\w+)\s+of\s+(?P<entity_name>\w+)'

    arch_match = re.finditer(arch_re, source_code)

    for m in arch_match :
      fimp_name = m.group('arch_name')
      entity_name = m.group('entity_name')

      new_fimp = FIMP(name = entity_name, type_name = fimp_name)
      new_fimp.input_ports = self.input_ports
      new_fimp.output_ports = self.output_ports
      self.fimps[fimp_name] = new_fimp

  def assign_cost(self, cost_dict) :
    for type_name, f in self.fimps.items() :
      fimp_cost = cost_dict[f.name][f.type_name]
      for k, v in fimp_cost.items() :
        setattr(f, k, v)

  @classmethod
  def elaborate(cls, vhdl_src_path, cost_dict) :
    if os.path.isfile(vhdl_src_path) :
      result = VHDL(vhdl_src_path)
      result.assign_cost(cost_dict)
    return result

def create_from_vhdl(cls, vhdl, architecture = 'FPGA', name = 'fimp lib') :
  lib = FIMP_Lib(architecture, name)
  vhdl = to_list(vhdl)
  for v in vhdl :
    lib.add_fimp_set(FIMP_Set(name = v.entity_name))
    lib[v.entity_name].generics = v.generics
    lib[v.entity_name].input_ports = v.input_ports
    lib[v.entity_name].output_ports = v.output_ports
    for type_name, f in v.fimps.items() :
      lib.add_fimp(f)

  return lib

FIMP_Lib.create_from_vhdl = classmethod(create_from_vhdl)
