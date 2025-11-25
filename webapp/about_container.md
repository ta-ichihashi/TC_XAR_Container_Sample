# TwinCATをコンテナ上で稼働

ユーザモードで動作するTwinCATは、 **コンテナ** 上においてもリアルタイムコンピューティングが可能です。
コンテナとはアプリケーションレベルで独立したコンピュータ環境を提供する仮想化システムです。

## コンテナ化のメリット

<img src="app/static/container_concept.png" width="300" align="right">

* **構成のソフトウェアデファインド**

  - コンピュータの設定やパッケージインストールを定義ファイルにより自動化
  - TwinCAT以外の複数コンテナと組み合わせたオーケストレーションや効率的なコンテナ間通信を実現
  - 稼働するIPC（ハードウェア）に依存せず、どこでも同じソフトウェア構成を再現

* **豊富なコンテナの活用**

    クラウド技術等で多用されている、既存の豊富なコンテナ資産を組合せたアプリケーション構築が容易
 
    nginx, python, JAVA, node.js, .NET, go-lang, PostgreSQL, Apache IoT DB, InfluxDB ....

* **ハードウェアリソースの有効活用**

    kubernetesを活用した分散型や集中型のコンピュータリソースの最適化と、分散型Input/Outputのベストミックス

    - リアルタイムアプリケーション(TwinCAT)     : フィールドバスポートのあるノードに配置
    - 非リアルタイムアプリケーション            : 計算リソース(CPUコア)に余裕のあるコンピュータに配置

* **DevOpsへの対応**

    - システム構成をソフトウェアデファインドとすることで運用後の変更管理が容易となります。これにより運用上で生じたさまざまな課題を開発サイクルに回し、迅速に解決する DevOps 環境の実現。
    - シミュレータによるテストやと実環境での実行環境構築の自動化が図れるため、システム開発の品質向上に貢献します。
    - システムのソフトウェア構成管理を一元化することにより、CRA（EUサイバーレジリエンス法）に求められる **SBOMによるソフトウェア構成管理** と脆弱性の修正がスムーズです。

<br clear="right">


<a href="https://beckhoff-jp.github.io/TwinCATHowTo/twincat_container/index.html"><img src="app/static/webdocument.png" width="150" align="right"></a>

## 本デモの構成

本デモでは、以下のようなTwinCATコンテナを構築しています。こちらのURLで詳細な構築マニュアルを掲載しています。QRコードを読み取ってください。
<br clear="right">

* 2つのTwinCATコンテナが、個別のPCIバスに直接アクセスするリアルタイムフィールドバス制御
* TwinCAT基本ランタイムに加えてTF5000(NC PTP)や、WEBベースのHMI TF1810（PLC HMI Web）を構成
* ボリューム定義によりコンテナ上でファイルに保存されるパラメータやレシピ等はストレージに保存
* nginx プロキシサーバ を通じた内部のWEBサーバソースの秘匿化とSSL化。
* Streamlit WEBフロントエンド、Python, pandas などデータの活用の基盤を稼働


![](app/static/twincat_container_structure.png)
