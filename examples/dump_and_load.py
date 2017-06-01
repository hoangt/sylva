##
# \package sylva.examples.dump_and_load_example
#
# Example of dump and load of SYLVABase objects
##

from sylva.base.sdf import DataTokenType

__author__ = 'Shuo Li <contact@shuol.li>'
__version__ = '2017-05-19'
__license__ = 'https://opensource.org/licenses/MIT'


##
# @brief      Dumps and load.
##
#
# This method will dump a DataTokenType obejct to file
# and reload if from that file
# then print the original object and the reloaded object.
#
##
def dump_and_load():

    # Create a new DataTokenType object
    int32 = DataTokenType(name='int32', size=32)

    # Convert DataTokenType object to dictionary object
    dict_object = dict(int32)

    # check the content of `dict_object`
    print(dict_object)

    # Deserialize a DataTokenType object from the created dictionary object
    another_type = DataTokenType(**dict_object)

    # check the content of the generated DataTokenType object
    print(another_type)


if __name__ == '__main__':

    dump_and_load()

    # Output should be:
    # `{'name': 'int32', 'size': 32, '_class': 'DataTokenType'}`
    # `{'_class': 'DataTokenType', 'name': 'int32', 'size': 32}`
