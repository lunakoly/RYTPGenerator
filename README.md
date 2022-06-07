# RYTP Generator

This code let's you generate a phrase by automatically combining parts of different audio files supplied. Splitting audio into words is done via [Vosk API](https://alphacephei.com/vosk/).

## How to use

This repo assumes there is a folder named `input` in the current working directory. This folder may contain arbitrary folders, and target files must reside inside those ones in forms of `wav` or `ogg` files (the latter will then be converted to `wav` automatically).

After the data has been prepared, run `python combinator.py`.

It is assumed the host machine has `ffmpeg` installed.
