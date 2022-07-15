from collections import defaultdict
from copy import deepcopy
from pathlib import Path

import yaml

from .leavedonto import LeavedOnto
from .trie import OntTrie
from .tag_to_onto import generate_to_tag, generate_to_tag_chunks, tagged_to_trie, get_entries


class OntoManager:
    def __init__(self, onto_basis=None):
        if onto_basis:
            self.onto1 = LeavedOnto(onto_basis)
        else:
            self.onto1 = LeavedOnto(OntTrie())

    def diff_ontos(self, onto2, mode="all"):
        """

        :param onto2: path to onto to diff or LeavedOnto object
        :param mode: all, base_only, other_only, shared
        :return:
        """
        if isinstance(onto2, LeavedOnto):
            other_onto = onto2
        elif isinstance(onto2, Path):
            other_onto = LeavedOnto(onto2)
        else:
            raise TypeError(
                "to_diff should be either a Path object, or a LeavedOnto object"
            )

        base_only, shared, other_only = self.__find_differences(other_onto, mode=mode)

        if mode == "all":
            return base_only, shared, other_only
        elif mode == "base_only":
            return base_only
        elif mode == "other_only":
            return other_only
        elif mode == "shared":
            return shared
        else:
            raise SyntaxError("either all, base_only, other_only or shared")

    def __find_differences(self, onto2, mode="all"):
        to_ignore = ["freq", "origin"]
        # comparison is done on cleaned entries ; original entries are returned
        entries_base = self.__expand_search_results(self.onto1.ont.find_entries())
        entries_base_cleaned = self.__clean_exported_entries(entries_base, to_ignore)
        entries_other = self.__expand_search_results(onto2.ont.find_entries())
        entries_other_cleaned = self.__clean_exported_entries(entries_other, to_ignore)

        only_in_base, only_in_other, shared = None, None, None
        if mode == "all" or mode == "base_only":
            only_in_base = [entries_base[n] for n, e in enumerate(entries_base_cleaned) if e not in entries_other_cleaned]
        if mode == "all" or mode == "other_only":
            only_in_other = [entries_other[n] for n, e in enumerate(entries_other_cleaned) if e not in entries_base_cleaned]
        if mode == "all" or mode == "shared":
            shared = []
            for n, o in enumerate(entries_other_cleaned):
                if o in entries_base_cleaned:
                    m = 0
                    for m, b in enumerate(entries_base_cleaned):
                        if o == b:
                            break
                    shared.append((entries_base[m], entries_other[n]))
        return only_in_base, shared, only_in_other

    @staticmethod
    def __expand_search_results(res):
        return [(path, e) for path, entries in res for e in entries]

    def __clean_exported_entries(self, entries, ignore_fields):
        if not entries:
            return entries

        cleaned = []
        for path_, entry in entries:
            new = deepcopy(entry)
            for i in ignore_fields:
                self.onto1.set_field_value(new, i, '', mode="replace")
            cleaned.append((path_, new))
        return cleaned

    def tag_segmented(self, in_file, out_file=None, fields=dict):
        # fields should at least contain "pos", "levels" and "l_colors" entries
        if 'pos' not in fields:
            raise ValueError('"pos" entry missing in fields')
        if 'levels' not in fields:
            raise ValueError('"levels" entry missing in fields')
        if 'l_colors' not in fields:
            raise ValueError('"l_colors" entry missing in fields')
        pos_list, levels, l_colors = fields.pop('pos'), fields.pop('levels'), fields.pop('l_colors')
        generate_to_tag(in_file, self.onto1, pos_list, levels, l_colors, out_file=out_file, fields=fields)

    def tag_segmented_chunks(self, in_file, out_file=None, line_mode="chunk", fields=dict):
        # fields should at least contain "pos", "levels" and "l_colors" entries
        if 'pos' not in fields:
            raise ValueError('"pos" entry missing in fields')
        if 'levels' not in fields:
            raise ValueError('"levels" entry missing in fields')
        if 'l_colors' not in fields:
            raise ValueError('"l_colors" entry missing in fields')
        pos_list, levels, l_colors = fields.pop('pos'), fields.pop('levels'), fields.pop('l_colors')

        # segment text into chunks
        chunks = self.__generate_chunks(in_file, line_mode)

        # write a config file that keeps the status of how each segment is parsed
        conf_file = out_file.parent / (out_file.stem.split('_')[0] + '.config')
        config = self.__load_chunks_config(conf_file, list(chunks.keys()))

        # process chunks and update config
        config = generate_to_tag_chunks(chunks, config, self.onto1, line_mode, pos_list, levels, l_colors, out_file=out_file, fields=fields)
        conf_file.write_text(yaml.safe_dump(config))

        # return status for not
        if 'todo' in config.values():
            return True
        else:
            return False

    @staticmethod
    def __generate_chunks(in_file, line_mode):
        dump = in_file.read_text().strip().strip('\ufeff')

        if line_mode == "sentence":
            chunk_size = 4  # sentences
            units = []
            for line in dump.split('\n'):
                w = line.strip().split(' ')
                units.append(w)
        elif line_mode == "chunk":
            chunk_size = 48  # words
            # create list of words
            units = []
            for line in dump.split('\n'):
                w = line.strip().split(' ')
                units.append(w)
        else:
            raise SyntaxError('line_mode is either "sentence" or "chunk".')

        # create chunks
        chunks = {}
        chunk = []
        c_count = 0
        w_count = 0
        for unit in units:
            if w_count < chunk_size - 1:
                chunk.append(unit)
                w_count += 1
            else:
                chunk.append(unit)
                chunks[c_count] = chunk
                c_count += 1
                w_count = 0
                chunk = []
        if chunk:
            chunks[c_count] = chunk

        return chunks

    @staticmethod
    def __load_chunks_config(conf_file, chunks):
        if not conf_file.is_file():
            content = '\n'.join([f'{c}: todo' for c in chunks])
            conf_file.write_text(content)
            return yaml.safe_load(content)
        else:
            return yaml.safe_load(conf_file.read_text())

    def onto_from_tagged(self, in_file, out_file=None):
        # first merge all ontos you want, then generate onto from tagged

        # load words and tags
        tagged = get_entries(in_file)
        if not tagged:
            print(f'{in_file} has no tagged word. Please tag and rerun.')
            return
        # generate trie
        trie = tagged_to_trie(tagged, self.onto1)
        # write it to out_file
        if not out_file:
            out_file = in_file.parent / (in_file.stem + "_onto.yaml")
        onto = LeavedOnto(trie, out_file)
        onto.convert2yaml(out_path=out_file)

    def batch_merge_to_onto(self, ontos, in_to_organize=False):
        if isinstance(ontos, str) or isinstance(ontos, Path):
            ontos = sorted(Path(ontos).glob('*.yaml'))
        elif isinstance(ontos, list):
            ontos = sorted(ontos)
        else:
            raise ValueError('ontos should be a str, a Path object or a list of filenames.')

        for onto in ontos:
            print(f'merging {onto}')
            self.merge_to_onto(onto, in_to_organize=in_to_organize)

    def merge_to_onto(self, onto2, in_to_organize=False, add_origin=True):
        # add to onto1 the entries that are only in onto2
        if not isinstance(onto2, LeavedOnto):
            onto2 = LeavedOnto(onto2)

        if not self.onto1.ont.legend:
            self.onto1.ont.legend = onto2.ont.legend

        if sorted(onto2.ont.legend) != sorted(self.onto1.ont.legend):
            raise SyntaxError(
                "the two ontos need to have the same elements in the legend, in the same order."
                "\nPlease retry after that."
            )

        _, shared, other_only = self.diff_ontos(onto2, mode="all")
        shared = [s[1] for s in shared]  # only keeping entries from onto2. (shared contains both)
        to_merge = shared + other_only

        def add_origin(entries):
            for i, t in enumerate(entries):
                path, entry = t[0], t[1]
                origin = onto2.ont_path.stem.split("_")[0]
                origin += f':{self.onto1.get_field_value(entry, "freq")}'
                self.onto1.set_field_value(entry, "origin", origin)
            return entries

        # add origins
        if add_origin:
            to_merge = add_origin(to_merge)

        if in_to_organize:
            for i in range(len(to_merge)):
                to_merge[i] = (["to_organize"] + to_merge[i][0], to_merge[i][1])

        for path, entry in to_merge:
            self.__merge_origins_n_add(path, entry)

        self.onto1._cleanup()

    def __merge_origins_n_add(self, path, entry, onto=None):
        onto = self.onto1 if not onto else onto
        found = onto.ont.find_entries(prefix=path, lemma=entry[0])
        if not found:
            onto.ont.add(path, entry)
        else:
            for f_path, f_entries in found:
                added = False
                for f_e in f_entries:
                    added = self.__merge_origins(onto, entry, f_e, path)
                    if added:
                        break
                if not added:
                    onto.ont.add(path, entry)

    @staticmethod
    def __merge_origins(onto, entry, f_e, path):
        # prepare comparison of entry to add and found entry
        entry_clean = []
        f_e_clean = []
        entry_origin = ''
        f_e_origin = ''
        entry_freq = ''
        f_e_freq = ''
        entry_level = ''
        f_e_level = ''
        for el in onto.ont.legend:
            if el == 'origin':
                entry_origin = onto.get_field_value(entry, el)
                f_e_origin = onto.get_field_value(f_e, el)
                e_el, f_el = '', ''
            elif el == 'freq':
                entry_freq = onto.get_field_value(entry, el)
                f_e_freq = onto.get_field_value(f_e, el)
                e_el, f_el = '', ''
            elif el == 'level':
                entry_level = onto.get_field_value(entry, el)
                f_e_level = onto.get_field_value(f_e, el)
                e_el, f_el = '', ''
            else:
                e_el = onto.get_field_value(entry, el)
                f_el = onto.get_field_value(f_e, el)
            entry_clean.append(e_el)
            f_e_clean.append(f_el)

        if entry_clean == f_e_clean:
            # only difference is the origin -> merge origins in the trie
            # 1. remove old entry
            onto.ont.remove_entry(path, f_e)

            # 2. merge origins
            origs = defaultdict(int)
            for o in [entry_origin, f_e_origin]:
                for orig in o.split(' — '):
                    a, b = orig.split(':')
                    origs[a] += int(b)
            origs = [f'{a}:{b}' for a, b in origs.items()]
            merged_origs = ' — '.join(sorted(origs))
            onto.set_field_value(f_e_clean, 'origin', merged_origs, mode='replace')

            # 3. merge freqs
            merged_freq = 0
            for f in [entry_freq, f_e_freq]:
                try:
                    f = int(f)
                except ValueError:
                    f = 0
                    pass
                merged_freq += f
            onto.set_field_value(f_e_clean, 'freq', merged_freq, mode='replace')

            # 4. merge levels: take lowest level, the first level on which the word was introduced
            merged_level = sorted([entry_level, f_e_level])[0]
            onto.set_field_value(f_e_clean, 'level', merged_level, mode='replace')

            # add new entry
            onto.ont.add(path, f_e_clean)
            return True
        return False

    def adjust_legends(self):
        template = "# legend list from the original onto.\n" \
                   "legend_orig: {orig}\n" \
                   "# new legend:\n" \
                   "# omitting elements will remove the whole field, together with all its content.\n" \
                   "# adding elements will add empty fields for all entries.\n" \
                   "# reordering elements will reorder all the entries.\n" \
                   "legend_new: {orig}\n" \
                   "# list of tuple(<old>, <new>): <old> becomes <new>, keeping all the content in the fields.\n" \
                   "# note: leave empty if there are no replacements.\n" \
                   "replacements: []"
        to_adjust = template.format(orig=self.onto1.ont.legend)

        legend_config = Path("adjust_legends.yaml")
        if not legend_config.is_file():
            legend_config.write_text(to_adjust)
            print(f"Please fill in the adjustment file: {legend_config}")
            return

        adjust = yaml.safe_load(legend_config.read_text())
        if to_adjust == adjust:
            print("Please modify adjust_legends.yaml and rerun.")

        self._adjust_entries(adjust["legend_orig"], adjust["legend_new"])
        self._replace_legend(adjust["legend_new"], adjust["replacements"])
        self.onto1.convert2yaml()
        legend_config.unlink(missing_ok=True)

    def _replace_legend(self, l_new, replc):
        # apply replacements
        for orig, new in replc:
            for n, el in enumerate(l_new):
                if orig == el:
                    l_new[n] = new
        self.onto1.ont.legend = l_new

    def _adjust_entries(self, l_orig, l_new):
        queue = [self.onto1.ont.head]
        while queue:
            current_node = queue.pop()
            if current_node.leaf:
                # remove duplicates and sort in tibetan order
                for n, entry in enumerate(current_node.data):
                    old = {l_orig[i]: entry[i] for i in range(len(l_orig))}
                    new = {l_new[i]: "" for i in range(len(l_new))}  # no values
                    new = {l: old[l] if l in old else "" for l, _ in new.items()}  # with values
                    new_entry = [new[e] for e in l_new]
                    current_node.data[n] = new_entry
            queue = [node for key, node in current_node.children.items()] + queue

    def recompose_ontos_from_master(self, overwrite=False):
        ontos_path = self.onto1.ont_path.parent
        # {<level_onto>: <LeavedOnto object>, <...>: ...}  ontos to reconstruct
        struct = {onto.stem.split('_')[0]: LeavedOnto(OntTrie(), ont_path=onto) for onto in ontos_path.rglob('*.yaml') if onto != self.onto1.ont_path}
        # set legends, add suffix to filename if needed
        for onto in struct.values():
            onto.set_legend(self.onto1.ont.legend)
            if not overwrite:
                onto.ont_path = onto.ont_path.parent / (onto.ont_path.stem + '_updated.yaml')

        # {<base-level onto>: [<base-level onto>, <level onto>], ...}  by which ontos a given entry should be ingested
        recompose_paths = {onto.stem.split('_')[0]: [onto.stem.split('_')[0], onto.parts[-2]] for level in ontos_path.glob('*') if level.is_dir() for onto in level.glob('*.yaml')}

        # reconstruct base-level ontos
        all_entries = self.onto1.ont.export_all_entries()

        # reconstruct ontos
        for path_, entries in all_entries:
            for entry in entries:
                origin = self.onto1.get_field_value(entry, 'origin')
                for orig in origin.split(' — '):
                    o, freq = orig.split(':')
                    if o not in recompose_paths:
                        continue

                    freq = int(freq)
                    for n, onto in enumerate(recompose_paths[o]):
                        norig_entry = deepcopy(entry)
                        self.onto1.set_field_value(norig_entry, 'freq', freq, mode='replace')
                        if n == 0:
                            # base-level ontos don't have origins. removing it before adding entries normally
                            self.onto1.set_field_value(norig_entry, 'origin', '', mode='replace')
                            struct[onto].ont.add(path_, data=norig_entry)
                        elif n == 1:
                            # level ontos join all base-level ontos of their level. adding origin + merging them
                            self.onto1.set_field_value(norig_entry, 'origin', f'{o}:{freq}', mode='replace')
                            self.__merge_origins_n_add(path_, norig_entry, onto=struct[onto])

        for onto in struct.values():
            onto.convert2yaml()

