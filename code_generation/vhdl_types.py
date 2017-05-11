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

if 'import dependencies' :

  import os, sys, math

  import sylva.base.sdf as sdf

def bit_value(self, value) :

  '''
  Returns the value of each bit of a data token.

  std_logic_vector : binary(value)
  integer          : binary(value - min)
  '''

  if self.name.startswith('integer') :
    minvalue = int(self.name.split(' ')[2])
    maxvalue = int(self.name.split(' ')[4])

  elif self.name.startswith('std_logic') :
    minvalue = 0
    maxvalue = int(math.pow(2, self.size) - 1)

  else :
    raise NotImplementedError

  if value > maxvalue :
    raise ValueError( 'Current value (%s) is larger than the maximum value (%s)' \
                      % (value, maxvalue) )
  if value < minvalue :
    raise ValueError( 'Current value (%s) is smaller than the minimum value (%s)' \
                      % (value, minvalue) )

  current_value = value - minvalue;
  return bin(current_value).__str__().split('b')[-1].zfill(self.size)

sdf.DataTokenType.bit_value = bit_value

def slv(size = 1) :
  if size < 1 :
    raise Exception.ValueError( 'The size of an std_logic_vector value can only be > 1 ' +
                                'not %s' % size )
  if size == 1:
    return sdf.DataTokenType( name = 'std_logic', size = 1 )
  else :
    return sdf.DataTokenType( name = 'std_logic_vector (%s downto 0)' % (size - 1), size = size )

def integer(max_value = 0, min_value = 0) :

  if min_value < 0 or max_value < 0 :
    raise Exception.ValueError( 'The range of an integer can only be > 1 ' +
                                'not (%s to %s)' % (minvalue, maxvalue) )
  if min_value > max_value :
    min_value, max_value = max_value, min_value
    raise Exception.SyntaxWarning( 'The input range is inversed due to ' +
                                   'min value (%s) > max value (%s)' % (minvalue, maxvalue))
  number_of_values = max_value - min_value + 1
  size = int(math.ceil(math.log(number_of_values, 2)))

  return sdf.DataTokenType( name = 'integer range %s to %s' % (min_value, max_value), size = size )

std_logic = slv(1)
clk  = sdf.port('clk', 0, std_logic, 1)
nrst = sdf.port('nrst', 0, std_logic, 1)
en   = sdf.port('nrst', 0, std_logic, 1)

def integer_vhdl(max_value, min_value=0) :
  return integer_vhdl(max_value, min_value).name


