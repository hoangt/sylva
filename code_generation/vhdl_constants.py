# coding: utf-8
# The MIT License (MIT)

  # Copyright (c) 2014 by Shuo Li (contact@shuo.li)

  # Permission is hereby granted, free of charge, to any person obtaining a
  # copy of this software and associated documentation files (the "Software"),
  # to deal in the Software without restriction, including without limitation
  # the rights to use, copy, modify, merge, publish, distribute, sublicense,
  # and/or sell copies of the Software, and to permit persons to whom the
  # Software is furnished to do so, subject to the following conditions:

  # The above copyright notice and this permission notice shall be included in
  # all copies or substantial portions of the Software.

  # THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
  # IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
  # FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
  # AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
  # LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
  # FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
  # DEALINGS IN THE SOFTWARE.

__author__ = 'Shuo Li <contact@shuol.li>'
__version__= '2014-06-11-08:40'

'''Default values used for generating VHDL files
'''

import sylva.code_generation.mit_license as mit_license

authors = [ {'name': 'Shuo Li', 'email': 'contact@shuo.li'} ]
license_header = mit_license.vhdl(width = 80, year = 2014, authors = authors)

libraries = [
            'IEEE'
            , 'work'
            ]

modules = [
          'IEEE.std_logic_1164.all'
          , 'ieee.numeric_std.all'
          , 'work.all'
          ]

global_generics = {
                  'data_width' : { 'type' : 'integer', 'value' : 16 }
                  # , 'input_count' : { 'type' : 'integer', 'value' : 1 }
                  }

local_generics = {
                 # 'func_a' : default_generics
                 # , 'func_b' : default_generics
                 }

global_inputs = {'clk' : 'std_logic', 'nrst' : 'std_logic'}

