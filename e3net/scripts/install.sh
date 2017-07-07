#! /bin/bash
zfs='zfs-lxc-tool'

rm -f /usr/bin/$zfs
cp ./$zfs /usr/bin/$zfs
