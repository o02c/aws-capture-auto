# AWS Capture Auto

このツールは以下の機能を提供します：

1. AWSコンソールへのログイン支援と認証情報の保存
2. 保存したセッション情報を使用して、指定したURLのスクリーンショットを取得
3. タグエディタを使用して、指定した条件に一致するAWSリソースの一覧を取得

## 環境構築

### 必要条件

- Python 3.13以上
- Playwrightとその依存関係
- boto3（AWS SDK for Python）

### セットアップ

1. リポジトリをクローン

```bash
git clone <リポジトリURL>
cd aws-capture-auto
```

2. 仮想環境を作成して有効化

```bash
python -m venv .venv
source .venv/bin/activate  # Linuxの場合
.venv\Scripts\activate  # Windowsの場合
```

3. 依存パッケージをインストール

```bash
pip install -r requirements.txt
```

4. Playwrightをセットアップ

```bash
playwright install
```

5. 環境変数を設定

`.env.example`をコピーして`.env`を作成し、必要な情報を入力してください。

```bash
cp .env.example .env
```

## 使い方

### AWSコンソールへのログイン

```bash
python src/main.py login <ログインURL>
```

例：
```bash
python src/main.py login https://signin.aws.amazon.com/console
# または
python src/main.py login https://123456789012.signin.aws.amazon.com/console
```

ブラウザが開いたら、手動でログイン操作を完了してください。ログイン後、ブラウザを閉じると自動的にセッション情報が保存されます。

### 指定URLのスクリーンショットを取得

```bash
python src/main.py capture https://console.aws.amazon.com/ec2/home
```

オプション：
- `--wait <秒数>`: ページ読み込み後の待機時間
- `--selector <CSSセレクタ>`: 待機する要素のCSSセレクタ
- `--filename <ファイル名>`: 保存するファイル名
- `--no-fullpage`: 全画面キャプチャしない

### 特定のタグを持つリソース一覧を取得

```bash
python src/main.py resource --tag-key Environment --tag-value Production
```

オプション：
- `--tag-key <キー>`: タグのキー（複数指定可）
- `--tag-value <値>`: タグの値（複数指定可）
- `--resource-type <タイプ>`: リソースタイプ（複数指定可）

## ディレクトリ構造

- `src/`: ソースコード
  - `aws_login.py`: AWSコンソールログイン処理
  - `aws_capture.py`: スクリーンショット取得処理
  - `aws_resource.py`: リソース一覧取得処理
  - `main.py`: メインのインターフェース
- `data/`: 生成されたデータ
  - `screenshots/`: スクリーンショット
  - `resources/`: リソース情報

## ライセンス

このプロジェクトは[MITライセンス](LICENSE)の下で公開されています。
