#!/bin/bash

. ./cuda_ver.sh
cpu=$1
widgets=$2
debsuffix=${widgets}_${cpu}
binsuffix=$cpu-$widgets

outdir=~/cudatext_build
mkdir -p $outdir
debname=cudatext_$cuda_ver-1_$debsuffix

dd=~/tmp/$debname
sudo rm -rf $dd

mkdir -p $dd
mkdir $dd/DEBIAN
cp debfiles/$debsuffix/control $dd/DEBIAN

mkdir $dd/usr
mkdir $dd/usr/bin
mkdir $dd/usr/share
mkdir $dd/usr/share/cudatext
mkdir -p $dd/usr/share/cudatext/py
mkdir $dd/usr/share/pixmaps
mkdir $dd/usr/share/applications
mkdir $dd/usr/share/doc
mkdir $dd/usr/share/doc/cudatext

cp ../app/bin/linux-$binsuffix/cudatext $dd/usr/bin
cp debfiles/cudatext.desktop $dd/usr/share/applications
cp debfiles/cudatext-512.png $dd/usr/share/pixmaps
cp -r ../app/data $dd/usr/share/cudatext
cp -r ../app/settings_default $dd/usr/share/cudatext
cp debfiles/copyright $dd/usr/share/doc/cudatext

###py
cp -r ../app/py/*.py $dd/usr/share/cudatext/py
for pydir in ../app/py/*/; do
  pyname=${pydir%/}
  pyname=${pyname##*/}
  case "$pyname" in
    __pycache__|cuda_testing*) continue ;;
  esac
  cp -r "$pydir" $dd/usr/share/cudatext/py
  rm -rf "$dd/usr/share/cudatext/py/$pyname/__pycache__"
done

cp debfiles/changelog $dd/usr/share/doc/cudatext
gzip --best -n $dd/usr/share/doc/cudatext/changelog
mv $dd/usr/share/doc/cudatext/changelog.gz $dd/usr/share/doc/cudatext/changelog.Debian.gz

sudo chmod -R 755 $dd
sudo chmod 644 $dd/usr/share/applications/cudatext.desktop
sudo chmod 644 $dd/usr/share/doc/cudatext/*
sudo chmod 644 $dd/usr/share/pixmaps/cudatext*.png
sudo chown -R root:root $dd
sudo rm -rf $dd/usr/share/cudatext/py/cuda_lexer_detecter/__pycache__

cd $dd/usr/share/cudatext
sudo find . -type f -exec chmod 644 {} +
sudo find . -type d -exec chmod 755 {} +

dpkg-deb --build $dd $outdir/$debname.deb