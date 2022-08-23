from pathlib import Path

from .leavedonto import LeavedOnto
from .ontomanager import OntoManager
from .trie import OntTrie


def merge_ontos(ontos_path, out_file, basis=None):
    if basis:
        om = OntoManager(basis)
    else:
        om = OntoManager()

    om.batch_merge_to_onto(ontos_path)

    out_file = Path(out_file)
    if out_file.suffix == '.yaml':
        om.onto1.convert2yaml(out_file)
    elif out_file.suffix == '.xlsx':
        om.onto1.convert2xlsx(out_file)
    else:
        print('Exiting. outfile should either be a .yaml or a .xlsx')


def export(onto, to, out_path=None):
    lo = LeavedOnto(onto)
    if to == 'yaml':
        lo.convert2yaml(out_path)
    elif to == 'xlsx':
        lo.convert2xlsx(out_path)
    else:
        print('Exiting. "to" should either be yaml or xlsx')
