#!/bin/bash
source ~/anaconda3/etc/profile.d/conda.sh
gnome-terminal -- conda init bash && conda activate vosk && python test_mic_vad.py -l && python test_mic_vad.py -d 10
