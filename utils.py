from datetime import datetime
from random import randint


md_comment_sign, md_comment_close = '<!---', '-->'
command_sign, response_sign = '>>', '<<'


def parse_markdown_comment(text: str):
    content_idx = text.find(md_comment_sign) + len(md_comment_sign)
    content = text[content_idx: len(text)-len(md_comment_close)]
    return content


def create_markdown_comment(text: str):
    return md_comment_sign+text+md_comment_close


def create_command(command: str):
    return create_markdown_comment(f' {command_sign}{command}{command_sign} ')


def create_command_response(command: str):
    return create_markdown_comment(f' {response_sign}{command}{response_sign} ')


def parse_command(text: str, response=False):
    sign = command_sign if response == False else response_sign
    comment = parse_markdown_comment(text)
    try:
        return comment[comment.index(sign)+len(sign):comment.rindex(sign)]
    except ValueError:
        return None


def get_random_message(input_messages=None):
    messages = ['idk', 'Sure', 'Need a repro',
                'Anyone got this working?', 'Second this', 'wtf'] if input_messages is None else input_messages
    return messages[randint(0, len(messages)-1)]


def create_markdown_timestamp():
    return f'[//]: # ({datetime.now()})'
