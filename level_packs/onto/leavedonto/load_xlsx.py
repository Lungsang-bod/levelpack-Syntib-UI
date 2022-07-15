from pathlib import Path

import yaml

from openpyxl import load_workbook
from openpyxl.utils import coordinate_to_tuple

from .triedicts import DictsToTrie


class LoadXlsx:
    def __init__(self, ont_path):
        self.dicts = {"ont": [], "legend": []}
        self.ont_path = Path(ont_path)

    def load_xlsx(self):
        # load xlsx
        wb = load_workbook(self.ont_path)
        ont = self.__load_ont_sheet(wb.worksheets[0])
        leaves = self.__load_ont_leaves(wb.worksheets[1:])
        ont = "\n".join(["".join(o) for o in ont])

        # convert to dicts
        self.dicts["ont"] = yaml.safe_load(ont)
        self.__add_leaves(self.dicts["ont"], leaves)
        self.dicts["legend"] = self.__find_legend(wb)

        # convert to OntTrie
        dt = DictsToTrie(self.dicts)
        dt.convert()
        ont = dt.trie
        return ont

    @staticmethod
    def __load_ont_sheet(sheet):
        # from sheet to list of lists
        ont = []
        max_row, max_col = coordinate_to_tuple(sheet.dimensions.split(":")[1])
        for r in range(1, max_row + 1):
            row = []
            is_indent = True
            indent = "    "
            for col in range(2, max_col + 1):
                # ignoring the first column containing the numbers
                value = sheet.cell(r, col).value
                if isinstance(value, str):
                    leaf_idx = sheet.cell(r, 1).value
                    # add leaf(sheet in the xlsx) idx as value to retrieve it later
                    if leaf_idx:
                        value += f" [{leaf_idx}]"  # yaml dict markup
                    else:
                        value += ":"
                    row.append(value)
                    is_indent = False
                elif is_indent:
                    row.append(indent)
            ont.append(row)
        return ont

    @staticmethod
    def __load_ont_leaves(sheets):
        leaves = {}
        for sheet in sheets:
            idx, _ = sheet.title.split(" ", 1)
            idx = int(idx)

            leaf = []
            max_row, max_col = coordinate_to_tuple(sheet.dimensions.split(":")[1])
            for r in range(1, max_row + 1):
                row = []
                for col in range(1, max_col + 1):
                    # ignoring the first column containing the numbers
                    value = sheet.cell(r, col).value
                    if not value:
                        row.append("")
                    else:
                        row.append(value)
                leaf.append(row)
            leaf = leaf[1:]  # leave out the legend

            leaves[idx] = leaf
        return leaves

    def __add_leaves(self, ont, leaves):
        for key, value in ont.items():
            if isinstance(value, dict):
                self.__add_leaves(value, leaves)
            else:
                if value[0] in leaves:
                    ont[key] = leaves[value[0]]

    @staticmethod
    def __find_legend(workbook):
        sheet1 = [s for s in workbook.worksheets if s.title.startswith("1 ")][0]
        _, max_col = coordinate_to_tuple(sheet1.dimensions.split(":")[1])
        legend = []
        for col in range(1, max_col + 1):
            value = sheet1.cell(1, col).value
            legend.append(value)
        return legend
