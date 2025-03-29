import argparse
import json
from pathlib import Path
from dotenv import load_dotenv
from capture_automation import CaptureAutomation, Capture
from image_to_excel import ImageToExcelConfig, insert_image_to_excel

load_dotenv()

def load_captures_from_json(json_file: str) -> list[Capture]:
    """JSONファイルからキャプチャ設定を読み込む"""
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    if isinstance(data, list):
        return [Capture(**item) for item in data]
    elif isinstance(data, dict):
        return [Capture(**data)]
    else:
        raise ValueError("Invalid JSON format. Expected an object or array of objects.")

def load_image_configs_from_json(json_file: str) -> list[ImageToExcelConfig]:
    """JSONファイルから画像貼り付け設定を読み込む"""
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    if isinstance(data, list):
        return [ImageToExcelConfig(**item) for item in data]
    elif isinstance(data, dict):
        return [ImageToExcelConfig(**data)]
    else:
        raise ValueError("Invalid JSON format. Expected an object or array of objects.")

def main() -> None:
    parser = argparse.ArgumentParser(description="Capture Automation Tool")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # ログインコマンド
    login_parser = subparsers.add_parser("login", help="Login to web service and save session")
    login_parser.add_argument("url", help="Login URL")
    
    # キャプチャコマンド
    capture_parser = subparsers.add_parser("capture", help="Capture screenshot of specified URL")
    capture_parser.add_argument("url", help="URL to capture")
    capture_parser.add_argument("--wait", type=int, default=5, help="Wait time after page load (seconds)")
    capture_parser.add_argument("--selector", help="CSS selector to wait for")
    capture_parser.add_argument("--filename", help="Output filename")
    capture_parser.add_argument("--no-fullpage", action="store_true", help="Disable full page capture")
    capture_parser.add_argument("--viewport", help="Viewport size (e.g., 1920x1080)")
    
    # 複数URLキャプチャコマンド（URLリスト）
    captures_parser = subparsers.add_parser("captures", help="Capture multiple URLs")
    captures_group = captures_parser.add_mutually_exclusive_group(required=True)
    captures_group.add_argument("--urls", nargs="+", help="URLs to capture")
    captures_group.add_argument("--json", help="JSON file containing capture configurations")
    captures_parser.add_argument("--wait", type=int, default=5, help="Wait time after page load (seconds)")
    captures_parser.add_argument("--selector", help="CSS selector to wait for")
    captures_parser.add_argument("--no-fullpage", action="store_true", help="Disable full page capture")
    captures_parser.add_argument("--viewport", help="Viewport size (e.g., 1920x1080)")

    # Excel画像貼り付けコマンド
    excel_parser = subparsers.add_parser("excel", help="Insert images into Excel")
    excel_parser.add_argument("input_excel", type=Path, help="Input Excel file path")
    excel_parser.add_argument("--output", "-o", type=Path, help="Output Excel file path")
    excel_group = excel_parser.add_mutually_exclusive_group(required=True)
    excel_group.add_argument("--json", help="JSON file containing image configurations")
    excel_group.add_argument("--config", "-c", nargs="+", help="Direct configuration in format: image_path,sheet,cell,width_cm,height_cm")

    # キャプチャ＆Excel貼り付けコマンド
    capture_excel_parser = subparsers.add_parser("capture-excel", 
        help="Capture screenshots and insert them into Excel")
    capture_excel_parser.add_argument("json", help="JSON file containing capture and excel configurations")
    capture_excel_parser.add_argument("input_excel", type=Path, help="Input Excel file path")
    capture_excel_parser.add_argument("--output", "-o", type=Path, help="Output Excel file path")

    args = parser.parse_args()
    
    if args.command == "excel":
        try:
            if args.json:
                # JSONファイルから設定を読み込む
                configs = load_image_configs_from_json(args.json)
            else:
                # コマンドライン引数から設定を作成
                configs = []
                for config_str in args.config:
                    img_path, sheet, cell, width, height = config_str.split(',')
                    configs.append(ImageToExcelConfig(
                        image_path=img_path,
                        sheet_name=int(sheet) if sheet.isdigit() else sheet,
                        cell=cell,
                        width_cm=float(width),
                        height_cm=float(height)
                    ))
            
            output_path = insert_image_to_excel(configs, args.input_excel, args.output)
            print(f"Images inserted successfully. Output saved to: {output_path}")
            
        except (ValueError, json.JSONDecodeError) as e:
            print(f"Error: {e}")
            return
        except FileNotFoundError as e:
            print(f"Error: File not found: {e}")
            return
    
    elif args.command == "login":
        ca = CaptureAutomation()
        session_file = ca.login(
            login_url=args.url
        )
        if session_file:
            print(f"Session information saved: {session_file}")
        
    elif args.command == "capture":
        ca = CaptureAutomation()
        
        try:
            capture = Capture(
                url=args.url,
                wait_time=args.wait,
                selector=args.selector,
                fullpage=not args.no_fullpage,
                filename=args.filename,
                viewport_size=args.viewport
            )
            
            screenshot_path = ca.capture(capture)
            print(f"Screenshot saved: {screenshot_path}")
            
        except ValueError as e:
            print(f"Error: {e}")
            return

    elif args.command == "captures":
        ca = CaptureAutomation()
        
        try:
            if args.json:
                # JSONファイルから設定を読み込む
                captures = load_captures_from_json(args.json)
            else:
                # コマンドライン引数から設定を作成
                captures = [
                    Capture(
                        url=url,
                        wait_time=args.wait,
                        selector=args.selector,
                        fullpage=not args.no_fullpage,
                        viewport_size=args.viewport
                    )
                    for url in args.urls
                ]
            
            results = ca.captures(captures)
            
            for result in results:
                print(f"URL: {result.url}")
                print(f"Saved to: {result.screenshot_path}\n")
            
        except (ValueError, json.JSONDecodeError) as e:
            print(f"Error: {e}")
            return
        except FileNotFoundError:
            print(f"Error: JSON file not found: {args.json}")
            return
        
    elif args.command == "capture-excel":
        try:
            # JSONファイルから設定を読み込む
            with open(args.json, 'r') as f:
                configs = json.load(f)

            # キャプチャ設定のみ先に作成
            captures = [
                Capture(
                    url=config['url'],
                    wait_time=config.get('wait_time', 5),
                    selector=config.get('selector'),
                    fullpage=config.get('fullpage', True),
                    viewport_size=config.get('viewport_size')
                )
                for config in configs
            ]

            # スクリーンショットを取得
            ca = CaptureAutomation()
            capture_results = ca.captures(captures)

            # キャプチャ結果を使ってExcel設定を作成
            excel_configs = [
                ImageToExcelConfig(
                    image_path=result.screenshot_path,
                    sheet_name=configs[i]['excel']['sheet_name'],
                    cell=configs[i]['excel']['cell'],
                    width_cm=configs[i]['excel']['width_cm'],
                    height_cm=configs[i]['excel']['height_cm']
                )
                for i, result in enumerate(capture_results)
            ]

            # Excelに画像を貼り付け
            output_path = insert_image_to_excel(excel_configs, args.input_excel, args.output)
            print(f"処理が完了しました。出力ファイル: {output_path}")

        except (ValueError, json.JSONDecodeError) as e:
            print(f"エラー: {e}")
            return
        except FileNotFoundError as e:
            print(f"エラー: ファイルが見つかりません: {e}")
            return
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 