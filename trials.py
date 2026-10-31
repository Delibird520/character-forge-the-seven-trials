"""The Seven Trials: a quiz built from the character's own strengths and weaknesses.

Each tag of the character (see Character.tags in forge.py) has one question in
data/trials.json. Seven tags are picked at random; general rules questions fill
the gap when a character has fewer than seven tags.
"""
import random

# General rules questions, used when a character has fewer than seven own tags.
GENERAL = ['opportunity', 'death_saves', 'advantage', 'help', 'short_rest', 'critical', 'cover']

# (minimum score, title), from best to worst.
TITLES = [
    (7, 'Legend of the Seven Trials'),
    (5, 'Seasoned Adventurer'),
    (3, 'Promising Recruit'),
    (0, 'Brave Newcomer'),
]


def pick_tags(character, bank, count=7):
    """Choose `count` question tags: the character's own tags first, then general ones."""
    own = sorted(tag for tag in character.tags() if tag in bank)
    chosen = random.sample(own, min(count, len(own)))
    fillers = [tag for tag in GENERAL if tag not in chosen]
    chosen += random.sample(fillers, count - len(chosen))
    return chosen


def title(score):
    """The title earned for a score out of 7."""
    for minimum, name in TITLES:
        if score >= minimum:
            return name
    return TITLES[-1][1]


def ask_answer(prompt, options):
    """Return the chosen option index, or None when the player presses Enter to skip."""
    while True:
        answer = input(prompt).strip()
        if answer == '':
            return None
        if answer.isdecimal() and 1 <= int(answer) <= options:
            return int(answer) - 1
        print('Please type a number from 1 to ' + str(options) + '.')


def run_trials(character, bank):
    """Ask seven questions and return the score.

    Each result is stored in character.trial_results as (tag, True / False / None),
    where None means the question was skipped.
    """
    print('\n' + '=' * 60)
    print('THE SEVEN TRIALS of ' + character.name + ' the ' + character.subtitle())
    print("Each question comes from YOUR character's strengths and weaknesses.")
    print('=' * 60)

    character.trial_results = []
    score = 0
    for number, tag in enumerate(pick_tags(character, bank), 1):
        question = bank[tag]
        order = list(range(len(question['options'])))
        random.shuffle(order)   # the correct answer is not always in the same place

        print(f'\nTrial {number}/7: ' + question['q'])
        for position, index in enumerate(order, 1):
            print(f'  {position}. ' + question['options'][index])

        picked = ask_answer('Your answer (Enter = skip): ', len(order))
        if picked is None:
            print('Skipped. The tip is still saved in your sheet.')
            character.trial_results.append((tag, None))
            continue

        correct = order[picked] == question['answer']
        if correct:
            score += 1
            print('Correct!')
        else:
            print('Not quite.')
        print('  Tip: ' + question['tip'])
        character.trial_results.append((tag, correct))

    skipped = 0
    for _, result in character.trial_results:
        if result is None:
            skipped += 1
    print(f'\nYou passed {score}/7 trials ({skipped} skipped). Title earned: {title(score)}')
    print('All seven tips will be saved in the Codex sheet (Notes and "Beginner Guide").')
    return score
