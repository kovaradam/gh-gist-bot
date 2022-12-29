#! /bin/python3
import argparse
import requests
from dotenv import dotenv_values
import time

parser = argparse.ArgumentParser(
    prog='bot.py',
    description='Bot script listening to commands on given gist channel'
)

try:
    github_token = dotenv_values(".env")['GITHUB_TOKEN']
except KeyError:
    github_token = None

parser.add_argument('gistId', help="Github gist id")
parser.add_argument('-v', '--verbose', help="Show logs",
                    action='store_true')
parser.add_argument(
    '-t', '--token', help='Github personal access token, required if not specified in .env file', required=github_token is None)


args = parser.parse_args()

if(github_token is None):
    github_token = args.token

gist_id = args.gistId
gist_url = f'https://api.github.com/gists/{gist_id}'
comments_url = f'{gist_url}/comments'

gist_response = requests.get(gist_url)
gist = gist_response.json()
headers = {"authorization": f'bearer {github_token}'}
state = {"last_update": gist['updated_at']}

try:
    print(f"Channel url: {gist['url']}")
except KeyError:
    print(f'Failed tof fetch gist: {gist_response}')
    exit()


def log(message):
    if not args.verbose:
        return
    print(message)


def get_latest_comments():
    response = requests.get(comments_url, headers=headers)
    comments = response.json()
    print(comments)
    latest = filter(
        lambda comment: comment['updated_at'] > state['last_update'], comments)
    return list(latest)


def get_commands(comments):
    return map(lambda comment: comment['body'], comments)


def post_comment(message):
    response = requests.post(
        comments_url, json={"body": message}, headers=headers)
    print(response)


while True:
    time.sleep(5)
    comments = get_latest_comments()
    print('fetching comments')
    if len(comments) > 0:
        state['last_update'] = comments[-1]['updated_at']
        for command in get_commands(comments):
            log(f'Received command "{command}"')
