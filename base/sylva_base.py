##
# \package sylva.base.sylva_base
# All basic classes and methods for SYLVA project
##

__author__ = 'Shuo Li <contact@shuol.li>'
__version__ = '2017-05-12'
__license__ = 'MIT'

##
# @brief      The base object for SYLVA project
# All objects are inherented from this object
##


class SYLVABase(object):

    def __init__(self, dict_object):
        for key, value in dict_object.items():
            setattr(self, key, value)

    ##
    # @brief      Create an iterator to be used for converting
    # the object to dictionary
    #
    # When dict(some_obj) is called, it will return a dictionary object.
    # Each value is obtaiend by invoking the created iterator in this method.
    #
    # @param      self  The object
    #
    # @return     a iterator
    ##
    def __iter__(self):
        for key, value in self.__dict__.items():
            if isinstance(value, SYLVABase):
                yield (key, dict(value))
            else:
                yield (key, value)

    ##
    # @brief      Loads an object from a dictionary object.
    #
    # @param      cls          The cls
    # @param      dict_object  The dictionary object
    ##
    # @return     Returns an SYLVABase object
    ##
    @classmethod
    def load_from_dict(cls, dict_object):
        msg = f'load {cls} from dict is not implemented yet.'
        raise NotImplementedError(msg)

    ##
    # @brief      Returns a string representation of the object.
    #
    # @param      self  The object
    ##
    # @return     String representation of the object.
    ##
    def __str__(self):
        msg = 'str representation of {self.__class__} is not implemented yet.'
        raise NotImplementedError(msg)

    ##
    # @brief      Returns a string representation of the object.
    #
    # This method will be invoked some time instead of self.__str__().
    #
    # @param      self  The object
    ##
    # @return     String representation of the object.
    ##
    def __repr__(self):
        return self.__str__()

    ##
    # @brief      Creates a new instance of the object with same properties than original.
    ##
    # @param      self  The object
    ##
    # @return     Copy of this object.
    ##
    @property
    def clone(self):
        msg = 'clone of {self.__class__} is not implemented yet.'
        raise NotImplementedError(msg)
