#!/usr/bin/env python

#
# 標準ライブラリのインポート
#
import argparse
import logging
import sys
from pathlib import Path

#
# 外部ライブラリのインポート
#
try:
    from jinja2 import Template
    from virl2_client import ClientLibrary
except ImportError as e:
    logging.critical(str(e))
    sys.exit(-1)

#
# ローカルファイルからの読み込み
#
from cml_config import CML_ADDRESS, CML_USERNAME, CML_PASSWORD
from cml_config import FRR_UBUNTU_USERNAME, FRR_UBUNTU_PASSWORD
from cml_config import FRR_LAB_NAME, FRR_UBUNTU_TAG
from cml_config import FRR_UBUNTU_IMAGE_DEFINITION

# このファイルへのPathオブジェクト
app_path = Path(__file__)

# このファイルの名前から拡張子を除いてプログラム名を得る
app_name = app_path.stem

# アプリケーションのホームディレクトリはこのファイルからみて一つ上
app_home = app_path.parent.joinpath('..').resolve()

# データ用ディレクトリ
data_dir = app_home.joinpath('data')

#
# ログ設定
#

# ログファイルの名前
log_file = app_path.with_suffix('.log').name

# ログファイルを置くディレクトリ
log_dir = app_home.joinpath('log')
log_dir.mkdir(exist_ok=True)

# ログファイルのパス
log_path = log_dir.joinpath(log_file)

# ロギングの設定
# レベルはこの順で下にいくほど詳細になる
#   logging.CRITICAL
#   logging.ERROR
#   logging.WARNING --- 初期値はこのレベル
#   logging.INFO
#   logging.DEBUG
#
# ログの出力方法
# logger.debug('debugレベルのログメッセージ')
# logger.info('infoレベルのログメッセージ')
# logger.warning('warningレベルのログメッセージ')

# 独自にロガーを取得するか、もしくはルートロガーを設定する

# ルートロガーを設定する場合
# logging.basicConfig()

# 独自にロガーを取得する場合
logger = logging.getLogger(__name__)

# 参考
# ロガーに特定の名前を付けておけば、後からその名前でロガーを取得できる
# logging.getLogger("main.py").setLevel(logging.INFO)

# ログレベル設定
logger.setLevel(logging.INFO)

# フォーマット
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# 標準出力へのハンドラ
stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setFormatter(formatter)
stdout_handler.setLevel(logging.INFO)
logger.addHandler(stdout_handler)

# ログファイルのハンドラ
file_handler = logging.FileHandler(log_path, 'a+')
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.INFO)
logger.addHandler(file_handler)

#
# ここからスクリプト
#
if __name__ == '__main__':

    def read_template_config(filename='') -> str:
        p = data_dir.joinpath(filename)
        try:
            with p.open() as f:
                return f.read()
        except FileNotFoundError:
            logger.error(f"{filename} not found")
            sys.exit(1)


    def main():

        # 引数処理
        parser = argparse.ArgumentParser(description='create frr lab')
        parser.add_argument('-d', '--delete', action='store_true', default=False, help='Delete lab')
        args = parser.parse_args()

        client = ClientLibrary(f"https://{CML_ADDRESS}/", CML_USERNAME, CML_PASSWORD, ssl_verify=False)

        # 接続を待機する
        client.is_system_ready(wait=True)

        # 同タイトルのラボを消す
        for lab in client.find_labs_by_title(FRR_LAB_NAME):
            lab.stop()
            lab.wipe()
            lab.remove()

        # -d で起動していたらここで処理終了
        if args.delete:
            return 0

        # ラボを新規作成
        lab = client.create_lab(title=FRR_LAB_NAME)

        # 外部接続用のNATを作る
        ext_conn_node = lab.create_node("ext-conn-0", "external_connector", 0, 0)

        # ubuntuのインスタンスを作る
        ubuntu_node = lab.create_node("frr", 'ubuntu', 0, 100)

        # 初期状態はインタフェースが存在しないので、追加する
        # Ubuntuのslot番号の範囲は0-7
        # slot番号はインタフェース名ではない
        # ens2-ens9が作られる
        for i in range(8):
            ubuntu_node.create_interface(i, wait=True)

        # NATとubuntuを接続する
        lab.connect_two_nodes(ext_conn_node, ubuntu_node)

        # Ubuntuに設定するcloud-init.yamlのJinja2テンプレートを取り出す
        template_config = read_template_config(filename='lab_frr.yaml.j2')

        # Jinja2のTemplateをインスタンス化する
        template = Template(template_config)

        # templateに渡すコンテキストオブジェクト
        context = {
            "HOSTNAME": "frr",
            "USERNAME": FRR_UBUNTU_USERNAME,
            "PASSWORD": FRR_UBUNTU_PASSWORD,
        }

        # cloud-initのテキストを作る
        config = template.render(context)

        # ノードのconfigにcloud-initのテキストを設定する
        ubuntu_node.config = config

        # 起動イメージを指定する
        ubuntu_node.image_definition = FRR_UBUNTU_IMAGE_DEFINITION

        # タグを設定（cml_config.pyで定義）
        # "serial:6000"
        ubuntu_node.add_tag(tag=FRR_UBUNTU_TAG)

        # start the lab
        lab.start()

        command_text = """\n
sudo -s -E
git clone https://github.com/takamitsu-iida/frr-on-cml.git
cd frr-on-cml
ansible-playbook playbook.yaml
"""
        logger.info("To install FRR, execute following playbook in the ubuntu terminal." + command_text)

        command_text = f"""\n
cd /var/local/virl2/images/{lab.id}/{ubuntu_node.id}
sudo qemu-img commit node0.img
"""

        logger.info("To commit changes, execute following commands in cml cockpit terminal." + command_text)

        return 0

    # 実行
    sys.exit(main())
