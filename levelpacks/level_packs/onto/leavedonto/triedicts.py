from .trie import OntTrie


def trie_to_dicts(trie):
    # very ugly hack using exec() to be able to populate the nested dicts from the lists of paths
    # the difficulty lies in growing "dicts['ont']" until "dicts['ont'][branch1][branch3][branch4]"
    # and, at every step, creating the nested dict if required
    #
    # [([branch1, branch2], data1),
    #  ([branch1, branch3, branch4], data2)]
    #
    # becomes:
    #
    # {branch1:
    #       {branch2: data1},
    #       {branch3:
    #               {branch4: data2}
    #       }
    # }
    dicts = {"legend": trie.legend, "ont": {}}

    all_branches = trie.find_entries()
    for branch in all_branches:
        path, entries = branch
        i = 0
        while i < len(path):
            part = 'dicts["ont"]' + "".join([f'["{p}"]' for p in path[:i]])
            test_n_create_nested_dict = (
                "if path[i] not in " + part + ":\n    " + part + "[path[i]] = {}"
            )
            try:
                exec(test_n_create_nested_dict)
            except TypeError:
                print(f'{part} ought to be a node in the onto, but there are entries in it.\nexiting...')
                break
            i += 1
        exec('dicts["ont"]' + "".join([f'["{p}"]' for p in path]) + " = entries")

    return dicts


class DictsToTrie:
    def __init__(self, dicts):
        self.dicts = dicts
        self.trie = OntTrie()
        self.trie.legend = dicts["legend"]

        # vars
        self.words = None
        self.result_path = None
        self.found = None

        self.convert()

    def convert(self):
        all_ = self.find_all_words()
        for a in all_:
            path, entry = a["path"], a["entry"]
            self.trie.add(path, entry)

    def find_all_words(self):
        words = self.list_words()
        all_words = []
        for w in words:
            all_words.extend(self.find_word(w))
        return all_words

    def list_words(self, ont=None, words=None):
        # initiate vars
        if not ont and not words:
            ont = self.dicts["ont"]
            words = self.words = []

        self.__recursive_list(ont)
        words = sorted(list(set(words)))
        return words

    def __recursive_list(self, onto):
        for key, value in onto.items():
            if isinstance(value, dict):
                self.__recursive_list(value)
            else:
                self.words.extend([v[0] for v in value])

    def find_word(self, word):
        # initiate vars
        self.result_path = []
        self.found = []
        level = 0
        self.__recursive_find(self.dicts["ont"], word, level)
        return self.found

    def __recursive_find(self, onto, word, level):
        for key, value in onto.items():
            self.result_path.append(key)
            if isinstance(value, dict):
                self.__recursive_find(value, word, level + 1)
            else:
                has_found = False
                for entry in value:
                    if entry[0] == word:
                        occ = {"path": self.result_path, "entry": entry}
                        self.found.append(occ)
                        has_found = True
                if has_found:
                    self.result_path = self.result_path[:level]
                else:
                    self.result_path = self.result_path[:-1]
        level -= 1
        self.result_path = self.result_path[:-1]
