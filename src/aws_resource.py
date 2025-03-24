import os
import json
import boto3
from dotenv import load_dotenv

load_dotenv()

class AWSResource:
    def __init__(self):
        self.aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.region = os.getenv("AWS_REGION", "ap-northeast-1")
        self.resources_dir = "data/resources"
        
        # リソース情報保存用ディレクトリの作成
        os.makedirs(self.resources_dir, exist_ok=True)
    
    def get_resource_groups_tagging_api_client(self):
        """ResourceGroupsTaggingAPIのクライアントを取得する"""
        session = boto3.Session(
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            region_name=self.region
        )
        return session.client('resourcegroupstaggingapi')
    
    def get_resources_by_tags(self, tag_filters=None, resource_types=None, save_to_file=True):
        """タグフィルターに一致するリソースを取得する
        
        Args:
            tag_filters (list): タグフィルターのリスト
                例: [{'Key': 'Environment', 'Values': ['Production']}]
            resource_types (list): リソースタイプのリスト
                例: ['ec2:instance', 's3:bucket']
            save_to_file (bool): 結果をファイルに保存するかどうか
            
        Returns:
            list: リソースのリスト
        """
        client = self.get_resource_groups_tagging_api_client()
        
        # デフォルト値の設定
        if tag_filters is None:
            tag_filters = []
        
        # API呼び出しのパラメータを準備
        params = {
            'TagFilters': tag_filters,
        }
        
        if resource_types:
            params['ResourceTypeFilters'] = resource_types
        
        # リソースの取得
        resources = []
        paginator = client.get_paginator('get_resources')
        
        try:
            for page in paginator.paginate(**params):
                resources.extend(page['ResourceTagMappingList'])
            
            print(f"{len(resources)}件のリソースが見つかりました。")
            
            # 結果をファイルに保存
            if save_to_file and resources:
                file_path = os.path.join(self.resources_dir, "aws_resources.json")
                with open(file_path, "w") as f:
                    json.dump(resources, f, indent=2)
                print(f"リソース情報を保存しました: {file_path}")
            
            return resources
            
        except Exception as e:
            print(f"リソース情報の取得中にエラーが発生しました: {str(e)}")
            return [] 