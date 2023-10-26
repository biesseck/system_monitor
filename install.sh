#!/bin/sh

conda deactivate

CONDA_ENV=system_monitor
conda create --name $CONDA_ENV python=3.9
conda activate $CONDA_ENV

pip3 install -r ./requirements.txt
