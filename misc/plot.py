# coding: utf-8
# The MIT License (MIT)
# Copyright (c) 2014 by Shuo Li (contact@shuo.li)
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

__author__ = 'Shuo Li <contact@shuol.li>'
__version__ = '2014-09-22-11:44'

'''Plot using matplotlib.
'''

from matplotlib.patches import Rectangle
from matplotlib import pyplot as plt
from sylva.misc.util import to_list

if 'define SDF schedule plot':

    def time_block(start, end, index,
                   color='gray', height=0.2,
                   subindex=1, subtotal=1, space=0.2):

        total_height = height * subtotal
        x = start
        y = 0
        y = y + index * total_height
        y = y + space
        y = y + height * (subtotal - subindex - 1)

        return Rectangle((x, y),
                         width=end - start + 1, height=height,
                         facecolor=color, edgecolor='black', linestyle='solid')

    def fimp_schedule_plot(fimps=[],
                           height=0.2, plt=plt,
                           input_color='green',
                           output_color='pink',
                           computation_color='grey',
                           buffer_color='darkred'):

        actors = [one_actor for one_fimp in fimps for one_actor in one_fimp.actors]

        return schedule_plot(actors,
                             height, plt,
                             input_color, output_color, computation_color, buffer_color)

    def schedule_plot(actors=[], height=0.2, plt=plt,
                      input_color='green', output_color='pink',
                      computation_color='grey',
                      buffer_color='darkred'):

        end_time = max(actors, key=lambda n: n.buffer_end).buffer_end
        fimp_count = max(actors, key=lambda n: n.fimp.index).fimp.index

        plt.axis([0, end_time + 2, 0, (fimp_count + 2) * height * 3])
        plt.gca().grid(True)

        for n in actors:
            input_block = time_block(n.start, n.input_end, n.fimp.index,
                                     subindex=0, subtotal=3, color=input_color)
            computation_block = time_block(n.start, n.end, n.fimp.index,
                                           subindex=1, subtotal=3, color=computation_color)
            output_block = time_block(n.output_start, n.end, n.fimp.index,
                                      subindex=2, subtotal=3, color=output_color)
            rx, ry = computation_block.get_xy()
            cx = rx + computation_block.get_width() / 2.0
            cy = ry + computation_block.get_height() / 2.0
            plt.gca().annotate('%s_%s' % (n.name, n.index), (cx, cy),
                               color='black',
                               # weight='bold',
                               # fontsize=16,
                               ha='center', va='center')
            plt.gca().add_patch(input_block)
            plt.gca().add_patch(output_block)

            if n.buffer_end > n.end:
                buffer_ext_block = time_block(n.end + 1, n.buffer_end, n.fimp.index,
                                              subindex=2, subtotal=3, color=buffer_color)
                plt.gca().add_patch(buffer_ext_block)
            plt.gca().add_patch(computation_block)

        return plt

    def fimp_execution_model_plot(fimps=[], height=0.2, plt=plt,
                                  input_color='green', output_color='pink',
                                  computation_color='grey',
                                  buffer_color='darkred'):

        end_time = max(fimps, key=lambda f: f.computation_phase).computation_phase
        fimp_count = len(fimps)

        plt.axis([0, end_time + 2, 0, fimp_count + 2])
        plt.gca().grid(True)

        for i in xrange(len(fimps)):
            input_block = time_block(start=0,
                                     end=fimps[i].input_phase - 1,
                                     index=i,
                                     subindex=0, subtotal=3, color=input_color)
            computation_block = time_block(start=0,
                                           end=fimps[i].computation_phase - 1,
                                           index=i,
                                           subindex=1, subtotal=3, color=computation_color)
            output_block = time_block(
                start=fimps[i].computation_phase - fimps[i].output_phase + 1,
                end=fimps[i].computation_phase - 1,
                index=i,
                subindex=2, subtotal=3, color=output_color)
            rx, ry = computation_block.get_xy()
            cx = rx + computation_block.get_width() / 2.0
            cy = ry + computation_block.get_height() / 2.0
            plt.gca().annotate(fimps[i], (cx, cy),
                               color='black', weight='bold',
                               fontsize=16, ha='center', va='center')
            plt.gca().add_patch(input_block)
            plt.gca().add_patch(output_block)
            plt.gca().add_patch(computation_block)

        return plt

if 'CGRA Floorplanning':

    class point(object):

        def __init__(self, x=None, y=None):
            self.x = x or 0
            self.y = y or 0
            self.xy = (self.x, self.y)

        def __getitem__(self, index):
            return self.xy(index)

        def __str__(self):
            return '({}, {})'.format(self.x, self.y)

        def __repr__(self):
            return '({}, {})'.format(self.x, self.y)

        def __add__(self, other):
            try:
                x = self.x + int(other.x)
                y = self.y + int(other.y)
                return point(x, y)
            except:
                pass
            try:
                x = self.x + int(other.__getattr__('x'))
                y = self.y + int(other.__getattr__('y'))
                return point(x, y)
            except:
                pass
            try:
                x = self.x + int(other['x'])
                y = self.y + int(other['y'])
                return point(x, y)
            except:
                pass
            try:
                x = self.x + int(other[0])
                y = self.y + int(other[1])
                return point(x, y)
            except:
                pass
            raise Exception('Cannot add {}, {}'.format(other, type(other)))

        def __iadd__(self, other):
            return self.__add__(other)

        def __sub__(self, other):
            try:
                x = self.x - int(other.__getattr__('x'))
                y = self.y - int(other.__getattr__('y'))
                return point(x, y)
            except:
                pass
            try:
                x = self.x - int(other['x'])
                y = self.y - int(other['y'])
                return point(x, y)
            except:
                pass
            try:
                x = self.x - int(other[0])
                y = self.y - int(other[1])
                return point(x, y)
            except:
                pass
            raise Exception('Cannot subtract {}'.format(other))

        def __isub__(self, other):
            return self.__sub__(other)

    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches

    default_rectangle_style = {
        'facecolor': 'white',
        'edgecolor': 'black',
        'linestyle': 'solid',
        'linewidth': 1,
        'width': 0.4,
        'height': 0.4,
    }

    default_annotation_style = {
        'color': 'black',
        'fontweight': 'normal',
        'fontsize': 12,
        'ha': 'center',
        'va': 'center'}

    class rectangle(object):

        def __init__(self, width, height, name=None,
                     xy=None, x=None, y=None):

            # top-left position
            self.xy = xy or point(x, y)
            self.name = name or str(self.xy)
            self.width = width
            self.height = height

        def overlaps(self, other):

            right = other.left.x >= self.right.x
            left = other.right.x <= self.left.x
            top = other.bottom.y <= self.top.y
            bottom = other.top.y >= self.bottom.y
            return not (right or left or top or bottom)

        def __contains__(self, other):
            if isinstance(other, rectangle):
                return self.top_left in other \
                    or self.top_right in other \
                    or self.bottom_left in other \
                    or self.bottom_right in other
            elif isinstance(other, point):
                x_in_range = self.left.x <= other.x <= self.right.x
                y_in_range = self.top.y <= other.y <= self.bottom.y
                return x_in_range and y_in_range
            return False

        @property
        def x(self):
            return self.xy.x

        @x.setter
        def x(self, value):
            self.xy.x = value

        @property
        def y(self):
            return self.xy.y

        @y.setter
        def y(self, value):
            self.xy.y = value

        @property
        def right(self):
            x = self.x + self.width
            y = self.y + self.height / 2
            return point(x, y)

        @property
        def left(self):
            x = self.x
            y = self.y + self.height / 2
            return point(x, y)

        @property
        def top(self):
            x = self.x + self.width / 2
            y = self.y
            return point(x, y)

        @property
        def bottom(self):
            x = self.x + self.width / 2
            y = self.y + self.height
            return point(x, y)

        @property
        def top_right(self):
            return point(self.right.x, self.y)

        @property
        def bottom_right(self):
            return point(self.right.x, self.bottom.y)

        @property
        def top_left(self):
            return point(self.x, self.y)

        @property
        def bottom_left(self):
            return point(self.x, self.bottom.y)

        @property
        def center(self):
            return self.top_left + point(self.width / 2, self.height / 2)

        @property
        def pixel_map(self):
            return [(x, y)
                    for x in range(self.x, self.x + self.width, 1)
                    for y in range(self.y, self.y + self.height, 1)]

        def get_patch(self, style=None):

            _style = default_rectangle_style
            _style.update(style or {})

            _style['width'] = self.width
            _style['height'] = self.height
            return mpatches.Rectangle((self.x, self.y), **_style)

        def place_right_of(self, other):
            self.xy = other.xy + (other.width, 0)

        def place_left_of(self, other):
            self.xy = other.top_left - (self.width, 0)

        def place_above_of(self, other):
            self.xy = other.top_left - (0, self.height)

        def place_below_of(self, other):
            self.xy = other.bottom_left

    def canvas_plot(rects, padding=0.1, rectangle_style=None, annotation_style=None,
                    width=None, height=None, show_axis=True, show_ticks=False, plt=plt):

        _rectangle_style = default_rectangle_style
        _rectangle_style.update(rectangle_style or {})

        _annotation_style = default_annotation_style
        _annotation_style.update(annotation_style or {})

        rects = to_list(rects)
        if not width:
            min_width = min([rect.x for rect in rects]) - padding
            max_width = max([rect.x + rect.width for rect in rects]) + padding
        else:
            min_width = 0
            max_width = width
        if not height:
            min_height = min([rect.y for rect in rects]) - padding
            max_height = max([rect.y + rect.height for rect in rects]) + padding
        else:
            min_height = 0
            max_height = height

        if show_axis:
            plt.axis([min_width, max_width, max_height, min_height])
            if show_ticks:
                plt.xticks(range(min_width, max_width + 1))
                plt.yticks(range(min_height, max_height + 1))
            else:
                plt.xticks(list(set([r.left.x for r in rects]
                                    + [int(min_width), int(max_width)] + [r.right.x for r in rects])))
                plt.yticks(list(set([r.top.y for r in rects]
                                    + [int(min_height), int(max_height)] + [r.bottom.y for r in rects])))
        else:
            plt.axis('off')

        plt.gca().set_aspect('equal')
        for rect in rects:
            plt.gca().add_patch(rect.get_patch())
            plt.gca().annotate(rect.name,
                               (rect.x + 0.5 * rect.width, rect.y + 0.5 * rect.height),
                               **_annotation_style)
        return plt

if __name__ == '__main__':
    p = point(2, 2)
    r = rectangle(4, 4, x=0, y=0)
    print(p)
    print(r.left, r.right, r.top, r.bottom)
    print(p in r)
