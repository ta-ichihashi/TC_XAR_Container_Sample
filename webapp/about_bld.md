# TwinCAT Linuxと従来のOSとの比較

従来のTwinCATは、コンピュータのハードウェアを直接制御可能なカーネルモードと呼ばれる特別な権限を持ったプロセスで動作するランタイムでしたが、LinuxのPREEMPT_RTカーネルを活用したTwinCATは、ユーザランドで動作するプロセスです。また、DebianをベースとしたBeckhoffオリジナルのディストリビューションにより整合の取れたパッケージを提供します。

||Windows|TC/BSD|BeckhoffLinux®Distribution|
|-------------|--------------------|-----------------------|---------|
|プラットフォーム|x86/amd64|x86/amd64|x86/amd64,ARM64(新世代のみ)|
|使用開始|1990年代|2020年|開発中(Beta09-2024)|
|現在OSバージョン|Windows11IoTEnterpriseLTSC2024|TC/BSD14.1|Linux6.9,Debian12.6|
|OSのライセンス|MicrosoftEULA|BSD|GPL(Kernel)|
|パッケージ管理|tcpkg(TwinCAT専用)|pkg（FreeBSD用）|apt（debian用）|
|パッケージサーバ|tcpkg.beckhoff-cloud.com|tcbsd.beckhoff.com|deb.beckhoff.com|
|ファイルシステム|NTFS|ZFS|Btrfs（バターFS）|
|動作モード|カーネルモード(TwinCATRT)|カーネルモード(TwinCATOS)|ユーザモード(RTLinux)|
|ハイパーバイザ|対応無し|bhyve|kvm/qemu(開発中)|
|コンテナ|対応無し|Jails|Linuxコンテナ(Docker,Podman,etc.)|
|ファイアウォール|WindowsFirewall|Pf（FreeBSDパケットフィルタ）|Nftables（Linuxネットワークフィルタ）|
|初期化システム|Windowsサービス|Rc（ランコマンド）|systemd|
|ユーザインターフェース|WindowsDesktop,ssh,Remote-Desktop,IPC-Diagnose,TF1200TwinCATUI-Client|Bourne-Shell,ssh,web-console,IPC-Diagnose,TF1200TwinCATUI-Client|Bash,ssh,web-console,IPC-Diagnose,TF1200TwinCATUI-Client(開発中)|

# TwinCAT Real-time Linux サポートIPC

* CX8200 (ARM Cortex A53)
* CX9240 (ARM Cortex A53)
* CX53x0 (Intel Atom® x6000E) and later
* C601x-0030 (Intel Atom® x6000E) and later
* CX56x0 (AMD Ryzen® R1000 Series)
* CX20x3 (AMD Ryzen® V1000 Series)
* C602x-0010 (Intel Core® 11th Generation) and later
* C6030-0080 (Intel Core® 11th Generation) and later
* C6043-0090 (Intel Core® 12th Generation) and later
* CPxxx and C69xx with same platform Generation

![](app/static/linux_products.png)