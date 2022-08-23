import csv
from pathlib import Path

from nltk import ParentedTree

from tempfile import TemporaryDirectory

from .utils import xlsxtotsv
from .botree import BoTree


def analyse_treespread(in_file):
    analysed = []

    if in_file.suffix == '.tsv':
        analysed.append(analyze_tsv_sentence(in_file))

    elif in_file.suffix == '.xlsx':
        with TemporaryDirectory() as dir:
            tsv_dir = Path(dir)
            xlsxtotsv(in_file, tsv_dir)
            ordered = sorted(tsv_dir.glob('*.tsv'), key=lambda x: int(x.stem))
            for tsv in ordered:
                analysed.append(analyze_tsv_sentence(tsv, tsv.stem))

    else:
        raise NotImplementedError('only .tsv and .xlsx are currently supported')

    return analysed


def analyze_tsv_sentence(filename, name):
    # read the tsv file in a single block
    content = filename.read_text(encoding="utf-8-sig")

    # get tree, derived trees and rules
    raw_tree, raw_derived = read_spreadtree(content)

    # gen BoTree
    bracketed = gen_bracketed_tree(raw_tree, raw_derived[0], name)
    tree = BoTree.fromstring(bracketed)

    derived_trees, rules = derive_trees_n_rules(tree, raw_derived)

    # calculate roof height
    from_roof = tree.height() * 25
    # add a bit
    if tree.height() >= 8:
        from_roof += 25

    return filename.stem, tree, derived_trees, rules, from_roof


def derive_trees_n_rules(tree, raw_derived):

    # gen derived_trees
    derived_trees = gen_derived_trees(raw_derived, tree)

    # gen rules
    rules = gen_rules(tree, derived_trees)

    return derived_trees, rules


def read_spreadtree(raw_content):
    def strip_empty_rows(rows):
        i = 0
        while i < len(rows):
            if not "".join(rows[i]):
                del rows[i]
            else:
                i += 1

        return rows

    def parse_rows(rows, translate_tree=None):
        # indentify POS and Words rows
        p, w = -1, -1
        for num, row in enumerate(rows):
            if "P" == row[0]:
                p = num
            if "W" == row[0]:
                w = num

        # run sanity checks
        assert p != -1 and w != -1, "The required P and W line markers aren't found"

        assert (
                len([r for r in rows[p] if r])
                == len([r for r in rows[w] if r])
                == len(rows[p])
                == len(rows[w])
        ), 'There is a problem on the "P" and "W" lines. maybe they are not correctly placed'

        # delete 1st column
        rows = [row[1:] for row in rows]

        # rows belonging to: the tree, the derived trees
        raw_tree, raw_derived = rows[: p + 1], rows[w:]

        return raw_tree, raw_derived

    rows = list(csv.reader(raw_content.split("\n"), delimiter="\t"))
    rows = strip_empty_rows(rows)
    raw_tree, raw_derived = parse_rows(rows)
    return raw_tree, raw_derived


def gen_bracketed_tree(raw_tree, words, name):
    def check_tree(tree):
        errors = []
        for num, row in enumerate(tree):
            state = None
            for cell in row:
                if cell and cell != "]":
                    if not cell.startswith("["):
                        errors.append(num)
                    if state and state != "end":
                        errors.append(num)
                    if "]" in cell:
                        if cell.endswith("]"):
                            state = "end"
                        else:
                            errors.append(num)
                            state = "begin"
                    else:
                        state = "begin"
                elif cell == "]":
                    if not state == "begin":
                        errors.append(num)
                    state = "end"
            if state != "end":
                errors.append(num)

        errors = sorted(list(set(errors)))

        return [", ".join(tree[e]) for e in errors]

    sanity = check_tree(raw_tree[:-1])
    if sanity:
        errors = "\n\t".join(sanity)
        raise SyntaxError(f"Errors in tree {name}, following rows:\n\t{errors}\n")

    tree = [
        [raw_tree[line][col] for line in range(len(raw_tree))]
        for col in range(len(raw_tree[0]))
    ]
    for num, col in enumerate(tree):
        new_line = [el for el in col if el]
        for mun, el in enumerate(new_line):
            if "]" in el and mun < len(new_line) - 1:
                count = el.count("]")
                new_line[mun] = new_line[mun].replace("]", "")
                new_line[mun + 1] += "]" * count
        new_line = [el for el in new_line if el]
        tree[num] = new_line

    # add words to tree
    for n, word in enumerate(words):
        word = word.replace(" ", "_")
        pos = tree[n][-1]
        if pos.endswith("]"):
            count = pos.count("]")
            pos = pos[:-count] + " –" + word + "]" * count
        else:
            pos = pos + " –" + word

        tree[n][-1] = pos

    # add boxes to final nodes for mshang
    for n, col in enumerate(tree):
        for m, cell in enumerate(col):
            if not cell.startswith("["):
                tree[n][m] = "[" + tree[n][m] + "]"

    bracketed_tree = " ".join([" ".join(col) for col in tree]).replace('–', '').replace("[", "(").replace("]", ")")
    return bracketed_tree


def gen_rules(tree, derived_trees):
    rules = [str(r) for r in tree.productions() if "'" not in str(r)]
    vocab = [str(r) for r in tree.productions() if "'" in str(r)]
    extra_rules = []
    for n, t in enumerate(derived_trees):
        for rule in t.productions():
            str_rule = str(rule)
            str_rule = str_rule.replace("--extra" + str(n + 1), "")
            if (
                    "'" not in str_rule
                    and str_rule not in rules
                    and str_rule not in extra_rules
            ):
                extra_rules.append(str_rule)

    rules = "\n".join(rules)
    extra_rules = "\n".join(extra_rules)
    vocab = "\n".join(vocab)

    return f"rules:\n{rules}\n\nextra rules:\n{extra_rules}\n\nvocab:\n{vocab}"


def gen_derived_trees(simplified_sentences, full_tree):
    parented_tree = ParentedTree(0, []).convert(full_tree)
    subtrees = []
    for n, sent in enumerate(simplified_sentences):
        new_tree = parented_tree.copy(deep=True)
        new_tree.set_label(f"{new_tree.label()}--extra{n}")
        # delete leafs
        to_del = list(reversed([num for num, word in enumerate(sent) if not word]))
        if not to_del:
            continue
        for num in to_del:
            postn = new_tree.leaf_treeposition(num)
            # go up deleting nodes until there are left siblings (we are starting
            while not (
                new_tree[postn[:-1]].left_sibling()
                or new_tree[postn[:-1]].right_sibling()
            ):
                postn = postn[:-1]

            del new_tree[postn[:-1]]

        subtrees.append(BoTree(0, []).convert(new_tree))

    return subtrees
