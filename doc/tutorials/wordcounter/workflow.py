#!/usr/bin/env python
"""Experiment 'exp2' from the Jupyter notebook tutorial.
"""
# pylint: disable=invalid-name,no-self-use

import random

import rflow


def compute_word_freq(input_filepath):
    """Compute word frequency from a input text file.

    Args:
        input_filepath (str): Input text file path.

    Returns:
        Dict[str: int]: Each key is a word, and its
         values are their frequency.
    """

    word_freq = {}

    # Count the words
    with open(input_filepath, 'r') as stream:
        for line in stream:
            for word in line.split():
                word = word.lower()
                word_freq[word] = word_freq.get(word, 0) + 1

    return word_freq


def print_kmost(word_freq, K=5):
    """Prints the K most frequent words.

    Args:
        word_freq (Dict[str: int]): Each key is a word,
         and its values are their frequency.
        K (int): Specify how many words to show.
    """

    ordered_words = sorted(word_freq.items(),
                           key=lambda item: item[1],
                           reverse=True)
    for i, (word, count) in enumerate(ordered_words):
        if i == K:
            break
        print('{}-nth word: "{}" happens {} times'.format(
            i, word, count))


def save_freq(word_freq, output_filepath):
    with open(output_filepath, 'w') as stream:
        for word, cont in word_freq.items():
            stream.write('{} {}\n'.format(word, cont))


def load_freq(input_filepath):
    with open(input_filepath, 'r') as stream:
        word_freq = {}
        for line in stream:
            word, cont = line.split()
            word_freq[word] = int(cont)
    return word_freq


class WordFrequency(rflow.Interface):
    """Compute word frequency from a input text file.
    """

    def evaluate(self, resource, input_resource):
        """Args:

            resource (skrkit.workflow.FSResource): Reentrancy checkpoint.

            input_resource (skrkit.workflow.FSResource): Resource pointing to
                the input text file path.

        Returns:
            Dict[str: int]: Each key is a word, and its values are their
             frequency.
        """

        word_freq = compute_word_freq(input_resource.filepath)
        save_freq(word_freq, resource.filepath)
        return word_freq

    def load(self, resource):
        """Loads the data from previous `evaluate()` call.

        Args:
            resource (skrkit.workflow.FSResource): Reentrancy checkpoint.

        Returns:
            Dict[str: int]: Each key is a word, and its values are their
             frequency.
        """

        return load_freq(resource.filepath)


class PrintKMost(rflow.Interface):
    """Prints the K most frequent words.
    """

    def evaluate(self, word_freq, K):
        """Args:

            word_freq (Dict[str: int]): Each key is a word, and its
             values are their frequency.

            K (int): Specify how many words to show.

        """
        ordered_words = sorted(word_freq.items(),
                               key=lambda item: item[1],
                               reverse=True)
        for i, (word, count) in enumerate(ordered_words):
            if i == K:
                break
            print('{}-nth word: "{}" happens {} times'.format(
                i, word, count))


class RandomText(rflow.Interface):
    """Generates random text.
    """

    def evaluate(self, resource, num_of_words, selected_words):
        """Args:

            resource (shrkit.workflow.FSResource): Recurso apontando
             para o arquivo onde as palavras serão escritas.

            num_of_words (int): How many words to generate.

            selected_words (List[str]): Which words to use.
        """

        with open(resource.filepath, 'w') as file_stream:
            for _ in range(num_of_words):
                random_word = random.sample(selected_words, 1)[0]
                file_stream.write(random_word)
                file_stream.write(' ')

    def load(self):
        """The `load()` method indicates to Shrkit that node is reentrant.  As
        `evaluate()` didn't return anything, we can leave the method
        empty.
        """
        pass


@rflow.graph()
def exp2(g):
    """
    Sample random text counting experiment.

    Args:

        g (:obj:`shrkit.workflow.Graph`): Experiment's initialized DAG.
    """
    g.random_text = RandomText(rflow.FSResource('random-text.txt'))
    with g.random_text as args:
        args.num_of_words = 50
        args.selected_words = [
            'lorem', 'ipsum', 'dolor', 'sit', 'amet',
            'consectetur', 'adipiscing', 'elit', 'vestibulum',
            'non', 'feugiat', 'felis']

    g.word_freq = WordFrequency(rflow.FSResource('random-text-freq.txt'))
    g.word_freq.args.input_resource = g.random_text.resource

    g.kmost_freq = PrintKMost()
    with g.kmost_freq as args:
        args.word_freq = g.word_freq
        args.K = 10
