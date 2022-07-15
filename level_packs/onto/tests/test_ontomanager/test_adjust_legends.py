# coding: utf8
from pathlib import Path

from leavedonto import OntoManager

ref = Path().absolute().parent / "resources" / "test_onto.yaml"
to_add = Path().absolute().parent / "resources" / "test_onto2.yaml"
different = Path().absolute().parent / "resources" / "test_onto_different.yaml"

om = OntoManager(ref)


def test_legends():
    om.adjust_legends()
    print()
