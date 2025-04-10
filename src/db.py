# Using docs https://www.alibabacloud.com/help/en/oss/developer-reference/getting-started-with-oss-sdk-for-python

import oss2
from oss2.credentials import EnvironmentVariableCredentialsProvider
import os
import logging
from typing import Union

# Configure logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class AlibabaCloudOSSStorageDB:
    def __init__(self):
        # Check whether the environment variables are configured
        required_env_vars = ['OSS_ACCESS_KEY_ID', 'OSS_ACCESS_KEY_SECRET']
        for var in required_env_vars:
            if var not in os.environ:
                logging.error(f"Environment variable {var} is not set.")
                raise ValueError(f"Environment variable {var} is not set.")

        # Obtain access credentials from environment variables
        self.auth = oss2.ProviderAuthV4(EnvironmentVariableCredentialsProvider())
        
        # Specify the endpoint and region
        self.endpoint = os.getenv('OSS_ENDPOINT')
        self.region = os.getenv('OSS_REGION')
        self.bucket_name = os.getenv('OSS_BUCKET_NAME')
        
        if not self.bucket_name:
            logging.error("Environment variable OSS_BUCKET_NAME is not set.")
            raise ValueError("Environment variable OSS_BUCKET_NAME is not set.")
        
        self.bucket = oss2.Bucket(self.auth, self.endpoint, self.bucket_name, region=self.region)
        self.bucket.create_bucket(oss2.models.BUCKET_ACL_PUBLIC_READ)
        logging.info(f"Bucket {self.bucket_name} ready for usage")

        logo_file_name = 'MoneyTales.jpg'
        self.bucket.put_object_from_file(logo_file_name, logo_file_name)
        self.logo_url = f"https://{self.bucket_name}.{self.endpoint.replace('https://', '')}/{logo_file_name}"
        logging.info(f"Podcast logo uploaded successfully")
    
    def save_to_file(self, content: Union[str, bytes], filename: str) -> str:
        """
        Save a story to Alibaba Cloud OSS
        
        Args:
            content: The content of the story to save
            filename: The name of the file to save as
            
        Returns:
            The URL of the uploaded file
        """
        try:
            # Upload the content
            if type(content) == str:
                content = content.encode('utf-8')
            
            result = self.bucket.put_object(filename, content)
            logging.info(f"File uploaded successfully, status code: {result.status}")
            
            # Generate the URL
            url = f"https://{self.bucket_name}.{self.endpoint.replace('https://', '')}/{filename}"
            return url
        except oss2.exceptions.OssError as e:
            logging.error(f"Failed to upload file: {e}")
            raise
    
    def get_file(self, filename: str) -> str:
        """
        Retrieve a file from Alibaba Cloud OSS
        
        Args:
            filename: The name of the file to retrieve
            
        Returns:
            The content of the file
        """
        try:
            file_obj = self.bucket.get_object(filename)
            content = file_obj.read().decode('utf-8')
            logging.info(f"File retrieved successfully: {filename}")
            return content
        except oss2.exceptions.OssError as e:
            logging.error(f"Failed to retrieve file: {e}")
            raise

    def get_file_url(self, filename: str) -> str:
        signed_url = self.bucket.sign_url('GET', filename, 0)
        permanent_url = signed_url.split('?')[0]  # Remove the query parameters
        return permanent_url
    
    def list_files(self, prefix: str = '') -> list:
        """
        List all files in the bucket
        
        Args:
            prefix: The prefix to filter stories by
            
        Returns:
            List of filenames
        """
        try:
            stories = []
            for obj in oss2.ObjectIterator(self.bucket, prefix=prefix):
                stories.append(obj.key)
            return stories
        except oss2.exceptions.OssError as e:
            logging.error(f"Failed to list stories: {e}")
            raise
    
    def delete_file(self, filename: str) -> None:
        """
        Delete a file from Alibaba Cloud OSS
        
        Args:
            filename: The name of the file to delete
        """
        try:
            self.bucket.delete_object(filename)
            logging.info(f"File deleted successfully: {filename}")
        except oss2.exceptions.OssError as e:
            logging.error(f"Failed to delete file: {e}")
            raise 