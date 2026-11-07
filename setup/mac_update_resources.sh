#!/bin/sh
from=~/cuda/cuda/app
app=~/cuda/cuda/app/cudatext.app

rm -rf $app/Contents/Resources/data
rm -rf $app/Contents/Resources/readme
rm -rf $app/Contents/Resources/sett*

cp -rf $from/data $app/Contents/Resources
cp -rf $from/settings_default $app/Contents/Resources

mkdir -p $app/Contents/Resources/py

cp $from/py/*.py $app/Contents/Resources/py

#copy all plugin dirs (except test plugins and caches), so new plugins are added automatically
for pydir in $from/py/*/; do
  pyname=${pydir%/}
  pyname=${pyname##*/}
  case "$pyname" in
    __pycache__|cuda_testing*) continue ;;
  esac
  mkdir -p $app/Contents/Resources/py/$pyname
  cp -rf "$pydir"* $app/Contents/Resources/py/$pyname
  rm -rf $app/Contents/Resources/py/$pyname/__pycache__
done

echo Done
