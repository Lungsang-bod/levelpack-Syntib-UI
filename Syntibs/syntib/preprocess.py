from openpyxl import load_workbook


def preprocess(in_file, mode='tagged_xlsx'):
    """

    :param mode:
    :param in_file:
    :return:
    """
    if mode == 'tagged_xlsx':
        sentences = parse_tagged_xlsx(in_file)
    else:
        raise ValueError('only tagged_xlsx is supported.')

    return sentences


def parse_tagged_xlsx(in_file):
    """
    parse pos and level tagged .xlsx files generated using level_packs
    :param in_file: .xlsx file
    :return: list of sentences where each sentence is a list of word-pos tuples
    """
    lines_per_sentence = 4

    wb = load_workbook(in_file)
    dump = list(wb.active.values)
    sentences = []
    for i in range(0, len(dump), lines_per_sentence):
        words = list(dump[i])
        pos = list(dump[i+1])
        sent = []
        i = 0
        while i < len(words):
            if words[i] and pos[i]:
                sent.append((words[i], pos[i]))
            else:
                break
            i += 1
        sentences.append(sent)

    return sentences
