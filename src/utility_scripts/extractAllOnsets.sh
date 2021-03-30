#!/bin/bash

# This script simply calls AUBIOONSET with a set of predefined parameters
# ON ALL THE WAW FILES IN THE CURRENT FOLDER
#
# Author: Domenico Stefani
#          - domenico.stefani[at]unitn.it
#          - domenico.stefani96[at]gmail.com
# Date:   05/11/2020

usage() { echo "Usage: $0 [-C <AUBIOONSET_COMMAND>] [-B <BUFFER_SIZE>] [-H <HOP_SIZE>] [-s <SILENCE_THRESHOLD>] [-t <ONSET_THRESHOLD> -O <ONSET_METHOD>] [-M <MINIMUM_INTER_ONSET_INTERVAL_SECONDS>] [-d <FILE_DIRECTORY>] [-e <OUTPUT_DIRECTORY>]" 1>&2; exit 1; }

while getopts “:C:B:H:s:t:O:M:d:e:” opt; do
  case $opt in
    C) AUBIOONSET_COMMAND=$OPTARG ;;
    B) BUFFER_SIZE=$OPTARG ;;
    H) HOP_SIZE=$OPTARG ;;
    s) SILENCE_THRESHOLD=$OPTARG ;;
    t) ONSET_THRESHOLD=$OPTARG ;;
    O) ONSET_METHOD=$OPTARG ;;
    M) MINIMUM_INTER_ONSET_INTERVAL_SECONDS=$OPTARG ;;
    d) FILEDIR=$OPTARG ;;
    e) ONSET_OUT_DIR=$OPTARG ;;
    *) usage ;;
  esac
done

echo "AUBIOONSET_COMMAND=$AUBIOONSET_COMMAND"

echo "INPUT DIRECTORY=$FILEDIR"
echo "OUTPUT DIRECTORY=$ONSET_OUT_DIR"

echo "BUFFER_SIZE=$BUFFER_SIZE"
echo "HOP_SIZE=$HOP_SIZE"
echo "SILENCE_THRESHOLD=$SILENCE_THRESHOLD"
echo "ONSET_THRESHOLD=$ONSET_THRESHOLD"
echo "ONSET_METHOD=$ONSET_METHOD"
echo "MINIMUM_INTER_ONSET_INTERVAL_SECONDS=$MINIMUM_INTER_ONSET_INTERVAL_SECONDS"

if [[ -z "$ONSET_OUT_DIR" ]]; then
    echo "using default value for ONSET_OUT_DIR"
    ONSET_OUT_DIR="onsets_extracted/"
fi

LOGFILE=$ONSET_OUT_DIR"logs/extractAllOnsets.log"
mkdir -p $ONSET_OUT_DIR/logs
rm -f $LOGFILE

# Available methods:<default|energy|hfc|complex|phase|specdiff|kl|mkl|specflux>
if [[ -z "$ONSET_METHOD" ]]; then
    echo "using default value for ONSET_METHOD" >> $LOGFILE
    ONSET_METHOD=default
fi

if [[ -z "$BUFFER_SIZE" ]]; then
    echo "using default value for BUFFER_SIZE" >> $LOGFILE
    BUFFER_SIZE=256
fi
if [[ -z "$HOP_SIZE" ]]; then
    echo "using default value for HOP_SIZE" >> $LOGFILE
    HOP_SIZE=128
fi
if [[ -z "$SILENCE_THRESHOLD" ]]; then
    echo "using default value for SILENCE_THRESHOLD" >> $LOGFILE
    SILENCE_THRESHOLD=-40.0
fi
if [[ -z "$ONSET_THRESHOLD" ]]; then
    echo "using default value for ONSET_THRESHOLD" >> $LOGFILE
    ONSET_THRESHOLD=0.75
fi
if [[ -z "$FILEDIR" ]]; then
    echo "using default value for FILEDIR" >> $LOGFILE
    FILEDIR="" # 20ms
fi
if [[ -z "$AUBIOONSET_COMMAND" ]]; then
    echo "using default value for AUBIOONSET_COMMAND" >> $LOGFILE
    AUBIOONSET_COMMAND="aubioonset"
fi

ONSETSUBDIR="onsets_extracted/"
ONSET_OUT_DIR="$ONSET_OUT_DIR$ONSETSUBDIR"
mkdir -p $ONSET_OUT_DIR
echo $ONSET_OUT_DIR

# Call extractOnset for all waw files in the folder
FILEEXT="*.wav"
FILEPATTERN="$FILEDIR$FILEEXT"
for audiofile in $FILEPATTERN; do
    if [ "$audiofile" = "$FILEEXT" ]
    then
        echo "No wav file in the current folder"
        exit
    fi

    echo "processing is $audiofile"
	source ./utility_scripts/extractOnset.sh $audiofile >> $LOGFILE
done

DELAY=$(python3 -c "print(int($HOP_SIZE*4.3))")

if [[ $ONSET_METHOD = "complex" ]] ; then
	DELAY=$(python -c "print(int($HOP_SIZE*4.6))")
fi

echo "To get the real detection time, add the delay of $DELAY samples"
