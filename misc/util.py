# coding: utf-8
# The MIT License (MIT)
  # Copyright (c) 2015 by Shuo Li (contact@shuo.li)
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
__version__= '2015-08-15-23:20'

'''Some handy things.
'''
import os, os.path, time


class status_log :

  def __init__(self, print_status = False, show_time_stamp = False) :

    self.log = []
    self.status = []
    self.print_status = print_status
    self.show_time_stamp = show_time_stamp

  def update(self) :
    if self.print_status :
      if self.show_time_stamp :
        print('\n'.join([ s[0] + s[1] for s in self.status]))
      else :
        print('\n'.join([s[1] for s in self.status]))
    self.log += self.status
    self.status = []

  def time_stamp(self) :
    return time.strftime("[%a, %d %b %Y %H:%M:%S] ", time.localtime())

  def __add__(self, msg) :
    self.status.append((self.time_stamp(), msg))
    return self

  def __iadd__(self, msg) :
    self.status.append((self.time_stamp(), msg))
    return self

  def write_to_file(self, name = 'log') :
    with open(name, 'w+') as fp :
      for l in self.log :
        fp.write(l[0] + l[1] + '\n')

def chunks(l, n):
  for i in range(0, len(l), n):
    yield l[i:i+n]

def all_files(path, ext_names = []) :
  path = to_list(path)
  result = []
  for p in path :
    result += [ os.path.join(dirpath, filename)
      for (dirpath, dirnames, filenames) in os.walk(p)
        for filename in filenames ]
  if not ext_names :
    return result
  ext_names = to_list(ext_names)
  return [f for f in result if os.path.splitext(f)[1] in ext_names]

def files_in_path(file_name, path) :
  paths = to_list(path)
  base_name = os.path.basename(file_name)
  result = [ os.path.join(dirpath, filename)
    for path in paths
      for (dirpath, dirnames, filenames) in os.walk(path)
        for filename in filenames
    if filename == base_name ]
  return result

def merge_dicts(a, b) :
  a.update(b)
  return a

def to_list(a) :
  if isinstance(a, list) :
    return a
  else :
    return [a]

def min_items(values) :
  return [(index, value) for index, value in enumerate(values) if value == min(values)]

def max_items(values) :
  return [(index, value) for index, value in enumerate(values) if value == max(values)]

def min_items_with_floor(values, floor) :
  return [(index, value) for index, value in enumerate(values)
    if value == min(values) and value >floor]

def max_items_with_ceil(values, ceil) :
  return [(index, value) for index, value in enumerate(values)
    if value == max(values) and value < ceil]

def min_index(values) :
  return values.index(min(value))

def max_index(values) :
  return values.index(max(value))

def evenly_pick(values, count) :
  step = len(values)/(count-1)
  mid = len(values)/2
  return values[:mid:step] + values[-1:mid+1:-step]

def mkdir(new_dir) :
  try :
    if not os.path.exists(new_dir) :
      os.mkdir(new_dir)
  except : pass

def dir_and_file(provided_name) :

  if provided_name.startswith('./') :
    provided_name = provided_name[2:]

  name, ext = os.path.splitext(os.path.basename(provided_name))
  dirname = os.path.dirname(provided_name)

  # when provided_name is a dir
  if name == provided_name :
    name = ''
    dirname = provided_name

  if ext :
    output_dir = dirname
  elif name :
    output_dir = os.path.join(dirname, name)
  else :
    output_dir = dirname

  return output_dir, name, ext

ceil = lambda x : int(math.ceil(x))
floor = lambda x : int(math.floor(x))
log = lambda x : math.log(x, 10)
log2 = lambda x : math.log(x, 2)