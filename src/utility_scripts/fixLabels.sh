#!/bin/bash

TMPFILE_DIR=$(dirname $1)
TMPFILE_NAME="tmp-$(basename $1)"
TMPFILE_FULLPATH="$TMPFILE_DIR/$TMPFILE_NAME"
echo $TMPFILE_FULLPATH

COUNTER=1
while read p; do   echo -e "$p\t$p\t$COUNTER";((COUNTER++)); done <$1 > $TMPFILE_FULLPATH

mv $TMPFILE_FULLPATH $1
