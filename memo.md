
```bash
python3 -m venv .venv
direnv allow
pip install --upgrade pip
pip install -r requirements.txt
```


# Ubuntuのカスタムイメージの作り方

    -  https://www.youtube.com/watch?v=dCWwtKXMUuU

    - CMLにログインして適当なラボを作り、外部接続したubuntuを1台作る

    - コックピットのターミナルにログイン

    - sudo -s -E  でrootのシェルを起動

    - cd /var/lib/libvirt/images/virl-base-images

    - cp -a ubuntu-22 ubuntu-22-iida  ファイル名は要確認（たぶんディレクトリ）

    - chown virl2:virl2 ubuntu-22-iida ファイル名は要確認

    - cd ubuntu-22-iida

    - mv ___.yaml ___-iida.yaml でYAMLファイルの名前をディレクトリの名前と同じになるように変える

    - vi ___-iida.yaml で編集

    - idの値はユニークである必要があるので、必ず変更する、ディレクトリ名と同じでいい

    - labelの値はGUIでOS選択するときにドロップダウンに表示されるので、分かりやすいものに変える

    - descriptionはlabelに合わせておく

    - read_onlyをtrueからfalseに変える

    - systemctl restart virl2.target でプロセスを再起動（稼働中のラボには影響しない）

    - CMLにログイン

    - ubuntuを選択して、SIMULATEタブからイメージを変更する

    - ラボを起動

    - ubuntuを操作して好みのアプリをインストールしてカスタマイズする

    - コックピットに戻る

    - この時点ではイメージファイルに変更は反映されていない

    - ブラウザのURLからラボのUUIDをコピーする

    - cd /var/local/virl2/images/{{UUID}}

    - ここにあるファイルは元のイメージからの変更をnodedisk_0ファイルに保持している

    - qemu-img commit nodedisk_0 で変更を元のイメージに反映する

    - ubuntuをwipeしてコンフィグを破棄して、再び起動すると、変更が反映された状態で起動する






<br>

> [!NOTE]
>
> virl2_clientはCMLのバージョンと一致させる必要がある。

<br>

外部接続 - NAT

```yaml
    configuration:
      - name: default
        content: NAT
```

外部接続 - システムブリッジ

```yaml
    configuration:
      - name: default
        content: System Bridge
```

外部接続 - 追加したブリッジ

```yaml
    configuration:
      - name: default
        content: bridge1
```







## ansible-pullの動作結果確認

cloud-initのログは /var/log/cloud-init.log にある。
その中にansible-pullの記録も残る。

ansible-pullは `/root/.ansible/pull` に展開されるので、うまくいってないときは、そこにちゃんとリポジトリのプレイブック一式が展開されているか確認する。

作成したアカウントのままだと/rootには行けないので、su -sで権限昇格したシェルを開ける。




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
    rsz () if [[ -t 0 ]]; then local escape r c prompt=$(printf '\e7\e[r\e[999;999H\e[6n\e8'); IFS='[;' read -sd R -p j"$prompt" escape r c; stty cols $c rows $r; fi
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



改良版。
できるだけ共通の項目だけを設定する。
起動後にOSをアップデートして、必要なモジュール類を追加する。

```bash
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

# FRRのユーザとグループを作成する。
groups:
  - frr
  - frrvty

users:
  - name: frr
    gecos: FRR suite
    shll: /sbin/nologin
    homedir: /var/run/frr
    system: true
    groups: frr, frrvty

# run apt-get update
# default false
package_update: true

# default false
package_upgrade: true

# add packages
packages:
  # needed to compile FRR
  - git
  - autoconf
  - automake
  - libtool
  - make
  - libreadline-dev
  - texinfo
  - pkg-config
  - libpam0g-dev
  - libjson-c-dev
  - bison
  - flex
  - libc-ares-dev
  - python3-dev
  - python3-sphinx
  - install-info
  - build-essential
  - libsnmp-dev
  - perl
  - libcap-dev
  - libelf-dev
  - libunwind-dev
  - protobuf-c-compiler
  - libprotobuf-c-dev

  # needed to compile libyang
  - libgrpc++-dev
  - protobuf-compiler-grpc

  # needed to use rollback
  - libsqlite3-dev

  # optional
  - libzmq5
  - libzmq3-dev


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


runcmd:

  - |
    cat - << 'EOS' >> /etc/bash.bashrc
    rsz () if [[ -t 0 ]]; then local escape r c prompt=$(printf '\e7\e[r\e[999;999H\e[6n\e8'); IFS='[;' read -sd R -p j"$prompt" escape r c; stty cols $c rows $r; fi
    rsz
    EOS

  - apt autoremove

```
