
```bash
python3 -m venv .venv
direnv allow
pip install --upgrade pip
pip install -r requirements.txt
```


# Ubuntuのカスタムイメージの作り方

<br>

> [!NOTE]
>
> この動画がわかりやすいです。
>
> https://www.youtube.com/watch?v=dCWwtKXMUuU

<br>

1. コックピットのターミナルにログイン

コックピットはポート番号9090をHTTPSで開けばよい。

すでにブラウザでCMLを開いているのであれば `TOOLS → System Administration` をたどると以下の表示があるので、
リンクをクリックすればよい。

```text
The Cockpit service runs independently of the CML2 platform,
and allows recovery in the event of a system issue.
It is available at https://192.168.122.212:9090 (opens in a new Tab/Window).
```

コックピットの左下に「端末」が見えるので、それを開く。

1. root権限のシェルを開く

root権限のシェルを起動するには以下のようにする。

```bash
sudo -s -E
```

プロンプトが `$` から `#` に変わる。

1. ubuntuイメージが格納されている場所に移動する

```bash
cd /var/lib/libvirt/images
cd virl-base-images
```

この場所には各種イメージが保存されている。

```bash
oot@cml-controller:/var/lib/libvirt/images/virl-base-images# ls -l
total 68
drwxrwxr-x 2 libvirt-qemu virl2 4096 Feb 21 04:32 alpine-base-3-20-3
drwxrwxr-x 2 libvirt-qemu virl2 4096 Feb 21 04:32 alpine-desktop-3-20-3
drwxrwxr-x 2 libvirt-qemu virl2 4096 Feb 21 04:32 alpine-trex-3-20-3
drwxrwxr-x 2 libvirt-qemu virl2 4096 Feb 21 04:32 alpine-wanem-3-20-3
drwxrwxr-x 2 libvirt-qemu virl2 4096 Feb 21 04:32 asav-9-22-1-1
drwxrwxr-x 2 libvirt-qemu virl2 4096 Feb 21 04:32 cat8000v-17-15-01a
drwxrwxr-x 2 libvirt-qemu virl2 4096 Feb 21 04:32 cat9000v-q200-17-15-01
drwxrwxr-x 2 libvirt-qemu virl2 4096 Feb 21 04:32 cat9000v-uadp-17-15-01
drwxrwxr-x 2 libvirt-qemu virl2 4096 Feb 21 04:32 csr1000v-17-03-08a
drwxrwxr-x 2 libvirt-qemu virl2 4096 Feb 21 04:32 iol-xe-17-15-01
drwxrwxr-x 2 libvirt-qemu virl2 4096 Feb 21 04:32 ioll2-xe-17-15-01
drwxrwxr-x 2 libvirt-qemu virl2 4096 Feb 21 04:32 iosv-159-3-m9
drwxrwxr-x 2 libvirt-qemu virl2 4096 Feb 21 04:32 iosvl2-2020
drwxrwxr-x 2 libvirt-qemu virl2 4096 Feb 21 04:32 iosxrv9000-24-3-1
drwxrwxr-x 2 libvirt-qemu virl2 4096 Feb 21 04:32 nxosv9300-10-5-1-f
drwxrwxr-x 2 libvirt-qemu virl2 4096 Feb 21 04:32 server-tcl-15-0
drwxrwxr-x 2 libvirt-qemu virl2 4096 Feb 21 04:32 ubuntu-24-04-20241004
root@cml-controller:/var/lib/libvirt/images/virl-base-images#
```

これらはすべてreadonlyになっていて、変更は反映されない。

1. ubuntuのイメージをコピーする

改造して使いたいのは `ubuntu-24-04-20241004` のイメージ。このディレクトリを属性付きでコピーする。名前は何でも良い。ここでは `-frr` を後ろに追加した。

```bash
cp -a ubuntu-24-04-20241004 ubuntu-24-04-20241004-frr
```

念の為、オーナーとグループをvirl2にする（-a付きのコピーなので、オーナーとグループも引き継いでいるはず）。

```bash
chown virl2:virl2 ubuntu-24-04-20241004-frr
```

1. コピーしたディレクトリに移動する

```bash
cd ubuntu-24-04-20241004-frr
```

ここにはイメージファイルとイメージ定義ファイル（YAMLファイル）が置かれている。

1. イメージ定義ファイルの名前をディレクトリ名と一致させる

イメージ定義ファイル（YAML形式のファイル）をディレクトリ名と一致するように変更する。

```bash
mv ubuntu-24-04-20241004.yaml  ubuntu-24-04-20241004-frr.yaml
```

1. イメージ定義ファイルを編集する


```bash
vi ubuntu-24-04-20241004-frr.yaml
```

もとのYAMLはこうなっている。

```YAML
#
# Ubuntu 24.04 image definition (cloud image, using cloud-init)
# generated 2024-10-12
# part of VIRL^2
#

id: ubuntu-24-04-20241004
label: Ubuntu 24.04 - 04 Oct 2024
description: Ubuntu 24.04 - 04 Oct 2024
node_definition_id: ubuntu
disk_image: noble-server-cloudimg-amd64.img
read_only: true
schema_version: 0.0.1
```

- idの値はユニークである必要があるので必ず変更する。ディレクトリ名と同じでよい

- labelの値はGUIでOS選択するときにドロップダウンに表示されるので、分かりやすいものに変える

- descriptionはlabelに合わせておく

- read_onlyをtrueからfalseに変える

編集後はこんな感じ。

```YAML
#
# Ubuntu 24.04 image definition (cloud image, using cloud-init)
# generated 2024-10-12
# part of VIRL^2
#

id: ubuntu-24-04-20241004-frr
label: Ubuntu 24.04 - 04 Oct 2024 - with FRR installed
description: Ubuntu 24.04 - 04 Oct 2024 -with FRR installed
node_definition_id: ubuntu
disk_image: noble-server-cloudimg-amd64.img
read_only: false
schema_version: 0.0.1
```

1. サービスを再起動する

```bash
systemctl restart virl2.target
```

サービスを再起動しても、稼働中のラボには影響しない。
ただし、ブラウザでCMLにログインしていた場合は、すべてログアウトされる。

1. 以上を自動化して実行する

ここまでの作業をシェルスクリプトにしたので、コックピットのターミナルを開いてから、以下をコピペするだけでよい。

```bash
curl -H 'Cache-Control: no-cache' -Ls https://raw.githubusercontent.com/takamitsu-iida/frr-on-cml/refs/heads/main/bin/copy_node_definition.sh | bash -s
```

スクリプトの中身は以下の通り。

```bash
#!/bin/bash

# 特権ユーザのシェルを取る
# パスワードを聞かれる
sudo -s -E

COPY_SRC="ubuntu-24-04-20241004"
COPY_DST="ubuntu-24-04-20241004-frr"

NODE_DEF_ID=${COPY_DST}
NODE_DEF_LABEL="Ubuntu 24.04 - 04 Oct 2024 FRR installed"

# ubuntuイメージのある場所に移動する
cd /var/lib/libvirt/images/virl-base-images

# すでにターゲットのディレクトリがあるなら消す
rm -rf ${COPY_DST}

# 属性付きでubuntuディレクトリをコピー
cp -a ${COPY_SRC} ${COPY_DST}

# オーナーをvirl2にする
chown virl2:virl2 ${COPY_DST}

# 作成したディレクトリに移動
cd ${COPY_DST}

# ノード定義ファイルの名前をディレクトリ名と一致させる
mv ${COPY_SRC}.yaml ${COPY_DST}.yaml

# ノード定義ファイルを編集する
sed -i -e "s/^id:.*\$/id: ${NODE_DEF_ID}/" ${COPY_DST}.yaml
sed -i -e "s/^label:.*\$/label: ${NODE_DEF_LABEL}/" ${COPY_DST}.yaml
sed -i -e "s/^description:.*\$/description: ${NODE_DEF_LABEL}/" ${COPY_DST}.yaml

systemctl restart virl2.target
```

<br><br>

1. コピーしたイメージで起動するubuntuを作る

ここからはCMLのダッシュボードで作業する。

適当なラボを作り、インターネットに出ていける外部接続とubuntuを作成する。

ubuntuのSETTINGSタブの Image Definition のドロップダウンから上記のlabelのものを選んでから起動する。

起動したらアップデート、FRRのインストール、などなどを実行して好みのubuntuに仕上げる。

1. 自動化してubuntuを作成する

この作業を手動でやるのは少々面倒なので、pythonで自動化する。

`bin/cml_create_frr` を実行すると "create frr" という名前のラボができる。
このラボを開始すると最新化された状態でubuntuが起動する。

気がすむまでubuntuを操作したら、ラボを停止する。

1. コックピットに戻って作成したラボのubuntuイメージの場所に移動する

この時点では、ubuntu起動時に使ったイメージはまだ変更されていない。

CMLのダッシュボードで当該ラボを開いた状態でURLの文字列をコピーする。

こんな感じのURLになっているので、最後のUUIDの部分をコピーする（この場合は7fe8ece7-6b23-49f3-a852-519c9f0a843aがUUID）

```text
https://192.168.122.212/lab/7fe8ece7-6b23-49f3-a852-519c9f0a843a
```

コックピットのターミナルで `/var/local/virl2/images/{{uuid}}` に移動する（`{{uuid}}`の部分は先ほどコピーしたものに置き換える）

もう一つ下のディレクトリに起動中のubuntuのイメージがある。

```bash
root@cml-controller:/var/local/virl2/images/7fe8ece7-6b23-49f3-a852-519c9f0a843a/2aa37c69-fcdc-4eb0-8e26-e00a95e6676e# ls -l
total 3114176
drwxr-xr-x 2 virl2        virl2       4096 Feb 21 07:38 cfg
-rw-r--r-- 1 libvirt-qemu kvm       376832 Feb 21 07:38 config.img
-rw-r--r-- 1 virl2        virl2        159 Feb 21 07:38 config.yaml
-rw-r--r-- 1 libvirt-qemu kvm   3188523008 Feb 21 07:49 node0.img
```

node0.imgファイルは元のイメージからの変更を保持している。

1. 変更を元のイメージに反映する

```bash
qemu-img commit node0.img
```

これで起動時に使ったイメージの方に変更が反映される。

1. ubuntuを起動しなおして動作確認する

ubuntuをwipeしてコンフィグを破棄して、再び起動すると、先ほど施した変更が反映された状態で起動する。


<br>

> [!NOTE]
>
> Pythonのモジュール virl2_client はCMLのバージョンと一致させる必要がある。

<br><br><br><br>

- 外部接続 - NAT

```yaml
    configuration:
      - name: default
        content: NAT
```

- 外部接続 - システムブリッジ

```yaml
    configuration:
      - name: default
        content: System Bridge
```

- 外部接続 - 追加したブリッジ

```yaml
    configuration:
      - name: default
        content: bridge1
```



## ansible-pullの動作結果確認

cloud-initのログは `/var/log/cloud-init.log` にある。
その中にansible-pullの記録も残る。

ansible-pullは `/root/.ansible/pull` に展開されるので、うまくいってないときは、そこにちゃんとリポジトリのプレイブック一式が展開されているか確認する。

作成したアカウントのままだと/rootには行けないので、su -sで権限昇格したシェルを開けてから移動する。


Ubuntuを作成

GUIでNICを4つ追加
GUIでcloud-initを設定

```yaml
#cloud-config
hostname: ubuntu
manage_etc_hosts: True
system_info:
  default_user:
    name: cisco
password: cisco
chpasswd: { expire: False }
ssh_pwauth: True
ssh_authorized_keys:
  - your-ssh-pubkey-line-goes-here
timezone: Asia/Tokyo
locale: ja_JP.utf8
write_files:
  - path: /etc/netplan/50-cloud-init.yaml
    content: |
      network:
        version: 2
        ethernets:
          ens2:
            dhcp4: true
            #nameservers:
            #  addresses:
            #    - 192.168.122.1

          ens3:
            dhcp4: false
            addresses:
              - 192.168.254.1/24
            #routes:
            #  - to: 10.0.0.0/8
            #    via: 192.168.254.101

runcmd:

  - |
    sudo cat - << 'EOS' >> /home/cisco/.bashrc
    rsz () if [[ -t 0 ]]; then local escape r c prompt=$(printf '\e7\e[r\e[999;999H\e[6n\e8'); IFS='[;' read -sd R -p "$prompt" escape r c; stty cols $c rows $r; fi
    rsz
    EOS
```

ens2を外部接続（NAT）する

タグにserial:6000を設定する

ターミナルでコンソール接続する（telnet CML 6000）

cisco/ciscoでログイン（初期アカウントはcloud-initで設定する）

Ubuntuそのものを最新化

sudo apt update
sudo apt dist-upgrade
sudo apt autoremove


FRRをインストールする（FRRのマニュアルにある通り）
https://docs.frrouting.org/projects/dev-guide/en/latest/building-frr-for-ubuntu2204.html

```bash
sudo apt install \
   git autoconf \
   automake libtool make libreadline-dev texinfo \
   pkg-config libpam0g-dev libjson-c-dev bison flex \
   libc-ares-dev python3-dev python3-sphinx \
   install-info build-essential libsnmp-dev perl \
   libcap-dev libelf-dev libunwind-dev \
   protobuf-c-compiler libprotobuf-c-dev
```

念の為、一度再起動。

libyangをインストールする。libyangは新しいものが必要。ソースコードからmakeする。

mkdir ~/src
cd ~/src
sudo apt install cmake
sudo apt install libpcre2-dev


```bash
git clone https://github.com/CESNET/libyang.git
cd libyang
git checkout v2.1.128
mkdir build; cd build
cmake --install-prefix /usr -D CMAKE_BUILD_TYPE:String="Release" ..
make
sudo make install
```

GRPCをインストールする。

```bash
sudo apt-get install libgrpc++-dev protobuf-compiler-grpc
```

ロールバック機能を使うにはsqlite3が必要。

```bash
sudo apt install libsqlite3-dev
```

ZeroMQをインストールする。これは任意。

```bash
sudo apt-get install libzmq5 libzmq3-dev
```


FRRのユーザとグループを作成する。

```bash
sudo groupadd -r -g 92 frr
sudo groupadd -r -g 85 frrvty
sudo adduser --system --ingroup frr --home /var/run/frr/ --gecos "FRR suite" --shell /sbin/nologin frr
sudo usermod -a -G frrvty frr
```

FRRをコンパイルする。

```bash
mkdir ~/src/frr
cd ~/src/frr

git clone https://github.com/frrouting/frr.git frr
cd frr

./bootstrap.sh

./configure \
    --prefix=/usr \
    --includedir=\${prefix}/include \
    --bindir=\${prefix}/bin \
    --sbindir=\${prefix}/lib/frr \
    --libdir=\${prefix}/lib/frr \
    --libexecdir=\${prefix}/lib/frr \
    --sysconfdir=/etc \
    --localstatedir=/var \
    --with-moduledir=\${prefix}/lib/frr/modules \
    --enable-configfile-mask=0640 \
    --enable-logfile-mask=0640 \
    --enable-snmp=agentx \
    --enable-multipath=64 \
    --enable-user=frr \
    --enable-group=frr \
    --enable-vty-group=frrvty \
    --with-pkg-git-version \
    --with-pkg-extra-version=-MyOwnFRRVersion

make

sudo make install

```

コンフィグファイルをインストールする。

```bash
sudo install -m 775 -o frr -g frr -d /var/log/frr
sudo install -m 775 -o frr -g frrvty -d /etc/frr
sudo install -m 640 -o frr -g frrvty tools/etc/frr/vtysh.conf /etc/frr/vtysh.conf
sudo install -m 640 -o frr -g frr tools/etc/frr/frr.conf /etc/frr/frr.conf
sudo install -m 640 -o frr -g frr tools/etc/frr/daemons.conf /etc/frr/daemons.conf
sudo install -m 640 -o frr -g frr tools/etc/frr/daemons /etc/frr/daemons
```

カーネル設定を変える。
/etc/sysctl.confの以下2行のコメントを外してルーティングを有効にする。

```bash
# Uncomment the next line to enable packet forwarding for IPv4
net.ipv4.ip_forward=1

# Uncomment the next line to enable packet forwarding for IPv6
#  Enabling this option disables Stateless Address Autoconfiguration
#  based on Router Advertisements for this host
net.ipv6.conf.all.forwarding=1
```

有効にするために再起動する。

MPLSは有効にしない（試したけどUbuntu22では動かなかった）。

サービス起動用のファイルをインストールする。

```bash
cd ~/src/frr/frr

sudo install -m 644 tools/frr.service /etc/systemd/system/frr.service
sudo systemctl enable frr
```

FRRのデーモン設定を変更してfabricdを有効にする。
/etc/frr/daemons

```text
fabricd=yes
```

起動する。

```bash
systemctl start frr
```

vtyshに入る。

```bash
sudo vtysh
```


<br><br>

# Ubuntuを最新化してFRRをインストールするansible playbook

root権限で作業する。

```bash
sudo -s -E

git clone https://github.com/takamitsu-iida/frr-on-cml.git
cd frr-on-cml

ansible-playbook playbook.yaml
```

このプレイブックの最後では `var/lib/cloud/` を削除して、cloud-initが実行されていなかったことにしている。
これをしないと、次にこのイメージで起動したときにcloud-initが実行されなくなる。


<br><br>

# 手順まとめ

### コックピットにログインして、Ubuntuのイメージをコピーするシェルスクリプトを実行する

```bash
curl -H 'Cache-Control: no-cache' -Ls https://raw.githubusercontent.com/takamitsu-iida/frr-on-cml/refs/heads/main/bin/copy_node_definition.sh | bash -s
```

### Pythonスクリプト `bin/cml_create_frr.py` を実行して "create frr" ラボを作る

```bash
bin/cml_create_frr.py
```

実行時に表示されるメッセージは後で利用する。

### Ubuntuのコンソールに接続する

CMLのアドレスが192.168.122.212の場合はこれで作成したUbuntuのシリアルコンソールに接続する。

```bash
telnet 192.168.122.212 6000
```

### FRRをインストールするプレイブックを実行する。

```bash
sudo -s -E

git clone https://github.com/takamitsu-iida/frr-on-cml.git
cd frr-on-cml

ansible-playbook playbook.yaml
```

### Ubuntuを停止する

```bash
shutdown -h now
```

### コックピットにログインして、イメージの変更をコミットする。

`cml_create_frr.py` を実行したときに表示された手順をコックピットで実行する。

以降はFRRインストール済みのイメージを使ってUbuntuを起動すればよい。
