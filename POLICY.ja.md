# certificateDB の運用方針

[English policy](POLICY.md)

## 目的と境界

このリポジトリは無線機器の認証根拠を記録します。認証を発行・再現・法的に判断したり、無線設定や送信を許可したりしません。

## 根拠の扱い

各記録は、公式 URL、取得情報、原本ハッシュ、抽出箇所を持たなければなりません。自動処理は `candidate` または `extracted` までに限定し、`reviewed` と `verified` への昇格には記録されたレビューが必要です。

`matchStatus: unconfirmed` または `mismatch` の記録は、機器・RF・ファームウェアの制約導出に使用できません。原本、秘密情報、MAC アドレス、校正・NVRAM ダンプはコミットしません。

## URL 一覧

`url list.txt` は公開資料の参照入口です。個別の `sourceUrl`、取得日時、SHA-256、証拠束を置き換えず、単体で証拠・認可・送信許可にはなりません。
