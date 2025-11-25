# コンテナ技術の活用

ユーザモードで動作するTwinCATは、「コンテナ」上においてもリアルタイムコンピューティングが可能です。

* Dockerなどの既存の豊富なアプリケーションコンテナイメージを組み合わせたコンテナを構築することができる
* さまざまなソフトウェアコンポーネント構成の構築をソフトウェアで定義することで、構成を再現する際の自動化が図れます
* 構築したコンテナは様々なIPCハードウェア上で動作。シミュレーション環境から実機へ移植したり、IPCのグレードアップの際の移植がスムーズに行えます

<img src="/app/static/container_concept.png" width="300" style="vertical-align:middle;">

# 本デモの構成

本デモにおけるコンテナ組合せ例

* 2つのTwinCATコンテナ
* TF5000(NC PTP)や、WEBベースのHMI TF1810（PLC HMI Web）稼働
* IPCの起動後に自動的に仮想PLCスタート
* nginx プロキシサーバを通じてSSLによる外部へセキュアに公開。
* Streamlit によるWEBフロントエンド
* Python, pandas を用いてTwinCATの稼働データの活用

![](/app/static/twincat_container_structure.png)
