import json

import pytest
from io import StringIO

from exquisite_corpus.preprocess import (
    preprocess_reddit,
    preprocess_twitter,
    strip_markdown,
)


def run_preprocess(func, test_obj):
    if isinstance(test_obj, dict):
        test_obj = json.dumps(test_obj)
    input_file = [test_obj]
    output_file = StringIO()
    func(input_file, output_file)
    output_file.seek(0)
    result = output_file.read()
    return result


@pytest.mark.parametrize(
    'text, expected',
    [
        pytest.param(
            "Don't blame me for that pic, blame [this site](http://url.com/)",
            "Don't blame me for that pic, blame this site",
            id='strip down markdown url',
        ),
        pytest.param(
            "Some [[url]](http://url.com/)", 'Some [url]', id='strip url with brackets'
        ),
        pytest.param(
            '_This_ is *important* and ~this~ is too.',
            'This is important and this is too.',
            id='strip markdown empasis characters',
        ),
        pytest.param(
            (
                '> This line starts with ">"\n# This one starts with "#"\n* This'
                ' one starts with an asterisk\n- This one starts with "-"\n And'
                ' this one with a space.'
            ),
            (
                'This line starts with ">" This one starts with "#" This'
                ' one starts with an asterisk This one starts with "-"'
                ' And this one with a space.'
            ),
            id='remove markdown from a start of line',
        ),
    ],
)
def test_strip_markdown(text, expected):
    assert strip_markdown(text) == expected


@pytest.mark.parametrize(
    'test_object, expected, func',
    [
        pytest.param(
            {'body': 'This is a Reddit comment with no score'},
            '',
            preprocess_reddit,
            id='Ignore a Reddit post with no score',
        ),
        pytest.param(
            {'score': 15}, '', preprocess_reddit, id='Ignore a Reddit post with no body'
        ),
        pytest.param(
            {'score': None, 'body': 'A post'},
            '',
            preprocess_reddit,
            id='Ignore a Reddit post when its score is None',
        ),
        pytest.param(
            {'score': 0, 'body': 'Underrated post'},
            '',
            preprocess_reddit,
            id='Ignore a Reddit post when its score is less than 1',
        ),
        pytest.param(
            {'body': '[deleted]', 'score': 15},
            '',
            preprocess_reddit,
            id='Ignore a Reddit post when its body was deleted',
        ),
        pytest.param(
            {
                'body': 'Probably a spam comment',
                'score': 15,
                'subreddit': 'amazondeals',
            },
            '',
            preprocess_reddit,
            id='Ignore a post from a banned subreddit',
        ),
        pytest.param(
            {
                'body': 'A post with \n a new line and some weird characters \u200b\n',
                'score': 3,
                'subreddit': 'some_subreddit',
            },
            'en\tA post with  a new line and some weird characters  \n',
            preprocess_reddit,
            id='Replace problematic characters in a Reddit post',
        ),
        pytest.param(
            {
                'body': '**https**://company.com is a url with some emphasis,'
                ' which will be removed',
                'score': 3,
                'subreddit': 'some_subreddit',
            },
            'en\t is a url with some emphasis, which will be removed\n',
            preprocess_reddit,
            id='Strip url after stripping markdown in a Reddit post',
        ),
        pytest.param(
            {
                'body': '**https**://company.com',
                'score': 3,
                'subreddit': 'some_subreddit',
            },
            '',
            preprocess_reddit,
            id='Ignore a Reddit post if no text left after preprocessing',
        ),
        pytest.param(
            {'body': 'Short text', 'score': 3, 'subreddit': 'some_subreddit'},
            '',
            preprocess_reddit,
            id='Ignore a Reddit post if we are not confident in language detection',
        ),
        pytest.param(
            {
                'body': 'Jag hade tvättat fönstren på våren men nu är de smutsiga igen.',
                'score': 2,
                'subreddit': 'some_subreddit',
            },
            'sv\tJag hade tvättat fönstren på våren men nu är de smutsiga igen.\n',
            preprocess_reddit,
            id='Write Reddit text in a language other than English',
        ),
        pytest.param(
            {
                'body': 'Sample text in English with a score of 1 and length of 58.',
                'score': 1,
                'subreddit': 'some_subreddit',
            },
            '',
            preprocess_reddit,
            id='Ignore English text with a score less than 2',
        ),
        pytest.param(
            'ar\tRT  A long-ish string in which there is a single tab',
            'en\tRT  A long-ish string in which there is a single tab\n',
            preprocess_twitter,
            id='Select Twitter text after a tab',
        ),
        pytest.param(
            'A long-ish string in which there are no tabs, not even one.',
            'en\tA long-ish string in which there are no tabs, not even one.\n',
            preprocess_twitter,
            id='Select Twitter text if there are no tabs',
        ),
        pytest.param(
            'A long-ish string in which there are multiple newlines\n\n\n\n',
            'en\tA long-ish string in which there are multiple newlines\n',
            preprocess_twitter,
            id='Remove whitespace from the end of a tweet',
        ),
        pytest.param(
            (
                'A string with a bunch of Twitter handles in it, such as '
                '@made_up_test_handle1 and @made_up_test_handle2'
            ),
            'en\tA string with a bunch of Twitter handles in it, such as  and \n',
            preprocess_twitter,
            id='Strip Twitter handles',
        ),
        pytest.param(
            'A string with a number of urls, such as http://t.co/somelink as well as '
            'https://t.co/someotherlink',
            'en\tA string with a number of urls, such as  as well as \n',
            preprocess_twitter,
            id='Remove urls from tweets',
        ),
        pytest.param(
            'fdmsfkresfjgre defrnefewf wdfmesnfesscvnds sdfwred',
            '',
            preprocess_twitter,
            id='Ignore a tweet if we are not confident in language detection'
        )
    ],
)
def test_preprocess(test_object, expected, func):
    assert run_preprocess(func, test_object) == expected
