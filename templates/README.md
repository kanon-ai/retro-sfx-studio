# 効果音テンプレート / Sound templates

各音源8種、合計40種のオリジナル効果音テンプレートです。既存12プリセットに続くPROGRAM 13〜52（MCP index 12〜51）として利用できます。

- GUI：PROGRAMから音源名付きの音色を選択。または「読込」でpatches内のJSONを開きます。
- MCP：list_presets → get_preset → パラメーター調整 → export_sound。
- 試聴：ZIPを全て展開し、preview.htmlをブラウザーで開いてください。
- WAVとJSONは同じ設定から生成。catalog.jsonに説明・設定・WAVのSHA-256を記録しています。
- プリセットは音作りの出発点です。長さ、基準音、包絡、FMオペレーターを自由に調整できます。
- PSGの「ベル」は矩形波による通知音、FMの「爆発・衝撃」は変調による音です。専用PCM音源ではありません。
- チップに応じた音程・包絡の量子化があります。実機の回路差は再現せず、実機未検証です。
- 本プロジェクト独自のパッチと音声はCC0-1.0で提供します。商用・非商用で利用・改変でき、クレジットは必須ではありません。
  詳細は[LICENSE](LICENSE)。本ツールのコードは引き続きMIT、第三者コードは各ライセンスです。

| PROGRAM / MCP index | 音源 | 音色・用途 | パッチ | 試聴 |
|---|---|---|---|---|
| 13 / 12 | PSG | コイン：アイテム取得 | [JSON](patches/psg-coin.json) | [WAV](audio/psg-coin.wav) |
| 14 / 13 | PSG | 決定音：メニューの決定・選択 | [JSON](patches/psg-confirm.json) | [WAV](audio/psg-confirm.wav) |
| 15 / 14 | PSG | ジャンプ：上昇する短いジャンプ音 | [JSON](patches/psg-jump.json) | [WAV](audio/psg-jump.wav) |
| 16 / 15 | PSG | レーザー：下降するSFショット | [JSON](patches/psg-laser.json) | [WAV](audio/psg-laser.wav) |
| 17 / 16 | PSG | 爆発・衝撃：低音の衝撃。PSGはノイズ、FMは変調による質感 | [JSON](patches/psg-impact.json) | [WAV](audio/psg-impact.wav) |
| 18 / 17 | PSG | ベル：アイテム・イベント通知の余韻 | [JSON](patches/psg-bell.json) | [WAV](audio/psg-bell.wav) |
| 19 / 18 | PSG | 警報：交互に音程が変わる警告音 | [JSON](patches/psg-alarm.json) | [WAV](audio/psg-alarm.wav) |
| 20 / 19 | PSG | パワーアップ：段階的に上昇する獲得音 | [JSON](patches/psg-powerup.json) | [WAV](audio/psg-powerup.wav) |
| 21 / 20 | OPLL | コイン：アイテム取得 | [JSON](patches/opll-coin.json) | [WAV](audio/opll-coin.wav) |
| 22 / 21 | OPLL | 決定音：メニューの決定・選択 | [JSON](patches/opll-confirm.json) | [WAV](audio/opll-confirm.wav) |
| 23 / 22 | OPLL | ジャンプ：上昇する短いジャンプ音 | [JSON](patches/opll-jump.json) | [WAV](audio/opll-jump.wav) |
| 24 / 23 | OPLL | レーザー：下降するSFショット | [JSON](patches/opll-laser.json) | [WAV](audio/opll-laser.wav) |
| 25 / 24 | OPLL | 爆発・衝撃：低音の衝撃。PSGはノイズ、FMは変調による質感 | [JSON](patches/opll-impact.json) | [WAV](audio/opll-impact.wav) |
| 26 / 25 | OPLL | ベル：アイテム・イベント通知の余韻 | [JSON](patches/opll-bell.json) | [WAV](audio/opll-bell.wav) |
| 27 / 26 | OPLL | 警報：交互に音程が変わる警告音 | [JSON](patches/opll-alarm.json) | [WAV](audio/opll-alarm.wav) |
| 28 / 27 | OPLL | パワーアップ：段階的に上昇する獲得音 | [JSON](patches/opll-powerup.json) | [WAV](audio/opll-powerup.wav) |
| 29 / 28 | OPN | コイン：アイテム取得 | [JSON](patches/opn-coin.json) | [WAV](audio/opn-coin.wav) |
| 30 / 29 | OPN | 決定音：メニューの決定・選択 | [JSON](patches/opn-confirm.json) | [WAV](audio/opn-confirm.wav) |
| 31 / 30 | OPN | ジャンプ：上昇する短いジャンプ音 | [JSON](patches/opn-jump.json) | [WAV](audio/opn-jump.wav) |
| 32 / 31 | OPN | レーザー：下降するSFショット | [JSON](patches/opn-laser.json) | [WAV](audio/opn-laser.wav) |
| 33 / 32 | OPN | 爆発・衝撃：低音の衝撃。PSGはノイズ、FMは変調による質感 | [JSON](patches/opn-impact.json) | [WAV](audio/opn-impact.wav) |
| 34 / 33 | OPN | ベル：アイテム・イベント通知の余韻 | [JSON](patches/opn-bell.json) | [WAV](audio/opn-bell.wav) |
| 35 / 34 | OPN | 警報：交互に音程が変わる警告音 | [JSON](patches/opn-alarm.json) | [WAV](audio/opn-alarm.wav) |
| 36 / 35 | OPN | パワーアップ：段階的に上昇する獲得音 | [JSON](patches/opn-powerup.json) | [WAV](audio/opn-powerup.wav) |
| 37 / 36 | OPNA | コイン：アイテム取得 | [JSON](patches/opna-coin.json) | [WAV](audio/opna-coin.wav) |
| 38 / 37 | OPNA | 決定音：メニューの決定・選択 | [JSON](patches/opna-confirm.json) | [WAV](audio/opna-confirm.wav) |
| 39 / 38 | OPNA | ジャンプ：上昇する短いジャンプ音 | [JSON](patches/opna-jump.json) | [WAV](audio/opna-jump.wav) |
| 40 / 39 | OPNA | レーザー：下降するSFショット | [JSON](patches/opna-laser.json) | [WAV](audio/opna-laser.wav) |
| 41 / 40 | OPNA | 爆発・衝撃：低音の衝撃。PSGはノイズ、FMは変調による質感 | [JSON](patches/opna-impact.json) | [WAV](audio/opna-impact.wav) |
| 42 / 41 | OPNA | ベル：アイテム・イベント通知の余韻 | [JSON](patches/opna-bell.json) | [WAV](audio/opna-bell.wav) |
| 43 / 42 | OPNA | 警報：交互に音程が変わる警告音 | [JSON](patches/opna-alarm.json) | [WAV](audio/opna-alarm.wav) |
| 44 / 43 | OPNA | パワーアップ：段階的に上昇する獲得音 | [JSON](patches/opna-powerup.json) | [WAV](audio/opna-powerup.wav) |
| 45 / 44 | OPM | コイン：アイテム取得 | [JSON](patches/opm-coin.json) | [WAV](audio/opm-coin.wav) |
| 46 / 45 | OPM | 決定音：メニューの決定・選択 | [JSON](patches/opm-confirm.json) | [WAV](audio/opm-confirm.wav) |
| 47 / 46 | OPM | ジャンプ：上昇する短いジャンプ音 | [JSON](patches/opm-jump.json) | [WAV](audio/opm-jump.wav) |
| 48 / 47 | OPM | レーザー：下降するSFショット | [JSON](patches/opm-laser.json) | [WAV](audio/opm-laser.wav) |
| 49 / 48 | OPM | 爆発・衝撃：低音の衝撃。PSGはノイズ、FMは変調による質感 | [JSON](patches/opm-impact.json) | [WAV](audio/opm-impact.wav) |
| 50 / 49 | OPM | ベル：アイテム・イベント通知の余韻 | [JSON](patches/opm-bell.json) | [WAV](audio/opm-bell.wav) |
| 51 / 50 | OPM | 警報：交互に音程が変わる警告音 | [JSON](patches/opm-alarm.json) | [WAV](audio/opm-alarm.wav) |
| 52 / 51 | OPM | パワーアップ：段階的に上昇する獲得音 | [JSON](patches/opm-powerup.json) | [WAV](audio/opm-powerup.wav) |
