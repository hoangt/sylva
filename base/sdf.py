# coding: utf-8

# @package docstring
# Documentation for this module.
# More details.

import json

if 'Data type class':

    # Data token type class
    #  This DataTokenType object will be used to represent the data token type in \ref sdfg.
    class DataTokenType(object):

        # Creates a new DataTokenType object.
        #  \param name The name of the user and it should be a str object.
        #  \param size The size of the data token in number of bits and it should be an int object.
        def __init__(self, name='int32', size=32):

            # \var name
            # The name of the user and it should be a str object.
            self.name = name

            # \var size
            # The size of the data token in number of bits and it should be an int object.
            self.size = size

        # Convert the current object to a string format.
        #  \return Returns a human friendly string (type is str) of this object
        def __str__(self):
            return f'{self.name} (size {self.size})'

        # Convert the current object to a string format.
        #  This method will be invoked some time instead of self.__str__().
        #  \return Returns a human friendly string (type is str) of this object
        def __repr__(self):
            return self.__str__()

        # Creates a dict object with only primitive python objects to store the current \ref DataTokenType object.
        #  Example:
        #  {'name': 'int32', 'size': 32}
        #  \return a dict object
        def serialize(self):
            return {'name': self.name, 'size': self.size}

        # Creates a DataTokenType object from a dict object that is produced by the serialize method.
        #  Example:
        #  DataTokenType_dict = {'name': 'int32', 'size': 32}
        #  \param DataTokenType_dict The dict object having all information to construct a new DataTokenType object.
        #  \return a DataTokenType object
        @classmethod
        def deserialize(cls, data_token_type_dict={'name': 'int32', 'size': 32}):
            return cls(name=data_token_type_dict['name'], size=data_token_type_dict['size'])

if 'SDF port class':

    class port(object):

        '''
          IO port class for an actor
          --------------------------

          The port is either input or output.
          The IO direction (input or output) is not defined in this class.
          A port emits or receives one data token per clock cycle.

          1. name: string, port name
          2. index: integer, port index in either input port list or output port list
          3. type: DataTokenType, data token type of this port.
            The width of the port is defined by `type`.
          4. count: integer, number of data tokens to be transferred via this port
        '''

        def __init__(self, name='no_port_name', index=0,
                     type=DataTokenType(name='integer range 0 to 3', size=2),
                     count=1):

            self.name = name
            self.index = index
            self.type = type
            self.count = count

            self.__repr__ = self.__str__

        def __str__(self):
            return 'SDF port %s index %s type %s count %s' \
                % (self.name, self.index, self.type, self.count)

        def clone(self):
            return port(self.name, self.index, self.type, self.count)

        def serialize(self):
            return {'name': self.name,
                    'index': self.index,
                    'type': self.type.serialize(),
                    'count': self.count}

    def load_sdf_port(json_dict):
        return port(name=str(json_dict['name']),
                    index=int(json_dict['index']),
                    type=DataTokenType.deserialize(json_dict['type']),
                    count=int(json_dict['count']))

if 'SDF edge class':

    class edge:

        '''
          Communication Edge
        '''

        def __init__(self,
                     src_actor=None, src_port=None,
                     dest_actor=None, dest_port=None):

            self.src_actor = src_actor
            self.dest_actor = dest_actor
            self.src_port = src_port
            self.dest_port = dest_port

            if isinstance(src_actor, actor):
                src_actor.next.append(self)
            if isinstance(dest_actor, actor):
                dest_actor.previous.append(self)

            self.__repr__ = self.__str__

        def __str__(self):
            result = f'SDF edge \n'
            result += f'  from {self.src_actor} ({self.src_port})\n'
            result += f'  to {self.dest_actor}, ({self.dest_port})'
            return result

        def clone(self):
            return edge(self.src_actor, self.src_port.clone(),
                        self.dest_actor, self.dest_port.clone())

        def serialize(self):
            return {'src_actor': self.src_actor.index,
                    'dest_actor': self.dest_actor.index,
                    'src_port': self.src_port.index,
                    'dest_port': self.dest_port.index}

    def load_sdf_edge_index(json_dict):

        src_actor_index = int(json_dict['src_actor'])
        src_port_index = int(json_dict['src_port'])

        dest_actor_index = int(json_dict['dest_actor'])
        dest_port_index = int(json_dict['dest_port'])

        return (src_actor_index, src_port_index, dest_actor_index, dest_port_index)

    def load_sdf_edge(json_dict, actors):

        src_actor_index, src_port_index, dest_actor_index, dest_port_index = load_sdf_edge_index(json_dict)

        src_actor = actors[src_actor_index]
        src_port = src_actor.output_ports[src_port_index]

        dest_actor = actors[dest_actor_index]
        dest_port = dest_actor.input_ports[dest_port_index]

        return edge(src_actor, src_port, dest_actor, dest_port)

    def create_sdf_edge(src_actor_index, src_port_index,
                        dest_actor_index, dest_port_index, actors):

        src_actor = actors[src_actor_index]
        src_port = src_actor.output_ports[src_port_index]

        dest_actor = actors[dest_actor_index]
        dest_port = dest_actor.input_ports[dest_port_index]

        return edge(src_actor, src_port, dest_actor, dest_port)

    def connect(src_actor, src_port_index, src_data_token_count,
                dest_actor, dest_port_index, dest_data_token_count,
                data_token_type=DataTokenType('noName', 1)):
        '''
          Create a connection between two ports of two actors.
          Ports are automatically generated.
        '''

        src_ports = [output_port
                     for output_port in src_actor.output_ports
                     if output_port.index == src_port_index]

        if len(src_ports) == 1:
            src_port = src_ports[0]
        else:
            src_port = port(name='%s_output_port_%d'
                            % (src_actor.name, src_port_index),
                            index=src_port_index,
                            type=data_token_type,
                            count=src_data_token_count)

        dest_ports = [input_port
                      for input_port in dest_actor.input_ports
                      if input_port.index == dest_port_index]

        if len(dest_ports) == 1:
            dest_port = dest_ports[0]
        else:
            dest_port = port(name='%s_input_port_%d'
                             % (dest_actor.name, dest_port_index),
                             index=dest_port_index,
                             type=data_token_type,
                             count=dest_data_token_count)

        return edge(src_actor, src_port, dest_actor, dest_port)

if 'SDF actor class':

    class actor:

        '''
          SDF actor class
          ---------------

          An actor is assumed to be within an SDF graph.
          An actor name is the identification of its functionality.
        '''

        def __init__(self, name='noName', index=-1,
                     input_ports=[], output_ports=[], base_actor=None,
                     next=[], previous=[]):

            self.base_actor = base_actor
            self.name = name
            self.index = index
            self.input_ports = input_ports
            self.output_ports = output_ports
            self.next = []
            self.previous = []

            self.__repr__ = self.__str__

        def __str__(self):
            return 'SDF actor %s index %s' % (self.name, self.index)

        def clone(self):
            return actor(self.name, self.index,
                         list(self.input_ports),
                         list(self.output_ports),
                         self.base_actor,
                         list(self.next), list(self.previous))

        def serialize(self, keys=[], include_base_actor=False):

            result = {'name': self.name,
                      'index': self.index,
                      'input_ports': [p.serialize() for p in self.input_ports],
                      'output_ports': [p.serialize() for p in self.output_ports],
                      'next': [e.serialize() for e in self.next],
                      'previous': [e.serialize() for e in self.previous]}

            for key in keys:
                result[key] = getattr(self, key)

            if include_base_actor:
                result['base_actor_index'] = self.base_actor.index

            return result

    def load_sdf_actor(json_dict, keys=[]):

        result = actor(name=str(json_dict['name']),
                       index=int(json_dict['index']),
                       input_ports=[load_sdf_port(p)
                                    for p in json_dict['input_ports']],
                       output_ports=[load_sdf_port(p)
                                     for p in json_dict['output_ports']],
                       next=[load_sdf_edge_index(e)
                             for e in json_dict['next']],
                       previous=[load_sdf_edge_index(e)
                                 for e in json_dict['previous']])
        actor_keys = keys or [
            'input_end', 'output_start',
            'buffer_end', 'start', 'end',
            'base_actor_index', 'fimp_index']

        for key in actor_keys:
            if key in json_dict.keys():
                setattr(result, key, json_dict[key])

        return result

    def make_sdf_actor(name, index, inports, outports,
                       input_token_type=[DataTokenType('std_logic', 1)],
                       output_token_type=[DataTokenType('std_logic', 1)]):

        input_ports = [port('%s_in_%s' % (name, i), i,
                            input_token_type[i], c)
                       for i, c in enumerate(inports)]
        output_ports = [port('%s_out_%s' % (name, i), i,
                             output_token_type[i], c)
                        for i, c in enumerate(outports)]

        return actor(name=name, index=index,
                     input_ports=input_ports, output_ports=output_ports)

if 'serialize/deserialize':

    def serialize_sdf_graph(actors, edges):
        result = {}
        result['actors'] = [actor.serialize() for actor in actors]
        result['edges'] = [edge.serialize() for edge in edges]
        return result

    def load_sdf_graph(json_dict, actor_keys=[]):
        actors = []
        edges = []
        actors = [load_sdf_actor(a, actor_keys) for a in json_dict['actors']]
        edges = [load_sdf_edge(e, actors) for e in json_dict['edges']]
        return (actors, edges)

    def dump_to_file(item, filepath, indent=2):
        f = open(filepath, 'w+')
        f.write(json.dumps(item, indent=2))
        f.close()

    def add_actor(actors, name, index, inports, outports,
                  input_token_type=[DataTokenType('std_logic', 1)],
                  output_token_type=[DataTokenType('std_logic', 1)]):

        actors.append(make_sdf_actor(name, index,
                                     inports, outports, input_token_type, output_token_type))

    def add_edge(edges, src_actor_index, src_port_index,
                 dest_actor_index, dest_port_index, actors):

        return edges.append(create_sdf_edge(
            src_actor_index, src_port_index,
            dest_actor_index, dest_port_index, actors))

if 'sdf graph':

    default_actor_style = {
        'node_shape': 'circle',
        'facecolor': 'white',
        'edgecolor': 'black',
        'linestyle': 'solid',
        'linewidth': 1,
        'radius': 0.4,
        'width': 0.4,
        'height': 0.4,
        'margin': 0.8,
    }

    default_annotation_style = {
        'color': 'black',
        'fontweight': 'normal',
        'fontsize': 12,
        'ha': 'center',
        'va': 'center'}

    import matplotlib.pyplot as plt

    def get_layered_actors(actors):
        result = []
        checked = []

        while not result or result[-1]:
            result.append([])
            for a in actors:
                if a not in checked:
                    if not a.previous:
                        result[-1].append(a)
                        continue
                    else:
                        for pa in a.previous:
                            if pa.src_actor in checked:
                                if a not in result[-1]:
                                    result[-1].append(a)
            checked += result[-1]

        return result[:-1]

    class sdfg(object):

        def __init__(self, actors, edges):
            self.actors = actors
            self.edges = edges

        @classmethod
        def load(cls, json_dict, actor_keys=[]):
            actors, edges = load_sdf_graph(json_dict, actor_keys)
            return sdfg(actors, edges)

        @property
        def layered_actors(self):
            return get_layered_actors(self.actors)

        def plot(self, actor_style=None, annotation_style=None):

            actors_2d = self.layered_actors

            _actor_style = default_actor_style
            _actor_style.update(actor_style or {})

            _annotation_style = default_annotation_style
            _annotation_style.update(annotation_style or {})

            margin = _actor_style.pop('margin', 0)
            node_shape = _actor_style.pop('node_shape', '')

            if node_shape.lower() == 'circle':
                _actor_style.pop('width', None)
                _actor_style.pop('height', None)
                shape_width = shape_height = 2 * _actor_style['radius']

            node_shape = eval('mpatches.{}'.format(node_shape.capitalize()))

            xmin = -(shape_width / 2 + margin)
            xmax = len(actors_2d) * (shape_width + margin)
            ymin = -max([len(l) for l in actors_2d]) * (shape_width + margin)
            ymax = (shape_width / 2 + margin)
            plt.axis([xmin, xmax, ymin, ymax])
            plt.gca().set_aspect('equal')
            plt.axis('off')
            actor_nodes = {}

            for layer_index, layer in enumerate(actors_2d):
                for actor_index, actor in enumerate(layer):
                    x = layer_index * (shape_width + margin)
                    y = -actor_index * (shape_height + margin)
                    actor_node = node_shape((x, y), **_actor_style)
                    actor_nodes[actor.index] = actor_node
                    plt.gca().add_patch(actor_node)
                    plt.gca().annotate(actor.index, (x, y), **_annotation_style)
                    actor.lpos = (layer_index, actor_index)
                    actor.pos = (x, y)
                    actor.left = (x - shape_width / 2, y)
                    actor.right = (x + shape_width / 2, y)
                    actor.top = (x, y + shape_width / 2)
                    actor.bottom = (x, y - shape_width / 2)

            for layer_index, layer in enumerate(actors_2d):
                for actor_index, actor in enumerate(layer):
                    for next_edge in actor.next:
                        na = next_edge.dest_actor
                        src = actor.pos
                        dest = na.pos
                        plt.gca().annotate('', dest, src,
                                           arrowprops=dict(arrowstyle='->',
                                                           patchA=actor_nodes[actor.index],
                                                           patchB=actor_nodes[na.index],
                                                           shrinkA=0, shrinkB=0,
                                                           ec=_actor_style['edgecolor'],
                                                           connectionstyle="arc3,rad=.1",
                                                           ),)

            return plt
