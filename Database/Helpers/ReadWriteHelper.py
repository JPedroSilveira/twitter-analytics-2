import _io
import re
import Database.Helpers.StructDataHelper as StructDataHelper
import Database.Helpers.ObjectHelper as ObjectHelper
import Database.Cons.SupportedTypes as SupportedTypes
import Database.Error.ReadWriteError as ReadWriteError
import Database.Cons.File as File

_STRING_SIZE_NAME = '_size'
_STRING_END = '\0'
_BOOL_END = False
_INT_END = 0
_FLOAT_END = 0.0


# WRITE FUNCTIONS: WRITE A TYPED VALUE WITH A BUFFER
def write_primitive_value(buffer: _io.BufferedRandom, value):
    prim_type_name = ObjectHelper.get_type_name(value)

    if prim_type_name == SupportedTypes.INT_NAME:
        write_int(buffer, value)

    elif prim_type_name == SupportedTypes.FLOAT_NAME:
        write_float(buffer, value)

    elif prim_type_name == SupportedTypes.BOOL_NAME:
        write_bool(buffer, value)

    else:
        raise ReadWriteError.WritingANonPrimitiveType('Value ' + value + ' can\'t be a non primitive type!')


def write_complex_value(buffer: _io.BufferedRandom, values, size, list_type=None):
    complex_type_name = ObjectHelper.get_type_name(values)

    if complex_type_name == SupportedTypes.STRING_NAME:
        write_str(buffer, values, size)
    elif complex_type_name == SupportedTypes.LIST_NAME:
        write_list(buffer, values, size, list_type)


def write_int(buffer: _io.BufferedRandom, value: int):
    buffer.write(StructDataHelper.convert_to_bin_int(value))


def write_float(buffer: _io.BufferedRandom, value: float):
    buffer.write(StructDataHelper.convert_to_bin_float(value))


def write_str(buffer: _io.BufferedRandom, value: str, max_size: int):
    stop_count = 0
    value = _remove_invalid_char(value)

    for char in value:
        if stop_count == max_size:
            break

        buffer.write(StructDataHelper.convert_to_bin_char(char))

        stop_count = stop_count + 1

    # Write the end of the string
    buffer.write(StructDataHelper.convert_to_bin_char(_STRING_END))

    # Seek the empty space
    if max_size > stop_count:
        # Gets the end of the file
        pos = buffer.tell()
        # Then seek to the end of the string max_size and write other end to preserve the fixed size
        # The minus one is to preserve the space for string final
        buffer.seek(pos + (max_size - stop_count - 1)*SupportedTypes.CHAR_SIZE, File.ABSOLUTE_FILE_POSITION)
        buffer.write(StructDataHelper.convert_to_bin_char(_STRING_END))


# A LIST NEED TO BE COMPOSED WITH JUST ONE TYPE
def write_list(buffer: _io.BufferedRandom, values: list, max_size: int, list_type: str):
    stop_count = 0

    # Verify if the type is valid
    if list_type not in SupportedTypes.PRIMITIVE_TYPES_NAMES_FOR_LIST:
        raise ReadWriteError.WritingAListOfInvalidType('Type ' + list_type + ' isn`t supported in lists!')

    # Error if the list size is bigger than the max_size
    if len(values) > max_size:
        raise ReadWriteError.WritingAListBiggerThanMaxSize(
            'The list size ' + str(len(values)) + ' is bigger than expected ' + max_size + '!')

    # First write the list size
    write_primitive_value(buffer, len(values))

    # Second write the values
    for value in values:
        value_type = ObjectHelper.get_type_name(value)

        # Verify if the current value type is equal to given param type (Lists should be just one value type)
        if value_type != list_type:
            raise ReadWriteError.WritingAListWithDifferentTypes(
                'List with multiple types!')

        write_primitive_value(buffer, value)

        stop_count = stop_count + 1

    # If not a complete array, seek for the final and write a symbolic empty value
    if len(values) < max_size:
        write_list_end_values(buffer, list_type, stop_count, max_size)


# Write empty values to complete the list size
def write_list_end_values(buffer: _io.BufferedRandom, value_type: str, stop_count: int, max_size: int):

    if value_type == SupportedTypes.INT_NAME:
        size = SupportedTypes.INT_SIZE
        end = _INT_END
        convert_function = StructDataHelper.convert_to_bin_int
    elif value_type == SupportedTypes.FLOAT_NAME:
        size = SupportedTypes.FLOAT_SIZE
        end = _FLOAT_END
        convert_function = StructDataHelper.convert_to_bin_float
    elif value_type == SupportedTypes.BOOL_NAME:
        size = SupportedTypes.BOOL_SIZE
        end = _BOOL_END
        convert_function = StructDataHelper.convert_to_bin_bool
    else:
        raise ReadWriteError.WritingAListOfInvalidType(
            'Type ' + value_type + ' isn`t part of the list of type ' + value_type + '!')

    # Gets the end of the file
    pos = buffer.tell()
    # Then seek to the end of the list max_size and write a end variable
    buffer.seek(pos + (max_size - stop_count - 1) * size, File.ABSOLUTE_FILE_POSITION)
    # White a end value
    buffer.write(convert_function(end))


def _remove_invalid_char(value: str) -> str:
    return re.sub(r'[^\x00-\x7f]', r' ', value)


def write_bool(buffer: _io.BufferedRandom, value: bool):
    buffer.write(StructDataHelper.convert_to_bin_bool(value))


# READ FUNCTIONS: READ A TYPED VALUE WITH A BUFFER
# READ PRIMITIVE TYPES
def read_primitive_type(buffer: _io.BufferedRandom, value):
    prim_type_name = ObjectHelper.get_type_name(value)

    if prim_type_name == SupportedTypes.INT_NAME:
        return read_int(buffer)

    if prim_type_name == SupportedTypes.FLOAT_NAME:
        return read_float(buffer)

    if prim_type_name == SupportedTypes.BOOL_NAME:
        return read_bool(buffer)

    raise ReadWriteError.ReadingANonPrimitiveType('Type ' + prim_type_name + ' ins\'t a valid non primitive type!')


# READ COMPLEX TYPES
def read_complex_type(buffer: _io.BufferedRandom, value, max_size=0, list_type=None):
    complex_type_name = ObjectHelper.get_type_name(value)

    if complex_type_name == SupportedTypes.STRING_NAME:
        return read_str(buffer, max_size)
    elif complex_type_name == SupportedTypes.LIST_NAME:
        return read_list(buffer, max_size, list_type)


def read_int(buffer: _io.BufferedRandom) -> int:
    return StructDataHelper.convert_from_bin_int(buffer.read(SupportedTypes.INT_SIZE))


def read_float(buffer: _io.BufferedRandom) -> float:
    return StructDataHelper.convert_from_bin_float(buffer.read(SupportedTypes.FLOAT_SIZE))


def read_bool(buffer: _io.BufferedRandom) -> bool:
    return StructDataHelper.convert_from_bin_bool(buffer.read(SupportedTypes.BOOL_SIZE))


def read_str(buffer: _io.BufferedRandom, max_size: int) -> str:
    value = ''
    char_count = 0

    # Remove one of the string end \0
    while char_count < max_size:
        new_char = StructDataHelper.convert_from_bin_char(buffer.read(SupportedTypes.CHAR_SIZE))

        # \0 is the end
        if new_char == _STRING_END:
            break

        value = value + new_char
        char_count = char_count + 1

    # Place the buffer in the end of the string
    if char_count != max_size:
        buffer.seek(buffer.tell() + (max_size - char_count) * SupportedTypes.CHAR_SIZE, File.ABSOLUTE_FILE_POSITION)

    return value


def read_list(buffer: _io.BufferedRandom, max_size: int, list_type: str) -> list:
    return_list = []
    list_size = StructDataHelper.convert_from_bin_int(buffer.read(SupportedTypes.INT_SIZE))
    count = 0

    if list_type == SupportedTypes.INT_NAME:
        convert_function = StructDataHelper.convert_from_bin_int
        type_size = SupportedTypes.INT_SIZE
    elif list_type == SupportedTypes.FLOAT_NAME:
        convert_function = StructDataHelper.convert_from_bin_float
        type_size = SupportedTypes.FLOAT_SIZE
    elif list_type == SupportedTypes.BOOL_NAME:
        convert_function = StructDataHelper.convert_from_bin_bool
        type_size = SupportedTypes.BOOL_SIZE
    else:
        raise ReadWriteError.ReadingAListOfInvalidType('The list has this invalid type:' + list_type)

    # Read all elements from the list
    while count < list_size:
        return_list.append(convert_function(buffer.read(type_size)))

        count = count + 1

    # Place the buffer in the end of the list
    if count != max_size:
        buffer.seek(buffer.tell() + (max_size - count) * type_size, File.ABSOLUTE_FILE_POSITION)

    return return_list