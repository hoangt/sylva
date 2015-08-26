# coding: utf-8
import tcl_parser
import os, json, imp, sys
import FileDialog
from sylva.base.fimp import fimp_lib as FIMP_Lib
import sylva.base.sdf as sdf
from sylva.base import fimp
from sylva.base.sdf_to_hsdf import sdf_to_hsdf

from sylva.misc.util import mkdir, to_list, files_in_path, \
                            all_files, chunks, dir_and_file, status_log
from sylva.misc.vhdl_ulti import VHDL as HDL
from sylva.base.sdf import sdfg as SDFG
from sylva.base.cgra import cgra as CGRA
from sylva.dse import dse
from sylva.dse.dse_engine_v1 import dse_v1
import sylva.frontend.simulink2sdf
import sylva.glic.glic as glic
from sylva.code_generation.air import air_to_vhdl
from sylva.code_generation.hsdf_to_vhdl import hsdf_to_vhdl
from sylva.misc.plot import schedule_plot
from sylva.code_generation.floorplanner import floorplanner

args_is_list = [
  'lib_search_path',
  'hdl_search_path',
  'vhdl_used_library',
]

args_is_bool = ['create_schedule_plot']
args_is_int = ['information_level', 'solutions_per_schedule', 'time_limit_in_sec',
 'low', 'high', 'mid', 'full']

show_path = [
  'fimp_library',
  'sdf_graph',
  'hsdf_graph',
  'hdl_cost_lib',
  'hdl_list',
  'current_solution'
]
show_count = [ 'solutions']
hide = [ 'cmds', 'log', 'critical_log']

to_clean = [
  'output_path',
  'plot_path',
  'dump_path',
  'output_hdl_path',
  'record_cmd_file_path',
  'log_file',
]

class DictObject(object) :
  def __init__(self, *args, **kwargs) :
    super(DictObject, self).__init__()
    for k, v in kwargs :
      self.__setattr__(k, v)
    for k in args :
      self.__setattr__(k, k)

  def __getitem__(self, key) :
    return self.__getattr__(key)

  def __setitem__(self, key, value) :
    self.__dict__[key] = value

  def __getattr__(self, key) :
    try :
      return self.__dict__[key]
    except KeyError :
      return None

  def __str__(self) :
    return self.__dict__.__str__()

  def __repr__(self) :
    return self.__dict__.__str__()

  @property
  def keys(self):
    return self.__dict__.keys()

class SYLVA(DictObject) :

  def __init__(self, show_info = True, show_time = True,
    no_log = False, log_file = None,
    record_cmd = True, record_cmd_file_path = None, *args, **kwargs) :
    super(SYLVA, self).__init__( *args, **kwargs)

    self._topinfo = 'SYLVA - System Architectural Synthesis Framework\n'
    self._topinfo += 'By Shuo Li (contact@shuo.li, www.shuo.li)\n\n'

    self.log = status_log(False, False)
    self.critical_log = status_log(False, False)
    self.show_info = show_info
    self.show_time = show_time
    self.record_cmd = record_cmd
    self.record_cmd_file_path = record_cmd_file_path or 'rc.tcl'
    self.cmds = []
    self.no_log = no_log
    self.log_file = log_file or 'sylva.log'

  @property
  def no_rc(self):
    return not self.record_cmd

  @no_rc.setter
  def no_rc(self, value):
    self.record_cmd = not value

  @property
  def show_time(self):
    return self._show_time

  @show_time.setter
  def show_time(self, value):
    self._show_time = value
    self.log.show_time_stamp = value
    self.critical_log.show_time_stamp = value

  @property
  def show_info(self):
    return self._show_info

  @show_info.setter
  def show_info(self, value):
    self._show_info = value
    if value :
      if self.information_level :
        self.critical_log.print_status = True
        self.log.print_status = False
      else :
        self.critical_log.print_status = False
        self.log.print_status = True
    else :
      self.critical_log.print_status = False
      self.log.print_status = False

  def log_normal(self, msg) :
    self.log += msg
    self.log.update()

  def log_critical(self, msg) :
    self.log_normal(msg)
    self.critical_log += msg
    self.critical_log.update()

  def log_kv(self, k, v) :
      self.log_critical('{} is set to {}'.format(k, v))

  def dump(self, item, file_name, target_dir = None, indent=2) :

    if target_dir :
      file_name = os.path.join(target_dir, file_name)

    if isinstance(item, SDFG) :
      item = sdf.serialize_sdf_graph(item.actors, item.edges)
    elif isinstance(item, dse.system_model) :
      item = item.serialize()
    elif isinstance(item, dse.design_specification) :
      item = item.serialize()
    elif isinstance(item, FIMP_Lib) :
      item.dump(file_name, indent=indent)
      return
    elif isinstance(item, status_log) :
      item.write_to_file(file_name)
      return

    with open(file_name, 'w+') as fp:
      json.dump(item, fp, indent=indent)

  def load(self, file_name, load_type) :
    if os.path.exists(file_name) :
      if os.path.isfile(file_name) :
        with open(file_name, 'r') as fp:
          json_dict = json.load(fp)

        if load_type.lower() == 'sdf_graph' :
          return SDFG.load(json_dict)
        elif load_type.lower() == 'cgra' :
          return CGRA.load(json_dict)
        elif load_type.lower() == 'hsdf_graph' :
          return SDFG.load(json_dict)
        elif load_type.lower() == 'fimp_library' :
          return fimp.load_fimp_lib(json_dict)
        else :
          return json_dict
      self.log_critical('ERROR: ' + file_name + ' is directory.')
      return False
    else :
      self.log_critical('ERROR: ' + file_name + ' does not exist.')
      return False

  def create_air(self, sdfg, hsdfg, solution) :

    hsdf_actors, hsdf_edges = hsdfg.actors, hsdfg.edges
    sdf_actors = sdfg.actors

    for one_actor in hsdf_actors:
      one_actor.base_actor = sdf_actors[one_actor.base_actor_index]
      delattr(one_actor, 'base_actor_index')

    fimp_instances = [ fimp.load_fimp(
      fimp_instance, load_actors = True, actors = hsdf_actors)
      for fimp_instance in solution['fimp_instances'] ]

    for fimp_instance in fimp_instances:
      for one_actor in fimp_instance.actors:
        one_actor.fimp = fimp_instance
      fimp_instance.base_actor = fimp_instance.actors[0]
      fimp_instance.global_index = fimp_instance.index
      first_start = fimp_instance.actors[0].start
      fimp_instance.first_start = first_start
      for hsdf_actors in fimp_instance.actors:
        hsdf_actors.start -= first_start
        hsdf_actors.output_start -= first_start
        hsdf_actors.input_end -= first_start
        hsdf_actors.buffer_end -= first_start
        hsdf_actors.end -= first_start

    return [ glic.create_abb(fimp_instance, hsdf_edges) for fimp_instance in fimp_instances ]

  def execute_command(self, cmd) :

    if self.record_cmd :
      self.cmds.append(cmd)

    if cmd[0] in ['set_attribute', 'set_attr'] :
      self.execute_set_attribute(cmd[1:])
    elif cmd[0] == 'read_hdl' :
      self.execute_read_hdl(cmd[1:])
    elif cmd[0] == 'create_fimp_library' :
      self.execute_create_fimp_library()
    elif cmd[0] in ['define_constraint', 'define_optimization' ]:
      self.execute_define_constraint_and_optimization(cmd[1:])
    elif cmd[0] == 'synthesize' :
      self.execute_synthesize(cmd)
    elif cmd[0] == 'write' :
      self.execute_write(cmd[1:])
    elif cmd[0] == 'dump' :
      self.execute_dump(cmd[1:])
    elif cmd[0] == 'load' :
      self.execute_load(cmd[1:])
    elif cmd[0] == 'source' :
      self.execute_source(cmd[1:])
    elif cmd[0] == 'generate' :
      self.execute_generate(cmd[1:])
    elif cmd[0] == 'run' :
      self.execute_run(cmd[1])
    elif cmd[0] == 'pick_solution' :
      self.execute_pick_solution(cmd[1:])
    elif cmd[0] == 'floorplan' :
      self.execute_floorplan(cmd[1:])
    elif cmd[0] == 'assign_fimps_to_cgra' :
      self.execute_assign_fimps_to_cgra()
    else :
      self.log_critical('Unaccepted command : {}'.format(cmd))

  def execute_write(self, args) :

    if args[0].lower() == 'hdl' :
      self.execute_write_hdl(args[1:])
    elif len(args) > 1 :
      if args[0].lower() == 'fimp' and args[1].lower() == 'plots' :
        self.execute_write_fimp_plots(args[2:])
      elif args[0].lower() == 'cgra' and args[1].lower() == 'floorplans' :
        self.execute_write_cgra_floorplans(args[2:])
    else :
      self.log_critical('Cannot execute {}.'.format(' '.join([write] + args)))

  def execute_pick_solution(self, args) :
    self.current_solution_file_path = str(args[0]) + ', '
    self.current_solution = self.solutions[int(args[0])]

    if len(args) > 1 :
      self.current_solution_file_path = (int(args[0]), int(args[1]))
      self.current_solution = self.current_solution[int(args[1])]
    else :
      self.current_solution_file_path = (int(args[0]), len(self.current_solution) - 1)
      self.current_solution = self.current_solution[-1]

    self.current_hsdfg = SDFG.load(self.current_solution)
    self.log_critical('Current solution is {}'.format(self.current_solution_file_path))

    if self.cgra :
      self.execute_assign_fimps_to_cgra()

  def execute_assign_fimps_to_cgra(self) :
    if self.cgra :
      self.cgra.fimps = [ fimp.load_fimp(f) for f in self.current_solution['fimp_instances'] ]
      self.log_critical('Assigned FIMPs from current solution to CGRA.')
    else :
      self.log_critical('Error: No CGRA is loaded.')

  def execute_floorplan(self, args) :

    self.log_critical('Executing CGRA floorplanning ...')
    if args :
      self.execute_pick_solution(args)

    if not self.current_solution :
      self.log_critical('Error: No solution is selected.')
    if not self.cgra :
      self.log_critical('Error: No CGRA is loaded.')
    if self.current_solution and self.cgra :
      for a in self.current_hsdfg.actors :
        a.assign_to(self.cgra.fimps[a.fimp_index])
      self.floorplanner = floorplanner(
        self.cgra,
        self.current_hsdfg.actors, time_limit = self.time_limit_in_sec * 1000)
      while self.floorplanner.solve() : pass
      if self.floorplanner.solutions :
        self.log_critical('Executing CGRA floorplanning is done.')
      else :
        self.log_critical('Executing CGRA floorplanning got no solution.')

  def execute_run(self, cmd) :
    # print('running command: ', cmd[1:-1])
    print(eval(cmd[1:-1]))

  def execute_generate(self, args) :
    o, i = args[:2]

    if len(args) > 2 :
      output_dir, name, ext = dir_and_file(args[2])
    else :
      output_dir, name, ext = self.output_path, None, None

    mkdir(output_dir)

    self.log_critical('Generating {} from {} ...'.format(o, i))

    if i not in tcl_parser.generate_inputs.keys :
      self.log_critical('Error: input format {} is not supported'.format(i))
      return

    if i == 'sdf_graph' : # o == 'hsdf_graph' is included
      self.prepare_from_sdf_graph()
    elif i == 'simulink' :
      if not self['simulink_model'] :
        self.log_critical('Error: simulink_model is not provided')
        return
      else :
        self.prepare_from_sdf_graph()
      if not self['fimp_library'] :
        self.log_critical('Error: fimp_library is not provided')
        return

    if o == 'vhdl' :
      self.prepare_to_vhdl()

      for a in self.hsdf_graph.actors :
        if a.name.lower() not in self.fimp_library.function_name_set :
          self.log_critical('Error: Cannot find {} in library'.format(a.name))
          return
        a.assign_to(self.fimp_library[a.name][0])
        self.fimp_library[a.name][0].base_actor = a.base_actor
        self.fimp_library[a.name][0].global_index = a.index

      entity_name = name or self.system_name or 'top'
      ext = ext or '.vhdl'
      output_file_path = os.path.join(output_dir, entity_name + ext)
      msg = hsdf_to_vhdl(
        self.hsdf_graph.actors, self.hsdf_graph.edges,
        self.fimp_library, entity_name = entity_name,
        used_libraries = self.vhdl_use_library,
        output_file = output_file_path)
      self.log_critical(msg)
      self.log_critical('Generating {} from {} is done'.format(o, i))
      return
    self.log_critical('Unsupported generation ({} > {}).'.format(i, o))

  def prepare_from_sdf_graph(self) :

    sdf_actors, sdf_edges = self.sdf_graph.actors, self.sdf_graph.edges
    a, e = sdf_to_hsdf( (sdf_actors, sdf_edges) )
    self.hsdf_graph = SDFG(a, e)

  def prepare_to_vhdl(self) :

    if not self.vhdl_use_library :
      self.log_critical('Warning: vhdl_use_library is not provided, no library will be used.')
      self.vhdl_use_library = {}

    lib_dict = {}
    for lib in self.vhdl_use_library :
      if '.' in lib :
        lib_list = lib.split('.')
        lib_name = lib_list[0]
        package_name = '.'.join(lib_list[1:])
        if lib_name in lib_dict :
          lib_dict[lib_name].append(package_name)
        else :
          lib_dict[lib_name] = [package_name]
      else :
        lib_dict[lib] = []
    self.vhdl_use_library = lib_dict
    self.system_name = self.system_name or 'top'

  def execute_write_hdl(self, hdl_output_dir) :

    self.log_critical('Writing HDLs ...')
    top_module_name = self.system_name or 'top'

    if hdl_output_dir :
      output_dir, name, _ = dir_and_file(hdl_output_dir[0])
    else :
      output_dir, name = self.output_path, None

    top_module_name = name or self.system_name or 'top'

    mkdir(output_dir)

    if self.solutions :
      for i, schedules in enumerate(self.solutions) :
        solution = schedules[-1]
        output_path = os.path.join(output_dir, self.hdl_output_dir_perfix + str(i))
        mkdir(output_path)
        hsdfg = SDFG.load(solution)
        air = self.create_air(self.sdf_graph, hsdfg, solution)
        sample_interval = solution['sample interval']
        air_to_vhdl(air, sample_interval, self.fimp_library, output_path, top_module_name)
      self.log_critical('Writing HDLs is done.')
    else :
      self.log_critical('No design space exploration solution for code generation.')

  def execute_write_fimp_plots(self, plot_output_dir) :

    self.log_critical('Writing FIMP plots ...')

    if plot_output_dir :
      output_dir, _, _ = dir_and_file(plot_output_dir[0])
    else :
      output_dir = self.plot_path

    mkdir(output_dir)

    for schedule_index, schedule in enumerate(self.solutions) :
      fimp_count = len(schedule[-1]['fimp_types'])
      plot_name = self.fimp_schedule_plot_pattern.replace('INDEX', str(schedule_index))
      plot_name = plot_name.replace('FIMPS', str(fimp_count))
      plot_path = os.path.join(output_dir, plot_name)
      hsdfg = SDFG.load(schedule[-1])
      fimps = [ fimp.load_fimp(f) for f in schedule[-1]['fimp_instances'] ]
      for a in hsdfg.actors :
        a.assign_to(fimps[a.fimp_index])

      p = schedule_plot(hsdfg.actors)
      p.savefig(plot_path)
      p.close()

    self.log_critical('Writing FIMP plots is done.')

  def execute_write_cgra_floorplans(self, plot_output_dir) :

    self.log_critical('Writing CGRA floorplans ...')
    if not self.floorplanner :
      self.log_critical('Error: Floorplanning has not been performed.')
    else :
      if plot_output_dir :
        output_dir, _, _ = dir_and_file(plot_output_dir[0])
      else :
        output_dir = self.plot_path

      mkdir(output_dir)

      name_pattern = self.cgra_schedule_plot_pattern.replace('INDEX', '{index}')
      name_pattern = name_pattern.replace('COST', '{cost}')
      self.floorplanner.plot_solutions(output_dir, name_pattern)
      self.log_critical('Writing CGRA floorplans is done.')

  def execute_source(self, args) :
    file_name = args[0]
    self.log_critical('Souring file '+ file_name + ' ...')
    if os.path.exists(file_name) :
      if os.path.isfile(file_name) :
        self.record_cmd = False
        cmds = tcl_parser.parse_script(file_name)
        for cmd in cmds :
          self.execute_command(cmd)
        self.log_critical('Souring file '+ file_name + ' is done.')
        self.record_cmd = True
      else :
        self.log_critical(file_name + ' is not a file.')
    else :
      self.log_critical(file_name + ' does not exist.')

  def execute_load(self, args) :
    attr_name, file_name = args
    self.log_critical('Loading {} from {} ...'.format(attr_name, file_name))

    if attr_name == 'simulink_model' :
      self.load_simulink_model(file_name)
      self.log_critical('Loading {} from {} is done.'.format(attr_name, file_name))
    else :
      self[attr_name] = self.load(file_name, attr_name)
      if self[attr_name] :
        self.log_critical('Loading {} from {} is done.'.format(attr_name, file_name))

  def execute_dump(self, args) :
    attr_name, file_name = args
    self.log_critical('Dumping {} to file {} ...'.format(attr_name, file_name))
    dirname, name, ext = dir_and_file(file_name)
    dump_path = dirname or self.dump_path or self.output_path
    mkdir(dump_path)
    try :
      self.dump(self[attr_name], name + ext, dump_path)
      self.log_critical('Dumping {} to file {} is done.'.format(attr_name, file_name))
    except Exception as e:
      self.log_critical('ERROR : Dumping {} to file {} failed.'.format(attr_name, file_name))
      self.log_critical(str(e))

  def execute_synthesize(self, args) :

    if len(args) > 1 :

      k = 0
      while k < len(args[1:]) :
        v = args[k]
        if v == 'to_fpga' :
          self.to_fpga = True
        elif v == 'to_asic' :
          self.to_fpga = True
        elif v == 'to_cgra' :
          self.to_fpga = True
        elif v == 'effort' :
          try :
            effort = int(args[k+1])
          except :
            effort = args[k+1]
          if isinstance(effort, str) :
            effort = int(self['effort_' + effort])
          self.effort = int(effort)
          k += 1
        k += 1

    if not self.system :
      self.constraint = dse.system_constraint(
        tmax = self.tmax,
        rmax = self.rmax,
        emax = self.emax,
        amax = self.amax)

      self.optimization_objective = dse.system_optimization_objective(
        kt = self.kt,
        kr = self.kr,
        ke = self.ke,
        ka = self.ka)

      if not self.sdf_graph :
        raise Exception('No SDF graph loaded, synthesizing abort.')

      self.system = dse.system_model(self.system_name,
        self.sdf_graph.actors,
        self.sdf_graph.edges,
        self.constraint,
        self.optimization_objective)

    if not self.design :
      if self.to_fpga :
        self.target_architecture = 'FPGA'
      elif self.to_asic :
        self.target_architecture = 'ASIC'
      elif self.to_cgra :
        self.target_architecture = 'CGRA'
      else :
        self.target_architecture = 'FPGA'

      if not self.fimp_library :
        raise Exception('No FIMP library loaded, synthesizing abort.')

      self.design = dse.design_specification(
        target_architecture = self.target_architecture,
        system = self.system, fimp_lib = self.fimp_library)

    self.dse_engine = dse_v1

    self.option = dse.solver_option( self.effort,
                              self.solutions_per_schedule,
                              self.time_limit_in_sec * 1000,
                              # self.create_schedule_plot,
                              self.dse_engine)

    self.solutions, self.hsdf_graph = dse.search_all(self.design, self.option,
      self.log, self.critical_log)

  def execute_define_constraint_and_optimization(self, args) :
    for arg in chunks(args, 2) :
      k, v = arg
      self.log_kv(k, v)
      self.__setattr__(k, int(v))

  def execute_create_fimp_library(self) :
    self.fimp_library = \
    FIMP_Lib.create_from_vhdl(self.hdl_list)

  def execute_read_hdl(self, args) :
    file_path = files_in_path(args[0], self.hdl_search_path)
    self.log_critical('Reading HDL file {} ...'.format(args[0]))
    if file_path :
      if not self.hdl_list :
        self.hdl_list_file_path = []
        self.hdl_list = []
      hdl = HDL.elaborate(file_path[0], self.hdl_cost_lib)
      self.hdl_list.append(hdl)
      self.hdl_list_file_path.append(file_path[0])
      self.log_critical('Reading HDL file {} is done.'.format(file_path))
    else :
      self.log_critical('ERROR: Cannot find HDL file {}.'.format(args[0]))

  def execute_set_attribute(self, args) :

    k, v = args
    if k in args_is_int :
      v = int(v)
      if k == 'information_level' :
        print_status = v == 0
        self.log.print_status = print_status and self.show_info
        self.critical_log.print_status = not print_status and self.show_info
    elif k in args_is_bool :
      v = (v == 'true' or v == 'True')
    elif k == 'fimp_library' :
      file_path = files_in_path(v, self.lib_search_path)
      if file_path :
        self.fimp_library_file_path = file_path[0]
        self[k] = fimp.load_from_file(file_path[0])
        self.log_kv(k, v)
        return
    elif k == 'hdl_cost_lib' :
      file_path = files_in_path(v, self.lib_search_path)
      if file_path :
        self.hdl_cost_lib_file_path = file_path[0]
        self[k] = imp.load_source('hdl_cost_lib', file_path[0]).cost_dict
        self.log_kv(k, v)
        return
    elif k == 'simulink_model' :
      self.load_simulink_model(v)
    elif k == 'sdf_graph' :
      file_path = files_in_path(v, os.getcwd())
      if file_path :
        with open(file_path[0], 'r') as fp:
          json_dict = json.load(fp)
        self['sdf_graph'] = SDFG.load(json_dict)
        self.log_kv(k, v)
        self.sdf_graph_file_path = file_path[0]
        return
    elif k in args_is_list:
      v = to_list(v)
    self.__setattr__(k, v)
    self.log_kv(k, v)

  def load_simulink_model(self, file_name) :
    self['simulink_model'] = file_name
    lib_path = self.lib_search_path
    if self.simulink_library_ext_name :
      lib_ext = self.simulink_library_ext_name
    else :
      lib_ext = ['.mdl']
    try :
      self.sdf_graph = SDFG.elaborate(file_name, lib_path, lib_ext)
    except Exception as e:
      m = re.match('.*in\s+library\s+([a-zA-Z_0-9]+)',str(e))
      lib_name = None
      if m :
        lib_name = m.groups()[0]
      if not self.lib_search_path :
        self.log_critical('ERROR: lib_search_path is not provided.')
      elif lib_name not in all_files(self.lib_search_path) :
        self.log_critical('ERROR: Cannot find library {}'.format(e))
        self.log_critical('lib_search_path is {}'.format(self.lib_search_path))
      else :
        self.log_critical('ERROR: {}'.format(e))
      return False
    return True

  def __del__(self) :
    if not self.no_log :
      self.log.write_to_file(self.log_file)

    if not self.no_rc :
      with open(self.record_cmd_file_path, 'w') as fp :
        for cmd in self.cmds :
          result = ''
          for v in cmd :
            if isinstance(v, list) :
              result += ' {' + ', '.join(v) +'}'
            else :
              result += ' {}'.format(v)
          fp.write(result[1:] + '\n')

def exit_command() :
  print('\nSYVLA exits normally.')
  if not sy.no_rc :
    print('Command record is in file {}.'.format(sy.record_cmd_file_path))
  if not sy.no_log:
    print('Log is in file {}.'.format(sy.log_file))
  sys.exit(0)

def cls_command() :
  os.system('cls')
  print(sy._topinfo)

def list_command() :
  result = []
  for k, v in sy.__dict__.items() :
    if k in show_count :
      result.append((k, len(to_list(sy[k]))))
    elif k in show_path :
      if (k + '_file_path') in sy.keys :
        result.append((k, sy[k + '_file_path']))
      else :
        result.append((k, type(sy[k])))
    elif not k.startswith('_') and k not in hide and not k.endswith('_file_path'):
      result.append((k, v))
  if result :
    print('')
    for i in sorted(result, key = lambda x : x[0]) :
      print('{} = {}'.format(i[0], i[1]))
  else :
    print('\nEmpty')

def reset_command() :
  global sy
  sy = SYLVA()
  if os.path.exists(default_setting_name) :
    cmds = tcl_parser.parse_script(args.default_setting)
    for cmd in cmds :
      sy.execute_command(cmd)
  print('\nSYLVA is reset.')

def clean_command() :
  print('')
  for a in to_clean :
    v = sy[a]
    if v :
      if v.startswith('./') :
        v = v[2:]
      dirname, name, ext = dir_and_file(v)
      if dirname == '.' and not name and not ext :
        pass
      elif name :
        path = os.path.join(dirname, name + ext)
        if os.path.exists(path) :
          os.remove(path)
          print('Deleted file {}'.format(path))
      else:
        if os.path.exists(dirname) :
          shutil.rmtree(dirname)
          print('Deleted directory {}'.format(dirname))

def ls_command() :
  files = []
  dirs = []
  print('')
  for f in os.listdir('./') :
    if os.path.isdir(f) :
      dirs.append('{}\\'.format(f))
    else :
      files.append(f)
  all_items = dirs + files
  result = ''
  for c in all_items :
    if len(result) + len(c) >= args.text_width :
      print(result)
      result = c + ' '
    else :
      result += c + ' '
  if result :
    print(result)

def pwd_command() :
  print('')
  print('PWD = {}'.format(os.getcwd()))

control_commands = {
  'exit' : exit_command,
  'cls' : cls_command,
  'list' : list_command,
  'reset' : reset_command,
  'clean' : clean_command,
  'ls' : ls_command,
  'pwd' : pwd_command}

def start_interactive_shell(sy, control_commands) :
  while True :
    sentinel = ''

    for cmd in iter(lambda : raw_input('\n>>'), sentinel):
      m = re.match('([a-zA-Z_0-9]+)\s*=\s*([./a-zA-Z_0-9]+)', cmd)
      cd_command = re.match('cd\s+([./\\a-zA-Z_0-9]+)', cmd)
      if cmd in control_commands :
        control_commands[cmd]()
      elif cmd in sy.keys :
        print('{} = {}'.format(cmd, sy[cmd]))
      elif cd_command :
        target_dir = cd_command.groups()[0]
        try :
          os.chdir(target_dir)
          print('Change directory to {}'.format(os.getcwd()))
        except Exception as e :
          print('ERROR: Cannot change directory to {}'.format(target_dir))
          if not os.path.exists(target_dir) :
            print('{} does not exist.'.format(target_dir))
      elif m :
        attr, value = m.groups()
        if value.lower() == 'True' :
          value = True
        else :
          try :
            value = int(value)
          except :
            value = str(value)
        cmd = ['set_attr', attr, value]
        sy.execute_command(cmd)
      else :
        try :
          sylva_cmd = tcl_parser.one_command.parseString(cmd).asList()
          sy.execute_command(sylva_cmd)
        except Exception as e :
          sy.log_critical(str(e))
          sy.log_critical('ERROR: Unsupported command {}.'.format(cmd))

if __name__ == '__main__' :

  import argparse, shutil, re, textwrap
  parser = argparse.ArgumentParser()
  parser.add_argument('-script_file_path', '-script', type=str,
                    help='Script file path',default='')
  parser.add_argument('-cmd', type=str,
                    help='One command',default='')
  parser.add_argument('-text_width', type=int,
                    help='Text width in number of chars', default=80)
  parser.add_argument('-do_not_record_cmd', '-norc',
                    action='store_true', default=False)
  parser.add_argument('-exit_when_done', '-exit',
                    action='store_true', default=False)
  parser.add_argument('-do_not_log', '-nolog',
                    action='store_true', default=False)
  parser.add_argument('-default_settings', type=str,
                    help='Default setting script file path',
                    default='default.tcl')
  parser.add_argument('-show_load_defautl', '-sld',
                    action='store_true', default=False)
  args = parser.parse_args()
  default_setting_name = args.default_settings
  sy = SYLVA()
  if os.path.exists(default_setting_name) :
    cmds = tcl_parser.parse_script(args.default_settings)
  else :
    print('Cannot find default_setting file: {}'.format(default_setting_name)
        + ', use build-in settings instead.')
    cmds = [
      'set_attribute information_level 0',
      'set_attribute create_schedule_plot true',
      'set_attribute effort_low 10',
      'set_attribute time_limit_in_sec 100',
      'set_attribute solutions_per_schedule 0',
      'set_attribute dse_engin dse_v1',
      'define_constraint -tmax 1000 -rmax 1000 -emax 1000 -amax 1000',
      'define_optimization -kr 1 -kt 1 -ka 1 -ke 1',
      'set_attribute dump_path ./',
      'set_attribute output_path ./output',
      'set_attribute output_hdl_path ./output/hdl',
      'set_attribute plot_path ./output/plots',
      'set_attribute lib_search_path {./lib}',
      'set_attribute vhdl_use_library {ieee.std_logic_1164.all, ieee.std_logic.all, work.all}',
    ]

    # with open(default_setting_name, 'w') as fp:
    #   fp.write('\n'.join(cmds) + '\n') # last \n is required

    cmds = [ tcl_parser.one_command.parseString(cmd) for cmd in cmds ]

  print(sy._topinfo)
  sy.log_critical('Collecting default settings ...')
  sy.record_cmd = False
  sy.show_info = args.show_load_defautl
  for cmd in cmds :
    sy.execute_command(cmd)

  sy.show_info = True
  sy.log_critical('Collecting default settings is done.')
  sy.record_cmd = True

  if args.script_file_path :
    sy.execute_command(['source', args.script_file_path])
    if not args.exit_when_done :
      start_interactive_shell(sy, control_commands)
  elif args.cmd :
    # try :
    if True :
      cmd = tcl_parser.one_command.parseString(args.cmd).asList()
      sy.log_critical('Executing command {} ...'.format(args.cmd))
      sy.execute_command(cmd)
      sy.log_critical('Executing command {} is done.'.format(args.cmd))
    # except Exception as e :
    #   sy.log_critical('{} is not a valid SYLVA command.'.format(args.cmd))
  else :
    start_interactive_shell(sy, control_commands)

