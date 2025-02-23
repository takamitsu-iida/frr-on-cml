#!/bin/bash

# 特権ユーザのシェルを取る
# パスワードを聞かれる
sudo -s -E

COPY_SRC="ubuntu-24-04-20241004"
COPY_DST="ubuntu-24-04-20241004-frr"

NODE_DEF_ID=${COPY_DST}
NODE_DEF_LABEL="Ubuntu 24.04 - 04 Oct 2024 FRR installed"
NODE_DEF_DESCRIPTION="Ubuntu 24.04 - 04 Oct 2024 FRR installed"

cd /var/lib/libvirt/images/virl-base-images

cp -a ${COPY_SRC} ${COPY_DST}

chown virl2:virl2 ${COPY_DST}

cd ${COPY_DST}

rm -f ${COPY_SRC}.yaml

cat << EOF > ${COPY_DST}.yaml
#
# Ubuntu 24.04 image definition (cloud image, using cloud-init)
# generated 2024-10-12
# part of VIRL^2
#

id: ${COPY_DST}
label: ${NODE_DEF_LABEL}
description: ${NODE_DEF_DESCRIPTION}
node_definition_id: ubuntu
disk_image: noble-server-cloudimg-amd64.img
read_only: false
schema_version: 0.0.1
EOF

systemctl restart virl2.target
