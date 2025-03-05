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
L * 2001:db8::1/128 is directly connected, lo, weight 1, 00:07:51
C>* 2001:db8::1/128 is directly connected, lo, weight 1, 00:07:51
f>* 2001:db8::2/128 [115/30] via fe80::4, ens2 onlink, weight 1, 00:07:13
  *                          via fe80::9, ens4 onlink, weight 1, 00:07:13
  *                          via fe80::10, ens5 onlink, weight 1, 00:07:13
  *                          via fe80::5054:ff:fef4:46f7, ens3 onlink, weight 1, 00:07:13
f>* 2001:db8::3/128 [115/30] via fe80::4, ens2 onlink, weight 1, 00:07:03
  *                          via fe80::9, ens4 onlink, weight 1, 00:07:03
  *                          via fe80::10, ens5 onlink, weight 1, 00:07:03
  *                          via fe80::5054:ff:fef4:46f7, ens3 onlink, weight 1, 00:07:03
f>* 2001:db8::4/128 [115/20] via fe80::4, ens2 onlink, weight 1, 00:07:21
f>* 2001:db8::5/128 [115/20] via fe80::5054:ff:fef4:46f7, ens3 onlink, weight 1, 00:07:21
f>* 2001:db8::6/128 [115/30] via fe80::4, ens2 onlink, weight 1, 00:07:01
  *                          via fe80::5054:ff:fef4:46f7, ens3 onlink, weight 1, 00:07:01
f>* 2001:db8::7/128 [115/30] via fe80::4, ens2 onlink, weight 1, 00:06:55
  *                          via fe80::5054:ff:fef4:46f7, ens3 onlink, weight 1, 00:06:55
f>* 2001:db8::8/128 [115/30] via fe80::4, ens2 onlink, weight 1, 00:06:51
  *                          via fe80::5054:ff:fef4:46f7, ens3 onlink, weight 1, 00:06:51
f>* 2001:db8::9/128 [115/20] via fe80::9, ens4 onlink, weight 1, 00:07:21
f>* 2001:db8::10/128 [115/20] via fe80::10, ens5 onlink, weight 1, 00:07:21
f>* 2001:db8::11/128 [115/30] via fe80::9, ens4 onlink, weight 1, 00:06:44
  *                           via fe80::10, ens5 onlink, weight 1, 00:06:44
f>* 2001:db8::12/128 [115/30] via fe80::9, ens4 onlink, weight 1, 00:06:39
  *                           via fe80::10, ens5 onlink, weight 1, 00:06:39
f>* 2001:db8::13/128 [115/30] via fe80::9, ens4 onlink, weight 1, 00:06:34
  *                           via fe80::10, ens5 onlink, weight 1, 00:06:34
C * fe80::/64 is directly connected, ens2, weight 1, 00:07:50
C * fe80::/64 is directly connected, ens8, weight 1, 00:07:50
C * fe80::/64 is directly connected, ens4, weight 1, 00:07:50
C * fe80::/64 is directly connected, ens5, weight 1, 00:07:50
C * fe80::/64 is directly connected, ens9, weight 1, 00:07:51
C * fe80::/64 is directly connected, ens3, weight 1, 00:07:51
C>* fe80::/64 is directly connected, ens6, weight 1, 00:07:51
R1#
```

# R4(T1ルータ)のルーティングテーブル

```text
R4# show ipv6 route
Codes: K - kernel route, C - connected, L - local, S - static,
       R - RIPng, O - OSPFv3, I - IS-IS, B - BGP, N - NHRP,
       T - Table, v - VNC, V - VNC-Direct, A - Babel, F - PBR,
       f - OpenFabric, t - Table-Direct,
       > - selected route, * - FIB route, q - queued, r - rejected, b - backup
       t - trapped, o - offload failure

IPv6 unicast VRF default:
f>* 2001:db8::1/128 [115/20] via fe80::1, ens2 onlink, weight 1, 00:08:05
f>* 2001:db8::2/128 [115/20] via fe80::2, ens3 onlink, weight 1, 00:08:05
f>* 2001:db8::3/128 [115/20] via fe80::5054:ff:fea8:95ac, ens4 onlink, weight 1, 00:08:01
L * 2001:db8::4/128 is directly connected, lo, weight 1, 00:09:06
C>* 2001:db8::4/128 is directly connected, lo, weight 1, 00:09:06
f>* 2001:db8::5/128 [115/30] via fe80::1, ens2 onlink, weight 1, 00:08:01
  *                          via fe80::2, ens3 onlink, weight 1, 00:08:01
  *                          via fe80::5054:ff:fea8:95ac, ens4 onlink, weight 1, 00:08:01
f>* 2001:db8::6/128 [115/20] via fe80::5054:ff:fe44:75dd, ens5 onlink, weight 1, 00:07:54
f>* 2001:db8::7/128 [115/20] via fe80::5054:ff:fe98:4c87, ens6 onlink, weight 1, 00:07:49
f>* 2001:db8::8/128 [115/20] via fe80::8, ens7 onlink, weight 1, 00:07:43
f>* 2001:db8::9/128 [115/30] via fe80::1, ens2 onlink, weight 1, 00:08:01
  *                          via fe80::2, ens3 onlink, weight 1, 00:08:01
  *                          via fe80::5054:ff:fea8:95ac, ens4 onlink, weight 1, 00:08:01
f>* 2001:db8::10/128 [115/30] via fe80::1, ens2 onlink, weight 1, 00:08:01
  *                           via fe80::2, ens3 onlink, weight 1, 00:08:01
  *                           via fe80::5054:ff:fea8:95ac, ens4 onlink, weight 1, 00:08:01
f>* 2001:db8::11/128 [115/40] via fe80::1, ens2 onlink, weight 1, 00:07:36
  *                           via fe80::2, ens3 onlink, weight 1, 00:07:36
  *                           via fe80::5054:ff:fea8:95ac, ens4 onlink, weight 1, 00:07:36
f>* 2001:db8::12/128 [115/40] via fe80::1, ens2 onlink, weight 1, 00:07:31
  *                           via fe80::2, ens3 onlink, weight 1, 00:07:31
  *                           via fe80::5054:ff:fea8:95ac, ens4 onlink, weight 1, 00:07:31
f>* 2001:db8::13/128 [115/40] via fe80::1, ens2 onlink, weight 1, 00:07:26
  *                           via fe80::2, ens3 onlink, weight 1, 00:07:26
  *                           via fe80::5054:ff:fea8:95ac, ens4 onlink, weight 1, 00:07:26
C * fe80::/64 is directly connected, ens5, weight 1, 00:09:05
C * fe80::/64 is directly connected, ens3, weight 1, 00:09:05
C * fe80::/64 is directly connected, ens2, weight 1, 00:09:05
C * fe80::/64 is directly connected, ens7, weight 1, 00:09:06
C * fe80::/64 is directly connected, ens4, weight 1, 00:09:06
C * fe80::/64 is directly connected, ens8, weight 1, 00:09:06
C>* fe80::/64 is directly connected, ens9, weight 1, 00:09:06
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
f>* 2001:db8::1/128 [115/4114] via fe80::4, ens2 onlink, weight 1, 00:08:27
  *                            via fe80::5, ens3 onlink, weight 1, 00:08:27
f>* 2001:db8::2/128 [115/4114] via fe80::4, ens2 onlink, weight 1, 00:08:27
  *                            via fe80::5, ens3 onlink, weight 1, 00:08:27
f>* 2001:db8::3/128 [115/4114] via fe80::4, ens2 onlink, weight 1, 00:08:27
  *                            via fe80::5, ens3 onlink, weight 1, 00:08:27
f>* 2001:db8::4/128 [115/4104] via fe80::4, ens2 onlink, weight 1, 00:08:27
f>* 2001:db8::5/128 [115/4104] via fe80::5, ens3 onlink, weight 1, 00:08:27
L * 2001:db8::6/128 is directly connected, lo, weight 1, 00:08:57
C>* 2001:db8::6/128 is directly connected, lo, weight 1, 00:08:57
f>* 2001:db8::7/128 [115/4114] via fe80::4, ens2 onlink, weight 1, 00:08:20
  *                            via fe80::5, ens3 onlink, weight 1, 00:08:20
f>* 2001:db8::8/128 [115/4114] via fe80::4, ens2 onlink, weight 1, 00:08:15
  *                            via fe80::5, ens3 onlink, weight 1, 00:08:15
f>* 2001:db8::9/128 [115/4124] via fe80::4, ens2 onlink, weight 1, 00:08:27
  *                            via fe80::5, ens3 onlink, weight 1, 00:08:27
f>* 2001:db8::10/128 [115/4124] via fe80::4, ens2 onlink, weight 1, 00:08:27
  *                             via fe80::5, ens3 onlink, weight 1, 00:08:27
f>* 2001:db8::11/128 [115/4134] via fe80::4, ens2 onlink, weight 1, 00:08:07
  *                             via fe80::5, ens3 onlink, weight 1, 00:08:07
f>* 2001:db8::12/128 [115/4134] via fe80::4, ens2 onlink, weight 1, 00:08:02
  *                             via fe80::5, ens3 onlink, weight 1, 00:08:02
f>* 2001:db8::13/128 [115/4134] via fe80::4, ens2 onlink, weight 1, 00:07:57
  *                             via fe80::5, ens3 onlink, weight 1, 00:07:57
C * fe80::/64 is directly connected, ens8, weight 1, 00:08:56
C * fe80::/64 is directly connected, ens4, weight 1, 00:08:56
C * fe80::/64 is directly connected, ens9, weight 1, 00:08:56
C>* fe80::/64 is directly connected, ens6, weight 1, 00:08:57
R6#
```