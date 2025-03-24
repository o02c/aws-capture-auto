import os
import json
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

load_dotenv()

class AWSLogin:
    def __init__(self):
        self.session_file = "data/aws_session.json"
        
        # セッション保存用ディレクトリの作成
        os.makedirs(os.path.dirname(self.session_file), exist_ok=True)
    
    def login(self, login_url):
        """指定されたURLでAWSコンソールにログイン
        ユーザーがブラウザを閉じた後にセッション情報を保存する
        
        Args:
            login_url (str): AWSコンソールのログインURL
            
        Returns:
            str: 保存されたセッションファイルのパス
        """
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()
            
            # 指定されたログインURLにアクセス
            page.goto(login_url)
            
            print("ブラウザが開きました。手動でログインを完了してください。")
            print("ログイン後、ブラウザを閉じるとセッション情報が保存されます。")
            
            # ブラウザが閉じられるまで待機
            try:
                # ページが閉じられるまで待機
                page.wait_for_event("close", timeout=0)
            except:
                # タイムアウトなどのエラーは無視
                pass
            
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
                browser.close()
            except:
                # ブラウザが既に閉じられている場合は無視
                pass
            
            return self.session_file
    
    def get_session_file(self):
        """保存されたセッションファイルのパスを返す"""
        if os.path.exists(self.session_file):
            return self.session_file
        return None 