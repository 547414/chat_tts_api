import datetime
import hashlib
import logging
import os
from datetime import timedelta
from typing import Dict
from minio import Minio


class BusinessError(Exception):
    def __init__(self, message: str, code: int = 500):
        self.code = code
        self.message = message
        super().__init__(message)


class MinioClient:
    def __init__(self, config: Dict):
        self.__MINIO_DEFAULT_BUCKET_NAME = config["MINIO_DEFAULT_BUCKET_NAME"]
        self.__MINIO_DEFAULT_BUCKET_PATH = config["MINIO_DEFAULT_BUCKET_PATH"]
        self.client = Minio(
            endpoint=config["MINIO_ENDPOINT"],
            access_key=config["MINIO_ACCESS_KEY"],
            secret_key=config["MINIO_SECRET_KEY"],
            secure=config.get("MINIO_SECURE", True)
        )

    def upload_file(self, bucket_name: str, original_name: str, file_path: str):
        object_name = original_name
        self.client.fput_object(bucket_name, object_name, file_path)
        return object_name

    def get_file_url(self, bucket_name: str, object_name: str, expiration: int = 3600):
        time_delta = timedelta(seconds=expiration)
        url = self.client.presigned_get_object(bucket_name, object_name, time_delta)
        return url

    def put_object(self, file_name: str, data, length: int = -1, part_size=10 * 1024 * 1024, bucket_name: str = None,
                   bucket_path: str = None):
        # 默认 bucket 名称和路径
        if not bucket_name:
            bucket_name = self.__MINIO_DEFAULT_BUCKET_NAME
        if not bucket_path:
            bucket_path = self.__MINIO_DEFAULT_BUCKET_PATH

        # 生成当前日期、时间和随机字符串
        now = datetime.datetime.now()
        formatted_date = now.strftime("%Y-%m-%d_%H-%M-%S")
        random_bytes = os.urandom(4)
        random_str = ''.join([format(byte, '02x') for byte in random_bytes])
        combined_str = formatted_date + random_str
        md5_hash = hashlib.md5(combined_str.encode()).hexdigest()

        # 固定部分长度：日期、MD5哈希值和连接符
        fixed_length = len(f"{formatted_date}_{md5_hash}_")

        # 文件路径长度 (bucket_path 和斜杠)
        bucket_path_length = len(f"{bucket_path}/")

        # 计算允许的 file_name 最大长度，确保 total 长度不超过 255
        max_file_name_length = 180 - (fixed_length + bucket_path_length)

        # 裁剪 file_name，如果超过最大长度
        if len(file_name) > max_file_name_length:
            file_name = file_name[:max_file_name_length]

        # 生成 object_name 和完整的 full_object_name
        file_object_name = f"{formatted_date}_{md5_hash}_{file_name}"
        object_name = f"{bucket_path}/{file_object_name}"

        # 上传对象
        res = self.client.put_object(bucket_name=bucket_name, object_name=object_name, data=data, length=length,
                                     part_size=part_size)

        return bucket_name, bucket_path, object_name, file_object_name

    def get_file_binary(self, bucket_name: str, object_name: str):
        """
        获取文件的二进制流
        :param bucket_name: 存储桶名称
        :param object_name: 对象名称
        :return: 文件的二进制流
        """
        try:
            response = self.client.get_object(bucket_name, object_name)
            binary_data = response.read()
            response.close()
            response.release_conn()
            return binary_data
        except Exception as e:
            logging.error(f"Error occurred while fetching binary file: {e}")
            raise BusinessError("获取文件二进制流失败")

