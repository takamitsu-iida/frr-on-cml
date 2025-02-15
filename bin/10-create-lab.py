#!/usr/bin/env python

#
# 標準ライブラリのインポート
#
import logging
import sys
from pathlib import Path

#
# 外部ライブラリのインポート
#
try:
    from jinja2 import Template
    from virl2_client import ClientLibrary
    from virl2_client.models import Lab, Node
except ImportError as e:
    logging.critical(str(e))
    sys.exit(-1)

#
# ローカルファイルからの読み込み
#
from config import CML_ADDRESS, CML_USERNAME, CML_PASSWORD
from config import LAB_TITLE
from config import SERIAL_PORT, UBUNTU_USERNAME, UBUNTU_PASSWORD


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

    def read_template_config() -> str:
        filename = 'cloud-init.yaml.j2'
        p = app_home.joinpath(filename)
        try:
            with p.open() as f:
                return f.read()
        except FileNotFoundError:
            logger.error(f"{filename} not found")
            sys.exit(1)


    def create_node(lab: Lab, label: str, x: int = 0, y: int = 0) -> Node:
        # create_node(
        #   label: str,
        #   node_definition: str,
        #   x: int = 0, y: int = 0,
        #   wait: bool | None = None,
        #   populate_interfaces: bool = False, **kwargs
        # )→ Node

        node = lab.create_node(label, 'ubuntu', x, y)

        # 初期状態はインタフェースが存在しないので、追加する
        # Ubuntuのslot番号の範囲は0-7
        # slot番号はインタフェース名ではない
        # ens2-ens9が作られる
        for i in range(8):
            node.create_interface(i, wait=True)

        return node



    def main():

        client = ClientLibrary(f"https://{CML_ADDRESS}/", CML_USERNAME, CML_PASSWORD, ssl_verify=False)

        # 接続を待機する
        client.is_system_ready(wait=True)

        # 同タイトルのラボを消す
        for lab in client.find_labs_by_title(LAB_TITLE):
            lab.stop()
            lab.wipe()
            lab.remove()

        # ラボを新規作成
        lab = client.create_lab(title=LAB_TITLE)

        # 外部接続用のNATを作る
        ext_conn_node = lab.create_node("ext-conn-0", "external_connector", 0, 0)

        # NATに接続するスイッチ（アンマネージド）
        nat_switch = lab.create_node("nat-sw", "unmanaged_switch", 0, 200)

        # NATとスイッチを接続する
        lab.connect_two_nodes(ext_conn_node, nat_switch)

        # Ubuntuに設定するcloud-init.yamlのJinja2テンプレートを取り出す
        template_config = read_template_config()

        # Jinja2のTemplateをインスタンス化する
        template = Template(template_config)

        # templateに渡すコンテキストオブジェクト
        context = {
            "HOSTNAME": "",
            "UBUNTU_USERNAME": UBUNTU_USERNAME,
            "UBUNTU_PASSWORD": UBUNTU_PASSWORD,
        }

        # X座標
        x = 0
        x_grid_width = 50

        # Ubuntuを8個作る
        # iは0始まり
        for i in range(8):
            x = i * x_grid_width

            # ubuntuを作成
            node_name = f"ubuntu-{i + 1}"
            node = create_node(lab, node_name, x, 400)

            # タグを設定
            # 例 serial:6001
            tag = f"serial:{SERIAL_PORT + i + 1}"
            node.add_tag(tag=tag)

            # NAT用スイッチと接続
            lab.connect_two_nodes(nat_switch, node)

            # 設定を作る
            context["HOSTNAME"] = node_name
            config = template.render(context)

            # ノードのconfigを設定する
            node.config = config


        # start the lab
        # lab.start()

        # print nodes and interfaces states:
        for node in lab.nodes():
            print(node, node.state, node.cpu_usage)
            for interface in node.interfaces():
                print(interface, interface.readpackets, interface.writepackets)


        return 0

    # 実行
    sys.exit(main())
