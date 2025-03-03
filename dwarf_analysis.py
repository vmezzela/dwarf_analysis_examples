#!/usr/bin/python3

import argparse
from elftools.dwarf.compileunit import CompileUnit
from elftools.dwarf.die import DIE
from elftools.elf.elffile import ELFFile
from elftools.elf.sections import SymbolTableSection
from functools import wraps
from pathlib import PurePath

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


def clean_relative_path(path: PurePath):
    """
    Drop all the leading ".." from the path

    Args:
        path: The path to clean.

    Returns:
        PurePath: The cleaned path.
    """
    parts = path.parts
    if parts and parts[0] != "..":
        return path

    new_path = PurePath(*parts[1:])
    return clean_relative_path(new_path)


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
    offset = 0 if lineprogram.header.version >= 5 else -1

    file_index = offset + int(attr_name.value)
    # TODO: value 0 means that no source has been specified
    assert 0 <= file_index < len(lineprogram.header.file_entry)
    file_entry = lineprogram.header.file_entry[file_index]
    file_name = PurePath(file_entry.name.decode('utf-8', errors='ignore'))

    dir_index = offset + int(file_entry.dir_index)
    assert 0 <= dir_index < len(lineprogram.header.include_directory)
    enc_dir_path = lineprogram.header.include_directory[dir_index]
    dir_path = PurePath(enc_dir_path.decode('utf-8', errors='ignore'))

    return dir_path/file_name


@require_attr("DW_AT_decl_line")
def desc_line(attr_name):
    """
    Retrieve and return the line number where a function is defined.

    Args:
        attr_name: The attribute containing the line number.

    Returns:
        int: The line number.
    """
    return attr_name.value

@require_attr("DW_AT_low_pc")
def desc_addr(attr_name):
    """
    Retrieve and return the address of the function.

    Args:
        attr_name: The attribute containing the address.

    Returns:
        int: The address.
    """
    return attr_name.value


FUNC_ATTR_DESCRIPTIONS = dict(
    DW_AT_name=desc_name,
    DW_AT_decl_file=desc_file,
    DW_AT_decl_line=desc_line,
    DW_AT_low_pc=desc_addr
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


def get_function_symtab_index(function, address):
    """
    Retrieve the symbol index of a given function identified by its name and
    its address. The address is needed because more function with the same name
    might be present in the symbol table.

    Args:
        function: The name of the function.
        address: The address of the function.

    Returns:
        int: The index of the function in the symbol table.
    """
    symtab = elf.get_section_by_name(".symtab")
    assert isinstance(symtab, SymbolTableSection)

    found = None
    for i in range(symtab.num_symbols()):
        sym = symtab.get_symbol(i)
        sym_type = sym['st_info']['type']

        # Skip entries that are not functions
        if sym_type != 'STT_FUNC':
            continue

        sym_addr = sym['st_value']
        if sym.name == function and sym_addr == address:
            # Make sure there are no other entries with same (name, address).
            # This slows down a lot the search, because we could otherwise just
            # do:
            #    return i
            #
            # NOTE: keep this until I make sure what's the minimal subset of
            # attributes that makes an entry unique
            assert not found
            found = i

    return found


def get_function_information(die: DIE, base_path="", filter_function_name=""):
    """
    Extract and print function details including its name, file, and line number.

    Args:
        die (DIE): The Debugging Information Entry for a function.
    """
    assert die_is_func(die)

    name = FUNC_ATTR_DESCRIPTIONS["DW_AT_name"](die)
    if filter_function_name and name != filter_function_name:
        return

    file = FUNC_ATTR_DESCRIPTIONS["DW_AT_decl_file"](die)
    line = FUNC_ATTR_DESCRIPTIONS["DW_AT_decl_line"](die)
    addr = FUNC_ATTR_DESCRIPTIONS["DW_AT_low_pc"](die)

    if all([name, file, line, addr]):
        file = clean_relative_path(file)
        if base_path:
            file = PurePath(base_path)/file
        idx = get_function_symtab_index(name, addr)
        print(f"{name} {file} {line} {hex(addr)} {idx}")


def desc_cu(cu: CompileUnit, base_path="", filter_cu_name="", filter_function_name=""):
    """
    Extract and print information about a Compilation Unit (CU) and its functions.

    Args:
        cu (CompileUnit): The Compilation Unit to analyze.
    """
    cu_die = cu.get_top_DIE()
    name_attr = cu_die.attributes.get('DW_AT_name')
    assert name_attr

    name = PurePath(name_attr.value.decode('utf-8', errors='ignore'))
    name = clean_relative_path(name)
    if filter_cu_name and name != PurePath(filter_cu_name):
        return

    print(f"\n[Compilation Unit] Offset: {cu.cu_offset}, Name: {name}")

    for die in cu.iter_DIEs():
        if die_is_func(die):
            get_function_information(die, base_path, filter_function_name)



def main():
    global elf
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug_info", type=str, required=True)
    parser.add_argument("--elf", type=str, required=False)
    parser.add_argument("--base_path", type=str, required=False)
    parser.add_argument("--cu", type=str, required=False)
    parser.add_argument("--function", type=str, required=False)
    args = parser.parse_args()

    with open(args.debug_info, 'rb') as f:
        debug_info_file = ELFFile(f)

        if args.elf:
            elf_file = open(args.elf, 'rb')
            elf = ELFFile(elf_file)
        else:
            elf = debug_info_file

        if not debug_info_file.has_dwarf_info():
            print("No DWARF info found.")
            exit(0)

        dwarf_info = debug_info_file.get_dwarf_info()

        for cu in dwarf_info.iter_CUs():
            desc_cu(cu, base_path=args.base_path, filter_cu_name=args.cu, filter_function_name=args.function)

        elf.close()


if __name__ == '__main__':
    main()
