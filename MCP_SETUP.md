# AI向けMCP接続

このサーバーは標準のstdio MCP（改行区切りJSON-RPC）です。
ASTRA等を使う開発環境のMCPクライアントに接続して利用します。
AIモデル自体の機能ではなく、利用する開発環境側にローカルstdio MCPの対応が必要です。
GUIのHTTPアドレス（7911）はMCPエンドポイントではありません。

## 実行ファイル版

以下は `C:\Tools\RetroSFX` に展開した場合の例です。実際の保存先へ置き換えてください。

コマンド: `C:\Tools\RetroSFX\RetroSFX.exe`

引数: `--mcp`

一般的なmcpServers形式の設定例（利用するクライアントの設定ファイルへ追加）:

```json
{
  "mcpServers": {
    "retro-sfx": {
      "command": "C:\\Tools\\RetroSFX\\RetroSFX.exe",
      "args": ["--mcp"]
    }
  }
}
```

配布フォルダーを移動した場合、commandをその絶対パスへ変更してください。
このプロジェクトはクライアントの既存設定を自動変更しません。

## Python版

```json
{
  "mcpServers": {
    "retro-sfx": {
      "command": "python",
      "args": ["C:\\Projects\\retro-sfx-studio\\mcp_server.py"]
    }
  }
}
```

追加Pythonパッケージ不要。ネイティブ音源エンジンの実行ファイルが必要です。
プロトコルは2025-11-25 / 2025-06-18 / 2025-03-26 / 2024-11-05を初期化時にネゴシエートします。

## 公開ツール

| ツール | 引数 | 内容 |
|---|---|---|
| list_presets | なし | 12プリセットと音源一覧 |
| get_preset | index: 0〜11 | 編集可能な完全パッチ |
| validate_patch | patch | 設定検証、既定値補完、イベント件数 |
| render_sound | patch | WAVとパッチJSONをファイル出力 |
| export_sound | patch | WAV/VGM/JSON/Cヘッダー/説明/ZIP/ハッシュ |
| get_handoff_text | patch | 完全な仕様テキストを返す。ファイル出力なし |

出力先は実行ファイルと同じフォルダー内の `outputs/日時-一意ID/`。
Python版はソースフォルダー内のoutputs。既存ファイルを上書きしません。
外部への通信、任意コマンド実行、任意パスへの保存機能はありません。

## AIへの依頼例

> retro-sfx MCPでMSX用PSGのコイン効果音を作成してください。
> list_presetsで候補を調べ、get_presetでパッチを取得し、0.3秒程度に調整してください。
> export_soundで出力したAI_HANDOFF.mdを読み、既存ゲームのサウンドドライバーに合わせて
> registers.jsonを組み込んでください。BGM用チャンネルとPSGのI/O方向ビットは維持してください。

最小呼び出し例:

```json
{
  "name": "export_sound",
  "arguments": {
    "patch": {
      "name": "MSX jump",
      "chip": "PSG",
      "note": 48,
      "sweep": 24,
      "duration": 0.35,
      "attack": 0,
      "decay": 0.1,
      "sustain": 0.6,
      "release": 0.12
    }
  }
}
```

返却テキストにローカル絶対パスを含みます。WAVを再生／解析するにはクライアント側のファイル機能を使ってください。
生成はymfmエミュレーションによるものです。実機での動作を保証する検証結果として扱わないでください。

MCPの初期化、ツール列挙、設定取得、無効値のエラー応答、別プロセスからのexport_soundと実ファイル生成をテスト済みです。
公式Python MCP SDK 2.2.0から実行ファイル版へ接続し、初期化・ツール列挙・プリセット読込・export_sound・無効値の拒否を検証しました。
特定のAIクライアントへの登録はまだ行っていません。
