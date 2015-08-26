# coding: utf-8

'''
  SDF graph to HSDF graph conversion.
'''

import os
import sys

from sylva.ortools.constraint_solver import pywrapcp

from sylva.base import sdf

def get_topology_matrix((actors, edges)) :

  result = [];

  for edge in edges :

    result.append([])
    edge_index = len(result) - 1

    for actor in actors :
      if (actor != edge.dest_actor and actor != edge.src_actor) :
        result[edge_index].append(0)
      else:
        if (actor == edge.dest_actor) :
          result[edge_index].append(-1 * edge.dest_port.count * edge.dest_port.type.size)
        else :
          result[edge_index].append(edge.src_port.count * edge.src_port.type.size)

  return result

def get_repetition_count((actors, edges)) :

  topology_matrix = get_topology_matrix((actors, edges))

  solver = pywrapcp.Solver('SDF actor repetition')

  # repetition count
  rc = [solver.IntVar(1, sys.maxint, 'repetition count %i' % actor.index) for actor in actors]

  # add constraints
  for i in range(len(edges)) :
    each_row = solver.ScalProd(rc, topology_matrix[i])
    solver.Add(each_row == 0);

  db = solver.Phase(rc,
                    solver.CHOOSE_FIRST_UNBOUND,
                    solver.ASSIGN_MIN_VALUE)
  solver.NewSearch(db);
  solver.NextSolution();

  result = []
  for c in rc :
    result.append(int(c.Value()))

  return result;

def sdf_to_hsdf((actors, edges)) :

  def create_HSDF_actors(sdf_actors, repetition_vector) :
    import copy
    hsdf_actors = []
    for n in sdf_actors:
      hsdf_actors.append([])
      for p in range(repetition_vector[n.index]):
        hsdf_actor = sdf.actor(n.name)
        hsdf_actor.base_actor = n
        hsdf_actors[-1].append(hsdf_actor)
      n.child_actors = hsdf_actors[-1]
    return hsdf_actors

  def index_HSDF_actors(hsdf_actors) :
    hsdf_actor_set = []
    index = 0
    for i in hsdf_actors :
      for j in i :
        j.index = index
        hsdf_actor_set.append(j)
        index += 1

    return hsdf_actor_set

  def create_HSDF_edges(sdf_edges, hsdf_actors, repetition_vector) :

    R = repetition_vector
    hsdf_edges = []

    for e in sdf_edges:

      src_index = e.src_actor.index
      dest_index = e.dest_actor.index
      tokens = min(e.src_port.count, e.dest_port.count)

      source_executes_more = R[src_index] > R[dest_index]

      less = R[dest_index]
      more = R[src_index]
      if (source_executes_more == False) :
        less = R[src_index]
        more = R[dest_index]

      ratio = int(more/less)
      more_index = 0
      less_index = 0

      for r_less in range(less) :

        less_index = r_less

        for r_more in range(ratio) :

          if (source_executes_more == True) :
            src_actor = hsdf_actors[src_index][more_index]
            dest_actor = hsdf_actors[dest_index][less_index]
          else :
            src_actor = hsdf_actors[src_index][less_index]
            dest_actor = hsdf_actors[dest_index][more_index]

          src_port = e.src_port.clone()
          src_port.token_count = tokens

          dest_port = e.dest_port.clone()
          dest_port.token_count = tokens

          new_edge = sdf.edge( src_actor = src_actor, src_port = src_port,
                           dest_actor = dest_actor, dest_port = dest_port )

          hsdf_edges.append( new_edge )
          more_index += 1

    return hsdf_edges

  repetition_vector = get_repetition_count((actors, edges))

  sdf_actors = actors
  sdf_edges = edges

  hsdf_actors_2D = create_HSDF_actors(sdf_actors, repetition_vector)
  hsdf_edges = create_HSDF_edges(sdf_edges, hsdf_actors_2D, repetition_vector)
  hsdf_actors_array = index_HSDF_actors(hsdf_actors_2D)

  for a in hsdf_actors_array :

    a.output_ports = []
    a.input_ports = []

    for e in a.next :
      if e.src_port.name not in \
      [ p.name for p in a.output_ports ] :
        a.output_ports.append(e.src_port)
      else :
        e.src_port = [ p for p in a.output_ports
                       if e.src_port.name == p.name ][0]

    for e in a.previous :
      if e.dest_port.name not in \
      [ p.name for p in a.input_ports ] :
        a.input_ports.append(e.dest_port)
      else :
        e.dest_port = [ p for p in a.input_ports
                       if e.dest_port.name == p.name ][0]

  return (hsdf_actors_array, hsdf_edges)

if __name__ == '__main__' :

  # import sys
  # root_dir = os.path.dirname(os.path.abspath(__file__))
  # verification_dir = root_dir + '/../verification'
  # sys.path.insert(0, verification_dir)

  import sylva.examples.sdf_examples as sdf_examples

  print 'Test for %s' % os.path.basename(__file__)
  print '========'
  print ''
  from pprint import pprint as pp

  (a, e) = sdf_to_hsdf(sdf_examples.example_in_text())

  pp(a)
  pp(e)

  print ''
  print '========'
  print 'end of test for %s' % os.path.basename(__file__)


