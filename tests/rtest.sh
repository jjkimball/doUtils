#!/bin/bash

SECRETS=$HOME/.secrets/digital-ocean.env

SCRIPTDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJDIR="$(cd "$SCRIPTDIR/../.." && pwd)"

SRCDIR=$PROJDIR/repo
TESTSDIR=$PROJDIR/repo/tests

export PYTHONPATH=$SRCDIR:$PYTHONPATH
source $SECRETS

SRCS=$(fgrep -l doctest.testmod $(find $SRCDIR -iname '*.py'))
EXER=$(find $TESTSDIR -iname 'exercise*.doctest')
PYTEST=$(find $TESTSDIR -iname 'test_*.py')
TESTEES="$SRCS $EXER $PYTEST"

case $1 in
    # No parms: default is process all test files
    '' ) ;;
    # -list: echo the test files
    *-list* ) for T in $TESTEES ; do echo $T ; done
              exit
              ;;
    # filenames: grab full paths to those test files:
    * ) sought=$(echo $* |sed -e 's/ /|/g')
        TESTEES=$(echo $TESTEES |sed -e 's/ /\n/g' |egrep "$sought")
        ;;
esac

for F in $TESTEES ; do
    echo ; echo ::::::::::::::::::::::::::::::::::::::::::::::::::
    echo ::: $F
    cd $(dirname $F)
    BF=$(basename $F)
    case "$F" in
        */test_*.py ) pipenv run pytest -s $BF
                    ;;
        *.py ) pipenv run ./$BF --unittest  || exit
               ;;
        *.doctest ) 
            pipenv run python -c "import doctest ; doctest.testfile('$BF', verbose=True)" ;;
    esac
done


echo //RTEST DONE
