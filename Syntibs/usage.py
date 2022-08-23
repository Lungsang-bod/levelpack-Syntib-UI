from pathlib import Path

from syntib import taggedxlsx_2_treespread, treespread_2_reports, total_struct_report


# mode = '2treespread'
mode = '2reports'

if mode == '2reports':
    in_path = Path('content/reports/A0')
    total_val_structs, total_structs = {}, {}
    for treespread in sorted(list(in_path.glob('*.xlsx'))):
        print(treespread.name)
        treespread_2_reports(treespread, total_val_structs, total_structs)
    total_struct_report(in_path, total_val_structs, total_structs)

if mode == '2treespread':
    in_path = Path('content/tagged2treespread')
    for tagged_file in sorted(list(in_path.glob('*.xlsx'))):
        print(tagged_file.name)
        has_parsed = taggedxlsx_2_treespread(tagged_file)
        if has_parsed:
            break
