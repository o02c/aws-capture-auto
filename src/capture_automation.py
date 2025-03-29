import json
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Literal, List, Tuple, Union
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
from pydantic import BaseModel, Field, validator
from urllib.parse import urlparse

load_dotenv()

BrowserType = Literal["chromium", "chrome", "firefox", "webkit"]

class Capture(BaseModel):
    """キャプチャ情報を格納するクラス"""
    url: str = Field(..., description="URL to capture")
    wait_time: int = Field(default=5, ge=0, description="Wait time after page load (seconds)")
    selector: Optional[str] = Field(default=None, description="CSS selector to wait for")
    fullpage: bool = Field(default=True, description="Whether to capture full page")
    filename: Optional[str] = Field(default=None, description="Output filename")
    viewport_size: Optional[Tuple[int, int]] = Field(default=None, description="Viewport size (width, height)")
    screenshot_path: Optional[str] = Field(default=None, description="Path to saved screenshot")

    @validator('selector')
    def validate_selector(cls, v):
        """セレクタの形式を検証"""
        if v is not None:
            if not v.strip():
                return None
            # 基本的なセレクタの形式チェック
            if any(char in v for char in '<>"\''):
                raise ValueError("Invalid characters in selector")
        return v

    @validator('url')
    def validate_url(cls, v):
        """URLの形式を検証"""
        try:
            result = urlparse(v)
            if not all([result.scheme, result.netloc]):
                raise ValueError("有効なURLではありません")
            return v
        except Exception as e:
            raise ValueError(f"URLの形式が正しくありません: {e}")

    @validator('viewport_size', pre=True)
    def validate_viewport_size(cls, v):
        """ビューポートサイズを検証し、文字列の場合は変換する"""
        if v is None:
            return None
            
        if isinstance(v, str):
            try:
                width, height = map(int, v.lower().split('x'))
                return (width, height)
            except ValueError:
                raise ValueError("ビューポートサイズの形式が正しくありません。例: '1920x1080'")
                
        if isinstance(v, (list, tuple)) and len(v) == 2:
            width, height = v
            if not all(isinstance(x, int) and x > 0 for x in (width, height)):
                raise ValueError("ビューポートサイズは正の整数である必要があります")
            return (width, height)
            
        raise ValueError("ビューポートサイズは 'widthxheight' 形式の文字列か (width, height) 形式のタプルである必要があります")

    def get_viewport_dict(self) -> Optional[Dict[str, int]]:
        """Playwrightに渡すためのビューポートサイズ辞書を返す"""
        if self.viewport_size is None:
            return None
        width, height = self.viewport_size
        return {"width": width, "height": height}

    @validator('filename')
    def validate_filename(cls, v):
        """ファイル名を検証"""
        if v is not None:
            if not v.endswith('.png'):
                v = f"{v}.png"
            if not all(c.isalnum() or c in '._-' for c in v):
                raise ValueError("ファイル名に使用できない文字が含まれています")
        return v

class CaptureAutomation:
    def __init__(self, session_file_path: str = "browser_session.json") -> None:
        self.session_file = Path(session_file_path)
        
        # セッション保存用ディレクトリの作成
        self.session_file.parent.mkdir(parents=True, exist_ok=True)
    
    def login(self, 
              login_url: str, 
              message: str = "ブラウザが開きました。手動でログインを完了してください。") -> Optional[str]:
        """指定されたURLでウェブサービスにログイン
        ユーザーがブラウザを閉じた後にセッション情報を保存する
        
        Args:
            login_url (str): ログインURL
            message (str): ユーザーに表示するメッセージ
            
        Returns:
            Optional[str]: 保存されたセッションファイルのパス、失敗時はNone
        """
        with sync_playwright() as p:
            browser = self._launch_browser(p)
            
            # コンテキスト作成オプションの準備
            context_options: Dict[str, Any] = {}
            
            # セッション情報があればそれを使用してコンテキストを作成
            if self.session_file.exists():
                context_options["storage_state"] = str(self.session_file)
                context = browser.new_context(**context_options)
                print("以前のセッション情報を読み込みました。")
            else:
                context = browser.new_context()
                print("新しいセッションを開始します。")
            
            page = context.new_page()
            
            # 指定されたログインURLにアクセス
            page.goto(login_url)
            
            print(message)
            print("ログイン後、ブラウザを閉じるとセッション情報が保存されます。")
            
            # ブラウザが閉じられるまで待機
            try:
                # ページが閉じられるまで待機
                page.wait_for_event("close", timeout=0)
            except Exception as e:
                print(f"待機中にエラーが発生しました: {e}")
            
            # セッション情報の保存
            try:
                storage_state = context.storage_state()
                with open(self.session_file, "w") as f:
                    json.dump(storage_state, f)
                print("ブラウザが閉じられました。セッション情報を保存しました。")
            except Exception as e:
                print(f"セッション情報の保存中にエラーが発生しました: {e}")
                return None
            
            try:
                # コンテキストを閉じる（ブラウザも自動的に閉じられる）
                context.close()
            except Exception as e:
                print(f"ブラウザを閉じる処理中にエラーが発生しました: {e}")
            
            return str(self.session_file)
    
    def get_session_file(self) -> Optional[str]:
        """保存されたセッションファイルのパスを返す
        
        Returns:
            Optional[str]: セッションファイルのパス、存在しない場合はNone
        """
        if self.session_file.exists():
            return str(self.session_file)
        return None
        
    def capture(self, 
                capture: Capture,
                screenshots_dir: str = "screenshots") -> str:
        """指定されたURLのスクリーンショットを取得する
        
        Args:
            capture (Capture): キャプチャ情報
            screenshots_dir (str): スクリーンショットを保存するディレクトリパス
            
        Returns:
            str: 保存されたスクリーンショットのパス
        """
        # スクリーンショット保存用ディレクトリの作成
        screenshots_path = Path(screenshots_dir)
        screenshots_path.mkdir(parents=True, exist_ok=True)
        
        with sync_playwright() as p:
            # ブラウザの起動
            browser = self._launch_browser(p)
            
            # コンテキスト作成オプションの準備
            context_options: Dict[str, Any] = {}
            
            # ビューポートサイズが指定されていれば設定
            viewport_dict = capture.get_viewport_dict()
            if viewport_dict:
                context_options["viewport"] = viewport_dict
            
            # セッション情報があればそれを使用してコンテキストを作成
            if self.session_file.exists():
                context_options["storage_state"] = str(self.session_file)
                context = browser.new_context(**context_options)
            else:
                context = browser.new_context(**context_options)
            
            page = context.new_page()
            
            # 指定されたURLに移動
            page.goto(capture.url)
            
            # 指定されたセレクタが表示されるまで待機
            if capture.selector:
                page.wait_for_selector(capture.selector, state="visible")
            
            # 追加の待機時間（ページの動的コンテンツ読み込みのため）
            time.sleep(capture.wait_time)
            
            # ファイル名の生成
            if not capture.filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                capture.filename = f"screenshot_{timestamp}.png"
            
            # パスの生成
            screenshot_path = screenshots_path / capture.filename
            
            # スクリーンショットの取得
            page.screenshot(path=str(screenshot_path), full_page=capture.fullpage)
            
            # 保存されたパスを設定
            capture.screenshot_path = str(screenshot_path)
            
            print(f"スクリーンショットを保存しました: {screenshot_path}")
            
            # ブラウザを閉じる
            browser.close()
            
            return str(screenshot_path)
            
    def captures(self, 
                captures: List[Capture],
                screenshots_dir: str = "screenshots") -> List[Capture]:
        """複数のURLのスクリーンショットを一括で取得する
        
        Args:
            captures (List[Capture]): キャプチャ情報のリスト
            screenshots_dir (str): スクリーンショットを保存するディレクトリパス
            
        Returns:
            List[Capture]: スクリーンショットのパスが設定されたキャプチャ情報のリスト
        """
        # スクリーンショット保存用ディレクトリの作成
        screenshots_path = Path(screenshots_dir)
        screenshots_path.mkdir(parents=True, exist_ok=True)
        
        # 結果のHTMLを生成するためのテンプレート
        html_template = '''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>Screenshot Results</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
            <style>
                body {{ 
                    font-family: 'Segoe UI', system-ui, sans-serif;
                    background-color: #f8f9fa;
                    padding: 2rem;
                }}
                .capture-card {{
                    background: white;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    margin-bottom: 2rem;
                    overflow: hidden;
                }}
                .capture-header {{
                    background: #f1f3f5;
                    padding: 1rem;
                    border-bottom: 1px solid #dee2e6;
                }}
                .capture-content {{
                    padding: 1.5rem;
                }}
                .screenshot {{
                    max-width: 100%;
                    height: auto;
                    border-radius: 4px;
                    margin: 1rem 0;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                }}
                .info-list {{
                    list-style: none;
                    padding: 0;
                }}
                .info-list li {{
                    margin-bottom: 0.5rem;
                    color: #495057;
                }}
                .timestamp {{
                    color: #868e96;
                    font-size: 0.9rem;
                    margin-top: 1rem;
                }}
                .url-link {{
                    color: #228be6;
                    text-decoration: none;
                    word-break: break-all;
                }}
                .url-link:hover {{
                    text-decoration: underline;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1 class="mb-4">Screenshot Results</h1>
                <div class="row">
                    {captures}
                </div>
            </div>
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
        </body>
        </html>
        '''
        
        capture_template = '''
        <div class="col-12 mb-4">
            <div class="capture-card">
                <div class="capture-header">
                    <h2 class="h5 mb-0">
                        <a href="{url}" class="url-link" target="_blank">{url}</a>
                    </h2>
                </div>
                <div class="capture-content">
                    <h3 class="h6 mb-3">Configuration</h3>
                    <ul class="info-list">
                        <li><strong>Wait Time:</strong> {wait_time} seconds</li>
                        <li><strong>Selector:</strong> {selector}</li>
                        <li><strong>Full Page:</strong> {fullpage}</li>
                        <li><strong>Viewport Size:</strong> {viewport_size}</li>
                        <li><strong>Filename:</strong> {filename}</li>
                    </ul>
                    <img class="screenshot" src="{screenshot_path}" alt="Screenshot">
                    <p class="timestamp">Captured at: {timestamp}</p>
                </div>
            </div>
        </div>
        '''
        
        with sync_playwright() as p:
            # ブラウザの起動
            browser = self._launch_browser(p)
            
            capture_results = []
            
            for capture in captures:
                # コンテキスト作成オプションの準備
                context_options: Dict[str, Any] = {}
                
                # ビューポートサイズが指定されていれば設定
                viewport_dict = capture.get_viewport_dict()
                if viewport_dict:
                    context_options["viewport"] = viewport_dict
                
                # セッション情報があればそれを使用してコンテキストを作成
                if self.session_file.exists():
                    context_options["storage_state"] = str(self.session_file)
                    context = browser.new_context(**context_options)
                else:
                    context = browser.new_context(**context_options)
                
                page = context.new_page()
                
                # 指定されたURLに移動
                page.goto(capture.url)
                
                # 指定されたセレクタが表示されるまで待機
                if capture.selector:
                    try:
                        page.wait_for_selector(capture.selector, state="visible", timeout=10000)  # タイムアウトを10秒に設定
                    except Exception as e:
                        print(f"Warning: Selector '{capture.selector}' not found for {capture.url}")
                        print(f"Error details: {e}")
                        # セレクタが見つからなくても続行
                
                # 追加の待機時間（ページの動的コンテンツ読み込みのため）
                time.sleep(capture.wait_time)
                
                # ファイル名の生成
                if not capture.filename:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    capture.filename = f"screenshot_{timestamp}.png"
                
                # パスの生成
                screenshot_path = screenshots_path / capture.filename
                
                # スクリーンショットの取得
                page.screenshot(path=str(screenshot_path), full_page=capture.fullpage)
                
                # 保存されたパスを設定
                capture.screenshot_path = str(screenshot_path)
                
                # キャプチャ結果をリストに追加
                capture_results.append(capture)
                
                print(f"キャプチャを保存しました: {screenshot_path}")
                
                # ページを閉じる（メモリ解放のため）
                page.close()
                context.close()
            
            # すべてのキャプチャが完了したらブラウザを閉じる
            browser.close()
            
            # 結果のHTMLを生成
            captures_html = []
            for capture in capture_results:
                # スクリーンショットの相対パスを生成
                relative_path = f"screenshots/{Path(capture.screenshot_path).name}"
                
                captures_html.append(capture_template.format(
                    url=capture.url,
                    wait_time=capture.wait_time,
                    selector=capture.selector or "なし",
                    fullpage="はい" if capture.fullpage else "いいえ",
                    viewport_size=f"{capture.viewport_size[0]}x{capture.viewport_size[1]}" if capture.viewport_size else "デフォルト",
                    filename=capture.filename,
                    screenshot_path=relative_path,
                    timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ))
            
            # HTMLファイルを保存
            result_html = html_template.format(captures="\n".join(captures_html))
            result_path = Path(".") / "capture_results.html"
            with open(result_path, "w", encoding="utf-8") as f:
                f.write(result_html)
            
            print(f"結果のHTMLを保存しました: {result_path}")
            
            return capture_results

    def _launch_browser(self, playwright):
        """通常のブラウザインスタンスを起動する
        
        Args:
            playwright: Playwrightインスタンス
            
        Returns:
            Browser: 起動されたブラウザインスタンス
        """
        launch_options = {
            "headless": False
        }
        
        return playwright.chromium.launch(**launch_options) 