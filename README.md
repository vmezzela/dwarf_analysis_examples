## Usage:

```
usage: dwarf_analysis.py [-h] --debug_info DEBUG_INFO [--elf ELF] [--base_path BASE_PATH] [--cu CU] [--function FUNCTION] [--relative_idx]

options:
  -h, --help            show this help message and exit
  --debug_info DEBUG_INFO
                        Path to the debug info file.
  --elf ELF             Path to the ELF binary file.
  --base_path BASE_PATH
                        Base directory for relative paths.
  --cu CU               Compilation unit to filter the debug information.
  --function FUNCTION   Function name to analyze.
  --relative_idx        Use relative indexing.
```

The `elf` option is useful to find the index of the same function in the symtab
of an ELF without the debug information.

The `base_path` option allows to adjust the files paths using this new base
path if they are relatives. Is useful when the object is compiled in a build
environment that is different and the paths hardcoded in the debug information
don't match with the location of your sources.

`relative_idx`, if enabled, makes the script returning the position of the
function among all the entries in the symtab with the same name instead of its
absolute index (1-based).

### Example test:

```sh
(cd ./duplicated_symbols/ && make)
./dwarf_analysis.py --debug_info ./duplicated_symbols/duplicated_syms
```
or
```sh
./test.sh $(debuginfod-find debuginfo ~/Work/klp/data/x86_64/lib/modules/4.12.14-122.194-default/kernel/drivers/scsi/pm8001/pm80xx.ko) ~/Work/klp/data/x86_64/usr/src/linux-4.12.14-122.194/
```
