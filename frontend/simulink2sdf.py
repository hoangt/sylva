import os

# current_path = os.path.dirname(__file__)
# sylva_path = os.path.abspath(os.path.join(current_path, os.pardir))
# base_path = os.path.abspath(os.path.join(sylva_path, 'base'))
# misc_path = os.path.abspath(os.path.join(sylva_path, 'misc'))
# frontend_path = os.path.abspath(os.path.join(sylva_path, 'frontend'))
# sys.path.append(base_path)
# sys.path.append(misc_path)
# sys.path.append(frontend_path)

import mdl_reader
from sylva.base import sdf
from sylva.misc.util import all_files, merge_dicts, to_list
from functools import reduce


def elaborate(cls, mdl_path, lib_path=None, lib_ext=['.mdl']):
    actors, edges = simulink2sdf(mdl_path, {}, lib_path, lib_ext)
    return cls(actors, edges)


sdf.sdfg.elaborate = classmethod(elaborate)


def create_port(port_dict, port_index):

    port_name = port_dict['name']
    port_type = sdf.DataTokenType(str(port_dict['token type']), int(port_dict['token size']))
    port_count = port_dict['token count']
    return sdf.port(port_name, port_index, port_type, port_count)


def simulink2sdf(mdl_path, func_lib={}, lib_path=None, lib_ext=['.mdl']):

    lib_paths = to_list(lib_path)
    model = mdl_reader.simulink_model()
    lib = {}
    if os.path.isfile(mdl_path):
        model = mdl_reader.read_mdl_model(mdl_path)
    for lib_path in lib_paths:
        if os.path.exists(lib_path):
            if os.path.isfile(lib_path):
                temp_lib = mdl_reader.read_mdl_lib_as_dict(lib_path)
            else:
                temp_lib = reduce(merge_dicts, [mdl_reader.read_mdl_lib_as_dict(f)
                                                for f in all_files(lib_path, lib_ext)])
            lib.update(temp_lib)
    lib.update(func_lib)

    actors = create_actors(lib, model)
    edges = create_edges(model, actors)
    (actors, edges) = assign_actor_indexes(actors, edges)
    return actors, edges


def create_actors(lib, model):

    all_actors = []

    for block_item in model.system.blocks:
        if 'SourceBlock' in block_item.keys():

            all_actors.append(sdf.actor())
            func_path = block_item['SourceBlock']
            func_name = func_path.split('/')[-1]
            lib_name = ''.join(func_path.split('/')[:-1])

            all_actors[-1].name = func_name

            # only use the first match
            source_block = [value for key, value in lib.items()
                            if key == func_path]

            if len(source_block) == 0:
                raise Exception('Function %s is not in library %s.'
                                % (func_name, lib_name))

            source_block = source_block[0]
            all_actors[-1].input_ports \
                = [create_port(source_block['input_ports'][i], i)
                   for i in source_block['input_ports'].keys()]
            all_actors[-1].output_ports \
                = [create_port(source_block['output_ports'][i], i)
                   for i in source_block['output_ports'].keys()]

    return all_actors


def create_edges(model, actors):

    edges = []

    for line_item in model.system.lines:

        src_actor = [a for a in actors
                     if a.name == line_item['SrcBlock']][0]
        src_port_index = int(line_item['SrcPort']) - 1  # to 0 based indexing
        src_port = src_actor.output_ports[src_port_index]
        dest_actor = [a for a in actors
                      if a.name == line_item['DstBlock']][0]
        dest_port_index = int(line_item['DstPort']) - 1
        dest_port = dest_actor.input_ports[dest_port_index]
        edges.append(sdf.edge(src_actor, src_port, dest_actor, dest_port))

    return edges


def assign_actor_indexes(actors, edges):

    index = 0

    assigned_actors = []
    # first, assign all root actors
    for a in actors:
        if a.previous == []:
            assigned_actors.append(a)
            a.index = index
            index += 1

    # then assign other actors
    for a in assigned_actors:
        for e in a.next:
            if e.dest_actor not in assigned_actors:
                p = e.dest_actor.previous
                all_done = True
                for edge in p:
                    if edge.src_actor not in assigned_actors:
                        all_done = False
                        break
                if all_done == True:
                    assigned_actors.append(e.dest_actor)
                    e.dest_actor.index = index
                    index += 1

    return (assigned_actors, edges)
