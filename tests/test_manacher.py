from __future__ import annotations

from beacon.manacher import longest_palindrome


class TestLongestPalindrome:
    def test_an_odd_length_palindrome(self):
        # "bab" and "aba" both qualify; the earliest is returned
        assert longest_palindrome("babad") == "bab"

    def test_an_even_length_palindrome(self):
        assert longest_palindrome("cbbd") == "bb"

    def test_a_palindrome_embedded_in_noise(self):
        assert longest_palindrome("forgeeksskeegfor") == "geeksskeeg"

    def test_a_single_character_is_its_own_palindrome(self):
        assert longest_palindrome("a") == "a"

    def test_the_whole_string_when_it_is_a_palindrome(self):
        assert longest_palindrome("racecar") == "racecar"

    def test_the_empty_string_returns_empty(self):
        assert longest_palindrome("") == ""

    def test_no_repeat_returns_a_single_character(self):
        assert len(longest_palindrome("abcde")) == 1
