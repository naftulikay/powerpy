#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import re
import string


class base36(object):

    matcher = re.compile(r'^([a-z0-9]+)$', re.I)

    alphabet = string.digits + string.lowercase

    @classmethod
    def encode(cls, value):
        """
        Converts a number into a base36 string.

        Arguments:
            value: A number.
        """
        if not isinstance(value, (int, long)):
            raise TypeError("Value for decoding must be an integer or a long.")

        result = ''
        sign = ''

        if value < 0:
            sign = '-'
            value = abs(value)

        if 0 <= value < len(cls.alphabet):
            return sign + cls.alphabet[value]

        while value != 0:
            value, i = divmod(value, len(cls.alphabet))
            result = cls.alphabet[i] + result

        return result

    @classmethod
    def decode(cls, value):
        """
        Converts a base-36 string into a number.

        Arguments:
            value: A base36 string.
        """
        if not base36.matcher.match(value):
            raise ValueError("Input value '{value}' is not a base36 string.".format(value=value))

        return int(value, 36)
