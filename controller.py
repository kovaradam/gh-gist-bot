#! /bin/python3
import argparse
import sys
import requests
from dotenv import dotenv_values

parser = argparse.ArgumentParser(
    prog='controller.py',
    description='Bot controller script, connect to given gist channel and send commands'
)

try:
    github_token = dotenv_values(".env")['GITHUB_TOKEN']
except KeyError:
    github_token = None

parser.add_argument('gistId', help="Github gist id")
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


def get_comments(latest_only=False):
    comments = requests.get(comments_url).json()
    if latest_only:
        comments = filter(
            lambda comment: comment['updated_at'] > state['last_update'], comments)

    comment_cards = map(lambda comment: f"""
    {comment['created_at']}: {comment['user']['login']}[{comment['user']['id']}]
    "{comment['body']}" """, comments)
    for card in comment_cards:
        print(card)


def post_comment(message):
    response = requests.post(
        comments_url, json={"body": message}, headers=headers)
    state["last_update"] = response.json()['updated_at']
    print(response)


while True:
    print(state["last_update"])
    sys.stdout.write("$ ")
    sys.stdout.flush()
    command = sys.stdin.readline().strip()
    match command:
        case 'comments':
            print('> fetching comments')
            get_comments()
        case 'latest':
            print('> fetching latest comments')
            get_comments(latest_only=True)

        case 'post':
            sys.stdout.write("> write comment: ")
            sys.stdout.flush()
            comment = sys.stdin.readline().strip()
            post_comment(comment)
        case other:
            print('> Unknown command: ' + command)
