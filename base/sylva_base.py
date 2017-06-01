##
# \package sylva.base.sylva_base
# All basic classes and methods for SYLVA project
##

import json
import os
import sys

import graphviz
from ortools.constraint_solver import pywrapcp

__author__ = 'Shuo Li <contact@shuol.li>'
__version__ = '2017-05-26'
__license__ = 'https://opensource.org/licenses/MIT'


##
# @brief      The base object for SYLVA project
#
# All objects are inherented from this object.
#
#
# + Use `dict(obj)` to convert a SYLVABase object to dictionary object
# for serialization (<https://en.wikipedia.org/wiki/Serialization>).
#
# + For de-serialization, use `**` before the dictioary object.
#
# Check \ref dump_and_load.py for example.
#
##


class SYLVABase(dict, object):

    ##
    # \example dump_and_load.py
    ##

    ##
    # @brief      Override python build-in set attribute method
    ##
    # @param      self        The object
    # @param      attr_name   The attribute name
    # @param      attr_value  The attribute value
    ##
    def __setattr__(self, attr_name, attr_value):
        self[attr_name] = attr_value

    ##
    # @brief      Override python build-in get attribute method
    ##
    # @param      self       The object
    # @param      attr_name  The attribute name
    ##
    # @return     value of the attribute
    ##
    def __getattr__(self, attr_name):
        return self.get(attr_name)

    ##
    # @brief      Returns a string representation of the object.
    ##
    # @param      self  The object
    ##
    # @return     String representation of the object.
    ##
    def __str__(self):
        return str(self.as_dict())

    ##
    # @brief      Get the storage form of this object
    #
    # It is possible that the field of this object is a list or a dictionary
    # and the elements/values are SYLVABase objects.
    ##
    # @param      self  The object
    ##
    # @return     A dict object as the storage form
    ##
    def as_dict(self, exclude=[]):
        result = {}
        for key, value in self.items():
            if key not in exclude:
                if isinstance(value, SYLVABase):
                    result[key] = value.as_dict()
                elif isinstance(value, list):
                    if value:
                        if isinstance(value[0], SYLVABase):
                            result[key] = [v.as_dict() for v in value]
                        else:
                            result[key] = value
                elif isinstance(value, dict):
                    if value:
                        result[key] = {}
                        for k, v in value.items():
                            if isinstance(v, SYLVABase):
                                result[key][k] = v.as_dict()
                            else:
                                result[key][k] = v
                elif isinstance(value, (str, int, complex)):
                    result[key] = value

        return result

    ##
    # @brief      Gets the clone.
    ##
    # @param      self  The object
    ##
    # @return     The clone.
    ##
    def get_clone(self):
        return self.__class__.load_from_dict(self.as_dict())

    ##
    # \var clone
    # Clone of the current object
    ##
    clone = property(get_clone)

    ##
    # @brief      Loads a from dictionary.
    ##
    # @param      cls       The cls
    # @param      dict_obj  The dictionary object
    ##
    # @return     Loaded object
    ##
    @classmethod
    def load_from_dict(cls, dict_obj):
        return cls(**dict_obj)

    ##
    # @brief      Loads an object from file.
    ##
    # @param      cls       The cls
    # @param      filepath  The filepath
    ##
    # @return     Loaded object
    ##
    @classmethod
    def load_from_file(cls, filepath=None):
        if filepath is None:
            filepath = f'{cls.__name__}_store.json'
        return cls.load(filepath)

    ##
    # @brief      Loads an object from dictionary or json file
    ##
    # @param      cls   The cls
    # @param      arg   The argument
    ##
    # @return     An object
    ##
    @classmethod
    def load(cls, arg):
        if isinstance(arg, dict):
            return cls.load_from_dict(arg)
        elif isinstance(arg, str) and os.path.exists(arg):
            with open(arg, 'r+', encoding='utf-8') as fp:
                dict_obj = json.load(fp)
            return cls.load_from_dict(dict_obj)
        elif isinstance(arg, str) and isinstance(eval(arg), dict):
            return cls.load_from_dict(eval(arg))
        elif arg is None:
            return None
        raise ValueError(f'useless argument {arg}.')

    ##
    # @brief      Dump to file
    ##
    # @param      self      The object
    # @param      filepath  The filepath
    ##
    ##
    def dump_to_file(self, filepath=None):
        if filepath is None:
            filepath = f'{self.__class__.__name__}_store.json'
        dict_obj = self.as_dict()
        with open(filepath, 'w+', encoding='utf-8') as fp:
            json.dump(dict_obj, fp, indent=4)
        return filepath

    ##
    # @brief      Test if two objects are equal
    ##
    # By default, if two objects has the same name or the same index
    # we consider they are equal.
    ##
    # @param      self          The object
    # @param      sylva_object  The sylva object
    ##
    # @return     { description_of_the_return_value }
    ##
    def __eq__(self, sylva_object):
        if hasattr(self, 'name') and hasattr(sylva_object, 'name'):
            return self.name == sylva_object.name
        elif hasattr(self, 'index') and hasattr(sylva_object, 'index'):
            return self.index == sylva_object.index
        return False


##
# @brief      Class for data token type.
#

# This DataTokenType object will be used to represent
# the data token type in SDF graph.
#
##


class DataTokenType(SYLVABase):

    ##
    # \var name
    # The name of the user and it should be a str object.
    #
    # \var size
    # The size of the data token in number of bits
    # and it should be an int object.
    ##

    ##
    # @brief      Constructs the object.
    ##
    # @param      self    The object
    # @param      name    \copydoc DataTokenType::name
    # @param      size    \copydoc DataTokenType::size
    # @param      kwargs  other keyworad arguments for future usage
    ##
    def __init__(self, name='bit', size=1):
        self.name = name
        self.size = size

    ##
    # @brief      Loads an object from dictionary.
    ##
    # @param      cls       The cls
    # @param      dict_obj  The dictionary object
    ##
    # @return     a DataTokenType object
    ##
    @classmethod
    def load_from_dict(cls, dict_obj):
        name = dict_obj.get('name')
        size = dict_obj.get('size')
        return cls(name=name, size=size)

    ##
    # @brief      Test if two DataTokenType objects are equal
    ##
    # If their name and size are the same,
    # we consider they are equal.
    ##
    # @param      self   The object
    # @param      dtype  The dtype
    ##
    # @return     { description_of_the_return_value }
    ##
    def __eq__(self, dtype):
        return self.name == dtype.name and self.size == dtype.size


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
# + One Port is an input port if it is placed in the Actor input_ports
# + One Port is an input port if it is placed in the Actor output_ports
#
##


class Port(SYLVABase):

    ##
    # \var name
    # The name of the port, e.g `din`.
    #
    # \var index
    # The index of the port among all ports in the same list,
    # e.g all ports in list `input_ports` have unique index values.
    #
    # \var dtype
    # The data token type of the port,
    # e.g `DataTokenType(name='int32', size=32)`
    #
    # \var count
    # The number of data tokens to be consumed or produced per invocation.
    # One token per clock cycle is the minimum throughput.
    ##

    ##
    # @brief      Constructs the object.
    #
    # @param      self   The object.
    #
    # @param      name   \copydoc Port::name
    # @param      index  \copydoc Port::index
    # @param      dtype  \copydoc Port::data_token_type
    # @param      count  \copydoc Port::count
    ##
    def __init__(self, name='din', index=0, dtype=DataTokenType(), count=1):
        self.name = name
        self.index = index
        if isinstance(dtype, dict):
            self.dtype = DataTokenType.load_from_dict(dtype)
        else:
            self.dtype = dtype
        self.count = count

    ##
    # @brief      Loads a from dictionary.
    ##
    # @param      cls       The cls
    # @param      dict_obj  The dictionary object
    ##
    # @return     { description_of_the_return_value }
    ##
    @classmethod
    def load_from_dict(cls, dict_obj):
        name = dict_obj.get('name')
        index = dict_obj.get('index')
        dtype = DataTokenType.load_from_dict(dict_obj.get('dtype'))
        count = dict_obj.get('count')
        return cls(name=name, index=index, dtype=dtype, count=count)

    ##
    # @brief      Test if two Port objects are equal
    ##
    # If their name and DataTokenType are equal,
    # we consider they are the same port.
    ##
    # @param      self  The object
    # @param      port  The port
    ##
    # @return     { description_of_the_return_value }
    ##
    def __eq__(self, port):
        return self.name == port.name and self.dtype == port.dtype

##
# @brief      Class for SDF actor.
#
# \dotfile "SDFG_example.gv" ["SDFG"]
# The name of the Actor is its function name, e.g `a`, `b`.
# The index of the Actor is the unique integer identifier
# of the actor in an SDFG or HSDFG.
# All the data source actors of one Actor object will have lower indexes
# than that Actor object.
# e.g `a.index = 0`, `d.index = 1`, `b.index = 2`, `c.index = 3`
##


class Actor(SYLVABase):

    ##
    # \var name
    # The functio name of this actor, e.g fft
    #
    # \var index
    # The unique index of this actor in an SDFG or HSDFG
    #
    # \var input_ports
    # The list of the input ports of this actor
    #
    # \var output_ports
    # The list of the output ports of this actor
    #
    # \var outgoing_edges
    # The outgoing Edge list.
    # Example:
    # \dotfile "SDFG_example.gv" ["SDFG"]
    # \dotfile "HSDFG_example.gv" ["HSDFG"]
    # in the SDFG b.outgoing_edges = [b->c],
    # in the HSDFG b_0.outgoing_edges = [b_0->c_0, b_0->c_1]
    #
    # \var incoming_edges
    # The incoming Edge list.
    # Example:
    # \dotfile "SDFG_example.gv" ["SDFG"]
    # \dotfile "HSDFG_example.gv" ["HSDFG"]
    # in the SDF graph `b.incoming_edges = [a->b, d->b]`,
    # in the HSDF graph
    # `b_0.incoming_edges = [a_0->b_0, d_0->b_0, d_1->b_0]`,
    # `b_1.incoming_edges = [a_0->b_1, d_2->b_1, d_2->b_1]`
    #
    # \var base_actor
    # When an actor is in one HSDFG,
    # `base_actor` is the corresponding SDFG Actor.
    # Example:
    # \dotfile "SDFG_example.gv" ["SDFG"]
    # \dotfile "HSDFG_example.gv" ["HSDFG"]
    # `a_0.base_actor` is `a`, `a_1.base_actor` is also `a`.
    #
    # \var child_actors
    # When an actor is in one HSDFG,
    # child_actors of the SDFG Actor is the corresponding HSDFG Actors.
    # Example:
    # \dotfile "SDFG_example.gv" ["SDFG"]
    # \dotfile "HSDFG_example.gv" ["HSDFG"]
    # `a.child_actors` is `[a_0]`, `b.child_actors` is `[b_0, b_1]`
    ##

    ##
    # \var _index
    # The default actor index holder
    ##
    _index = 0

    ##
    # @brief      Reset the building index of Actor
    ##
    # @param      cls     The Actor class
    # @param      value   The value to reset, default 0
    ##
    @classmethod
    def reset_index(cls, value=0):
        cls._index = value

    ##
    # @brief      Constructs the object.
    ##
    # @param      self            The object
    # @param      name            \copydoc Actor::name
    # @param      index           \copydoc Actor::index
    # @param      input_ports     \copydoc Actor::input_ports
    # @param      output_ports    \copydoc Actor::output_ports
    # @param      outgoing_edges  \copydoc Actor::outgoing_edges
    # @param      incoming_edges  \copydoc Actor::incoming_edges
    # @param      base_actor      \copydoc Actor::base_actor
    # @param      child_actors    \copydoc Actor::child_actors
    ##
    def __init__(self, name='actor_name', index=-1, input_ports=[], output_ports=[], incoming_edges=[], outgoing_edges=[],
                 base_actor=None, child_actors=[]):

        self.name = name

        # if index is not provided
        # we will use Actor._index as index
        # and add one after using Actor._index
        if index < 0:
            index = Actor._index
            Actor._index += 1

        self.index = index

        # The default [] is evaluated when module is loaded and
        # every object's __init__ method will use the SAME empty list.
        # We should avoid it.
        #
        # So here we need to copy input lists so that
        # when initilized with empty list
        # it will not point to the same empty list []
        self.input_ports = list(input_ports)
        self.output_ports = list(output_ports)
        self.outgoing_edges = list(outgoing_edges)
        self.incoming_edges = list(incoming_edges)

        self.base_actor = base_actor
        self.child_actors = list(child_actors)

    ##
    # @brief      Loads an Actor object from dictionary.
    ##
    # @param      cls       The cls
    # @param      dict_obj  The dictionary object
    ##
    # @return     Actor object
    ##
    @classmethod
    def load_from_dict(cls, dict_obj):

        name = str(dict_obj.get('name', 'actor_name'))
        index = int(dict_obj.get('index', -1))

        input_ports = [Port.load(p)
                       for p in dict_obj.get('input_ports', [])]
        output_ports = [Port.load(p)
                        for p in dict_obj.get('output_ports', [])]

        incoming_edges = [Edge.load(e)
                          for e in dict_obj.get('incoming_edges', [])]
        outgoing_edges = [Edge.load(e)
                          for e in dict_obj.get('outgoing_edges', [])]

        base_actor = Actor.load(dict_obj.get('base_actor', None))
        child_actors = [Actor.load(c)
                        for c in dict_obj.get('child_actors', [])]

        return cls(name, index, input_ports, output_ports,
                   incoming_edges, outgoing_edges, base_actor, child_actors)

    ##
    # @brief      Test if two Actor objecets are equal
    ##
    # If their name and index are equal,
    # we consider they are the same actor.
    ##
    # @param      self   The object
    # @param      actor  The actor
    ##
    # @return     { description_of_the_return_value }
    ##
    def __eq__(self, actor):
        return self.name == actor.name and self.index == actor.index

    ##
    # @brief      Get the dictionary representation of this object
    ##
    # @param      self     The object
    # @param      exclude  The exclude
    ##
    # @return     dictionary object
    ##
    def as_dict(self, exclude=[]):
        return SYLVABase.as_dict(self, exclude=['base_actor', 'fimp_instance'] + exclude)


##
# @brief      Class for communication edge.
#
# One Edge object will be used to represent
# one data communication edge between two Port objects
# of two Actor objects in SDFG, where
# a port on an actor emits or receives a constat number of data token
# per clock cycle.
# Each Edge object has one source actor, one source port,
# one destination actor and one destination port.
##


class Edge(SYLVABase):

    ##
    # \var src_actor
    # The source Actor.
    # The current Edge object will be added to \ref Actor.outgoing_edges
    # "src_actor.outgoing_edges" (list of outgoing edges)
    #
    # \var src_port
    # The source Port
    #
    # \var dest_actor
    # The destination Actor.
    # The current Edge object will be added to \ref Actor.incoming_edges
    # "dest_actor.incoming_edges" (list of incoming edges)
    #
    # \var dest_port
    # The destination Port
    ##

    ##
    # @brief      Constructs the object.
    ##
    # @param      self         The object
    # @param      src_actor    \copydoc Edge::src_actor
    # @param      src_port     \copydoc Edge::src_port
    # @param      dest_actor   \copydoc Edge::dest_actor
    # @param      dest_port    \copydoc Edge::dest_port
    ##
    def __init__(self, src_actor, src_port, dest_actor, dest_port):

        self.src_actor = src_actor
        self.src_port = src_port
        self.dest_actor = dest_actor
        self.dest_port = dest_port

        self.src_actor.outgoing_edges.append(self)
        self.dest_actor.incoming_edges.append(self)

    def as_dict(self, exclude=[]):

        result = {}
        actor_exclude = ['incoming_edges', 'outgoing_edges']

        if 'src_actor' not in exclude:
            result['src_actor'] = self.src_actor.as_dict(actor_exclude)
        if 'src_port' not in exclude:
            result['src_port'] = self.src_port.as_dict()
        if 'dest_actor' not in exclude:
            result['dest_actor'] = self.dest_actor.as_dict(actor_exclude)
        if 'dest_port' not in exclude:
            result['dest_port'] = self.dest_port.as_dict()

        return result

    @classmethod
    def load_from_dict(cls, dict_obj):
        src_actor = Actor.load(dict_obj.get('src_actor', {}))
        src_port = Port.load(dict_obj.get('src_port', {}))
        dest_actor = Actor.load(dict_obj.get('dest_actor', {}))
        dest_port = Port.load(dict_obj.get('dest_port', {}))
        return cls(src_actor, src_port, dest_actor, dest_port)

##
# @brief      Class for Data Flow Graph.
#
# DFG is composed of two lists: actors and edges.
##


class DFG(SYLVABase):

    ##
    # \var actors
    # The DFG Actor list.
    # The index of each Actor object is the index in this list.
    #
    # \var edges
    # The DFG Edge list.
    ##

    ##
    # @brief      Constructs the object.
    #
    # More information about DFG, SDFG and HSDFG,
    # check <https://goo.gl/3Gio5l> (last checked 017-05-16)
    ##
    # @param      self                    The object
    # @param      actors                  \copydoc DFG::actors
    ##
    def __init__(self, actors, reassign_actor_indexes=False):
        self.actors = list(actors)
        self.edges = [e for a in self.actors for e in a.outgoing_edges]
        if reassign_actor_indexes:
            self.reassign_actor_indexes()
        else:
            self.sort_actors()

    @classmethod
    def load_from_dict(cls, dict_obj):
        actors = [Actor.load(a) for a in dict_obj.get('actors', [])]
        for a in actors:
            for e in a.outgoing_edges:
                e.src_actor = a
                port_name = e.src_port.name
                e.src_port = next(p for p in a.output_ports
                                  if p.name == port_name)
                e.dest_actor = next(a for a in actors
                                    if a == e.dest_actor)
                e.dest_port = next(p for p in e.dest_actor.input_ports
                                   if p.name == e.dest_port.name)
        return DFG(actors)

    ##
    # @brief      Sort actors based on index, ascending order
    ##
    # @param      self  The object
    ##
    def sort_actors(self):
        self.actors = sorted(self.actors, key=lambda a: a.index)

    ##
    # @brief      Get actor layers
    ##
    # Each layer has all the data dependent actors in the last layer
    # and possibly also in previous layers.
    ##
    # @param      self  The object
    ##
    # @return     List of list
    ##

    def get_actor_layers(self):

        result = []
        checked_actors = []

        def add_actor(current_actor, checked_actors):
            if current_actor in checked_actors:
                return False

            if not current_actor.incoming_edges:
                return True

            for one_edge in current_actor.incoming_edges:
                if one_edge.src_actor not in checked_actors:
                    return False

            return True

        while not result or result[-1]:
            result.append([])
            for current_actor in self.actors:
                if add_actor(current_actor, checked_actors):
                    if current_actor not in result[-1]:
                        result[-1].append(current_actor)
            checked_actors += result[-1]

        return result[:-1]

    ##
    # \var actor_layers
    # \copybrief HSDFG::\_actor\_layers
    # \copydetails HSDFG::\_actor\_layers
    ##
    actor_layers = property(get_actor_layers)

    ##
    # @brief      Assign indexes to Actor objects based on data dependency
    #
    # Data source Actor will alwyas has less index then data sink Actor.
    ##
    # @param      self  The object
    ##
    def reassign_actor_indexes(self):
        result = []
        index = 0
        for one_layer in self.actor_layers:
            for one_actor in one_layer:
                one_actor.index = index
                result.append(one_actor)
                index += 1
        self.actors = result

    ##
    # @brief      Create a DOT object (graphviz.Digraph)
    #
    # Check <http://www.graphviz.org/> (last check 2017-05-16) for
    # more information about DOT format. An online editor can be
    # found at <http://viz-js.com/> (last check 2017-05-16). #
    ##
    # @param      self           The object
    # @param      name           The name of the graph, default = `DFG`
    # @param      render_format  The render format
    # @param      graph_attr     Graph style attributes for rendering
    # @param      node_attr      Actor style attributes for rendering
    # @param      edge_attr      Edge style attributes for rendering
    #
    # @return     graphciz.Digraph object.
    #
    def get_digraph(self, name=None, render_format='svg', graph_attr=None, node_attr=None, edge_attr=None):

        if name is None:
            name = self.__class__.__name__

        if graph_attr is None:
            graph_attr = {}

        if node_attr is None:
            node_attr = {'fillcolor': 'white', 'style': 'filled'},

        if edge_attr is None:
            edge_attr = {'labeldistance': '1'}

        result = graphviz.Digraph(name=name, graph_attr=graph_attr,
                                  format=render_format,
                                  node_attr=node_attr,
                                  edge_attr=edge_attr)

        for actor in self.actors:
            actor_name = f'{actor.name}_{actor.index}'
            actor_label = f'{actor.name}\\n{actor.index}'
            result.node(name=actor_name, label=actor_label,
                        tooltip=actor_name, URL=r'\ref Actor')

        for edge in self.edges:
            src_name = f'{edge.src_actor.name}_{edge.src_actor.index}'
            dest_name = f'{edge.dest_actor.name}_{edge.dest_actor.index}'
            result.edge(tail_name=src_name, head_name=dest_name,
                        taillabel=str(edge.src_port.count) + ' ',
                        headlabel=str(edge.dest_port.count) + ' ')

        return result

    def as_dict(self, exclude=[]):
        return SYLVABase.as_dict(self, exclude=['edges'] + exclude)


##
# @brief      Class for HSDFG.
#
# HSDFG is composed of two lists: actors and edges
# just like DFG.
#
# HSDFG is a special case of SDFG,
# therefore, HSDFG has less mainpulation methods than SDFG.
##


class HSDFG(DFG):
    pass


##
# @brief      Class for SDFG Graph
#
# SDFG class is an extension to the HSDFG class.
# Methods related to HSDFG generation is added in this class.
##


class SDFG(HSDFG):

    ##
    # @brief      Get the topoloty matrix of the current SDFG
    #
    # More information about topology matrix of SDFG can be found at
    # <https://goo.gl/hZmXQq> (last check at 2017-05-16)
    ##
    # @param      self  The object
    ##
    # @return     a matrix (list of list)
    ##
    def _topology_matrix(self):

        result = []

        for edge in self.edges:
            # One row in the topology matrix is for one Edge

            result.append([])
            edge_index = len(result) - 1

            for actor in self.actors:
                # One coloumn in the topology matrix is for one Actor
                if (actor != edge.dest_actor and actor != edge.src_actor):
                    result[edge_index].append(0)
                else:
                    if (actor == edge.dest_actor):
                        data_size = -1 * edge.dest_port.count
                        # minus sign means this actor is consuming data tokens
                        result[edge_index].append(data_size)
                    else:
                        data_size = +1 * edge.src_port.count
                        # plus sign means this actor is producing data tokens
                        result[edge_index].append(data_size)

        return result

    ##
    # \var topology_matrix
    # \copybrief SDFG::\_topology\_matrix()
    # \copydetails SDFG::\_topology\_matrix()
    ##
    topology_matrix = property(_topology_matrix)

    ##
    # @brief      Compute the repetition vector of the current SDFG
    #
    # It is a list and each element of this list is corresponding to
    # the number of invocations of one SDFG Actor object
    # in one system iteration.
    #
    # More information about repetition vector,
    # check <https://goo.gl/5mcWew> (last check 2017-05-16)
    ##
    # @param      self  The object
    ##
    # @return     repetition vector (a list)
    ##
    def _repetition_vector(self):

        # create a constraint problem solver object from ortools
        solver = pywrapcp.Solver('Get repetition vector')

        topology_matrix = self.topology_matrix

        # Repetition vector P
        # Each element is the number of invocatios of each SDF actor
        # in one system iteration.
        # The value of each repetition can be from value `1`
        # to value `sys.maxsize` (the maximum integer value of the system).
        # e.g in 32-bit operating system, `sys.maxsize` = \f$2^{31}-1\f$
        P = [solver.IntVar(1, sys.maxsize, f'repetition count {actor.index}')
             for actor in self.actors]

        # Add constraints
        # sum of P element-wise multiply with
        # one row (corresponding for one edge) in topology matrix
        # should be zero.
        # `ScalProd()` is a method in ortools,
        # e.g A = [a0, a1, a2], B = [b0, b1, b2]
        # ScalProd(A, B) = sum(a0*b0 + a1*b1 + a2*b2)
        for row in topology_matrix:
            each_row = solver.ScalProd(P, row)
            # add a constraint that `each_row` should be 0
            # to balance all the edges.
            solver.Add(each_row == 0)

        # Create a database for solver
        db = solver.Phase(P,                            # variables to search
                          solver.CHOOSE_FIRST_UNBOUND,  # Branching strategy
                          solver.ASSIGN_MIN_VALUE)      # Assignment strategy

        # Initialize a new search using the created database
        solver.NewSearch(db)

        # Perform one search and assign a value to the search variables
        # For search variable `var`,
        # use `var.Value()` to get its current assigned value
        solver.NextSolution()

        result = [int(var.Value()) for var in P]
        # .Value() is for getting the current assigned value
        # of the search variable.
        # This method is from ortools

        return result

    ##
    # \var repetition_vector
    # \copybrief SDFG::\_repetition\_vector()
    # \copydetails SDFG::\_repetition\_vector()
    ##
    repetition_vector = property(_repetition_vector)

    ##
    # @brief      Create one HSDFG from the current SDFG
    ##
    # @param      self  The object
    ##
    # @return     HSDFG of the current SDFG
    ##
    def get_hsdf(self):
        self.reassign_actor_indexes()
        repetition_vector = self.repetition_vector

        ##
        # Creates HSDFG Actor objects.
        ##
        # returns list of list.
        # Each SDFG Actor object will result one list
        # of HSDFG Actor objects
        ##
        def create_HSDF_actors():
            # each SDFG Actor will generate `p` number of HSDFG Actors.
            # `p` is the number of invocations of the SDFG Actor
            # in one system iteration
            hsdf_actors = []
            for one_sdf_actor in self.actors:
                hsdf_actors.append([])
                for p in range(repetition_vector[one_sdf_actor.index]):
                    hsdf_actor = Actor(name=one_sdf_actor.name)
                    hsdf_actor.base_actor = one_sdf_actor
                    hsdf_actors[-1].append(hsdf_actor)
                one_sdf_actor.child_actors = hsdf_actors[-1]
            return hsdf_actors

        ##
        # Creates edges for the generated HSDFG Actor objects.
        ##
        # hsdf_actors is the HSDFG Actor list.
        # It is a list of list.
        # Each SDFG Actor has one list of generated HSDFG Actor objects.
        ##
        # returns None
        ##
        def create_HSDF_edges(hsdf_actors):

            for e in self.edges:

                src_index = e.src_actor.index
                dest_index = e.dest_actor.index
                token_count = min(e.src_port.count, e.dest_port.count)

                ##
                # check if the data producing Actor should execute more than
                # the data consuming Actor
                #
                # if repetition vector P = [1, 4, 2, 2]
                #                for actor [a, d, b, c]
                # consider edge a->b
                # src_index = 0 (a)
                # dest_index = 2 (b)
                #
                # more = 1
                # less = 2
                # source_executes_more = False
                ##
                more = repetition_vector[src_index]
                less = repetition_vector[dest_index]
                source_executes_more = more > less

                ##
                # then we swap less and more
                # more = 2
                # less = 1
                ##
                if not source_executes_more:
                    less, more = more, less

                ##
                # Compute the ratio of the executions of
                # Actor executes more times over
                # Actor executes less times
                # We can divide data tokens
                # but one of the following conditions should be met:
                #
                # 1. data productio / data consumption is integer
                # 2. data consumption / data production is integer
                #
                # `ratio = 2/1` for actor `b` and `a`
                ##
                ratio = int(more / less)

                more_index = 0
                less_index = 0

                for r_less in range(less):
                    ##
                    # for each HSDFG Actor object that executes less
                    # we create a list of Edge objects
                    # for the corresponding HSDFG Actor objects
                    # that execute more
                    ##

                    less_index = r_less

                    for r_more in range(ratio):

                        if source_executes_more:
                            ##
                            # For creating a new Edge object.
                            ##
                            # If data source Actor objectexecutes more,
                            # we put this Actor object as source Actor,
                            # else
                            # we put this Actor object as destination Actor.
                            #
                            ##
                            src_actor = hsdf_actors[src_index][more_index]
                            dest_actor = hsdf_actors[dest_index][less_index]
                        else:
                            src_actor = hsdf_actors[src_index][less_index]
                            dest_actor = hsdf_actors[dest_index][more_index]

                        ##
                        # After generatig Edge,
                        # we need to change the number of data tokens
                        # to be produced or consumed on each Port.
                        #
                        # In this case, the generated Port objects
                        # will NOT be the same as the Port objects
                        # on the corresponding HSDFG Actor.
                        #
                        # We will update HSDFG Actor objects later.
                        ##
                        src_port = e.src_port.clone
                        src_port.count = token_count
                        dest_port = e.dest_port.clone
                        dest_port.count = token_count

                        Edge(src_actor=src_actor,
                             src_port=src_port,
                             dest_actor=dest_actor,
                             dest_port=dest_port)

                        more_index += 1

        ##
        # Assign indexes to the generated HSDFG Actor objects
        ##
        # hsdf_actors_2D is the HSDFG Actor list.
        # It is a list of list.
        # Each SDFG Actor has one list of generated HSDFG Actor objects.
        ##
        # returns a list of HSDFG Actor objects with correct indexes.
        ##
        def index_HSDF_actors(hsdf_actors_2D):
            result = []
            index = 0
            for hsdf_actors_from_one_sdf_actor in hsdf_actors_2D:
                for one_hsdf_actor in hsdf_actors_from_one_sdf_actor:
                    one_hsdf_actor.index = index
                    result.append(one_hsdf_actor)
                    index += 1

            return result

        hsdf_actors_2D = create_HSDF_actors()
        create_HSDF_edges(hsdf_actors_2D)
        hsdf_actors = index_HSDF_actors(hsdf_actors_2D)

        for one_hsdf_actor in hsdf_actors:
            ##
            # Now we update the Port object on HSDFG Actor objects.
            # The resulting Port object will have different `count` value
            # than the Port in the original SDFG Actor object.
            # This is INTENDED,
            # since we do not want create new ports,
            # we only change the `count` value based to the repetition value.
            ##
            output_ports = []
            input_ports = []

            for one_edge in one_hsdf_actor.outgoing_edges:
                ##
                # if the Port with name `port_name` is NOT in the port list,
                # we append the Port object to the port list.
                # else we use the Port object in the port list as
                # `one_edge.src_port`
                ##
                try:
                    one_edge.src_port = next(p for p in output_ports
                                             if p == one_edge.src_port)
                except StopIteration:
                    one_edge.src_port.index = len(output_ports)
                    output_ports.append(one_edge.src_port)

            for one_edge in one_hsdf_actor.incoming_edges:
                ##
                # if the Port with name `port_name` is NOT in the port list,
                # we append the Port object to the port list.
                # else we use the Port object in the port list as
                # `one_edge.dest_port`.
                ##
                try:
                    one_edge.dest_port = next(p for p in input_ports
                                              if p == one_edge.dest_port)
                except StopIteration:
                    one_edge.dest_port.index = len(input_ports)
                    input_ports.append(one_edge.dest_port)

            one_hsdf_actor.output_ports = output_ports
            one_hsdf_actor.input_ports = input_ports

        return HSDFG(hsdf_actors, reassign_actor_indexes=False)


##
# @brief      Class for sylva test.
##


class SYLVATest(object):

    ##
    # @brief      Check if a reloaded object is correct
    #
    # 1. dump object
    # 2. load object from the dump file.
    # 3. check if object == loaded object.
    ##
    # @param      obj          The object
    # @param      clean_store  flag for clean intermediate result
    # True = clean, False = do not clean
    #

    @staticmethod
    def check_reloaded(obj, clean_store=False):
        if isinstance(obj, type):
            obj = obj()
        file_path = obj.dump_to_file()
        loaded_obj = obj.__class__.load_from_file()
        if clean_store:
            os.remove(file_path)
        try:
            assert(obj == loaded_obj)
            print(f'Test {obj.__class__.__name__} passed.')
        except AssertionError:
            print(f'Test {obj.__class__.__name__} failed.')
            print('original:')
            print(obj)
            print()
            print('reloaded:')
            print(loaded_obj)


##
# @brief      Class for SVG object in SYLVA project.
##
#
# It is only a small subset of SVG.
#
##


class SYLVASVG(SYLVABase):

    ##
    # \var default_style
    # Default styles
    ##
    default_style = {
        'all':
        {
            'fill': 'white',
            'stroke': 'black',
            'stroke_width': 0.5,
            'x': 0,
            'y': 0
        },
        'rect': {
            'width': 32,
            'height': 32,
        },
        'text': {
            'fill': 'black',
            'text_anchor': 'start',
            'font_size': 10
        },
        'foreignObject': {
            'font_size': 10
        }
    }

    ##
    # \var name
    # The name of the graph.
    # It will also be used as the file name when saving to `.svg` file
    #
    # \var parent
    # The parent SYLVASVG object or None
    #
    # \var children
    # The list of child SYLVASVG objects

    ##
    # @brief      Constructs the object.
    ##
    # @param      self      The object
    # @param      name      \copydoc SYLVASVG::name
    # @param      parent    \copydoc SYLVASVG::parent
    # @param      children  \copydoc SYLVASVG::children
    # @param      source    The SVG source code
    ##
    def __init__(self, name='svg object', parent=None, children=None, source=''):

        self.name = name
        if children is None:
            children = []
        elif isinstance(children, SYLVASVG):
            children = [children]
        elif not isinstance(children, list):
            bad_type = children.__class__.__name__
            msg = f'children can only be None/list/SYLVASVG not {bad_type}.'
            raise TypeError(msg)

        self.children = children
        self.parent = parent
        if isinstance(self.parent, SYLVASVG):
            self.parent.children.append(self)
        self._source = source

    ##
    # @brief      Create a dictionary representation of this object
    ##
    # @param      self     The object
    # @param      exclude  The exclude
    ##
    # @return     dictionary object
    ##
    def as_dict(self, exclude=[]):
        return SYLVABase.as_dict(self, exclude=['parent', '_source'] + exclude)

    ##
    # @brief      Loads a from dictionary.
    ##
    # @param      cls       The cls
    # @param      dict_obj  The dictionary object
    ##
    # @return     dictionary object
    ##
    @classmethod
    def load_from_dict(cls, dict_obj):
        name = dict_obj.get('name', 'svg object')
        children = dict_obj.get('children', [])
        children = [SYLVASVG.load(c) for c in children]
        return cls(name=name, parent=None, children=children)

    ##
    # @brief      Setter function of attribute self.source.
    ##
    # @param      self   The object
    # @param      value  The value
    ##

    def set_source(self, value):
        self._source = value

    ##
    # @brief      Getter function of attribute self.source.
    #
    # When the current SYLVASVG object has no parent,
    # svg source code will be generated based on self.children.
    ##
    # @param      self  The object
    ##
    # @return     The source.
    ##
    def get_source(self):

        if self.parent:
            return self._source
        else:
            result = ['<?xml version = "1.0" encoding = "utf-8" ?>']
            result += ['<svg xmlns = "http://www.w3.org/2000/svg" ']
            result += ['xmlns:xlink="http://www.w3.org/1999/xlink" >']
            for c in self.children:
                result.append(c.source)
            result += ['</svg>']
            return ''.join(result)

    ##
    # \var source
    # The SVG source code
    ##
    source = property(get_source, set_source)

    ##
    # @brief      Generate SYLVASVG object based on the context
    #
    # This method will be invoked by `add_{*}` methods,
    # where {*} can be `rect`, `text` or `foreignObject`
    ##
    # @param      cls           The cls
    # @param      local_kwargs  The local kwargs
    # This is the keyword arguments passed from the caller method.
    # The name of the svg element, e.g `rect` or `text`,
    # is extracted from the caller method, e.g `add_rect` or  `add_text`.
    #
    ##
    # @return     One SYLVASVG object
    # The parent of the generated object will always be the `self` object.
    # E.g invoking `self.add_rect` with `label` argument
    # will call SYLVASVG.generate()
    # to create one `rect` svg element and one `text` svg element.
    # The parent of both generted SYLVASVG objects is `self`.
    ##
    @classmethod
    def generate(cls, local_kwargs):
        name = sys._getframe().f_back.f_code.co_name[4:]
        style = dict(cls.default_style['all'])
        if name in cls.default_style:
            style.update(cls.default_style[name])
        style.update(local_kwargs)
        style.pop('self')
        style.pop('attributes')
        style.update(local_kwargs['attributes'])
        text = style.pop('text', '')
        attributes = ' '.join([f'{k}="{v}"' for k, v in style.items()])
        source = f'<{name} {attributes}>{text}</{name}>'.replace('_', '-')
        result = SYLVASVG(name, parent=local_kwargs['self'], source=source)
        for k, v in style.items():
            setattr(result, k, v)
        return result

    ##
    # @brief      Adds a rectangle.
    ##
    # @param      self        The object
    # @param      attributes  The attributes
    ##
    # @return     One SYLVASVG object
    ##
    def add_rect(self, **attributes):
        label = attributes.pop('label', '123')
        if label:
            attributes.update({'text': label})
            del label
            rect = SYLVASVG.generate(locals())
            text = self.add_text(**attributes)
            return rect
        else:
            del label
            return SYLVASVG.generate(locals())

    ##
    # @brief      Adds a text.
    ##
    # @param      self        The object
    # @param      attributes  The attributes
    # if attribute 'word_wrap' is True,
    # this method will create a `foreignObject` object by invoking
    # add_foreignObject()
    ##
    # @return     One SYLVASVG object
    ##
    def add_text(self, **attributes):
        text_color = attributes.get('text_color',
                                    attributes.get('fill', 'black'))
        attributes['fill'] = text_color
        text_stroke = attributes.get('text_stroke',
                                     attributes.get('stroke', 'black'))
        attributes['stroke'] = text_stroke
        if attributes.pop('word_wrap', False):
            return self.add_foreignObject(**attributes)
        else:
            if 'font_size' not in attributes:
                default_font_size = SYLVASVG.default_style['text']['font_size']
                attributes['font_size'] = default_font_size

            attributes['y'] = attributes['y'] + attributes['font_size']
            attributes['x'] = attributes['x'] + attributes.get('text_padding', 0)
            return SYLVASVG.generate(locals())

    ##
    # @brief      Adds a text with word wrap
    ##
    # @param      self        The object
    # @param      attributes  The attributes
    ##
    # @return     One SYLVASVG object
    ##
    def add_foreignObject(self, **attributes):
        text = attributes['text']
        attributes['text'] = '<p xmlns="http://www.w3.org/1999/xhtml">'
        attributes['text'] += f'{text}</p>'
        del text
        attributes['y'] = attributes['y'] - attributes['font_size']
        return SYLVASVG.generate(locals())

    ##
    # @brief      Adds a grid.
    ##
    # @param      self         The object
    # @param      rows         The rows
    # @param      cols         The cols
    # @param      cell_width   The cell width
    # @param      cell_height  The cell height
    # @param      label_pos    creat cell postition lable or not
    ##
    # @return     a list of SYLVASVG objects corresponding to grid cells.
    ##
    def add_grid(self, rows=2, cols=2, cell_width=0, cell_height=0, label_pos=True):

        if not cell_width:
            cell_width = SYLVASVG.default_style['rect']['width']
        if not cell_height:
            cell_height = SYLVASVG.default_style['rect']['height']
        result = []
        for x in range(cols):
            result.append([])
            for y in range(rows):
                if label_pos:
                    label = f'{x},{y}'
                else:
                    label = ''

                obj = self.add_rect(x=x * cell_width,
                                    y=y * cell_height,
                                    width=cell_width,
                                    height=cell_height,
                                    label=label,
                                    text_color='gray',
                                    text_stroke='gray',
                                    stroke='gray')
                result[-1].append(obj)
        return result

    ##
    # @brief      Save the svg to file
    ##
    # @param      self       The object
    # @param      file_path  The file path
    # If not provided, `self.name` will be used as filename and
    # `file_path` will be `self.name + '.svg'`.
    ##
    def save(self, file_path=None):
        if file_path is None:
            file_path = f'{self.name}.svg'
        with open(file_path, 'w+', encoding='utf-8') as fp:
            fp.write(self.source)


##
# @brief      Class for CGRA
#
##


class CGRA(SYLVABase):

    ##
    # \var name
    # The name of this CGRA.
    #
    # \var width
    # CRGA fabric width in number of CGRA elements
    ##
    # \var height
    # CRGA fabric height in number of CGRA elements
    ##
    # \var hop_x
    # ((Window width - 1) / 2) for sliding window communication scheme
    # in number of CGRA elements.
    ##
    # \var hop_y
    # ((Window height - 1) / 2) for sliding window communication scheme
    # in number of CGRA elements.
    ##
    # \var TC
    # cross-window communication time in clock cycles
    ##
    # \var TW
    # intra-window communication time in clock cycles
    ##
    # \var fimp_instances
    # FIMP instances mapped on this CGRA
    ##
    #

    ##
    # @brief      Constructs the object.
    ##
    # @param      self            The object
    # @param      name            \copydoc CGRA::name
    # @param      width           \copydoc CGRA::width
    # @param      height          \copydoc CGRA::height
    # @param      hop_x           \copydoc CGRA::hop_x
    # @param      hop_y           \copydoc CGRA::hop_y
    # @param      TC              \copydoc CGRA::TC
    # @param      TW              \copydoc CGRA::TW
    # @param      fimp_instances  \copydoc CGRA::fimp_instances
    ##
    def __init__(self, name='CGRA', width=1, height=1,
                 hop_x=1, hop_y=1, TC=1, TW=1, fimp_instances=[]):

        self.width = width
        self.height = height
        self.hop_x = hop_x
        self.hop_y = hop_y
        self.TC = TC
        self.TW = TW
        self.fimp_instances = list(fimp_instances)

    ##
    # @brief      Adds a FIMPInstance to this CGRA
    ##
    # @param      self           The object
    # @param      fimp_instance  The FIMP object
    ##
    def add(self, fimp_instance):
        if fimp_instance not in self.fimp_instances:
            self.fimp_instances.append(fimp_instance)

    def get_svg(self, name='CGRA', padding=2, text_padding=2):

        svg = SYLVASVG(name)
        grids = svg.add_grid(rows=self.height, cols=self.width, label_pos=True)
        for f in self.fimp_instances:
            w_unit = grids[0][0].width
            h_unit = grids[0][0].height
            w = f.cost.width * w_unit - 2 * padding
            h = f.cost.height * h_unit - 2 * padding
            x = f.x * w_unit + padding
            y = f.y * h_unit + padding
            svg.add_rect(x=x, y=y, width=w, height=h,
                         label=f.function_name, fill='gray',
                         text_color='blue', text_stroke='blue',
                         opacity='0.6',
                         text_padding=text_padding)

        return svg
