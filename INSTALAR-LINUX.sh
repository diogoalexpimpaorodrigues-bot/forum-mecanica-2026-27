#!/bin/sh
set -eu
forum_project_dir=$(CDPATH= cd -P "$(dirname "$0")" && pwd)
case $(uname -m) in
  aarch64|arm64) forum_arch=arm64 ;;
  x86_64|amd64) forum_arch=amd64 ;;
  *) echo "Arquitetura não suportada. Consulta INSTALAR.md."; exit 1 ;;
esac
forum_installer="$forum_project_dir/installer/bin/forum-linux-$forum_arch"
chmod u+x "$forum_installer"
exec "$forum_installer" --project "$forum_project_dir" "$@"
