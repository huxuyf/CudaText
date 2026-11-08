#!/usr/bin/bash
#Clones the CudaText build dependencies at exact commits, so that a new
#checkout matches the versions used for the release. To update a dependency,
#change its commit here in the same commit which needs the new version.
set -euo pipefail

clone_pinned() {
  url=$1
  dir=$2
  commit=$3
  git clone --quiet "$url" "$dir"
  git -C "$dir" checkout --quiet --detach "$commit"
}

clone_pinned https://github.com/bgrabitmap/bgrabitmap bgrabitmap 743788ac473db0cf005db5f32feaa1c09206c9ca
clone_pinned https://github.com/Alexey-T/python-for-lazarus python-for-lazarus 49eff18fa790240aea69af4948511ca9b40eb88b
clone_pinned https://github.com/Alexey-T/atflatcontrols atflatcontrols ede5b4928ce9dbc33e490655687e7f1e2fa8e750
clone_pinned https://github.com/Alexey-T/encconv encconv 2c91927514ca25ac705cd7b2f4c638507c671317
clone_pinned https://github.com/Alexey-T/atsynedit atsynedit 9f5e1679c136aad4cb0a9bfa1d094e4dde6d1558
clone_pinned https://github.com/Alexey-T/econtrol econtrol 1d42098d1648272f55a530e505f8820054f967bc
clone_pinned https://github.com/Alexey-T/atsynedit_ex atsynedit_ex c4dc1f67b91b42221b75e131fbc95abfe584ca3b
clone_pinned https://github.com/Alexey-T/atsynedit_cmp atsynedit_cmp 3680a9aa6d3147c4955b10d36c7c02919a37bbdf
clone_pinned https://github.com/Alexey-T/atbinhex-lazarus atbinhex-lazarus ac03d543d888beae8b12d38165e0cf63efe14a3e
clone_pinned https://github.com/Alexey-T/emmet-pascal emmet-pascal e737deae6cd0f932154304af5b7906d5ad61398c
clone_pinned https://github.com/Alexey-T/cudatext cudatext b36f4f07a8753df6a002b0d65d59109c4536751e
