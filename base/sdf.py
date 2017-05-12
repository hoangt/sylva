##
# \package sylva.base.sdf
#
# All SDF graph related classes and methods.
##

import json

from sylva.base.sylva_base import SYLVABase


__author__ = 'Shuo Li <contact@shuol.li>'
__version__ = '2017-05-12'
__license__ = 'MIT'


##
# @brief      Class for data token type.
#
# This DataTokenType object will be used to represent
# the data token type in SDF graph.
##


class DataTokenType(SYLVABase):

    ##
    # \var size
    # The size of the data token in number of bits
    # and it should be an int object.
    #
    # \var name
    # The name of the user and it should be a str object.
    ##

    ##
    # @brief      Constructs the object.
    ##
    # @param      self  The object
    # @param      name  The name (str) of the data token type, e.g. int32
    # @param      size  The size (int) of the data token type
    # @param      dict_object  For loading from a stored dictionary object
    # Example:
    # \code{python}
    # int32 = DataTokenType('int32', 32)
    # int32_dict = dict(int32)
    # another_type = DataTokenType(dict_object=int32_dict)
    # print(another_type)
    # \endcode
    # Output: `Data token type: int32 (size: 32)`
    ##
    def __init__(self, name='int32', size=32, dict_object={}):

        self.name = name
        self.size = size

        if dict_object:
            SYLVABase.__init__(self, dict_object)

    ##
    # \copydoc sylva::base::sylva_base::SYLVABase::load_from_dict()
    ##
    @classmethod
    def load_from_dict(cls, dict_object):
        return cls(name=dict_object['name'], size=dict_object['size'])

    ##
    # \copydoc sylva::base::sylva_base::SYLVABase::__str__()
    ##
    def __str__(self):
        return f'Data token type: {self.name} (size: {self.size})'


d = DataTokenType()
dc = dict(d)
d = DataTokenType(dict_object=dc)
print(d)

##
# @brief      Class for port.
#
# One Port object will be used to represent
# one data communication port on an actor in SDF graph, where
# a port on an actor emits or receives one data token per clock cycle.
# <br /><br />
# The port is either input or output.
# The IO direction (input or output) is not defined in this class.
#
# + One Port is an input port if it is placed in the \ref Actor input_ports
# + One Port is an input port if it is placed in the \ref Actor output_ports
#
##


class Port(SYLVABase):

    ##
    # \var name
    # The name of the port, e.g. `din`.
    #
    # \var index
    # The index of the port among all ports in the same list,
    # e.g. all ports in list `input_ports` have unique index values.
    #
    # \var token_type
    # The data token type of the port, e.g. `DataTokenType(name='int32', size=32)`
    #
    # \var count
    # The number of data tokens to be consumed or produced per invocation.
    # One token per clock cycle is the minimum throughput.
    ##

    ##
    # @brief      Constructs the object.
    #
    # @param      self        The object.
    #
    # @param      name        The name of the port.
    # Example: `din`
    #
    # @param      index       The index of the port.
    # It is among all ports in the same list,
    # Example: all ports in list `input_ports` have unique index values.
    #
    # @param      token_type  The data token type of the port.
    # Example: `DataTokenType(name='int32', size=32)`
    # @param      count       The count
    ##
    def __init__(self, name='No name', index=0,
                 token_type=DataTokenType(name='int32', size=32),
                 count=1):

        self.name = name
        self.index = index
        self.token_type = token_type
        self.count = count

        self.__repr__ = self.__str__

    ##
    # \copydoc sylva::base::sylva_base::SYLVABase::__str__()
    ##
    def __str__(self):
        result = ''
        result += f'SDF port {self.name} index {self.index}' + '\n'
        result += f'  Token type  {self.token_type}' + '\n'
        result += f'  Token count {self.count}'
        return result

    ##
    # \copydoc sylva::base::sylva_base::SYLVABase::clone()
    ##
    def clone(self):
        return Port(self.name, self.index, self.type, self.count)

    ##
    # \copydoc sylva::base::sylva_base::SYLVABase::dict_object()
    ##
    def dict_object(self):
        return {'name': self.name,
                'index': self.index,
                'type': self.token_type.dict_object(),
                'count': self.count}


def load_sdf_port(json_dict):
    return Port(name=str(json_dict['name']),
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

        input_ports = [Port('%s_in_%s' % (name, i), i,
                            input_token_type[i], c)
                       for i, c in enumerate(inports)]
        output_ports = [Port('%s_out_%s' % (name, i), i,
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
