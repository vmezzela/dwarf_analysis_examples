## Usage:
```sh
(cd ./duplicated_symbols/ && make)
python3 dwarf_analysis.py --file ./duplicated_symbols/duplicated_syms
```

### Example test:
```sh
./test.sh $(debuginfod-find debuginfo ~/Work/klp/data/x86_64/lib/modules/4.12.14-122.194-default/kernel/drivers/scsi/pm8001/pm80xx.ko) ~/Work/klp/data/x86_64/usr/src/linux-4.12.14-122.194/
```
