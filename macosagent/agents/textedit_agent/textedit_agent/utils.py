import time
import string
import shortuuid
import os
from typing import Union
from omegaconf import OmegaConf, DictConfig, ListConfig
from dotenv import load_dotenv


# 加载 .env 文件
# load_dotenv()

CACHE_FOLDER = ".cache"

os.makedirs(CACHE_FOLDER, exist_ok=True)

def get_uuid_builder() -> shortuuid.ShortUUID:
    alphabet = string.ascii_lowercase + string.digits
    su = shortuuid.ShortUUID(alphabet=alphabet)
    return su

def load_config(path) -> Union[DictConfig, ListConfig]:
    
    return OmegaConf.load(path)


uuid_builder = get_uuid_builder()

def gen_random_id():
    return f"{int(time.time()*1000)}_{uuid_builder.random(length=8)}"    
