import sys
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import ConfigDict

sys.path.append(str(Path(__file__).parent.parent))



def load_yaml_config(file_path: str) -> dict:
    import yaml

    with open(file_path, 'r') as file:
        return yaml.safe_load(file)
    

config_yaml = load_yaml_config('config/tool.yaml')

class Settings(BaseSettings):
    model_arn: str = config_yaml['bedrock']['model_arn']
    provider: str = config_yaml['bedrock']['provider']
    model_id: str = config_yaml['bedrock']['model_id']
    region: str = config_yaml['bedrock']['region']
    runtime: str = config_yaml['bedrock']['runtime']
    endpoint_url: str = config_yaml['bedrock'].get('endpoint_url', '')
    top_p: float = config_yaml['bedrock'].get('top_p', 1.0)
    frequency_penalty: float = config_yaml['bedrock'].get('frequency_penalty', 0.0)
    presence_penalty: float = config_yaml['bedrock'].get('presence_penalty', 0.0)
    aws_access_key_id: str = config_yaml['bedrock'].get('aws_access_key_id', '')
    aws_secret_access_key: str = config_yaml['bedrock'].get('aws_secret_access_key', '')
    aws_session_token: str = config_yaml['bedrock'].get('aws_session_token', '')
    deepgram_api_key: str = config_yaml['deepgram'].get('deepgram_api_key', '')
    daily_api_key: str = config_yaml['daily'].get('daily_api_key', '')
    daily_room_name: str = config_yaml['daily'].get('daily_room_name', '')
    daily_url: str = config_yaml['daily'].get('daily_room_url', '')
    
    model_config = ConfigDict(
        env_prefix='BEDROCK_',
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore'
    )#type: ignore
    
settings = Settings()
    