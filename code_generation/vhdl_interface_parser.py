# coding: utf-8

import os, re, argparse

status_level = 0
warning_level = 0

def status(s = 'working ...', level = 0, status_level = status_level) :
  if level >= status_level :
    print('Status: ' + s)

def warning(w = 'warning ...', level = 0, warning_level = warning_level) :
  if level >= warning_level :
    print('Warning: ' + w)

def read_vhdl(file_name) :

  # read source file
  fo = open(file_name, 'r')
  source_code = fo.read().lower()
  fo.close()

  # eliminate comments, extra \n and whitespace
  source_code = re.sub(r'\s*-{2}.*', '', source_code)
  source_code = re.sub(r'\n+', '\n', source_code)
  source_code = re.sub(r'\s+\n', '\n', source_code)
  source_code = re.sub(r'\s\s+', ' ', source_code)

  return source_code

def read_fimp_info(source_code) :

  # read entity_name
  entity_re = r'entity[\s\n]+(?P<entity_name>\w+)[\s\n]+is[\s\n]+'
  m = re.search(entity_re, source_code)
  entity_name = None

  if m != None :
    entity_name = m.group('entity_name')

  if entity_name != None:
    generics, input_ports, output_ports = {}, {}, {}
    status('found function definition \'%s\'.' % entity_name)

    # read generics
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

    generics = {}
    if generic_content != None :
      one_generic_re = r'[\n\s]*(?P<generic_name>\w+)[\n\s]+:[\n\s]+' + \
                       r'(?P<generic_type>[^:]+)[\n\s]+:=[\n\s]+' + \
                       r'(?P<default_value>[^;]+)'
      generic_matches = re.finditer(one_generic_re, generic_content)
      generics = { gm.group('generic_name') : {
                     'type' : gm.group('generic_type'),
                     'value' : gm.group('default_value')}
                    for gm in generic_matches }
      status('found generic: %s for function \'%s\'.' % \
             (generics, entity_name))
    else :
      status('no generic is found for function \'%s\'' % entity_name)

    # ports
    port_re = r'port[\n\s]*\([\n\s]*(?P<ports>.+)\)[\n\s]*;' + \
              r'[\n\s]*end[\n\s]+%s' % entity_name
    port_m = re.search(port_re, source_code, flags = re.S)

    if port_m != None :
      port_content = port_m.group('ports')

      one_port_re = r'[\n\s]*(?P<port_name>\w+)[\n\s]+:[\n\s]+' + \
                    r'(?P<port_direction>((in)|(out)))[\n\s]+' + \
                    r'(?P<port_type>[^;]+)'

      port_matches = re.finditer(one_port_re, port_content, flags = re.S)

      input_ports = {}
      output_ports = {}

      for m in port_matches :
        if m.group('port_direction') == 'in' :
          input_ports[m.group('port_name')] = m.group('port_type')
        else :
          output_ports[m.group('port_name')] = m.group('port_type')

        status( 'found %sput port \'%s\' type \'%s\' for function \'%s\'.' % \
                (m.group('port_direction'),
                 m.group('port_name'),
                 m.group('port_type'),
                 entity_name) )

    return entity_name, generics, input_ports, output_ports
  else :
    return None, None, None, None

def get_fimps(source_code, file_name, lib) :

  fimps = {}
  arch_re = r'(?<=architecture)\s+' + \
            r'(?P<arch_name>\w+)\s+of\s+(?P<entity_name>\w+)'

  arch_match = re.finditer(arch_re, source_code)

  for m in arch_match :
    fimp_name = m.group('arch_name')
    func_name = m.group('entity_name')
    status('found fimp \'%s\' for function \'%s\' in %s.' % \
           (fimp_name, func_name, file_name))
    if func_name in fimps.keys() :
      fimps[func_name].append(fimp_name)
    else :
      fimps[func_name] = [fimp_name]

  if fimps == {}:
    warning('no FIMP found in %s.' % file_name)

  # return fimp_count, architecture_match
  return fimps

def add_func_to_lib(lib, func_name, generics, input_ports, output_ports) :

  if func_name != None :
    if func_name in lib.keys() :
      warning('multiple definition found for function %s' % func_name)

    if func_name not in lib :
      lib[func_name] = {}

    lib[func_name]['generics'] = generics
    lib[func_name]['input_ports'] = input_ports
    lib[func_name]['output_ports'] = output_ports

  return lib

def autocfg(current_path) :

  func_name = None
  fimp_files = None
  fimp_count = 0
  architectures = []

  current_path = os.path.abspath(current_path)

  is_dir = os.path.isdir(current_path)
  fimp_files = []

  if is_dir :
    file_list = os.listdir(current_path)
    fimp_files = [current_path + '\\' + f for f in file_list
                  if f.endswith('.vhd') or f.endswith('.vhdl') ]
  else :
    if current_path.endswith('.vhd') or current_path.endswith('.vhdl') :
      fimp_files = [ current_path ]

  status('checking folder: ' + current_path)
  lib = {}

  # print fimp_files

  if len(fimp_files) == 0 :
    warning('no vhdl source code file found in ' + current_path)
  else :
    for file_name in fimp_files :
      status('checking ' + file_name)
      source_code = read_vhdl(os.path.abspath(file_name))
      func_name, generics, input_ports, output_ports\
      = read_fimp_info(source_code)
      lib = add_func_to_lib(lib, func_name,
        generics, input_ports, output_ports)
      fimps = get_fimps(source_code, file_name, lib)

      for func in fimps.keys() :
        if func in lib :
          if 'fimps' not in lib[func].keys() :
            lib[func]['fimps'] = []
          for fimp in fimps[func] :
            lib[func]['fimps'].append(fimp)
        else :
          lib[func] = {'fimps' : fimps[func]}

  return lib

def add_fake_info(lib) :

  for func in lib.values() :
    func['input_time'] = 1
    func['output_time'] = 1
    func['computation_time'] = 1

    func['computation_end_time'] = func['computation_time'] - 1
    func['input_end_time'] = func['input_time'] - 1
    func['output_start_time'] = func['computation_time'] \
                              - func['output_time']
    func['area'] = {}
    func['energy'] = {}

    for fimp in func['fimps'] :
      func['area'][fimp] = 29
      func['energy'][fimp] = 22

  return lib

def export_lib(lib, file_name = 'fimp_lib.py') :
  fo = open(file_name,'w')
  fo.write('fimp_lib = ')
  # pprint(lib, fo)
  fo.close()

if __name__ == '__main__' :
  parser = argparse.ArgumentParser(
             description = 'FIMP automatic configuration' )

  parser.add_argument('--path', '-p',
                      default = os.path.dirname(os.path.abspath(__file__)),
                      help = 'FIMP source code path. ' +
                             'Default is current path.')
  parser.add_argument('--out', '-o',
                      default = 'fimp_lib.py',
                      help = 'output fimp library .py file name')

  args = parser.parse_args()
  lib = autocfg(args.path)
  export_lib(lib, args.out)
