import pickle

from .preprocess import preprocess
from .lark_parser import lark_parser
from .larktree2treespread import larktree2treespread
from .analyse_treespread import analyse_treespread
from .utils import xlsxtotsv
from .valency_report import gen_valency_report, get_valency_structures
from .structure_report import get_structures, gen_struct_sentence_report, gen_structure_total_report


def taggedxlsx_2_treespread(in_file):
    # create folder + files
    folder = in_file.parent / in_file.stem
    if not folder.is_dir():
        folder.mkdir(exist_ok=True)
    conf_file = folder / (in_file.stem + '.config')
    trees_file = folder / (in_file.stem + '_treespread.xlsx')
    pickled = folder / (in_file.stem + '.pickle')

    # extracting sentences in word/POS tuples
    sentences = preprocess(in_file)

    # parsing sentences into trees (pickle parsed files to avoid reparsing)
    if not pickled.is_file():
        trees = lark_parser(sentences, conf_file)
        pickle.dump(trees, open(pickled, "wb"))
    else:
        print(f'"{pickled.name}" exists.\t\t\tIt will be loading instead of parsing the sentences.')
        trees = pickle.load(open(pickled, "rb"))

    # exporting to treespread
    if trees_file.is_file():
        print(f'"{trees_file.name}" already contains the trees in treespread format.\n\nexiting...')
        return False
    else:
        larktree2treespread(trees, trees_file)
        return True


def treespread_2_reports(in_file, total_val_structures, total_structures):
    # create folder
    folder = in_file.parent / in_file.stem
    if not folder.is_dir():
        folder.mkdir(exist_ok=True)

    # output files
    valency_file = folder / (in_file.stem.split('_')[0] + '_raw_valency.docx')
    sentences_file = folder / (in_file.stem.split('_')[0] + '_sentences.docx')
    structures_file = folder / (in_file.stem.split('_')[0] + '_structures.docx')

    # process treespreads
    analysed = analyse_treespread(in_file)

    # generate reports' content
    val_structures = {}
    structures = {}
    for sent_num, a in enumerate(analysed):
        tree_name, tree, derived_trees, rules, from_roof = a
        get_structures(tree, structures, total_structures, tree_name)
        get_valency_structures(tree, val_structures, total_val_structures)

    # export reports
    gen_valency_report(val_structures, valency_file)
    gen_struct_sentence_report(structures, sentences_file)
    gen_structure_total_report(structures, structures_file)

    # export_tree(tree, derived_trees, rules, out_dir, filename, format, from_roof, draw_square, font, write_all)


def total_struct_report(folder, total_val_structs, total_structs):
    valency_file = folder / (folder.stem + '_raw_valency.docx')
    sentences_file = folder / (folder.stem + '_sentences.docx')
    structures_file = folder / (folder.stem + '_structures.docx')
    gen_valency_report(total_val_structs, valency_file)
    gen_struct_sentence_report(total_structs, sentences_file)
    gen_structure_total_report(total_structs, structures_file)
