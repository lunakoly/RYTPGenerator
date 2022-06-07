import json
import pyphen

from pathlib import Path

import collect_wavs
import recognize_words

syllables = collect_wavs.wav_input_directory / 'syllables.json'

ENGLISH = 'en'
RUSSIAN = 'ru'

def divide_word(word, word_data, divider):
    syllables_collector = {}

    length = word_data['end'] - word_data['start']
    offset = word_data['start']

    for part in divider.inserted(word).split('-'):
        size = len(part) / len(word) * length

        if part not in syllables_collector:
            syllables_collector[part] = []

        variant = {
            'start': offset,
            'end': offset + size,
            'path': word_data['path'],
        }

        syllables_collector[part].append(variant)
        offset += size

    return syllables_collector

def divide_recognition(recognition, divider):
    collector = {}

    for folder in recognition:
        collector[folder] = {}

        for word in recognition[folder]:
            for word_data in recognition[folder][word]:
                syllables_collector = divide_word(word, word_data, divider)
                collector[folder].update(syllables_collector)

    with open(syllables, 'w', encoding='utf8') as file:
        json.dump(collector, file, ensure_ascii=False, indent=2)

    return collector

def collect_syllables(cache=True, language=RUSSIAN, model_path=recognize_words.RUSSIAN_SMALL):
    recognition = recognize_words.collect_recognition(model_path=model_path)
    divider = pyphen.Pyphen(lang=language)

    if not cache:
        return divide_recognition(recognition, divider)

    if not syllables.exists():
        return divide_recognition(recognition, divider)

    with open(syllables, 'r', encoding='utf8') as file:
        return json.load(file)

if __name__ == '__main__':
    collect_syllables(cache=False)
    print('Done')
