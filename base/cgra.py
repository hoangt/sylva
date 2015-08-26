# coding: utf-8

import json
from matplotlib import pyplot as plt
from matplotlib import patches as mpatches
from sylva.misc.plot import point as Point, rectangle as Rectangle, canvas_plot

class cgra :
  '''simple cgra class for floorplanner'''

  def __init__ (self, width = 1, height = 1, hop_x = 1, hop_y = 1, TC = 1, TW = 1, fimps = None) :

    # TC : time for cross-window communication
    # TW : time for intra-window communication

    self.width = width
    self.height = height
    self.hop_x = hop_x
    self.hop_y = hop_y
    self.TC = TC
    self.TW = TW
    self.fimps = [] if not fimps else fimps

  def add_fimp(self, fimp) :
    if fimp not in self.fimps :
      self.fimps.append(fimp)
      self.fimpindexes.append(fimp.index)

  def plot_old(self, show_fimp_name = False, show_ticks = False, show_cgra_nodes = False) :

    width = self.width
    height = self.height

    plt.axis([0, width, height, 0])
    plt.gca().set_aspect('equal')
    plt.gca().set_title('CGRA width: {}, height: {}'.format(self.width, self.height))
    margin = 0.1
    size = 0.8

    # plotfloorplan(plt, 4, 5, [2], [3], [a.fimp.width], [a.fimp.height])
    total_size = size + 2 * margin

    plt.axis([0, width * total_size, height * total_size, 0])

    total_size = size + 2 * margin

    if show_ticks :
      plt.xticks([i for i in range(width)])
      plt.yticks([i for i in range(height)])
    else :
      plt.xticks(list(set([f.x for f in self.fimps] + [f.x + f.width for f in self.fimps])))
      plt.yticks(list(set([f.y for f in self.fimps] + [f.y + f.width for f in self.fimps])))

    # plot empty cgra
    if show_cgra_nodes :
      for h in range(height) :
        for w in range(width) :
          cgra_block = mpatches.Rectangle((w * total_size + margin, h * total_size + margin), size, size, \
            facecolor='white', edgecolor='black', linestyle = 'dashed', linewidth=0.1)
          plt.gca().add_patch(cgra_block)

    # plot fimps
    for f in self.fimps:
      if f.x >= 0 and f.y >= 0 :
        fimp_block = mpatches.Rectangle((f.x * total_size, f.y * total_size), \
          width = f.width * total_size, height = f.height * total_size, \
          facecolor='lightgrey')
        plt.gca().add_patch(fimp_block)
        rx, ry = fimp_block.get_xy()
        cx = rx + fimp_block.get_width()/2.0
        cy = ry + fimp_block.get_height()/2.0

        if show_fimp_name == True :
          annotation = '%s: %s' % (f.index, f.name)
        else :
          annotation = f.index

        plt.gca().annotate(annotation, (cx, cy),
          color='black', weight='bold',
          fontsize=20, ha='center', va='center')
      else :
        pass
        # raise AttributeError('fimp %s is not mapped yet.')

    return plt

  def plot(self, show_fimp_name = False,
    show_axis = False, show_ticks = False, show_cgra_nodes = False, compact = False) :

    plt.gca().set_title('CGRA width: {}, height: {}'.format(self.width, self.height))

    if compact :
      width = height = None
    else :
      width = self.width
      height = self.height

    return canvas_plot([ Rectangle(f.width, f.height, x = f.x, y = f.y,
      name = str(f.index) + ((':$' + f.name + '$') if show_fimp_name else ''))
      for f in self.fimps if f.x >= 0 and f.y >= 0], rectangle_style = {'fc' : 'lightgrey'},
      width = width, height = height)

  def serialize(self) :
    return dict([(k, v) for k, v in self.__dict__.items() if k != 'plt'])

  @classmethod
  def load(cls, json_dict) :
    return cgra(**json_dict)

  def dump(self, filepath, indent = 2) :
    with open(filepath, 'w+') as f :
      f.write(json.dumps(self.serialize(), indent = 2))
