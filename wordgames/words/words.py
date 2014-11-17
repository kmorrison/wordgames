import os

from django.utils.functional import cached_property

import config


class WordList(object):

    @cached_property
    def wordlist(self):
        with open(os.path.join(config.BASE_DIR, 'lowerwords.txt')) as word_file:
            return [line for line in word_file]

    @cached_property
    def wordset(self):
        return set(self.wordlist)

    def is_valid_start(self, start):
        return [word for word in self.wordlist if word.startswith(start)]


wordlist = WordList()
