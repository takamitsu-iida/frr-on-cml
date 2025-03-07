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

    # 作成するラボのタイトル
    LAB_TITLE = "FRR ISIS"

    # このラボで使うシリアルポートの開始番号
    SERIAL_PORT = 7000


    def read_template_config(filename='') -> str:
        p = data_dir.joinpath(filename)
        try:
            with p.open() as f:
                return f.read()
        except FileNotFoundError:
            logger.error(f"{filename} not found")
            sys.exit(1)


    def indent_string(text):
        """文字列の行頭にスペースを挿入する"""
        lines = text.splitlines()  # 文字列を改行で分割
        indented_lines = ["      " + line for line in lines]  # 各行の先頭にスペース4個を追加
        return "\n".join(indented_lines)  # 改行で連結して返す


    def main():

        # 引数処理
        parser = argparse.ArgumentParser(description='create isis lab')
        parser.add_argument('-d', '--delete', action='store_true', default=False, help='Delete lab')
        args = parser.parse_args()

        # CMLを操作するvirl2_clientをインスタンス化
        client = ClientLibrary(f"https://{CML_ADDRESS}/", CML_USERNAME, CML_PASSWORD, ssl_verify=False)

        # 接続を待機する
        client.is_system_ready(wait=True)

        # 同タイトルのラボを消す
        for lab in client.find_labs_by_title(LAB_TITLE):
            lab.stop()
            lab.wipe()
            lab.remove()

        # -d で起動していたらここで処理終了
        if args.delete:
            return 0

        # ラボを新規作成
        lab = client.create_lab(title=LAB_TITLE)

        # (X, Y)座標
        x = 0
        y = 0
        grid_width = 160

        # 外部接続用のブリッジを作る
        ext_conn_node = lab.create_node("bridge1", "external_connector", x, y)

        # デフォルトはNATなので、これを"bridge1"に変更する
        # bridge1は追加したブリッジで、インターネット接続はない
        # このLANに足を出せば、別のラボの仮想マシンであっても通信できる
        ext_conn_node.configuration = "bridge1"

        # bridge1に接続するスイッチ（アンマネージド）を作る
        # 場所はブリッジの下
        y += grid_width
        ext_switch_node = lab.create_node("ext-sw", "unmanaged_switch", x, y)

        # bridge1とスイッチを接続する
        lab.connect_two_nodes(ext_conn_node, ext_switch_node)

        # ubuntuに設定するcloud-init.yamlのJinja2テンプレートを取り出す
        template_config = read_template_config(filename='lab_isis.yaml.j2')

        # Jinja2のTemplateをインスタンス化する
        template = Template(template_config)

        frr_template_config = read_template_config(filename='frr_conf_isis.j2')
        frr_template = Template(frr_template_config)
        frr_context = {
            "HOSTNAME": "R",
            "IPv4_ROUTER_ID": "",
            "IPv6_ROUTER_ID": "",
        }

        # templateに渡すコンテキストオブジェクトを作成する
        lab_context = {
            "HOSTNAME": "",
            "USERNAME": FRR_UBUNTU_USERNAME,
            "PASSWORD": FRR_UBUNTU_PASSWORD,
            "ROUTER_ID": "",
            "FRR_CONF": ""
        }

        # ルータを区別するための番号
        router_number = 1

        # 作成するt2ノードを格納しておくリスト
        t2_nodes = []

        # t2のUbuntuを3個作る
        x += grid_width
        for i in range(3):
            # Y座標
            y = i * grid_width

            # ubuntuをインスタンス化する
            # create_node(
            #   label: str,
            #   node_definition: str,
            #   x: int = 0, y: int = 0,
            #   wait: bool | None = None,
            #   populate_interfaces: bool = False, **kwargs
            # )→ Node

            # ルータの名前
            node_name = f"R{router_number}"

            # その名前でUbuntuをインスタンス化する
            node = lab.create_node(node_name, 'ubuntu', x, y)

            # 初期状態はインタフェースが存在しないので追加する
            # Ubuntuのslot番号範囲は0-7なので、最大8個のNICを作れる
            # slot番号はインタフェース名ではない
            # OSから見えるインタフェース目はens2, ens3, ...ens9となる
            for _ in range(8):
                node.create_interface(_, wait=True)

            # 起動イメージを指定する
            node.image_definition = FRR_UBUNTU_IMAGE_DEFINITION

            # スマートタグを設定
            node.add_tag(tag="TIER2")

            # ノード個別のタグを設定
            # 例 serial:7001
            node_tag = f"serial:{SERIAL_PORT + router_number}"
            node.add_tag(tag=node_tag)

            # 外部接続用スイッチと接続
            # lab.connect_two_nodes(ext_switch_node, node)

            # FRRの設定を作る
            frr_context["HOSTNAME"] = node_name
            frr_context["IPv4_ROUTER_ID"] = str(router_number)
            frr_context["IPv6_ROUTER_ID"] = "{:0=2}".format(router_number)
            frr_context["TIER"] = "2"
            frr_config = frr_template.render(frr_context)
            frr_config = indent_string(frr_config)

            # nodeに適用するcloud-init設定を作る
            lab_context["HOSTNAME"] = node_name
            lab_context["ROUTER_ID"] = router_number
            lab_context["FRR_CONF"] = frr_config

            # ノードに設定する
            node.configuration = template.render(lab_context)

            # リストに追加する
            t2_nodes.append(node)

            # ルータを作ったので一つ数字を増やす
            router_number += 1

        # 続いてクラスタを2個作る
        x += grid_width
        y = 0
        num_clusters = 2
        for i in range(num_clusters):

            # クラスタ内のスパインルータ（T1ルータ）を格納するリスト
            t1_nodes = []

            # クラスタ内にT1ルータを2個作る
            for j in range(2):
                node_name = f"R{router_number}"
                node = lab.create_node(node_name, 'ubuntu', x, y)
                y += grid_width

                # NICを8個追加
                for _ in range(8):
                    node.create_interface(_, wait=True)

                # 起動イメージを指定
                node.image_definition = FRR_UBUNTU_IMAGE_DEFINITION

                # スマートタグを設定
                node.add_tag(tag=f"cluster-{i + 1}")

                # ノード個別のタグを設定
                # 例 serial:7201
                node_tag = f"serial:{SERIAL_PORT + router_number}"
                node.add_tag(tag=node_tag)

                # FRRの設定を作る
                frr_context["IPv4_ROUTER_ID"] = str(router_number)
                frr_context["IPv6_ROUTER_ID"] = "{:0=2}".format(router_number)
                frr_context["TIER"] = "1"
                frr_config = frr_template.render(frr_context)
                frr_config = indent_string(frr_config)

                # cloud-init設定
                lab_context["HOSTNAME"] = node_name
                lab_context["ROUTER_ID"] = router_number
                lab_context["FRR_CONF"] = frr_config
                node.configuration = template.render(lab_context)

                # tier1ルータと接続する
                for n in t2_nodes:
                    lab.connect_two_nodes(n, node)

                # リストに追加
                t1_nodes.append(node)

                router_number += 1


            # 続いてクラスタ内にT0ルータを作る
            t0_x = x + grid_width
            t0_y = i * grid_width * 2 + int(grid_width / 2)
            for k in range(3):

                node_name = f"R{router_number}"
                node = lab.create_node(node_name, 'ubuntu', t0_x, t0_y)
                t0_x += grid_width

                # NICを8個追加
                for _ in range(8):
                    node.create_interface(_, wait=True)

                # 起動イメージを指定
                node.image_definition = FRR_UBUNTU_IMAGE_DEFINITION

                # スマートタグを設定
                node.add_tag(tag=f"cluster-{i + 1}")

                # ノード個別のタグを設定
                # 例 serial:7301
                node_tag = f"serial:{SERIAL_PORT + router_number}"
                node.add_tag(tag=node_tag)

                # FRRの設定を作る
                frr_context["IPv4_ROUTER_ID"] = str(router_number)
                frr_context["IPv6_ROUTER_ID"] = "{:0=2}".format(router_number)
                frr_context["TIER"] = "0"
                frr_config = frr_template.render(frr_context)
                frr_config = indent_string(frr_config)

                # 設定
                lab_context["HOSTNAME"] = node_name
                lab_context["ROUTER_ID"] = router_number
                lab_context["FRR_CONF"] = frr_config
                node.configuration = template.render(lab_context)

                # Tier2と接続
                for n in t1_nodes:
                    lab.connect_two_nodes(n, node)

                router_number += 1


        # start the lab
        # lab.start()

        # print nodes and interfaces states:
        #for node in lab.nodes():
        #    print(node, node.state, node.cpu_usage)
        #    for interface in node.interfaces():
        #        print(interface, interface.readpackets, interface.writepackets)

        return 0

    # 実行
    sys.exit(main())
