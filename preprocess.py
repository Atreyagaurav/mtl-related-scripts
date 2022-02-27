#!/usr/bin/env python
import re
import sys
import json
import os
import time

from enum import Flag
from collections import namedtuple
import itertools


class Names(Flag):
    NONE = 0
    FULL_NAME = 1
    FIRST_NAME = 2
    FULL_AND_FIRST = 3
    LAST_NAME = 4
    FULL_AND_LAST = 5
    FIRST_AND_LAST = 6
    ALL_NAMES = 7


Character = namedtuple('Character', 'jp_name en_name')


VERBOSE = True
SINGLE_KANJI_FILTER=True
text = ''
rep = dict()
total_replacements = 0
JP_NAME_SEPS = ["・", ""]


def out_filename(in_file):
    p, e = os.path.splitext(in_file)
    return f'{p}-rep{e}'


def replace_single_word(word, replacement):
    global text, total_replacements
    n = text.count(word)
    if n == 0:
        return 0
    # print(word, n)
    text = text.replace(word, replacement)
    total_replacements += n
    return n


def loop_names(character,
               replace=Names.FULL_NAME,
               honorific=Names.ALL_NAMES):
    jp_names = character.jp_name.split(" ")
    en_names = character.en_name.split(" ")
    try:
        assert len(jp_names)==len(en_names)
    except AssertionError:
        print("Names do not match")
        print(character)
        raise SystemExit(0)
    if Names.FULL_NAME in replace:
        indices = range(len(jp_names))
        combinations = (
            itertools.chain(
                *[itertools.combinations(indices, i)
                  for i in range(2, len(indices)+1)]))
        for comb in combinations:
            for sep in JP_NAME_SEPS:
                yield (
                    " ".join(map(lambda i: en_names[i], comb)),
                    sep.join(map(lambda i: jp_names[i], comb)),
                    Names.FULL_NAME in honorific
                )

    if Names.FIRST_NAME in replace:
        yield (en_names[0],
               f'{jp_names[0]}',
               Names.FIRST_NAME in honorific)
    if Names.LAST_NAME in replace:
        yield (en_names[-1],
               f'{jp_names[-1]}',
               Names.LAST_NAME in honorific)


def replace_name(character,
                 replace=Names.FULL_NAME,
                 no_honorific=Names.ALL_NAMES,
                 replaced_names=list()):
    for nen, njp, no_honor in loop_names(character, replace, no_honorific):
        if njp in replaced_names:
            continue
        data = dict()
        for hon, hon_en in rep['honorifics'].items():
            data[hon_en] = replace_single_word(
                f'{njp}{hon}',
                f'{nen}-{hon_en}'
            )
        if no_honor:
            if len(njp) > 1 or not SINGLE_KANJI_FILTER:
                data['NA'] = replace_single_word(njp, nen)

        total = sum(data.values())
        replaced_names[njp] = total
        if not VERBOSE or total == 0:
            continue

        print(f'    {nen} :{total} (', end='')
        print(", ".join(map(lambda x: f'{x}-{data[x]}',
                            filter(lambda x: data[x]>0, data))), end=')\n')


def main(input_file, rep_file):
    global text, rep, total_replacements
    with open(input_file,'r', encoding='utf-8') as r:
        text = r.read()

    with open(rep_file,'r', encoding='utf-8') as r:
        rep = json.load(r)

    replace()    
    out_file = out_filename(input_file)
    with open(out_file, 'w', encoding='utf-8') as w:
        w.write(text)

    print(f'Output written to: {out_file}')


def initialize(input_text, replacements):
    global text, rep, total_replacements
    text = input_text
    rep = replacements
    total_replacements = 0
    return


def replace():
    global text, rep
    rules = [
        # title, json_key, is_name, replace_name, no_honorifics
        ('Special', 'specials', False),
        ('Basic', 'basic', False),
        ('Imp Names', 'names', True, Names.ALL_NAMES, Names.ALL_NAMES),
        ('Semi Imp Names', 'last-names', True,
         Names.ALL_NAMES, Names.FULL_AND_LAST),
        ('Remaining Names', 'full-names', True,
         Names.ALL_NAMES, Names.FULL_NAME),
        ('Single Names', 'single-names', True, Names.LAST_NAME, Names.LAST_NAME),
        ('Name like', 'name-like', True, Names.LAST_NAME, Names.NONE),
        ('Cleaning Up', 'cleaning-up', False)
    ]

    replaced_names = dict()
    time_start = time.time()
    for rule in rules:
        prev_count = total_replacements
        if VERBOSE:
            print(f'* {rule[0]} Replacements:')
        if rule[2]:             # if it is a name
            try:
                for k, v in rep[rule[1]].items():
                    if not isinstance(v, list):
                        v = [v]
                    char = Character(" ".join(v), k)
                    replace_name(char, rule[3], rule[4], replaced_names)
            except KeyError:
                continue
        else:
            try:
                for k, v in rep[rule[1]].items():
                    n = replace_single_word(k, v)
                    if n > 0:
                        print(f'    {k} → {v}:{n}')
            except KeyError:
                continue
        print(f'  SubTotal: {total_replacements-prev_count}')

    time_end = time.time()
    print(f'Total Replacements: {total_replacements}')
    print(f'Time Taken: {time_end-time_start} seconds')
    return text


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(f'Usage: {sys.argv[0]} input_file replacement_json')
        exit(0)
    main(sys.argv[1], sys.argv[2])
