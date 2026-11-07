#!/bin/bash
. ./cuda_ver.sh
cd ../app

cpu=$1
outdir=$2
exedir=bin/windows-$cpu
pydir=$outdir/lib_win_$cpu

if [[ "$pydir" == "" ]]; then
  echo "Need script params"
  exit
fi

if [ ! -f "$exedir/cudatext.exe" ]; then
    echo "Error: file 'cudatext.exe' not found in dir '$exedir'"
    exit 1
fi

zipname2=cudatext-windows-$cpu-$cuda_ver.zip
zipname=tmp_$zipname2
mkdir -p $outdir
mkdir $outdir/src
mkdir $pydir

rm $outdir/$zipname
rm $outdir/$zipname2

#include all plugin dirs from app/py (except test plugins and caches), so new plugins are packaged automatically
py_plugins=`cd py && for d in */; do case "$d" in __pycache__/|cuda_testing*/) continue;; esac; echo "py/${d%/}"; done`

zip -r -x*.pyc $outdir/$zipname data readme settings_default *.manifest py/*.py $py_plugins

# Take exe
cd $exedir
zip $outdir/$zipname cudatext.exe

cd $pydir
zip -r $outdir/$zipname *

cd $outdir
rm -rf cudatext/
unzip -d cudatext $zipname
zip -r $outdir/$zipname2 cudatext
rm $outdir/$zipname
rm -rf cudatext/
