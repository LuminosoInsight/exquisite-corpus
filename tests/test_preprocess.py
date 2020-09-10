import json

import pytest
from io import StringIO

from exquisite_corpus.preprocess import (
    preprocess_reddit_lines,
    preprocess_twitter,
    strip_markdown,
)


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
    'test_object, expected',
    [
        pytest.param(
            'ar\tRT  A long-ish string in which there is a single tab',
            'en\tRT  A long-ish string in which there is a single tab\n',
            id='Select Twitter text after a tab',
        ),
        pytest.param(
            'A long-ish string in which there are no tabs, not even one.',
            'en\tA long-ish string in which there are no tabs, not even one.\n',
            id='Select Twitter text if there are no tabs',
        ),
        pytest.param(
            'A long-ish string in which there are multiple newlines\n\n\n\n',
            'en\tA long-ish string in which there are multiple newlines\n',
            id='Remove whitespace from the end of a tweet',
        ),
        pytest.param(
            (
                'A string with a bunch of Twitter handles in it, such as '
                '@made_up_test_handle1 and @made_up_test_handle2'
            ),
            'en\tA string with a bunch of Twitter handles in it, such as  and \n',
            id='Strip Twitter handles',
        ),
        pytest.param(
            'A string with a number of urls, such as http://t.co/somelink as well as '
            'https://t.co/someotherlink',
            'en\tA string with a number of urls, such as  as well as \n',
            id='Remove urls from tweets',
        ),
        pytest.param(
            'fdmsfkresfjgre defrnefewf wdfmesnfesscvnds sdfwred',
            '',
            id='Ignore a tweet if we are not confident in language detection',
        ),
    ],
)
def test_preprocess_twitter(test_object, expected):
    input_file = [test_object]
    output_file = StringIO()
    preprocess_twitter(input_file, output_file)
    output_file.seek(0)
    assert output_file.read() == expected


@pytest.mark.parametrize(
    'test_object, expected',
    [
        pytest.param(
            {'body': 'This is a Reddit comment with no score'},
            [],
            id='Ignore a Reddit post with no score',
        ),
        pytest.param(
            {'score': 15}, [], id='Ignore a Reddit post with no body'
        ),
        pytest.param(
            {'score': None, 'body': 'A post'},
            [],
            id='Ignore a Reddit post when its score is None',
        ),
        pytest.param(
            {'score': 0, 'body': 'Underrated post'},
            [],
            id='Ignore a Reddit post when its score is less than 1',
        ),
        pytest.param(
            {'body': '[deleted]', 'score': 15},
            [],
            id='Ignore a Reddit post when its body was deleted',
        ),
        pytest.param(
            {
                'body': 'Probably a spam comment',
                'score': 15,
                'subreddit': 'amazondeals',
            },
            [],
            id='Ignore a post from a banned subreddit',
        ),
        pytest.param(
            {
                'body': 'A post with \n a new line and some weird characters \u200b\n',
                'score': 3,
                'subreddit': 'some_subreddit',
            },
            [('en', 'A post with  a new line and some weird characters  ')],
            id='Replace problematic characters in a Reddit post',
        ),
        pytest.param(
            {
                'body': '**https**://company.com is a url with some emphasis,'
                ' which will be removed',
                'score': 3,
                'subreddit': 'some_subreddit',
            },
            [('en', ' is a url with some emphasis, which will be removed')],
            id='Strip url after stripping markdown in a Reddit post',
        ),
        pytest.param(
            {
                'body': '**https**://company.com',
                'score': 3,
                'subreddit': 'some_subreddit',
            },
            [],
            id='Ignore a Reddit post if no text left after preprocessing',
        ),
        pytest.param(
            {'body': 'tooshort', 'score': 3, 'subreddit': 'some_subreddit'},
            [],
            id='Ignore a Reddit post if we are not confident in language detection',
        ),
        pytest.param(
            {
                'body': 'Jag hade tvättat fönstren på våren men nu är de smutsiga igen.',
                'score': 2,
                'subreddit': 'some_subreddit',
            },
            [('sv', 'Jag hade tvättat fönstren på våren men nu är de smutsiga igen.')],
            id='Write Reddit text in a language other than English',
        ),
        pytest.param(
            {
                'body': 'Sample text in English with a score of 1 and length of 58.',
                'score': 1,
                'subreddit': 'some_subreddit',
            },
            [],
            id='Ignore English text with a score less than 2',
        ),
    ],
)
def test_preprocess_reddit(test_object, expected):
    input_lines = [json.dumps(test_object)]
    assert list(preprocess_reddit_lines(input_lines)) == expected
