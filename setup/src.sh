#!/bin/bash
#Builds the CudaText source archive.
#Dependency archives are pinned to exact commits and verified by sha256, so the
#archive content is reproducible. If a dependency must be updated, change the
#commit and its sha256 together in the same commit.
set -eu

. ./cuda_ver.sh

fetch() {
  name=$1
  repo=$2
  commit=$3
  sum=$4
  url=https://github.com/$repo/archive/$commit.zip
  curl -fsSL "$url" -o "$name.zip"
  if command -v sha256sum >/dev/null 2>&1; then
    echo "$sum  $name.zip" | sha256sum -c -
  else
    echo "$sum  $name.zip" | shasum -a 256 -c -
  fi
}

mkdir ~/cudatext_build/src
cd ~/cudatext_build/src

fetch ATBinHex Alexey-T/ATBinHex-Lazarus ac03d543d888beae8b12d38165e0cf63efe14a3e efd16ccb303e959a155215c90b48460fbc3aa15a51c5698011d6837cb5fff33e
fetch ATFlatControls Alexey-T/ATFlatControls ede5b4928ce9dbc33e490655687e7f1e2fa8e750 f5610d3a13befdee4e95be6766a88b6686b1e55d2ca0cd376ca9bf9ebb9b0d79
fetch EncConv Alexey-T/EncConv 2c91927514ca25ac705cd7b2f4c638507c671317 cf898ce528ef596b9d6ed420ebb1988caec9e2776ef8c5f55cfc2fd64b8c0ffe
fetch ATSynEdit Alexey-T/ATSynEdit 9f5e1679c136aad4cb0a9bfa1d094e4dde6d1558 6167c279618b4a2e6afae97dc0c5adc8d7fcacc3ce09e0a03900ca8416f86054
fetch ATSynEdit_Cmp Alexey-T/ATSynEdit_Cmp 3680a9aa6d3147c4955b10d36c7c02919a37bbdf 9078827eaf26c584c8483d03198f65cb1c8996a3ec5b87d8c12164adb21c95c2
fetch ATSynEdit_Ex Alexey-T/ATSynEdit_Ex c4dc1f67b91b42221b75e131fbc95abfe584ca3b 851118e29ffde8d43325ce6d6c9663c9135130f6edbeb4cb9af8b736b5f35d60
fetch CudaText Alexey-T/CudaText b36f4f07a8753df6a002b0d65d59109c4536751e 40b41379d4dcdb7e1af83ef87aa0c13e334976dffe5b2dc4d77be7188099f8d0
fetch EControl Alexey-T/Econtrol 1d42098d1648272f55a530e505f8820054f967bc bd6cf8c89fdf7b37ce4a7f41d4c48178cc62d65c9279d4f3935c7109e723a4d5
fetch Python Alexey-T/Python-for-Lazarus 49eff18fa790240aea69af4948511ca9b40eb88b eb54d13ab7fa0f654d99061ff6d63af26c98a33ec498c8c76eaf2e52c3a6090c
fetch Emmet Alexey-T/Emmet-Pascal e737deae6cd0f932154304af5b7906d5ad61398c 1c4dea75d89fadeffd464ff892ff10efeedc61fa7bc887af81b919b0750761e5

cd ..
zip -r cudatext-src-$cuda_ver.zip src/
