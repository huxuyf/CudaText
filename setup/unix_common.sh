#!/bin/bash
. ./cuda_ver.sh
cd ../app

os=$1
widgets=$2
cpu=$3
exedir=bin/$os-$cpu-$widgets
outdir=$4

if [ ! -f "$exedir/cudatext" ]; then
    echo "Error: file 'cudatext' not found in dir '$exedir'"
    exit 1
fi

if [[ "$outdir" == "" ]]; then
    echo "Need script params"
    exit
fi

mkdir -p $outdir
tarfile2=$outdir/cudatext-$os-$widgets-$cpu-$cuda_ver.tar
tarfile=$outdir/tmp_cudatext-$os-$widgets-$cpu-$cuda_ver.tar

rm $outdir/cudatext-$os-$widgets-$cpu-*.xz
rm $tarfile

#include all plugin dirs from app/py (except test plugins and caches), so new plugins are packaged automatically
py_plugins=`cd py && for d in */; do case "$d" in __pycache__/|cuda_testing*/) continue;; esac; echo "py/${d%/}"; done`

tar --exclude=*.pyc -cf $tarfile readme data settings_default py/*.py $py_plugins

cd ../setup/debfiles
tar -rf $tarfile cudatext-512.png

cd ../../app
cd $exedir
tar -rf $tarfile cudatext

if [[ "$os" == "linux" && ( "$widgets" == "qt5" || "$widgets" == "qt6" ) ]]; then
	cd $outdir/lib_${os}_${widgets}_${cpu}
	tar -rf $tarfile *
fi

cd $outdir
rm -rf cudatext/
mkdir cudatext
cd cudatext
tar -xf $tarfile
cd ..
tar -rf $tarfile2 cudatext/
rm $tarfile
rm -rf cudatext/

xz -z $tarfile2
