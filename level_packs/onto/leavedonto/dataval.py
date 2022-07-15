from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.utils.cell import (
    coordinate_from_string,
    column_index_from_string,
    get_column_letter,
)


""" ***usage example***
# prepare validators
validator1, values1 = 'animals', ['Cat', 'Dog', 'Lion', 'Tiger']
validator2, values2 = 'other', ['a', 'b', 'c']

# add validators
dv = DataVal(workbook)
wb.add_validator(validator1, values1)
wb.add_validator(validator2, values2)

# apply validators to a worksheet
wb.add_val_to_cell(validator1, sheet_name, idx='B1')  # add validation to B1
wb.add_val_to_row(validator1, sheet_name, 3)  # add validation to row 3
wb.add_val_to_col(validator2, sheet_name, 1)  # add validation to col 1
"""


class DataVal:
    def __init__(self, wb):
        self.wb = wb
        self.msgs = {
            "error": "Your entry is not in the list",
            "error_title": "Invalid Entry",
            "prompt": "",
            "prompt_title": "",
        }
        self.validators = {}

    def add_validator(self, title, values):
        values = ",".join(values)
        dv = DataValidation(type="list", formula1=f'"{values}"')
        dv.error = self.msgs["error"]
        dv.errorTitle = self.msgs["error_title"]
        dv.prompt = self.msgs["prompt"]
        dv.promptTitle = self.msgs["prompt_title"]

        self.validators[title] = dv

    def add_val_to_row(self, val_name, sheet_name, row):
        for col in range(1, self.wb[sheet_name].max_column + 1):
            self.add_val_to_cell(val_name, sheet_name, row=row, col=col)

    def add_val_to_col(self, val_name, sheet_name, col):
        for row in range(1, self.wb[sheet_name].max_row + 1):
            self.add_val_to_cell(val_name, sheet_name, row=row, col=col)

    def add_val_to_cell(self, val_name, sheet_name, idx=None, row=None, col=None):
        if idx:
            col, row = coordinate_from_string(idx)
            col = column_index_from_string(col)
        if not idx:
            idx = f"{get_column_letter(col)}{row}"
        if (
            self.validators[val_name]
            not in self.wb[sheet_name].data_validations.dataValidation
        ):
            self.wb[sheet_name].add_data_validation(self.validators[val_name])

        self.validators[val_name].add(idx)
