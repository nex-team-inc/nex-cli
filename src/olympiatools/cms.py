import click
import os
import requests
from tqdm import tqdm
from tqdm.utils import CallbackIOWrapper

@click.group()
@click.option("--production", is_flag=True)
def cli(production):
    """PlayOS CMS environment"""
    global API_URL
    API_URL = "https://cms.x.poseidon.npg.games/api" if production else "https://cms.dev.poseidon.npg.games/api"

@click.command("upload")
@click.argument("file")
def upload(file):
    print(API_URL)

    file_size = os.stat(file).st_size

    with open(file, 'rb') as file:
        with tqdm(total=file_size, unit='B', unit_scale=True, desc='Uploading', leave=True) as progress_bar:
            response = requests.post(API_URL + "/upload", files={'file': file}, stream=True)

            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    progress_bar.update(len(chunk))

            if response.status_code != 200:
                print(f'File upload failed: {response.status_code}')
    
    # Check https://gist.github.com/yejianye/3b08730d4ed31ae18c7d

    # file_size = os.stat(file).st_size
    # with open(file, 'rb') as f:
    #     with tqdm(total=file_size, unit="B", unit_scale=True, unit_divisor=1024) as t:
    #         wrapped_file = CallbackIOWrapper(t.update, f, "read")
    #         response = requests.post(API_URL + "/upload")
    #         # response = requests.post(API_URL + "/upload", files={'file': wrapped_file})
    #         if response.status_code != 200:
    #             print(f'File upload failed: {response.status_code}')

cli.add_command(upload)