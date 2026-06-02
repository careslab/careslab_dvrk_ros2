#!/bin/bash
source ~/anaconda3/etc/profile.d/conda.sh
source /etc/environment
gnome-terminal -- conda init bash && conda activate vosk && python vosk_gptchat.py -l && python vosk_gptchat.py -d 10
