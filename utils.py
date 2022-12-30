from datetime import datetime
from random import randint


md_comment_sign = '[//]: # ('


def parse_markdown_comment(text: str):
    content_idx = text.find(md_comment_sign) + len(md_comment_sign)
    content = text[content_idx: len(text)-1]
    return content


def create_markdown_comment(text: str):
    return md_comment_sign+text+')'


def get_random_message(input_messages=None):
    messages = ['idk', 'Sure', 'Need a repro',
                'Anyone got this working?', 'Second this', 'wtf'] if input_messages is None else input_messages
    return messages[randint(0, len(messages)-1)]


def get_markdown_timestamp():

    return f'<!-- {datetime.now()} -->'


def get_comment_text(comment: str):
    print(comment.find("/n/n"))
    return comment[0:comment.find('/n/n')]
