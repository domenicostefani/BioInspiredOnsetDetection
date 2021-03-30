#!/usr/bin/env bash

if [[ $# -ne 1 ]]
then
    echo "Provide one argument (Buffer size)"
    exit
fi

BUFSIZE=$1
echo BUFSIZE: $BUFSIZE

LOGFILE="evolutionaryOptimizerResults/progress.log"
rm -f $LOGFILE
touch $LOGFILE

echo "( $BUFSIZE ) start at $(date +"%T")" >> $LOGFILE
python3 evolutionaryoptimizer.py 42 "mkl(noaw)" $BUFSIZE
echo "( $BUFSIZE ) mkl(noaw) finished $(date +"%T") " >> $LOGFILE
python3 evolutionaryoptimizer.py 42 hfc $BUFSIZE
echo "( $BUFSIZE ) hfc finished $(date +"%T") " >> $LOGFILE
python3 evolutionaryoptimizer.py 42 energy $BUFSIZE
echo "( $BUFSIZE ) energy finished $(date +"%T") " >> $LOGFILE
python3 evolutionaryoptimizer.py 42 complex $BUFSIZE
echo "( $BUFSIZE ) complex finished $(date +"%T") " >> $LOGFILE
python3 evolutionaryoptimizer.py 42 phase $BUFSIZE
echo "( $BUFSIZE ) phase finished $(date +"%T") " >> $LOGFILE
python3 evolutionaryoptimizer.py 42 specdiff $BUFSIZE
echo "( $BUFSIZE ) specdiff finished $(date +"%T") " >> $LOGFILE
python3 evolutionaryoptimizer.py 42 kl $BUFSIZE
echo "( $BUFSIZE ) kl finished $(date +"%T") " >> $LOGFILE
python3 evolutionaryoptimizer.py 42 mkl $BUFSIZE
echo "( $BUFSIZE ) mkl finished $(date +"%T") " >> $LOGFILE
python3 evolutionaryoptimizer.py 42 specflux $BUFSIZE
echo "( $BUFSIZE ) specflux finished $(date +"%T") " >> $LOGFILE
