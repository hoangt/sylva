# coding = utf-8
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
__version__= '2014-06-12-11:43'

import time
year = time.strftime('%Y', time.localtime())
authors = [ {'name': 'Shuo Li', 'email': 'contact@shuo.li'} ]

width = 80
vhdl_indention_size = 3
python_indention_size = 2

if 'hidden details' :

  lic_title = 'The MIT License (MIT)'

  permission = 'Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:'

  permission_extra = 'The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.'

  final = 'THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER  DEALINGS IN THE SOFTWARE.'

import textwrap

def get_contact(year = year, authors = authors) :
  '''Generate the 'contact' part of the license body.

    year
      integer, e.g. 2014

    authors
      authors with their emails
      e.g.
      [
        { 'name' : 'one author',
          'email' : 'one@author.com' }
        { 'name' : 'another author',
          'email' : 'another@author.com' }
      ]
  '''

  author_string = ['%s (%s)' % (a['name'], a['email']) for a in authors]
  author_string = author_string.__str__()
  author_string = author_string.replace(',', ' and')[2:][:-2]
  return 'Copyright (c) %s by %s' % ( year, author_string )

def get_wrapped_text(lic_title = lic_title,
  contact = get_contact(year, authors),
  permission = permission,
  permission_extra = permission_extra,
  final = final,
  width = 80,
  comment_perfix = '#',
  indention_size = 2) :

  comment_length = len(comment_perfix)

  result = ''
  lic_title = textwrap.wrap(lic_title, width - comment_length - 2)

  for line in lic_title :
    result += comment_perfix + ' ' + line + '\n'

  for section in [contact, permission, permission_extra, final] :
    section = textwrap.wrap(section, width - comment_length - indention_size - 2)
    result += '\n'
    for line in section :
      result += ' ' * indention_size + comment_perfix + ' ' + line + '\n'

  return result[:-1]

def vhdl(year = year, authors = authors, width = width, indention_size = vhdl_indention_size) :
  return get_wrapped_text( width = width,
                           contact = get_contact(year, authors),
                           comment_perfix = '--',
                           indention_size = indention_size )

def python(year = year, authors = authors, width = width, indention_size = python_indention_size) :
  return get_wrapped_text( width = width,
                           contact = get_contact(year, authors),
                           comment_perfix = '#',
                           indention_size = indention_size )