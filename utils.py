from random import randint


md_comment_sign = '[//]: # ('


def parse_markdown_comment(text: str):
    content_idx = text.find(md_comment_sign) + len(md_comment_sign)
    content = text[content_idx: len(text)-1]
    return content


def create_markdown_comment(text: str):
    return md_comment_sign+text+')'


def get_random_message():
    messages = ['idk', 'Sure', 'Need a repro',
                'Anyone got this working?', 'Second this', 'wtf']
    return messages[randint(0, len(messages)-1)]
