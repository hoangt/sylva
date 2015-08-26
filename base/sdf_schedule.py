# coding: utf-8

'''Schedule extension for HSDF nodes
'''

import os
from sylva.base.sdf import actor
from sylva.base.fimp import fimp

class schedule :

  '''
    Execution schedule class
    ------------------------

    start, end, input_end, output_start, buffer_end
  '''

  def __init__(self,
    start = 0, end = 0,
    input_end = 0, output_start = 0,
    buffer_end = -1) :

    self.start = start
    self.input_end = input_end
    self.output_start = output_start
    self.end = end

    if buffer_end < 0 :
      self.buffer_end = end
    else :
      self.buffer_end = buffer_end

    self.__repr__ = self.__str__

  def __str__(self) :
    msg  = 'start: %s' % self.start
    msg += os.linesep
    msg += 'input end: %s' % self.input_end
    msg += os.linesep
    msg += 'output start: %s' % self.output_start
    msg += os.linesep
    msg += 'end: %s' % self.end
    msg += os.linesep
    msg += 'buffer end: %s' % self.buffer_end
    return msg

def add_schedule(self, start, buffer_end = -1) :

  '''
    Specify the execution schedule of an actor based on the start and buffer end time.
  '''

  if 'fimp' in dir(self) :

    self.ts = start

    self.te = self.ts + self.fimp.computation_phase - 1
    self.tie = self.ts + self.fimp.input_phase - 1
    self.tos = self.te - self.fimp.output_phase + 1

    if buffer_end < 0 :
      self.tbe = self.te
    else :
      self.tbe = buffer_end

    self.start = self.ts
    self.end = self.te
    self.input_end = self.tie
    self.output_start = self.tos
    self.buffer_end = self.tbe

    self.schedule = schedule( start = self.ts,
                              input_end = self.tie,
                              output_start = self.tos,
                              end = self.te,
                              buffer_end = self.tbe)
  else :
    errmsg  = 'Cannot assign schedule to SDF actor %s . ' % self.name
    errmsg += 'Assign a FIMP instance to this actor first.'
    raise AttributeError(errmsg)

def update_schedule(self) :

  '''
    Update the execution schedule of an actor based on the start and buffer end time.
  '''

  self.add_schedule(self.ts, self.tbe)

actor.add_schedule = add_schedule
actor.update_schedule = update_schedule
