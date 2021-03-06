import argparse

import nltk
import nltk.sentiment.vader
import pandas
from matplotlib import pyplot

from models.tweets.preprocessed_tweet import PreprocessedTweet


class SentimentAnalyzer:
    def __init__(self):
        self.sid = nltk.sentiment.vader.SentimentIntensityAnalyzer()


def sentiment_analysis(sentiment_analyzer: SentimentAnalyzer, tweet: PreprocessedTweet) -> dict:
    assert tweet
    polarity_scores = sentiment_analyzer.sid.polarity_scores(tweet.text)
    return {'tweet': tweet, 'polarity_scores': polarity_scores}


def analyze_tweets(dataset_path: str, limit=None) -> list:
    analysed_tweets = []
    sentiment_analyzer = SentimentAnalyzer()
    dataset = pandas.read_csv(dataset_path, delimiter=' ', quotechar='|')
    for row in dataset.iterrows():
        if limit and row[0] >= limit:
            break
        preprocessed_tweet = PreprocessedTweet(text=row[1]['Text'],
                                               timestamp_ms=row[1]['Timestamp'])
        # Ignore tweets that are referring to another tweet
        if 'https://t.co' in preprocessed_tweet.text:
            continue

        print('Analyzing tweet #{0}'.format(row[0]))
        analysed_tweet = sentiment_analysis(sentiment_analyzer, preprocessed_tweet)
        analysed_tweets.append(analysed_tweet)

    return analysed_tweets


def is_tweet_negative(analysed_tweet: dict) -> bool:
    return analysed_tweet['polarity_scores']['neg'] > 0\
           and analysed_tweet['polarity_scores']['neg'] > analysed_tweet['polarity_scores']['pos']


def is_tweet_positive(analysed_tweet: dict) -> bool:
    return analysed_tweet['polarity_scores']['pos'] > 0 \
           and analysed_tweet['polarity_scores']['pos'] > analysed_tweet['polarity_scores']['neg']


def is_tweet_neutral(analysed_tweet: dict) -> bool:
    return analysed_tweet['polarity_scores']['neu'] > 0\
           and analysed_tweet['polarity_scores']['neu'] > analysed_tweet['polarity_scores']['neg']\
           and analysed_tweet['polarity_scores']['neu'] > analysed_tweet['polarity_scores']['pos']


def classify_tweets(analysed_tweets: list) -> tuple:
    """
    Creates a tuple of three lists: positive, negative and neutral tweets from list of analysed_tweets.
    Suggested use:
        positive_tweets, negative_tweets, neutral_tweets = classify_tweets(analysed_tweets)
    :param analysed_tweets: list of dicts with 'polarity_scores' field
    :return: tuple of three lists - ([positive], [negative], [neutral])
    """
    classified_tweets = ([], [], [])
    for t in analysed_tweets:
        if is_tweet_positive(t):
            classified_tweets[0].append(t)
        if is_tweet_negative(t):
            classified_tweets[1].append(t)
        if is_tweet_neutral(t):
            classified_tweets[2].append(t)

    return classified_tweets


def print_overall_metrics(analysed_tweets: list, positive_tweets: list, negative_tweets: list):
    # Overall metrics
    positive_tweets_ratio = (len(positive_tweets) / len(analysed_tweets)) * 100
    negative_tweets_ratio = (len(negative_tweets) / len(analysed_tweets)) * 100

    print('Positive tweets ratio: {0}%'.format(positive_tweets_ratio))
    print('Negative tweets ratio: {0}%'.format(negative_tweets_ratio))

    positive_sentiment_score = sum([x['polarity_scores']['pos'] for x in positive_tweets])
    negative_sentiment_score = sum([x['polarity_scores']['neg'] for x in negative_tweets])

    print('Positive sentiment score: {0}'.format(positive_sentiment_score))
    print('Negative sentiment score: {0}'.format(negative_sentiment_score))

    print('Positive sentiment score percentage: {0}'.format(positive_sentiment_score /
                                                            (positive_sentiment_score + negative_sentiment_score)
                                                            * 100))
    print('Negative sentiment score percentage: {0}'.format(negative_sentiment_score /
                                                            (positive_sentiment_score + negative_sentiment_score)
                                                            * 100))

    print('Analysed tweets: {0}'.format(len(analysed_tweets)))
    print('Positive tweets: {0}'.format(len(positive_tweets)))
    print('Negative tweets: {0}'.format(len(negative_tweets)))


def show_polarity_histogram(positive_tweets: list, negative_tweets: list):
    assert positive_tweets
    assert negative_tweets

    # Positive tweets histogram
    pos_scores = [pos['polarity_scores']['pos'] for pos in positive_tweets]
    pyplot.hist(pos_scores, 20, alpha=0.5, color='green', label='positive')

    # Negative tweets histogram
    neg_scores = [neg['polarity_scores']['neg'] for neg in negative_tweets]
    pyplot.hist(neg_scores, 20, alpha=0.5, color='red', label='negative')

    pyplot.legend()

    pyplot.show()


def download_required_corpora():
    nltk.download(info_or_id="vader_lexicon")


def parse_args():
    parser = argparse.ArgumentParser(description='Perform sentiment analysis on given dataset of tweets.')
    parser.add_argument('-d', '--dataset-path', required=True,
                        type=str, help='Path to dataset CSV file.')
    parser.add_argument('-l', '--limit', type=int, required=False,
                        help='Limit number of items to analyze.')
    parser.add_argument('-p', '--plot', action='store_true')
    return parser.parse_args()


def main():
    args = parse_args()
    download_required_corpora()

    analysed_tweets = analyze_tweets(args.dataset_path, args.limit)
    positive_tweets, negative_tweets, neutral_tweets = classify_tweets(analysed_tweets)

    # Negative tweets
    print('\nTop 10 negative tweets:')
    for neg in sorted(negative_tweets, key=lambda x: x['polarity_scores']['neg'])[-10:]:
        print('N score: {0}, {1}'.format(neg['polarity_scores']['neg'], neg['tweet'].text))

    # Positive tweets
    print('\nTop 10 positive tweets:')
    for pos in sorted(positive_tweets, key=lambda x: x['polarity_scores']['pos'])[-10:]:
        print('Positive score: {0}, {1}'.format(pos['polarity_scores']['pos'], pos['tweet'].text))

    # neutral tweets
    print('\nTop 10 neutral tweets:')
    for neu in sorted(neutral_tweets, key=lambda x: x['polarity_scores']['neu'])[-10:]:
        print('Neutral score: {0}, {1}'.format(neu['polarity_scores']['neu'], neu['tweet'].text))

    print_overall_metrics(analysed_tweets, positive_tweets, negative_tweets)

    if args.plot:
        show_polarity_histogram(positive_tweets, negative_tweets)


if __name__ == '__main__':
    main()
