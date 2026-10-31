"""Lucky-number generation: mix the player's 8-digit lucky number with five dice.

The result, the "hero code", is used as the random seed for a lucky-number hero.
Only course material is used: + * // ** % and str()/int() (Lab 2), lists (Lab 4),
for loops (Lab 5) and recursion (Lab 11).
"""
import random

DICE = [4, 6, 8, 10, 20]   # the five common dice: d4, d6, d8, d10, d20


def roll_dice():
    """Roll every die in DICE once and return the results as a list."""
    rolls = []
    for sides in DICE:
        rolls.append(random.randint(1, sides))
    return rolls


def remove_digit(number, digit):
    """Return number with every copy of one digit removed, e.g. remove_digit(18381, '8') -> 131."""
    return int(strip_digit(str(number), digit) or '0')


def strip_digit(text, digit):
    """Remove every copy of digit from text, recursively (Lab 11).

    Check the first character, then repeat the same work on the rest of the text.
    """
    if text == '':   # base case: nothing left to check
        return ''
    rest = strip_digit(text[1:], digit)
    if text[0] == digit:
        return rest
    return text[0] + rest


def mix(lucky, rolls):
    """Mix the lucky number with the five rolls.

    Returns (hero code, steps), where steps is a list of printable lines.
    """
    d4, d6, d8, d10, d20 = rolls
    steps = []

    # Step 1: add the d4
    value = lucky + d4
    steps.append(f'{lucky} + {d4} (d4) = {value}')

    # Step 2: multiply by the d6
    old = value
    value = value * d6
    steps.append(f'{old} x {d6} (d6) = {value}')

    # Step 3: floor-divide by the d8 (the result stays a whole number)
    old = value
    value = value // d8
    steps.append(f'{old} // {d8} (d8) = {value}')

    # Step 4: square
    old = value
    value = value ** 2
    steps.append(f'{old} squared = {value}')

    # Step 5: remove every copy of the ones digit of the five dice's total
    total = d4 + d6 + d8 + d10 + d20
    digit = str(total % 10)
    value = remove_digit(value, digit)
    steps.append(f'remove every "{digit}" ({d4}+{d6}+{d8}+{d10}+{d20} = {total}) -> {value}')

    # Step 6: keep the last eight digits
    code = value % 100000000
    steps.append(f'last 8 digits -> {code}')
    return code, steps


def clean_lucky(text):
    """Accept '20010412' or '2001-04-12'. Return the 8-digit number, or None if invalid."""
    digits = ''
    for char in text:
        if char != '-' and char != ' ':
            digits = digits + char
    if len(digits) == 8 and digits.isdecimal():
        return int(digits)
    return None
