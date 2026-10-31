"""Character Forge: a beginner-friendly D&D character builder (SRD 5.2 rules).

Run:   python main.py
Tests: python main.py --test

Builds a level-1 hero, runs the Seven Trials quiz and exports a .codex.json file
for Valdur's Heroic Codex in Owlbear Rodeo. See README.md.
"""
import json
import os
import random
import sys

import forge
from forge import ABILITIES, ABILITY_NAMES, SKILLS, SRD, Character
from lucky import clean_lucky, mix, remove_digit, roll_dice
from trials import pick_tags, run_trials

EXPORTS = os.path.join(forge.ROOT, 'exports')
BANK = forge.load_json('trials.json')

# Level-1 spells in the 2024 rules: [cantrips, prepared level-1 spells].
SPELL_COUNTS = {
    'Bard': [2, 4],
    'Cleric': [3, 4],
    'Druid': [2, 4],
    'Paladin': [0, 2],
    'Ranger': [0, 2],
    'Sorcerer': [4, 2],
    'Warlock': [2, 2],
    'Wizard': [3, 4],
}

# One-line explanations shown to beginners before each kind of choice.
HINTS = {
    'skill': 'Skill proficiency: add your Proficiency Bonus (+2) to checks with that skill.',
    'tool': "Tool proficiency: add +2 when you use that tool (e.g. Thieves' Tools to pick a lock).",
    'casting': 'Spellcasting ability: the ability that powers the spells this trait gives you.',
    'feat': 'Feat: a special talent. Its rules are copied into your sheet.',
    'expertise': 'Expertise: your bonus for those skills is doubled (+4 instead of +2).',
}


# ===================================================================
# Input helpers
# ===================================================================

def choose(title, options, auto=False, labels=None):
    """Let the player pick one option by number. Enter (or auto mode) picks at random."""
    if not options:
        raise ValueError('No options available for ' + title)
    if auto:
        return random.choice(options)

    labels = labels or options
    print('\n' + title)
    for number, label in enumerate(labels, 1):
        print(f'  {number}. {label}')

    while True:
        answer = input('Choose a number (Enter = random): ').strip()
        if answer == '':
            picked = random.choice(options)
            label = str(labels[options.index(picked)])
            print('  Randomly picked: ' + label.split(' - ')[0])
            return picked
        if answer.isdecimal() and 1 <= int(answer) <= len(options):
            return options[int(answer) - 1]
        print('Please type a number from 1 to ' + str(len(options)) + '.')


def pick_many(title, options, count, auto=False):
    """Pick `count` different options, one at a time."""
    picked = []
    for number in range(count):
        remaining = [option for option in options if option not in picked]
        picked.append(choose(f'{title} ({number + 1}/{count})', remaining, auto))
    return picked


def ask_text(prompt, default):
    """Ask for a short line of text; Enter keeps the default."""
    value = input(prompt).strip()
    if value == '':
        return default
    return value[:60]


def ask_lucky_number():
    """Return the player's 8-digit lucky number, or None to build the hero by hand."""
    print('\nHow do you want to create your hero?')
    print('  - Random hero: type an 8-digit lucky number '
          '(for example your birth date YYYY-MM-DD).')
    print('  - Build it yourself: press Enter (no random generation; you choose every option).')
    while True:
        text = input('Lucky number, or Enter to build it yourself: ').strip()
        if text == '':
            return None
        lucky = clean_lucky(text)
        if lucky is not None:
            return lucky
        print('Please type exactly 8 digits, like 20010412 or 2001-04-12.')


def lucky_seed(lucky):
    """Roll the five dice, mix them into the lucky number and print every step."""
    rolls = roll_dice()
    print('Dice: d4={}, d6={}, d8={}, d10={}, d20={}'.format(*rolls))
    code, steps = mix(lucky, rolls)
    for step in steps:
        print('  ' + step)
    print(f'Your hero code is {code}. It decides every random choice below.')
    return code


# ===================================================================
# Creation steps
# ===================================================================

def resolve_choice(character, choice, auto, source):
    """Apply one SRD choice. `source` says where it comes from, e.g. 'Tiefling species'."""
    kind = choice['kind']
    count = choice.get('count', 1)
    label = choice['label'] + ' [' + source + ']'
    if not auto and kind in HINTS:
        print('\n' + HINTS[kind])

    if kind == 'skill':
        if choice['from'] == 'any':
            pool = list(SKILLS.values())
        else:
            pool = choice['from']
        pool = [skill for skill in pool if skill not in character.skills]
        if len(pool) < count:   # already know them all: allow any other skill
            for skill in SKILLS.values():
                if skill not in character.skills and skill not in pool:
                    pool.append(skill)
        character.skills += pick_many(label, pool, count, auto)

    elif kind == 'tool':
        pool = [tool for tool in choice['from'] if tool not in character.tools]
        character.tools += pick_many(label, pool, count, auto)

    elif kind == 'option':
        names = [option['name'] for option in choice['options']]
        labels = [option['name'] + ' - ' + option['desc'] for option in choice['options']]
        character.options[choice['label']] = choose(label, names, auto, labels)

    elif kind == 'casting':
        names = [ABILITY_NAMES[ability] for ability in choice['from']]
        ability = choose(label, choice['from'], auto, names)
        character.options[choice['label']] = ABILITY_NAMES[ability]

    elif kind == 'feat':
        add_feat(character, choose(label, choice['from'], auto), auto)

    elif kind == 'expertise':
        character.expertise += pick_many(label + ' (double proficiency)',
                                         character.skills, count, auto)


def add_feat(character, feat, auto):
    """Add an origin feat; the Skilled feat also grants three extra skills."""
    character.feats.append(feat)
    if feat == 'Skilled':
        pool = [skill for skill in SKILLS.values() if skill not in character.skills]
        character.skills += pick_many('Extra skill [Skilled feat]', pool, 3, auto)


def ability_bonus(character, auto):
    """Background ability increases: +2/+1 or +1/+1/+1 among the background's three abilities."""
    allowed = character.background_data()['abilityChoice']
    names = [ABILITY_NAMES[ability] for ability in allowed]
    character.bonus = dict.fromkeys(ABILITIES, 0)

    if auto:   # put +2 and +1 on the abilities the class needs most
        priorities = forge.PRIORITIES[character.cls]
        ranked = sorted(allowed, key=lambda a: priorities.index(a) if a in priorities else 9)
        character.bonus[ranked[0]] = 2
        character.bonus[ranked[1]] = 1
        return

    title = f'Ability increase [{character.background} background] ({", ".join(names)})'
    layout = choose(title, ['+2 / +1', '+1 / +1 / +1'])
    if layout == '+1 / +1 / +1':
        for ability in allowed:
            character.bonus[ability] = 1
    else:
        first = choose('Ability that gets +2', allowed, labels=names)
        rest = [ability for ability in allowed if ability != first]
        second = choose('Ability that gets +1', rest, labels=[ABILITY_NAMES[a] for a in rest])
        character.bonus[first] = 2
        character.bonus[second] = 1


def ability_scores(character, auto):
    """Roll five sets of ability scores and recommend the best one for the class."""
    priorities = forge.PRIORITIES[character.cls]
    sets = []
    for _ in range(5):
        sets.append({ability: forge.roll_ability() for ability in ABILITIES})

    def key_total(index):
        return sum(sets[index][ability] for ability in priorities)

    best = 0
    for index in range(1, 5):
        if key_total(index) > key_total(best):
            best = index

    chosen = best
    if not auto:
        key_names = ', '.join(ABILITY_NAMES[ability] for ability in priorities)
        print('\nFive rolled ability sets (4d6, drop the lowest die).')
        print('Your class relies on: ' + key_names)
        print('Set  ' + ''.join(f'{ability.upper():>5}' for ability in ABILITIES) + '   key total')
        for index, values in enumerate(sets):
            row = f'{index + 1:<5}' + ''.join(f'{values[a]:>5}' for a in ABILITIES)
            mark = '  <- recommended' if index == best else ''
            print(row + f'{key_total(index):>11}' + mark)
        answer = input('Press Enter for the recommended set, or type 1-5: ').strip()
        if answer in ('1', '2', '3', '4', '5'):
            chosen = int(answer) - 1
    character.base = sets[chosen]


def equipment_choice(character, source, data, auto):
    """Choose a starting equipment package (A, B, ...) from the class or background."""
    letters = [option['label'] for option in data['equipment']]
    if auto:   # random heroes take the ready-made gear package
        character.equipment[source] = letters[0]
        return

    labels = []
    for option in data['equipment']:
        items = ', '.join(item['name'] for item in option['items'])
        gear = items + ' + ' if items else ''
        labels.append(f"Option {option['label']}: {gear}{option['gp']} GP")
    title = data['name'] + ' starting equipment'
    character.equipment[source] = choose(title, letters, auto, labels)


def spell_label(spell):
    """Menu text for a spell, e.g. 'Fire Bolt (cantrip, 120 ft., 1d10 fire)'."""
    level = 'cantrip' if spell['level'] == 0 else 'level 1'
    damage = ''
    for part in spell['dmg']:
        damage = f", {part['n']}d{part['d']} {part['type']}"
    return f"{spell['name']} ({level}, {spell['range']}{damage})"


def spell_choice(character, auto):
    """Learn class cantrips and level-1 spells, plus spells from species options."""
    character.spells = []

    species = character.species_data()
    for choice in species['choices']:
        for option in choice.get('options', []):
            if option['name'] == character.options.get(choice['label']):
                character.spells += option.get('spells', [])
    for name, level in species['grants'].get('spells', []):
        if level == 1:
            character.spells.append(name)
    if character.cls == 'Ranger':
        character.spells.append("Hunter's Mark")   # Favored Enemy: always prepared

    if character.cls not in SPELL_COUNTS:
        return
    for level, count in enumerate(SPELL_COUNTS[character.cls]):
        pool = []
        for spell in SRD['spells']:
            if (spell['level'] == level and character.cls in spell['classes']
                    and spell['name'] not in character.spells):
                pool.append(spell)
        labels = [spell_label(spell) for spell in pool]
        title = character.cls + (' cantrip' if level == 0 else ' level-1 spell')
        for number in range(count):
            picked = choose(f'{title} ({number + 1}/{count})', pool, auto, labels)
            index = pool.index(picked)
            pool.pop(index)
            labels.pop(index)
            character.spells.append(picked['name'])


def create_character(name, lucky=None, auto=False, cls=None, species=None, background=None):
    """Run every creation step. cls, species and background can be fixed in advance (tests)."""
    character = Character(name)
    if lucky is not None:
        character.hero_code = lucky_seed(lucky)
        random.seed(character.hero_code)
        auto = True

    class_names = [c['name'] for c in SRD['classes']]
    class_labels = [n + ' - ' + forge.ROLES[n] for n in class_names]
    character.cls = cls or choose('Choose a class (what you do in a fight)',
                                  class_names, auto, class_labels)

    species_names = [s['name'] for s in SRD['species']]
    species_labels = [n + ' - ' + forge.SPECIES_NOTES[n] for n in species_names]
    character.species = species or choose('Choose a species (your people and their gifts)',
                                          species_names, auto, species_labels)

    background_names = [b['name'] for b in SRD['backgrounds']]
    character.background = background or choose(
        'Choose a background (your life before adventuring; '
        'the free SRD 5.2 rules include these four)', background_names, auto)

    data = character.background_data()
    character.skills = list(data['grants'].get('skills', []))
    character.tools = list(data['grants'].get('tools', []))
    add_feat(character, data['feat'], auto)
    for choice in data['choices']:
        resolve_choice(character, choice, auto, character.background + ' background')
    for choice in character.species_data()['choices']:
        resolve_choice(character, choice, auto, character.species + ' species')

    character.languages = ['Common'] + pick_many(
        'Language [every hero knows Common + 2 more]', SRD['languages'], 2, auto)
    ability_bonus(character, auto)
    ability_scores(character, auto)
    for choice in character.class_data()['choices']:
        resolve_choice(character, choice, auto, character.cls + ' class')

    equipment_choice(character, 'class', character.class_data(), auto)
    equipment_choice(character, 'background', data, auto)
    spell_choice(character, auto)
    random.seed()   # back to normal randomness after a lucky-number hero
    return character


def summary(character):
    """A short text overview of the character."""
    line = '=' * 60
    title = f'{character.name} | {character.subtitle()} | {character.background} background'
    darkvision = 'yes' if character.has_darkvision() else 'NO'
    lines = ['', line, title, line,
             f'HP {character.max_hp()}   AC {character.armor_class()}   '
             f'Speed {character.speed()} ft   Darkvision: {darkvision}']

    scores = []
    for ability in ABILITIES:
        scores.append(f'{ability.upper()} {character.score(ability)} ({character.mod(ability):+d})')
    lines.append('  '.join(scores))

    lines.append('Skills: ' + ', '.join(character.skills))
    if character.expertise:
        lines.append('Expertise: ' + ', '.join(character.expertise))
    lines.append('Feats: ' + ', '.join(character.feats))
    for label, value in character.options.items():
        lines.append(f'{label}: {value}')
    weapons = [name for name, _ in character.weapons()]
    lines.append('Weapons: ' + (', '.join(weapons) or 'none'))
    if character.spells:
        lines.append('Spells: ' + ', '.join(character.spells))
    if character.hero_code is not None:
        lines.append(f'Hero code: {character.hero_code}')
    lines.append('Role: ' + forge.ROLES[character.cls])
    if character.trial_results:
        passed = sum(result is True for _, result in character.trial_results)
        lines.append(f'Seven Trials: {passed}/7 passed')
    return '\n'.join(lines)


# ===================================================================
# Main menu
# ===================================================================

def export(character):
    """Save the .codex.json file. Untaken trials are saved as seven [skipped] tips."""
    if not character.trial_results:
        print('Seven Trials not taken: all seven tips are saved as [skipped].')
        character.trial_results = [(tag, None) for tag in pick_tags(character, BANK)]
    print('Saved: ' + forge.export_codex(character, BANK, EXPORTS))
    print('Import it in Owlbear Rodeo: Heroic Codex > ... > Import a sheet file.')


def main():
    print('CHARACTER FORGE - build a D&D hero, pass the Seven Trials, play it in Owlbear Rodeo')
    character = None
    while True:
        print('\n1. Create a new character')
        print('2. View character')
        print('3. Take the Seven Trials')
        print('4. Export .codex.json for Owlbear Rodeo')
        print('0. Quit')
        action = input('Menu: ').strip()
        try:
            if action == '0':
                return
            elif action == '1':
                name = ask_text('Character name (Enter = Unnamed adventurer): ',
                                'Unnamed adventurer')
                character = create_character(name, ask_lucky_number())
                print(summary(character))
                answer = input('\nTake the Seven Trials now? (Enter = yes, n = later): ')
                if answer.strip().lower() != 'n':
                    run_trials(character, BANK)
            elif action not in ('2', '3', '4'):
                print('Please type 0-4.')
            elif character is None:
                print('Create a character first (menu 1).')
            elif action == '2':
                print(summary(character))
            elif action == '3':
                run_trials(character, BANK)
            else:
                export(character)
        except (ValueError, OSError) as error:
            print('Something went wrong: ' + str(error))


# ===================================================================
# Tests (Lab 10 style): python main.py --test
# ===================================================================

def test_rules():
    """Dice, modifiers, AC, HP and tags for two fixed characters."""
    for _ in range(200):
        assert 3 <= forge.roll_ability() <= 18
    assert forge.modifier(8) == -1
    assert forge.modifier(10) == 0
    assert forge.modifier(15) == 2

    # Elf Druid: Leather Armor + Shield with Dex 14 -> AC 11 + 2 + 2 = 15; HP d8 + 1 = 9.
    druid = Character('Test Druid')
    druid.cls, druid.species, druid.background = 'Druid', 'Elf', 'Criminal'
    druid.base = {'str': 8, 'dex': 14, 'con': 12, 'int': 10, 'wis': 15, 'cha': 10}
    assert druid.armor_class() == 15
    assert druid.max_hp() == 9
    assert {'darkvision', 'sleep_immune', 'charm_adv', 'spellcaster'} <= druid.tags()
    assert 'no_darkvision' not in druid.tags()

    # Human Fighter: Chain Mail -> AC 16; HP d10 + 2 = 12.
    fighter = Character('Test Fighter')
    fighter.cls, fighter.species, fighter.background = 'Fighter', 'Human', 'Soldier'
    fighter.base = {'str': 16, 'dex': 10, 'con': 14, 'int': 8, 'wis': 12, 'cha': 10}
    assert fighter.armor_class() == 16
    assert fighter.max_hp() == 12
    assert {'no_darkvision', 'frontline', 'heavy_stealth'} <= fighter.tags()

    for character in (druid, fighter):
        chosen = pick_tags(character, BANK)
        assert len(chosen) == 7 and len(set(chosen)) == 7


def test_lucky_number():
    """The mixing steps and input cleaning in lucky.py."""
    # 12345678 + 3 -> x 2 -> // 5 = 4938272 -> squared;
    # 3 + 2 + 5 + 7 + 20 = 37, so every '7' is removed; then keep the last 8 digits.
    code, steps = mix(12345678, [3, 2, 5, 7, 20])
    squared = str(4938272 ** 2)
    without_sevens = int(''.join(char for char in squared if char != '7'))
    assert code == without_sevens % 100000000
    assert len(steps) == 6
    assert remove_digit(18381, '8') == 131
    assert remove_digit(888, '8') == 0
    assert clean_lucky('2001-04-12') == 20010412
    assert clean_lucky('1234') is None


def test_data_and_exports():
    """Data loading errors, the question bank, and every possible sheet."""
    try:
        forge.load_json('no_such_file.json')
        raise AssertionError('A missing data file was accepted.')
    except forge.DataFileError:
        pass
    for question in BANK.values():
        assert 0 <= question['answer'] < len(question['options'])
        assert question['tip']

    for cls in SRD['classes']:
        for species in SRD['species']:
            for background in SRD['backgrounds']:
                random.seed(cls['name'] + species['name'] + background['name'])
                c = create_character('Auto', auto=True, cls=cls['name'],
                                     species=species['name'], background=background['name'])
                c.trial_results = [(tag, True) for tag in pick_tags(c, BANK)]
                sheet = json.loads(json.dumps(forge.build_sheet(c, BANK)))
                assert set(sheet['skills']) == set(SKILLS)
                assert set(sheet['abilities']) == set(ABILITIES)
                assert all(value in (0, 1, 2) for value in sheet['skills'].values())
                assert sheet['hp']['max'] >= 1 and 5 <= sheet['ac'] <= 22
                assert all(3 <= sheet['abilities'][a]['score'] <= 20 for a in ABILITIES)
                assert 'SEVEN TRIALS' in sheet['notes']
                expected = sum(SPELL_COUNTS.get(c.cls, [0, 0])) + (c.cls == 'Ranger')
                assert len(sheet['spells']) >= expected
                assert len(set(c.spells)) == len(c.spells)


def self_test():
    random.seed(9001)
    test_rules()
    test_lucky_number()
    test_data_and_exports()
    random.seed()
    print('PASS: rules, lucky number, data files and all 432 class/species/background exports.')


if __name__ == '__main__':
    try:
        if '--test' in sys.argv:
            self_test()
        else:
            main()
    except (EOFError, KeyboardInterrupt):
        print('\nGoodbye!')
