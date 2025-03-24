import argparse
import os
from dotenv import load_dotenv
from aws_login import AWSLogin
from aws_capture import AWSCapture
from aws_resource import AWSResource

load_dotenv()

def main():
    parser = argparse.ArgumentParser(description="AWS自動キャプチャおよびリソース取得ツール")
    subparsers = parser.add_subparsers(dest="command", help="コマンド")
    
    # ログインコマンド
    login_parser = subparsers.add_parser("login", help="AWSコンソールにログインしてセッション情報を保存")
    login_parser.add_argument("url", help="AWSコンソールのログインURL")
    
    # キャプチャコマンド
    capture_parser = subparsers.add_parser("capture", help="AWSコンソールの指定URLをキャプチャ")
    capture_parser.add_argument("url", help="キャプチャするURL")
    capture_parser.add_argument("--wait", type=int, default=5, help="ページ読み込み後の待機時間（秒）")
    capture_parser.add_argument("--selector", help="待機するCSS selector")
    capture_parser.add_argument("--filename", help="保存するファイル名")
    capture_parser.add_argument("--no-fullpage", action="store_true", help="全画面キャプチャしない")
    capture_parser.add_argument("--viewport", help="ビューポートサイズ (例: 1920x1080)")
    
    # リソース取得コマンド
    resource_parser = subparsers.add_parser("resource", help="タグエディタでリソース一覧を取得")
    resource_parser.add_argument("--tag-key", action="append", help="タグキー")
    resource_parser.add_argument("--tag-value", action="append", help="タグ値")
    resource_parser.add_argument("--resource-type", action="append", help="リソースタイプ")
    
    args = parser.parse_args()
    
    if args.command == "login":
        login = AWSLogin()
        session_file = login.login(args.url)
        if session_file:
            print(f"セッション情報を保存しました: {session_file}")
        
    elif args.command == "capture":
        # 最新のセッションファイルを取得
        login = AWSLogin()
        session_file = login.get_session_file()
        
        if not session_file:
            print("セッション情報が見つかりません。先に 'login' コマンドを実行してください。")
            return
        
        capture = AWSCapture(session_file)
        fullpage = not args.no_fullpage
        
        # ビューポートサイズの処理
        viewport_size = None
        if args.viewport:
            try:
                width, height = map(int, args.viewport.split('x'))
                viewport_size = {"width": width, "height": height}
            except ValueError:
                print("ビューポートサイズの形式が正しくありません。例: 1920x1080")
                return
        
        screenshot_path = capture.capture(
            url=args.url,
            wait_time=args.wait,
            selector=args.selector,
            fullpage=fullpage,
            filename=args.filename,
            viewport_size=viewport_size
        )
        print(f"キャプチャを保存しました: {screenshot_path}")
        
    elif args.command == "resource":
        # タグフィルターの作成
        tag_filters = []
        if args.tag_key and args.tag_value:
            for key, value in zip(args.tag_key, args.tag_value):
                tag_filters.append({
                    'Key': key,
                    'Values': [value]
                })
        
        resource = AWSResource()
        resources = resource.get_resources_by_tags(
            tag_filters=tag_filters,
            resource_types=args.resource_type
        )
        
        print(f"{len(resources)}件のリソースが取得されました。")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 