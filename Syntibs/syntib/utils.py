import csv
from pathlib import Path

import yaml
from openpyxl import load_workbook


class Config:
    def __init__(self, in_file, sentence_amount):
        self.conf_file = Path(in_file)
        self.state = self.load_chunks_config(list(range(sentence_amount)))

    def load_chunks_config(self, sent_amount):
        if not self.conf_file.is_file():
            content = '\n'.join([f'{c}: todo' for c in sent_amount])
            self.conf_file.write_text(content)
            return yaml.safe_load(content)
        else:
            return yaml.safe_load(self.conf_file.read_text())


def xlsxtotsv(in_file, tsv_folder):
    # write all sheets to temp tsv files
    workbook = load_workbook(in_file, data_only=True)
    sheets = workbook.get_sheet_names()
    for s in sheets:
        sheet = workbook.get_sheet_by_name(s)
        tsv = tsv_folder / f"{s}.tsv"
        with tsv.open("w") as w:
            writer = csv.writer(w, delimiter="\t")
            for row in sheet.rows:
                row = [c.value if c.value else '' for c in row]
                if ''.join(row):
                    writer.writerow(row)
