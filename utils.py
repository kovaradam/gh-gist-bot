from datetime import datetime
from random import randint


md_comment_sign, md_comment_close = '<!---', '-->'


def parse_markdown_comment(text: str):
    content_idx = text.find(md_comment_sign) + len(md_comment_sign)
    content = text[content_idx: len(text)-len(md_comment_close)]
    return content


def create_markdown_comment(text: str):
    return md_comment_sign+text+md_comment_close


def get_random_message(input_messages=None):
    messages = ['idk', 'Sure', 'Need a repro',
                'Anyone got this working?', 'Second this', 'wtf'] if input_messages is None else input_messages
    return messages[randint(0, len(messages)-1)]


def create_markdown_timestamp():
    return f'[//]: # ({datetime.now()})'
