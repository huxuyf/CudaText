#!/bin/bash
#Downloads the prebuilt Windows libraries used by the release build.
#The archive has no version in its name, so it is pinned by sha256: if
#upstream replaces the file, update the hash here in the same commit.
set -eu

CUDDIR=~/cudatext_build
mkdir $CUDDIR
cd $CUDDIR

url=https://sourceforge.net/projects/cudatext/files/libs_for_release_making/cudatext-windows-libs.zip/download
sum=9ce3aeceffa67351647889379457ab68ba0e82c31b867b7ce0e43f72e61d5b3a

curl -fL "$url" -o winlibs.zip
if command -v sha256sum >/dev/null 2>&1; then
  echo "$sum  winlibs.zip" | sha256sum -c -
else
  echo "$sum  winlibs.zip" | shasum -a 256 -c -
fi

unzip winlibs.zip -d .
