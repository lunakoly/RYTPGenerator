import re
import json
import random
import pyphen

from subprocess import Popen

import recognize_words
import craft_syllables

def take_all_folders(collection, folder):
    return [collection[it] for it in collection]

def take_specific_folder(collection, folder):
    return [collection[folder]]

def pick_one_from(collection, word, folder, take_folders):
    variants = []

    for it in take_folders(collection, folder):
        if word in it:
            variants += it[word]

    if len(variants) == 0:
        return None

    return random.choice(variants)

def slice_word(part, word, word_data):
    variants = []

    for it in word_data:
        length = it['end'] - it['start']
        size = len(part) / len(word) * length
        offset = word.index(part) / len(word) * length

        variant = {
            'start': offset,
            'end': offset + size,
            'path': it['path'],
        }

        variants.append(variant)

    return variants

def pick_as_word_part(recognition, part, folder, take_folders):
    variants = []

    for it in take_folders(recognition, folder):
        for word in it:
            if part not in word:
                continue

            variants += slice_word(part, word, it[word])

    if len(variants) == 0:
        return None

    return random.choice(variants)

def pick_from_syllables(syllables, recognition, word, folder, divider, take_folders):
    result = []

    for part in divider.inserted(word).split('-'):
        picked = pick_one_from(syllables, part, folder, take_folders)

        if picked is None:
            picked = pick_as_word_part(recognition, part, folder, take_folders)

        if picked is None:
            print(f'Sorry, couldn\'t find anything for `{part}` (in the word `{word}`)')
            return None

        result.append(picked)

    return result

def generate_phrase(
    phrase, output, folder,
    language=craft_syllables.RUSSIAN,
    model_path=recognize_words.RUSSIAN_SMALL,
):
    if folder is None:
        take_folders = take_all_folders
    else:
        take_folders = take_specific_folder

    text = re.sub('''\s+''', ' ', phrase)
    text = re.sub('''[^а-яА-ЯёЁa-zA-Z ]''', '', phrase)
    text = text.lower()
    words = text.split(' ')

    recognition = recognize_words.collect_recognition(model_path=model_path)
    syllables = craft_syllables.collect_syllables(language=language)
    divider = pyphen.Pyphen(lang=language)
    parts = []

    for word in words:
        picked = pick_one_from(recognition, word, folder, take_folders)

        if picked is not None:
            parts.append(picked)
            continue

        picked = pick_from_syllables(syllables, recognition, word, folder, divider, take_folders)

        if picked is not None:
            parts += picked
            continue

        return None

    args = [
        'ffmpeg', '-hide_banner', '-y',
        '-f', 'lavfi', '-i', 'anullsrc',
        ]

    for it in parts:
        args += ['-i', it['path']]

    args.append('-filter_complex')
    all_variables = ';'

    trims = [
        '[0]atrim=start=0:duration=1[n0]',
    ]

    for it in range(len(parts)):
        duration = (parts[it]['end'] - parts[it]['start'])
        trims.append(f'[{it+1}:a:0]atrim=start={parts[it]["start"]}:duration={duration}[n{it+1}]')
        all_variables += f'[n{it+1}]'

    args.append(';'.join(trims) + all_variables + f'[n0]concat=n={len(parts)+1}:v=0:a=1')
    args.append(output)

    process = Popen(args)
    process.wait()

if __name__ == '__main__':
    generate_phrase(
        'Some phrase',
        'output/phrase.wav',
        folder=None,
    )

    print('Done')
