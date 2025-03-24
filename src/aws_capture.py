import os
import time
from datetime import datetime
from playwright.sync_api import sync_playwright

class AWSCapture:
    def __init__(self, session_file=None):
        self.session_file = session_file
        self.screenshots_dir = "data/screenshots"
        
        # スクリーンショット保存用ディレクトリの作成
        os.makedirs(self.screenshots_dir, exist_ok=True)
    
    def capture(self, url, wait_time=5, selector=None, fullpage=True, filename=None, viewport_size=None):
        """指定されたURLのスクリーンショットを取得する
        
        Args:
            url (str): キャプチャするAWSコンソールのURL
            wait_time (int): ページ読み込み後の待機時間（秒）
            selector (str): 特定の要素が表示されるまで待機するCSS selector
            fullpage (bool): 全画面キャプチャするかどうか
            filename (str): 保存するファイル名（指定がなければタイムスタンプで生成）
            viewport_size (dict): ブラウザのビューポートサイズ（例: {"width": 1280, "height": 720}）
            
        Returns:
            str: 保存されたスクリーンショットのパス
        """
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            
            # コンテキスト作成オプションの準備
            context_options = {}
            
            # ビューポートサイズが指定されていれば設定
            if viewport_size:
                context_options["viewport"] = viewport_size
            
            # セッション情報があればそれを使用してコンテキストを作成
            if self.session_file and os.path.exists(self.session_file):
                context_options["storage_state"] = self.session_file
                context = browser.new_context(**context_options)
            else:
                context = browser.new_context(**context_options)
            
            page = context.new_page()
            
            # 指定されたURLに移動
            page.goto(url)
            
            # 指定されたセレクタが表示されるまで待機
            if selector:
                page.wait_for_selector(selector, state="visible")
            
            # 追加の待機時間（ページの動的コンテンツ読み込みのため）
            time.sleep(wait_time)
            
            # ファイル名の生成
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"aws_capture_{timestamp}.png"
            
            # パスの生成
            screenshot_path = os.path.join(self.screenshots_dir, filename)
            
            # スクリーンショットの取得
            page.screenshot(path=screenshot_path, full_page=fullpage)
            
            print(f"スクリーンショットを保存しました: {screenshot_path}")
            
            # ブラウザを閉じる
            browser.close()
            
            return screenshot_path 