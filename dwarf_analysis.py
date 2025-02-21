import sys
from elftools.dwarf.compileunit import CompileUnit
from elftools.dwarf.die import DIE
from elftools.elf.elffile import ELFFile
from functools import wraps


def require_attr(attr, require_die=False):
    def decorator(func):
        @wraps(func)
        def wrapper(die: DIE):
            attr_value = die.attributes.get(attr)
            if attr_value:
                return func(attr_value, die) if require_die else func(attr_value)
            return None
        return wrapper
    return decorator


@require_attr("DW_AT_name")
def desc_name(attr_name):
    """
    Decode and return the name of a function from its DWARF attribute.

    Args:
        attr_name: The attribute containing the function name.

    Returns:
        str: The decoded function name.
    """
    return attr_name.value.decode('utf-8', errors='ignore')


@require_attr("DW_AT_decl_file", require_die=True)
def desc_file(attr_name, die):
    """
    Retrieve and return the file path where a function is defined.

    Args:
        attr_name: The attribute containing the file index.
        die (DIE): The Debugging Information Entry associated with the function.

    Returns:
        str: The full file path (directory + file name).
    """
    cu = die.cu
    dwarfinfo = cu.dwarfinfo
    lineprogram = dwarfinfo.line_program_for_CU(cu)

    # Filename/dirname arrays are 0-based in DWARF v5
    offset = 0 if lineprogram.header.version >= 5 else 1

    file_index = offset + int(attr_name.value)
    file_entry = lineprogram.header.file_entry[file_index]
    file_name = file_entry.name.decode('utf-8', errors='ignore')

    dir_index = offset + int(file_entry.dir_index)
    dir_name = lineprogram.header.include_directory[dir_index].decode('utf-8', errors='ignore')

    return dir_name + "/" + file_name


@require_attr("DW_AT_decl_line")
def desc_line(attr_name):
    """
    Retrieve and return the line number where a function is defined.

    Args:
        attr_name: The attribute containing the line number.

    Returns:
        str: The line number as a string.
    """
    return str(attr_name.value)


FUNC_ATTR_DESCRIPTIONS = dict(
    DW_AT_name=desc_name,
    DW_AT_decl_file=desc_file,
    DW_AT_decl_line=desc_line
)


def die_is_func(die: DIE):
    """
    Check if a DIE represents a function (subprogram).

    Args:
        die (DIE): The Debugging Information Entry to check.

    Returns:
        bool: True if the DIE is a function, False otherwise.
    """
    return die.tag == 'DW_TAG_subprogram'


def get_function_information(die: DIE):
    """
    Extract and print function details including its name, file, and line number.

    Args:
        die (DIE): The Debugging Information Entry for a function.
    """
    assert die_is_func(die)

    name = FUNC_ATTR_DESCRIPTIONS["DW_AT_name"](die)
    file = FUNC_ATTR_DESCRIPTIONS["DW_AT_decl_file"](die)
    line = FUNC_ATTR_DESCRIPTIONS["DW_AT_decl_line"](die)

    if any([name, file, line]):
        print(f"\t{name} @ {file} : {line}")


def desc_cu(cu: CompileUnit):
    """
    Extract and print information about a Compilation Unit (CU) and its functions.

    Args:
        cu (CompileUnit): The Compilation Unit to analyze.
    """
    cu_die = cu.get_top_DIE()
    name_attr = cu_die.attributes.get('DW_AT_name')
    assert name_attr

    name = name_attr.value.decode('utf-8', errors='ignore')
    print(f"\n[Compilation Unit] Offset: {cu.cu_offset}, Name: {name}")

    for die in cu.iter_DIEs():
        if die_is_func(die):
            get_function_information(die)


if __name__ == '__main__':
    elf_path = sys.argv[1]

    with open(elf_path, 'rb') as f:
        elf = ELFFile(f)

        if not elf.has_dwarf_info():
            print("No DWARF info found.")
            exit(0)

        dwarf_info = elf.get_dwarf_info()

        for cu in dwarf_info.iter_CUs():
            desc_cu(cu)
