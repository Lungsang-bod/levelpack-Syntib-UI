from pathlib import Path

import yaml

from lark import Lark
from lark.exceptions import UnexpectedCharacters, UnexpectedEOF
import time
import datetime

from .utils import Config


def lark_parser(tagged_sents, conf_file):
    grammar_template = (Path(__file__).parent / 'resources' / 'grammar.lark').read_text()
    tagset = yaml.safe_load((Path(__file__).parent / 'resources' / 'postagset.yaml').read_text())
    root = 's'
    log_file = Path('log.txt')
    log_file.write_text('')
    config = Config(conf_file, len(tagged_sents))

    total_start = time.time()
    trees = []
    for n, sentence in enumerate(tagged_sents):
        if config.state[n] == 'done':
            continue
        # generate terminals and sentence to parse
        parse_start = time.time()
        terminals, sentence = parse_tagged(sentence, tagset)
        print(f'{n}. {sentence} (row {n*4+1})')
        # instantiate parser
        grammar = grammar_template.format(terminals)
        parser = Lark(grammar, start=root, regex=True)  # allow both "np" and "sentence" to be root nodes
        # generate tree
        errors = []
        parsed = None
        try:
            parsed = parser.parse(sentence)
            if parsed.data == 's' and len(parsed.children) == 1:
                parsed = parsed.children[0]
        except (UnexpectedCharacters, UnexpectedEOF) as e:
            errors.append(e)

        if parsed:
            print(parsed.pretty())
            trees.append(parsed)
            config.state[n] = 'done'
            conf_file.write_text(yaml.safe_dump(config.state))
        else:
            # ensure we write the parsed sents in the config
            conf_file.write_text(yaml.safe_dump(config.state))

            print('something went wrong...')
            for e in errors:
                start, end = e.pos_in_stream, e.pos_in_stream
                while start > 0 and sentence[start] != ' ':
                    start -= 1
                while end < len(sentence) and sentence[end] != ' ':
                    end += 1
                error_loc = f'{sentence[:start + 1]}|——>{sentence[start + 1:end]}<——|{sentence[end:]}'
                words = '\n'.join([t for t in terminals.split('\n') if '#' not in t])
                log = [error_loc, words]
                log = '\n'.join(log)
                log_file.write_text(f'{log_file.read_text()}\n{log}')
            trees.append(None)

        parse_end = time.time()
        print(f'parse: {str(datetime.timedelta(seconds=parse_end - parse_start))}\n')

    total_end = time.time()
    print(f'total: {str(datetime.timedelta(seconds=total_end - total_start))}')

    conf_file.write_text(yaml.safe_dump(config.state))
    return trees


def parse_tagged(sentence, tagset):
    terminals = {"DET": [], "QUES": [], "ADV": [], "CONJ": [], "VERB": [],
                 "NOUN": [], "PRON": [], "PUNCT": [], "ADJ": []}

    ambiguous_pos = ['བྱ་གྲོགས།', 'ཚིག་ཕྲད།']
    sent = []
    for word, pos in sentence:
        sent.append(word)

        if pos in ambiguous_pos:
            continue
        else:
            terminals[tagset[pos]].append(word)

    # can't leave empty terminals in the grammar
    for tag, words in terminals.items():
        if not words:
            words.append('#')

    formatted = ''
    for tag, words in terminals.items():
        if not words:
            words.append('#')  # add empty word for lark
        formatted += f'{tag}: '
        formatted += ' | '.join([f'"{w}"' for w in words]) + '\n'

    return formatted, ' '.join(sent)
