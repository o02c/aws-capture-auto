# Browser Automation Tool

このツールは以下の機能を提供します：

1. 認証情報を含むセッション情報の保存
2. 保存したセッション情報を使用して、指定したURLのスクリーンショットを取得
3. 複数URLの一括キャプチャ
4. スクリーンショットのExcelへの貼り付け

## 環境構築

### 必要条件

- Python 3.13以上
- Playwrightとその依存関係

### セットアップ

1. リポジトリをクローン

```bash
git clone <リポジトリURL>
cd browser-automation
```

2. 仮想環境を作成して有効化

```bash
uv sync
source .venv/bin/activate  # Linuxの場合
.venv\Scripts\activate  # Windowsの場合
```

3. Playwrightをセットアップ

```bash
playwright install
```

## 使い方

### Webサービスへのログイン

```bash
python src/main.py login <ログインURL>
```

例：

```bash
python src/main.py login 'https://example.com/login'
```

ブラウザが開いたら、手動でログイン操作を完了してください。ログイン後、ブラウザを閉じると自動的にセッション情報が保存されます。

### 指定URLのスクリーンショットを取得

```bash
python src/main.py capture <URL>
```

オプション：
- `--wait`: ページ読み込み後の待機時間（秒、デフォルト: 5）
- `--selector`: 特定の要素が表示されるまで待機するCSS selector
- `--filename`: 保存するファイル名（指定がない場合はタイムスタンプで生成）
- `--no-fullpage`: 全画面キャプチャを無効化
- `--viewport`: ビューポートサイズ（例: 1920x1080）

例：

```bash
python src/main.py capture https://example.com --wait 10 --viewport 1920x1080
```

### 複数URLの一括キャプチャ

```bash
python src/main.py captures --urls <URL1> <URL2> ... [オプション]
```

または、JSONファイルから設定を読み込む場合：

```bash
python src/main.py captures --json <設定ファイル.json> [オプション]
```

設定ファイルのJSON形式：
```json
[
  {
    "url": "https://example.com",
    "wait_time": 3,
    "viewport_size": "1920x1080",
    "fullpage": true
  },
  {
    "url": "https://example.com/about",
    "wait_time": 5,
    "selector": ".header",
    "viewport_size": "1280x720",
    "fullpage": false
  }
]
```

オプション：
- `--wait`: ページ読み込み後の待機時間（秒、デフォルト: 5）
- `--selector`: 特定の要素が表示されるまで待機するCSS selector
- `--no-fullpage`: 全画面キャプチャを無効化
- `--viewport`: ビューポートサイズ（例: 1920x1080）

### Excelへの画像貼り付け

```bash
python src/main.py excel <入力Excelファイル> --json <設定ファイル.json>
```

または、直接設定を指定する場合：

```bash
python src/main.py excel <入力Excelファイル> --config "画像パス,シート名,セル,幅cm,高さcm"
```

設定ファイルのJSON形式：
```json
[
  {
    "image_path": "data/screenshots/example1.png",
    "sheet_name": "Sheet1",
    "cell": "A1",
    "width_cm": 10.0,
    "height_cm": 8.0
  },
  {
    "image_path": "data/screenshots/example2.png",
    "sheet_name": 2,
    "cell": "B5",
    "width_cm": 15.0,
    "height_cm": 12.0
  }
]
```

オプション：
- `--output`, `-o`: 出力Excelファイルのパス（指定がない場合は上書き）

### キャプチャとExcel貼り付けの一括実行

```bash
python src/main.py capture-excel <設定ファイル.json> <入力Excelファイル> [--output <出力Excelファイル>]
```

設定ファイルのJSON形式：
```json
[
  {
    "url": "https://example.com",
    "wait_time": 3,
    "viewport_size": "1920x1080",
    "fullpage": false,
    "excel": {
      "sheet_name": 0,
      "cell": "B26",
      "width_cm": 10.0,
      "height_cm": 7.0
    }
  },
  {
    "url": "https://example.com/products",
    "wait_time": 2,
    "selector": "#product-list",
    "viewport_size": "1920x1080",
    "fullpage": true,
    "excel": {
      "sheet_name": 1,
      "cell": "C5",
      "width_cm": 15.0,
      "height_cm": 10.0
    }
  }
]
```

スクリーンショットは`data/screenshots`ディレクトリに保存されます。
