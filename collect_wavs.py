from asyncio import subprocess
import os
import json
import shutil

from pathlib import Path
from subprocess import Popen

input_directory = Path('input')
wav_input_directory = Path('wav_input')
wav_info = wav_input_directory / 'info.json'

def transfer_wav(source, destination, logs_path):
    shutil.copyfile(source, destination)

def transfer_ogg(source, destination, logs_path):
    with open(logs_path, 'ab') as file:
        args = ['ffmpeg', '-hide_banner', '-i', source, '-ac', '1', destination]
        process = Popen(args, stdout=file, stderr=file)
        process.wait()

def transfer_with_cache(delegate):
    def transfer(source, destination, logs_path):
        if destination.exists():
            print(' [CACHE]', end='')
        else:
            delegate(source, destination, logs_path)

    return transfer

def process_folder(folder, transfer_wav, transfer_ogg):
    os.makedirs(wav_input_directory / folder)
    recording_collector = {}

    for filename in os.listdir(input_directory / folder):
        base_filename = os.path.splitext(filename)[0]
        source = input_directory / folder / filename
        logs = wav_input_directory / folder / f'{base_filename}_logs.txt'

        print(f'Input File > {folder} > {filename}', end='')

        if filename.endswith('.wav'):
            print(' > Copying', end='')
            destination = wav_input_directory / folder / filename
            transfer_wav(source, destination, logs)

        elif filename.endswith('.ogg') and base_filename not in recording_collector:
            print(' > Converting', end='')
            destination = wav_input_directory / folder / (base_filename + '.wav')
            transfer_ogg(source, destination, logs)

        else:
            print(' > Skipped', end='')
            continue

        recording_collector[base_filename] = str(destination)
        print('')

    return recording_collector

def process_all_folders(transfer_wav, transfer_ogg):
    folder_collector = {}

    for filename in os.listdir(input_directory):
        if not os.path.isdir(input_directory / filename):
            continue

        folder_collector[filename] = process_folder(filename, transfer_wav, transfer_ogg)

    with open(wav_info, 'w', encoding='utf8') as file:
        json.dump(folder_collector, file, indent=2)

    return folder_collector

def collect_info(cache=True):
    if not cache:
        shutil.rmtree(wav_input_directory)
        return process_all_folders(transfer_wav, transfer_ogg)

    if not wav_info.exists():
        return process_all_folders(
            transfer_with_cache(transfer_wav),
            transfer_with_cache(transfer_ogg)
        )

    with open(wav_info, 'r', encoding='utf8') as file:
        return json.load(file)

if __name__ == '__main__':
    collect_info(cache=False)
    print('Done')
