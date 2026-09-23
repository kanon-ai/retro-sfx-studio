# 免責事項 / Disclaimer

## 提供条件

本ソフトウェアはMITライセンスに基づき、現状有姿（AS IS）で提供されます。
商品性、特定目的への適合性、権利非侵害を含む明示・黙示の保証はありません。
責任制限等の正式な条件は [LICENSE](LICENSE) を参照してください。
適用法令により認められない責任制限について、その法令の適用を妨げるものではありません。

## エミュレーションと実機

- 音源生成にはymfmエミュレーターを使用します。オリジナル実機との完全一致を保証しません。
- PSGはYM2149モデルです。AY-3-8910搭載MSXとの音量特性やアナログ回路の差があります。
- 基準クロックは固定です。機種・拡張ボード・再生環境によって差が生じます。
- OPNAのADPCM・リズム、OPMのノイズ、複数チャンネルの同時編集は未対応です。
- 公開時点ではエミュレーターとソフトウェア上で検証しており、実機での動作は未検証です。

## 生成データとゲームへの組み込み

- WAV、VGM、レジスター列、Cヘッダーの利用・調整・検証は利用者の責任で行ってください。
- 本ツールは実機用ROMやサウンドドライバーを自動生成するものではありません。
- 実機では書込み待ち、共有レジスター、チャンネルの割当て、BGMとの競合、タイマー精度を扱う必要があります。
- PSG/SSGのR7はI/O方向ビットを含みます。対象機の既存I/O設定を維持するアダプターが必要です。
- 高い出力レベルや特定の音色設定ではクリッピングが発生する場合があります。再生音量を調整してください。
- 本プロジェクトは自動生成した音声・パラメーターに追加の利用料やクレジット条件を課しません。
  第三者の音色・素材を持ち込む場合は、その権利と利用条件を別途確認してください。
- 本ツールのソースコードを再配布する場合は、該当するライセンス条件を維持してください。

## AI・MCP

- AIモデルは同梱しません。自然言語を解釈するAIとMCPクライアントは利用者が用意します。
- MCPで提供するのは音色データの取得・検証・合成・出力機能です。AIの判断や生成する統合コードの正確性を保証しません。
- ASTRAを含む特定モデルやクライアントとの連携を保証するものではありません。ローカルstdio MCPへの対応が必要です。
- 本サーバー自体は音色データを外部のAIサービスへ送信しません。
  接続したAIクライアントがデータを送信するかどうかは、利用者の環境と設定によります。
- ローカルパスを含むツール結果を共有する際は、共有範囲を確認してください。

## 商標・独立性

MSX、PC-9801、X68000、Yamaha、KORG、およびその他の製品名・商標は各権利者に帰属します。
本プロジェクトは独立したソフトウェアであり、各メーカー、OpenAI、AIモデル提供者による公式製品・公認製品ではありません。
ハードウェア風UIは独自に作成したもので、メーカーのロゴや製品画像を使用していません。

## English summary

This software is provided **AS IS**, without warranty, under the [MIT License](LICENSE).
Chip emulation is not a guarantee of hardware accuracy. Real-hardware integration has not been verified.
Users must implement and validate target-specific timing, register ownership, I/O handling and audio-driver integration.
The application includes no AI model. AI-assisted use requires a compatible local stdio MCP client and an independently provided AI model.
No affiliation with or endorsement by the named hardware manufacturers or AI providers is implied.
Third-party components retain their own licenses; see [THIRD_PARTY.md](THIRD_PARTY.md).
