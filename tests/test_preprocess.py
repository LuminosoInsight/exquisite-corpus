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


def test_reddit_ignore_post_when_no_score():
    test_json = {'body': 'This is a Reddit comment with no score'}
    output = run_preprocess(preprocess_reddit, test_json)
    assert output == ''


def test_reddit_ignore_post_when_no_body():
    test_json = {'score': 15}
    output = run_preprocess(preprocess_reddit, test_json)
    assert output == ''


def test_reddit_ignore_post_when_score_is_none():
    test_json = {'score': None, 'body': 'A post'}
    output = run_preprocess(preprocess_reddit, test_json)
    assert output == ''


def test_reddit_ignore_post_when_score_less_than_1():
    test_json = {'score': 0, 'body': 'Underrated post'}
    output = run_preprocess(preprocess_reddit, test_json)
    assert output == ''

    test_json = {'score': -10, 'body': 'Meh post'}
    output = run_preprocess(preprocess_reddit, test_json)
    assert output == ''


def test_reddit_ignore_post_when_body_deleted():
    test_json = {'body': '[deleted]', 'score': 15}
    output = run_preprocess(preprocess_reddit, test_json)
    assert output == ''


def test_reddit_ignore_post_from_banned_subreddit():
    test_json = {
        'body': 'Probably a spam comment',
        'score': 15,
        'subreddit': 'amazondeals',
    }
    output = run_preprocess(preprocess_reddit, test_json)
    assert output == ''


def test_reddit_replace_problematic_characters():
    test_json = {
        'body': 'A post with \n a new line and some weird characters \u200b\n',
        'score': 3,
        'subreddit': 'some_subreddit',
    }
    output = run_preprocess(preprocess_reddit, test_json)
    assert output == 'en\tA post with  a new line and some weird characters  \n'


def test_reddit_strip_url_after_stripping_markdown():
    test_json = {
        'body': '**https**://company.com is a url with some emphasis,'
        ' which will be removed',
        'score': 3,
        'subreddit': 'some_subreddit',
    }
    output = run_preprocess(preprocess_reddit, test_json)
    assert output == 'en\t is a url with some emphasis, which will be removed\n'


def test_reddit_ignore_if_no_text_left_after_processing():
    test_json = {
        'body': '**https**://company.com',
        'score': 3,
        'subreddit': 'some_subreddit',
    }
    output = run_preprocess(preprocess_reddit, test_json)
    assert output == ''


def test_reddit_ignore_if_not_confident_in_language_detection():
    test_json = {'body': 'Short text', 'score': 3, 'subreddit': 'some_subreddit'}
    output = run_preprocess(preprocess_reddit, test_json)
    assert output == ''


def test_reddit_write_text_in_language_other_than_english():
    test_json = {
        'body': 'Jag hade tvättat fönstren på våren men nu är de smutsiga igen.',
        'score': 2,
        'subreddit': 'some_subreddit',
    }
    output = run_preprocess(preprocess_reddit, test_json)
    assert (
        output == 'sv\tJag hade tvättat fönstren på våren men nu är de smutsiga igen.\n'
    )


def test_reddit_ignore_english_text_with_score_less_than_2():
    test_json = {
        'body': 'Sample text in English with a score of 1 and length of 58.',
        'score': 1,
        'subreddit': 'some_subreddit',
    }
    output = run_preprocess(preprocess_reddit, test_json)
    assert output == ''


def test_twitter_select_text_after_tab():
    test_str = 'ar\tRT  A long-ish string in which there is a single tab'
    output = run_preprocess(preprocess_twitter, test_str)
    assert output == 'en\tRT  A long-ish string in which there is a single tab\n'


def test_twitter_select_text_with_no_tab():
    test_str = 'A long-ish string in which there are no tabs, not even one.'
    output = run_preprocess(preprocess_twitter, test_str)
    assert output == 'en\tA long-ish string in which there are no tabs, not even one.\n'


def test_twitter_strip_writespace_from_end():
    test_str = 'A long-ish string in which there are multiple newlines\n\n\n\n'
    output = run_preprocess(preprocess_twitter, test_str)
    assert output == 'en\tA long-ish string in which there are multiple newlines\n'


def test_twitter_strip_twitter_handle():
    test_str = (
        'A string with a bunch of Twitter handles in it, such as '
        '@made_up_test_handle1 and @made_up_test_handle2'
    )
    output = run_preprocess(preprocess_twitter, test_str)
    assert (
        output == 'en\tA string with a bunch of Twitter handles in it, such as  and \n'
    )


def test_twitter_remove_url():
    test_str = (
        'A string with a number of urls, such as '
        'http://t.co/somelink as well as '
        'https://t.co/someotherlink'
    )
    output = run_preprocess(preprocess_twitter, test_str)
    assert output == 'en\tA string with a number of urls, such as  as well as \n'


def test_twitter_ignore_if_not_confident_in_language_detection():
    test_str = 'fdmsfkresfjgre defrnefewf wdfmesnfesscvnds sdfwred'
    output = run_preprocess(preprocess_twitter, test_str)
    assert output == ''
