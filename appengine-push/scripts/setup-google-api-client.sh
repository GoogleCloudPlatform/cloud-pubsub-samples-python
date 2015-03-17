#!/bin/sh

set -e

if [ -z "$1" ]; then
    echo "Usage: $0 targetdir"
    exit
fi

TMP=${1}/pip-setup-$$.$RANDOM
LIBDIR=${1}/lib

if [ "$2" == "--clean" ]; then
    echo "Removing the ${LIBDIR} first"
fi

if [ -e ${TMP} ]; then
    echo "Sorry, couldn't choose a temp directory."
    exit
fi

mkdir -p ${TMP}

virtualenv -p python2.7 --no-site-packages ${TMP}
source ${TMP}/bin/activate
pip install --upgrade google-api-python-client

function copylib() {
    $(pip show $1 | egrep "^Location|^Requires" | \
      awk -F ": " '{print "export "$1"="$2}' | sed -e "s/, /,/g")
    if [ -e $Location/$1 ]; then
        cp -R $Location/$1 $2
    elif [ -e $Location/$1.py ]; then
        cp $Location/$1.py $2
    else
        cp -R $Location/googleapiclient $2
    fi;
    if [ $Requires ]; then
        echo $Requires | tr , "\n" | while read r; do
            copylib $r $2;
        done;
    fi;
}

mkdir -p ${LIBDIR}
copylib google-api-python-client ${LIBDIR}
copylib apiclient ${LIBDIR}
rm -rf ${TMP}
echo "The project is setup successfully."
