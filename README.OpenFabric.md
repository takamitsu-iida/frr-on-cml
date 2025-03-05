# OpenFabricメモ

draft-white-openfabric-07.txt

概要

- 2025年2月時点で-07版
- ISISの機能をしぼってスケーラビリティを向上
- スパインリーフ型トポロジに特化
- レベル2のポイントツーポイント接続のみをサポート
- 隣接関係形成を効率化
- ファブリック内の階層を決定し、それを広告するメカニズムを導入
- 隣接ノードとさらにその先の隣接ノードの情報を利用した高度なフラッディング制御
- トランジットリンクの到達可能性の広告を抑制
- T0（トップオブラック）中間システムをトランジットノードとして使用しないように最適化
- FRRoutingで実装されている

<br>

![lab](./asset/lab.png)

<br>

# R1(T2ルータ)のルーティングテーブル

```text
R1# show ipv6 route
Codes: K - kernel route, C - connected, L - local, S - static,
       R - RIPng, O - OSPFv3, I - IS-IS, B - BGP, N - NHRP,
       T - Table, v - VNC, V - VNC-Direct, A - Babel, F - PBR,
       f - OpenFabric, t - Table-Direct,
       > - selected route, * - FIB route, q - queued, r - rejected, b - backup
       t - trapped, o - offload failure

IPv6 unicast VRF default:
L * 2001:db8::1/128 is directly connected, lo, weight 1, 00:03:02
C>* 2001:db8::1/128 is directly connected, lo, weight 1, 00:03:02
f>* 2001:db8::2/128 [115/30] via fe80::4, ens2 onlink, weight 1, 00:02:24
  *                          via fe80::5, ens3 onlink, weight 1, 00:02:24
  *                          via fe80::9, ens4 onlink, weight 1, 00:02:24
  *                          via fe80::10, ens5 onlink, weight 1, 00:02:24
f>* 2001:db8::3/128 [115/30] via fe80::4, ens2 onlink, weight 1, 00:02:18
  *                          via fe80::5, ens3 onlink, weight 1, 00:02:18
  *                          via fe80::9, ens4 onlink, weight 1, 00:02:18
  *                          via fe80::10, ens5 onlink, weight 1, 00:02:18
f>* 2001:db8::4/128 [115/20] via fe80::4, ens2 onlink, weight 1, 00:02:32
f>* 2001:db8::5/128 [115/20] via fe80::5, ens3 onlink, weight 1, 00:02:32
f>* 2001:db8::6/128 [115/30] via fe80::4, ens2 onlink, weight 1, 00:02:13
  *                          via fe80::5, ens3 onlink, weight 1, 00:02:13
f>* 2001:db8::7/128 [115/30] via fe80::4, ens2 onlink, weight 1, 00:02:06
  *                          via fe80::5, ens3 onlink, weight 1, 00:02:06
f>* 2001:db8::8/128 [115/30] via fe80::4, ens2 onlink, weight 1, 00:01:55
  *                          via fe80::5, ens3 onlink, weight 1, 00:01:55
f>* 2001:db8::9/128 [115/20] via fe80::9, ens4 onlink, weight 1, 00:02:32
f>* 2001:db8::10/128 [115/20] via fe80::10, ens5 onlink, weight 1, 00:02:32
f>* 2001:db8::11/128 [115/30] via fe80::9, ens4 onlink, weight 1, 00:01:56
  *                           via fe80::10, ens5 onlink, weight 1, 00:01:56
f>* 2001:db8::12/128 [115/30] via fe80::9, ens4 onlink, weight 1, 00:01:43
  *                           via fe80::10, ens5 onlink, weight 1, 00:01:43
f>* 2001:db8::13/128 [115/30] via fe80::9, ens4 onlink, weight 1, 00:01:43
  *                           via fe80::10, ens5 onlink, weight 1, 00:01:43
C * fe80::/64 is directly connected, ens3, weight 1, 00:03:01
C * fe80::/64 is directly connected, ens2, weight 1, 00:03:01
C * fe80::/64 is directly connected, ens9, weight 1, 00:03:01
C * fe80::/64 is directly connected, ens5, weight 1, 00:03:01
C * fe80::/64 is directly connected, ens4, weight 1, 00:03:01
C * fe80::/64 is directly connected, ens8, weight 1, 00:03:02
C * fe80::/64 is directly connected, ens7, weight 1, 00:03:02
C>* fe80::/64 is directly connected, ens6, weight 1, 00:03:02
R1#

```

# R4(T1ルータ)のルーティングテーブル

R4はR5と共にクラスタにおけるスパインルータを形成している。

R4からみてR5にたどり着く経路に注目すると、ECMPで3経路登録されていて、中継先はいずれも上位のルータ(R1, R2, R3)になっている。

OpenFabricにはT0ルータ（末端のルータ）を経由して通信しないような仕組みが導入されている。

```text
R4# show ipv6 route
Codes: K - kernel route, C - connected, L - local, S - static,
       R - RIPng, O - OSPFv3, I - IS-IS, B - BGP, N - NHRP,
       T - Table, v - VNC, V - VNC-Direct, A - Babel, F - PBR,
       f - OpenFabric, t - Table-Direct,
       > - selected route, * - FIB route, q - queued, r - rejected, b - backup
       t - trapped, o - offload failure

IPv6 unicast VRF default:
f>* 2001:db8::1/128 [115/20] via fe80::1, ens2 onlink, weight 1, 00:03:43
f>* 2001:db8::2/128 [115/20] via fe80::2, ens3 onlink, weight 1, 00:03:36
f>* 2001:db8::3/128 [115/20] via fe80::3, ens4 onlink, weight 1, 00:03:31
L * 2001:db8::4/128 is directly connected, lo, weight 1, 00:04:36
C>* 2001:db8::4/128 is directly connected, lo, weight 1, 00:04:36
f>* 2001:db8::5/128 [115/30] via fe80::1, ens2 onlink, weight 1, 00:03:31
  *                          via fe80::2, ens3 onlink, weight 1, 00:03:31
  *                          via fe80::3, ens4 onlink, weight 1, 00:03:31
f>* 2001:db8::6/128 [115/20] via fe80::6, ens5 onlink, weight 1, 00:03:24
f>* 2001:db8::7/128 [115/20] via fe80::7, ens6 onlink, weight 1, 00:03:19
f>* 2001:db8::8/128 [115/20] via fe80::8, ens7 onlink, weight 1, 00:03:05
f>* 2001:db8::9/128 [115/30] via fe80::1, ens2 onlink, weight 1, 00:03:31
  *                          via fe80::2, ens3 onlink, weight 1, 00:03:31
  *                          via fe80::3, ens4 onlink, weight 1, 00:03:31
f>* 2001:db8::10/128 [115/30] via fe80::1, ens2 onlink, weight 1, 00:03:31
  *                           via fe80::2, ens3 onlink, weight 1, 00:03:31
  *                           via fe80::3, ens4 onlink, weight 1, 00:03:31
f>* 2001:db8::11/128 [115/40] via fe80::1, ens2 onlink, weight 1, 00:03:07
  *                           via fe80::2, ens3 onlink, weight 1, 00:03:07
  *                           via fe80::3, ens4 onlink, weight 1, 00:03:07
f>* 2001:db8::12/128 [115/40] via fe80::1, ens2 onlink, weight 1, 00:03:01
  *                           via fe80::2, ens3 onlink, weight 1, 00:03:01
  *                           via fe80::3, ens4 onlink, weight 1, 00:03:01
f>* 2001:db8::13/128 [115/40] via fe80::1, ens2 onlink, weight 1, 00:02:56
  *                           via fe80::2, ens3 onlink, weight 1, 00:02:56
  *                           via fe80::3, ens4 onlink, weight 1, 00:02:56
C * fe80::/64 is directly connected, ens3, weight 1, 00:04:35
C * fe80::/64 is directly connected, ens2, weight 1, 00:04:35
C * fe80::/64 is directly connected, ens9, weight 1, 00:04:35
C * fe80::/64 is directly connected, ens5, weight 1, 00:04:35
C * fe80::/64 is directly connected, ens4, weight 1, 00:04:35
C * fe80::/64 is directly connected, ens8, weight 1, 00:04:35
C * fe80::/64 is directly connected, ens7, weight 1, 00:04:36
C>* fe80::/64 is directly connected, ens6, weight 1, 00:04:36
R4#
```

# R6(T0ルータ)のルーティングテーブル

```text
R6# show ipv6 route
Codes: K - kernel route, C - connected, L - local, S - static,
       R - RIPng, O - OSPFv3, I - IS-IS, B - BGP, N - NHRP,
       T - Table, v - VNC, V - VNC-Direct, A - Babel, F - PBR,
       f - OpenFabric, t - Table-Direct,
       > - selected route, * - FIB route, q - queued, r - rejected, b - backup
       t - trapped, o - offload failure

IPv6 unicast VRF default:
f>* 2001:db8::1/128 [115/4114] via fe80::4, ens2 onlink, weight 1, 00:03:58
  *                            via fe80::5, ens3 onlink, weight 1, 00:03:58
f>* 2001:db8::2/128 [115/4114] via fe80::4, ens2 onlink, weight 1, 00:03:58
  *                            via fe80::5, ens3 onlink, weight 1, 00:03:58
f>* 2001:db8::3/128 [115/4114] via fe80::4, ens2 onlink, weight 1, 00:03:58
  *                            via fe80::5, ens3 onlink, weight 1, 00:03:58
f>* 2001:db8::4/128 [115/4104] via fe80::4, ens2 onlink, weight 1, 00:03:58
f>* 2001:db8::5/128 [115/4104] via fe80::5, ens3 onlink, weight 1, 00:03:58
L * 2001:db8::6/128 is directly connected, lo, weight 1, 00:04:28
C>* 2001:db8::6/128 is directly connected, lo, weight 1, 00:04:28
f>* 2001:db8::7/128 [115/4114] via fe80::4, ens2 onlink, weight 1, 00:03:53
  *                            via fe80::5, ens3 onlink, weight 1, 00:03:53
f>* 2001:db8::8/128 [115/4114] via fe80::4, ens2 onlink, weight 1, 00:03:40
  *                            via fe80::5, ens3 onlink, weight 1, 00:03:40
f>* 2001:db8::9/128 [115/4124] via fe80::4, ens2 onlink, weight 1, 00:03:58
  *                            via fe80::5, ens3 onlink, weight 1, 00:03:58
f>* 2001:db8::10/128 [115/4124] via fe80::4, ens2 onlink, weight 1, 00:03:58
  *                             via fe80::5, ens3 onlink, weight 1, 00:03:58
f>* 2001:db8::11/128 [115/4134] via fe80::4, ens2 onlink, weight 1, 00:03:41
  *                             via fe80::5, ens3 onlink, weight 1, 00:03:41
f>* 2001:db8::12/128 [115/4134] via fe80::4, ens2 onlink, weight 1, 00:03:34
  *                             via fe80::5, ens3 onlink, weight 1, 00:03:34
f>* 2001:db8::13/128 [115/4134] via fe80::4, ens2 onlink, weight 1, 00:03:30
  *                             via fe80::5, ens3 onlink, weight 1, 00:03:30
C * fe80::/64 is directly connected, ens7, weight 1, 00:04:28
C * fe80::/64 is directly connected, ens4, weight 1, 00:04:28
C * fe80::/64 is directly connected, ens6, weight 1, 00:04:28
C * fe80::/64 is directly connected, ens2, weight 1, 00:04:28
C * fe80::/64 is directly connected, ens8, weight 1, 00:04:28
C * fe80::/64 is directly connected, ens9, weight 1, 00:04:28
C * fe80::/64 is directly connected, ens3, weight 1, 00:04:29
C>* fe80::/64 is directly connected, ens5, weight 1, 00:04:29
R6#
```