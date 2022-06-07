import os
import wave
import json

from vosk import Model, KaldiRecognizer, SetLogLevel
from pathlib import Path

import collect_wavs

RUSSIAN_SMALL = 'vosk_models/vosk-model-small-ru-0.22'
RUSSIAN_BIG = 'vosk-model-ru-0.22'

def model_tag(model):
    if model == RUSSIAN_SMALL:
        return 'smallrus'

    return 'unknown'

recognition = collect_wavs.wav_input_directory / 'recognition.json'

# Thanks,
# https://towardsdatascience.com/speech-recognition-with-timestamps-934ede4234b2

def recognize(waveform, recognition):
    # get the list of JSON dictionaries
    results = []

    # recognize speech using vosk model
    while True:
        data = waveform.readframes(4000)

        if len(data) == 0:
            break

        if recognition.AcceptWaveform(data):
            part_result = json.loads(recognition.Result())
            results.append(part_result)

    part_result = json.loads(recognition.FinalResult())
    results.append(part_result)

    return results

def recognize_path(path, model):
    with wave.open(path, "rb") as waveform:
        recognition = KaldiRecognizer(model, waveform.getframerate())
        recognition.SetWords(True)
        return recognize(waveform, recognition)

def collect_words(results, path):
    meaningful_result = None

    for it in results:
        if 'result' in it:
            meaningful_result = it['result']

    if not meaningful_result:
        return {}

    words_collector = {}

    for it in meaningful_result:
        start = it['start']
        word = it['word']
        end = it['end']

        if word not in words_collector:
            words_collector[word] = []

        entry = {
            'start': start,
            'end': end,
            'path': str(path),
        }

        words_collector[word].append(entry)

    return words_collector

def recognize_and_collect(source, destination, model):
    results = recognize_path(source, model)
    words_collector = collect_words(results, source)

    with open(destination, 'w', encoding='utf8') as file:
        json.dump(words_collector, file, ensure_ascii=False, indent=2)

def recognize_and_collect_with_cache(source, destination, model):
    if destination.exists():
        print(' [CACHE]', end='')
    else:
        recognize_and_collect(source, destination, model)

def recognize_folder(info, folder, recognize_and_collect, model):
    for entry in info[folder]:
        print(f'Input File > {folder} > {entry}', end='')
        destination = collect_wavs.wav_input_directory / folder / f'{entry}_{model_tag(model)}_words.json'
        recognize_and_collect(info[folder][entry], destination, model)
        print('')

def recognize_all_folders(info, recognize_and_collect, model_path):
    model = Model(model_path)

    for folder in info:
        recognize_folder(info, folder, recognize_and_collect, model)

def merge_entry(folder, entry, tag, words_collector):
    destination = collect_wavs.wav_input_directory / folder / f'{entry}_{tag}_words.json'

    with open(destination, 'r', encoding='utf8') as file:
        words = json.load(file)

    for word in words:
        if word not in words_collector:
            words_collector[word] = []

        for data in words[word]:
            words_collector[word].append(data)

def merge_all_tags_for_entry(folder, entry, words_collector):
    for filename in os.listdir(collect_wavs.wav_input_directory / folder):
        if not filename.startswith(entry) or not filename.endswith('_words.json'):
            continue

        tag = filename.split('_')[-2]
        merge_entry(folder, entry, tag, words_collector)

def merge_all_folders(info):
    collector = {}

    for folder in info:
        collector[folder] = {}

        for entry in info[folder]:
            merge_all_tags_for_entry(folder, entry, collector[folder])

    with open(recognition, 'w', encoding='utf8') as file:
        json.dump(collector, file, ensure_ascii=False, indent=2)

    return collector

def collect_recognition(cache=True, model_path=RUSSIAN_SMALL):
    info = collect_wavs.collect_info()

    if not cache:
        recognize_all_folders(info, recognize_and_collect, model_path)
        return merge_all_folders(info)

    if not recognition.exists():
        recognize_all_folders(info, recognize_and_collect_with_cache, model_path)
        return merge_all_folders(info)

    with open(recognition, 'r', encoding='utf8') as file:
        return json.load(file)

if __name__ == '__main__':
    collect_recognition(cache=False)
    print('Done')
