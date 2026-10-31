"""Character model, rule calculations and the .codex.json export.

All rule data is read from data/srd52.json (SRD 5.2, CC-BY-4.0).
The export follows the sheet format of Valdur's Heroic Codex (schema version 1).
"""
import json
import os
import random
import re
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.abspath(__file__))


# ===================================================================
# Constants
# ===================================================================

ABILITIES = ['str', 'dex', 'con', 'int', 'wis', 'cha']

ABILITY_NAMES = {
    'str': 'Strength',
    'dex': 'Dexterity',
    'con': 'Constitution',
    'int': 'Intelligence',
    'wis': 'Wisdom',
    'cha': 'Charisma',
}

# Skill keys used by the Codex, mapped to their full names.
SKILLS = {
    'acrobatics': 'Acrobatics',
    'animal': 'Animal Handling',
    'arcana': 'Arcana',
    'athletics': 'Athletics',
    'deception': 'Deception',
    'history': 'History',
    'insight': 'Insight',
    'intimidation': 'Intimidation',
    'investigation': 'Investigation',
    'medicine': 'Medicine',
    'nature': 'Nature',
    'perception': 'Perception',
    'performance': 'Performance',
    'persuasion': 'Persuasion',
    'religion': 'Religion',
    'sleight': 'Sleight of Hand',
    'stealth': 'Stealth',
    'survival': 'Survival',
}

# Project choice (not an official rule): the three abilities each class relies on most.
PRIORITIES = {
    'Barbarian': ['str', 'con', 'dex'],
    'Bard': ['cha', 'dex', 'con'],
    'Cleric': ['wis', 'con', 'str'],
    'Druid': ['wis', 'con', 'dex'],
    'Fighter': ['str', 'con', 'dex'],
    'Monk': ['dex', 'wis', 'con'],
    'Paladin': ['str', 'cha', 'con'],
    'Ranger': ['dex', 'wis', 'con'],
    'Rogue': ['dex', 'con', 'wis'],
    'Sorcerer': ['cha', 'con', 'dex'],
    'Warlock': ['cha', 'con', 'dex'],
    'Wizard': ['int', 'con', 'dex'],
}

# One-line class descriptions for beginners.
ROLES = {
    'Barbarian': 'Front line: huge Hit Points, Rage to hit hard and shrug off blows.',
    'Bard': 'Support caster: inspires allies, talks the party out of trouble.',
    'Cleric': 'Healer and armored caster: keeps the party alive.',
    'Druid': 'Nature caster: healing, control spells, later turns into beasts.',
    'Fighter': 'Front line: best armor and weapons, very forgiving for beginners.',
    'Monk': 'Fast skirmisher: unarmed strikes, quick in and out of melee.',
    'Paladin': 'Armored front line with healing hands and holy spells.',
    'Ranger': 'Archer and scout: strong at range, good in the wild.',
    'Rogue': 'Sneaky skirmisher: Sneak Attack, skills, picks locks.',
    'Sorcerer': 'Back-line blaster: innate magic, few Hit Points.',
    'Warlock': 'Back-line caster: few spell slots that return on a Short Rest.',
    'Wizard': 'Back-line scholar: the biggest spell list, the fewest Hit Points.',
}

# One-line species descriptions for beginners.
SPECIES_NOTES = {
    'Dragonborn': 'Breath Weapon, resists one damage type, Darkvision.',
    'Dwarf': 'Extra HP, resists Poison, senses through stone, Darkvision.',
    'Elf': "Magic can't make you sleep, hard to Charm, keen senses, Darkvision.",
    'Gnome': 'Advantage on Int/Wis/Cha saves against magic, Darkvision.',
    'Goliath': 'Big and strong, giant-ancestry power, speed 35. No Darkvision.',
    'Halfling': 'Reroll natural 1s, hard to Frighten, very sneaky. No Darkvision.',
    'Human': 'Extra skill and an extra feat, Heroic Inspiration. No Darkvision.',
    'Orc': 'Drops to 1 HP instead of 0 once per rest, fast Dash, Darkvision.',
    'Tiefling': 'Fiendish magic and resistance, Darkvision.',
}

# SRD feature name -> Seven Trials tag.
FEATURE_TAGS = {
    'Trance': 'sleep_immune',
    'Fey Ancestry': 'charm_adv',
    'Dwarven Resilience': 'poison_res',
    'Stonecunning': 'stonecunning',
    'Luck': 'lucky',
    'Brave': 'brave',
    'Halfling Nimbleness': 'nimble',
    'Gnomish Cunning': 'gnome_cunning',
    'Breath Weapon': 'breath_weapon',
    'Damage Resistance': 'resistance',
    'Fiendish Legacy': 'resistance',
    'Relentless Endurance': 'relentless',
    'Adrenaline Rush': 'adrenaline',
    'Powerful Build': 'large_build',
    'Resourceful': 'heroic_inspiration',
    'Rage': 'rage',
    'Unarmored Defense': 'unarmored',
    'Sneak Attack': 'sneak_attack',
    'Second Wind': 'second_wind',
    'Lay On Hands': 'lay_on_hands',
    'Bardic Inspiration': 'bardic_inspiration',
    'Martial Arts': 'martial_arts',
    'Ritual Adept': 'ritual',
    'Weapon Mastery': 'weapon_mastery',
    'Pact Magic': 'pact_magic',
}


# ===================================================================
# Data loading
# ===================================================================

class DataFileError(Exception):
    """Raised when a file in the data folder is missing or damaged."""


def load_json(name):
    """Read data/<name> and return its contents. Raise DataFileError on failure."""
    path = os.path.join(ROOT, 'data', name)
    try:
        with open(path, encoding='utf-8') as source:
            return json.load(source)
    except FileNotFoundError:
        raise DataFileError('Missing ' + path + '. Keep the data folder next to main.py.')
    except json.JSONDecodeError as error:
        raise DataFileError(name + ' is damaged (line ' + str(error.lineno) + ').')


SRD = load_json('srd52.json')


def find(group, name):
    """Return the SRD entry called name from 'species', 'classes' or 'backgrounds'."""
    for entry in SRD[group]:
        if entry['name'] == name:
            return entry
    raise ValueError('Unknown ' + group + ': ' + str(name))


# ===================================================================
# Small helpers
# ===================================================================

def modifier(score):
    """Ability modifier, e.g. 8 -> -1, 10 -> 0, 15 -> +2."""
    return (score - 10) // 2


def roll_ability():
    """Roll 4d6 and drop the lowest die."""
    dice = sorted(random.randint(1, 6) for _ in range(4))
    return sum(dice[1:])


def new_id(prefix):
    """A random id such as 'a1f3c09e2' for Codex entries."""
    return prefix + format(random.getrandbits(32), '08x')


# ===================================================================
# Character
# ===================================================================

class Character:
    """A level-1 hero: the player's choices plus methods that work out the numbers."""

    def __init__(self, name='Unnamed adventurer'):
        self.name = name
        self.hero_code = None       # 8-digit code from the lucky-number generator
        self.cls = ''
        self.species = ''
        self.background = ''
        self.base = dict.fromkeys(ABILITIES, 10)     # rolled ability scores
        self.bonus = dict.fromkeys(ABILITIES, 0)     # background ability increases
        self.skills = []            # full skill names, e.g. 'Stealth'
        self.expertise = []
        self.tools = []
        self.languages = ['Common']
        self.feats = []
        self.options = {}           # e.g. {'Elven Lineage': 'Wood Elf'}
        self.equipment = {'class': 'A', 'background': 'A'}
        self.spells = []            # spell names
        self.trial_results = []     # (tag, True / False / None for skipped)

    # ----- SRD data for the chosen class, species and background -----

    def class_data(self):
        return find('classes', self.cls)

    def species_data(self):
        return find('species', self.species)

    def background_data(self):
        return find('backgrounds', self.background)

    def subtitle(self):
        """Short description such as 'Elf Wizard 1'."""
        return self.species + ' ' + self.cls + ' 1'

    # ----- Abilities, HP and speed -----

    def score(self, ability):
        """Final ability score (rolled score + background bonus, at most 20)."""
        return min(20, self.base[ability] + self.bonus[ability])

    def mod(self, ability):
        return modifier(self.score(ability))

    def max_hp(self):
        """Level-1 HP: class hit die + Constitution modifier (+1 for Dwarves)."""
        hp = self.class_data()['hitDie'] + self.mod('con')
        hp += self.species_data()['grants'].get('hpPerLevel', 0)
        return max(1, hp)

    def speed(self):
        if self.options.get('Elven Lineage') == 'Wood Elf':
            return 35
        return self.species_data()['grants'].get('speed', 30)

    def has_darkvision(self):
        for feature in self.species_data()['features']:
            if feature['name'] == 'Darkvision':
                return True
        return False

    # ----- Equipment -----

    def items(self):
        """Return (starting items, gold) from the chosen class and background packages."""
        items = []
        gold = 0
        sources = [('class', self.class_data()), ('background', self.background_data())]
        for source, data in sources:
            for option in data['equipment']:
                if option['label'] == self.equipment[source]:
                    items += option['items']
                    gold += option['gp']
        return items, gold

    def items_with_info(self):
        """Starting items paired with their SRD item data (items without SRD data are left out)."""
        result = []
        for item in self.items()[0]:
            info = SRD['items'].get(item.get('srd') or '')
            if info:
                result.append((item, info))
        return result

    def weapons(self):
        """Starting weapons as a list of (name, SRD info), without duplicates."""
        seen = []
        result = []
        for item, info in self.items_with_info():
            if info['type'] == 'Weapon' and item['srd'] not in seen:
                seen.append(item['srd'])
                result.append((item['srd'], info))
        return result

    def armor_class(self):
        """Best AC from worn armor (plus shield) or the class's Unarmored Defense."""
        dex = self.mod('dex')
        names = [item.get('srd') for item, _ in self.items_with_info()]
        shield = 2 if 'Shield' in names else 0
        best = 10 + dex + shield

        for item, info in self.items_with_info():
            match = re.match(r'(Light|Medium|Heavy) armor, AC (\d+)', info['desc'])
            if match:
                kind = match.group(1)
                base = int(match.group(2))
                if kind == 'Light':
                    best = max(best, base + dex + shield)
                elif kind == 'Medium':
                    best = max(best, base + min(2, dex) + shield)
                else:
                    best = max(best, base + shield)

        unarmored = self.class_data()['grants'].get('unarmored')
        if unarmored:
            value = unarmored['base']
            for ability in unarmored['add']:
                value += self.mod(ability)
            if unarmored['shield']:
                value += shield
            best = max(best, value)
        return best

    # ----- Strengths and weaknesses -----

    def tags(self):
        """Tags describing the character. Each tag has one question in the Seven Trials."""
        tags = set()

        if self.has_darkvision():
            tags.add('darkvision')
        else:
            tags.add('no_darkvision')

        features = self.species_data()['features'] + self.class_data()['features']
        for feature in features:
            if feature['name'] in FEATURE_TAGS:
                tags.add(FEATURE_TAGS[feature['name']])

        caster = self.class_data()['caster']
        if caster:
            tags.add('spellcaster')
            tags.add('concentration_hit')
            if caster != 'pact':
                tags.add('slots')

        hit_die = self.class_data()['hitDie']
        ac = self.armor_class()
        if (hit_die >= 10 and ac >= 15) or self.cls == 'Barbarian':
            tags.add('frontline')
        if hit_die <= 6 or ac <= 12:
            tags.add('fragile')

        for name, info in self.weapons():
            if 'ranged weapon' in info['desc']:
                tags.add('ranged')
        for item in self.items()[0]:
            if item.get('srd') == 'Chain Mail':
                tags.add('heavy_stealth')

        if self.mod('con') <= 0:
            tags.add('low_con')
        if self.mod('dex') <= 0:
            tags.add('low_dex')
        return tags


# ===================================================================
# Export to Valdur's Heroic Codex
# ===================================================================

def weapon_action(character, name, info):
    """Build a Codex attack action from an SRD weapon description."""
    desc = info['desc']
    dice = re.search(r'(\d+)d(\d+) (\w+)', desc)
    ranged = 'ranged weapon' in desc
    finesse = 'Finesse' in desc

    # Ranged weapons use Dexterity; Finesse weapons use the better of Str and Dex.
    ability = 'dex' if ranged else 'str'
    if finesse and character.mod('dex') > character.mod('str'):
        ability = 'dex'

    # Proficiency from the class's weapon training.
    training = character.class_data()['grants']['weapons']
    text = ' '.join(training)
    proficient = 'Simple' in desc and 'Simple weapons' in training
    if 'Martial' in desc:
        if 'Martial weapons' in training:
            proficient = True
        elif 'Finesse or Light' in text:
            proficient = finesse or 'Light' in desc
        elif 'Light property' in text:
            proficient = 'Light' in desc

    reach = re.search(r'Range (\d+/\d+)', desc)
    if ranged:
        attack_range = 'Ranged · ' + reach.group(1) + ' ft'
    else:
        attack_range = 'Melee · 5 ft'
        if reach:
            attack_range += ' (thrown ' + reach.group(1) + ' ft)'

    damage = {'n': int(dice.group(1)), 'd': int(dice.group(2)), 'ab': ability,
              'flat': 0, 'type': dice.group(3).lower()}
    return {'id': new_id('a'), 'name': name, 'act': 'A', 'range': attack_range,
            'hit': {'ab': ability, 'prof': proficient, 'flat': 0}, 'save': None,
            'dmg': [damage], 'uses': None, 'desc': desc}


def unarmed_strike():
    """Every character can punch: 1 + Strength modifier bludgeoning damage."""
    return {'id': new_id('a'), 'name': 'Unarmed Strike', 'act': 'A', 'range': 'Melee · 5 ft',
            'hit': {'ab': 'str', 'prof': True, 'flat': 0}, 'save': None,
            'dmg': [{'n': 0, 'd': 4, 'ab': 'str', 'flat': 1, 'type': 'bludgeoning'}],
            'uses': None, 'desc': ''}


def spell_entries(character):
    """Copy the chosen spells from the SRD list into the Codex spell format."""
    keys = ['name', 'level', 'act', 'range', 'conc', 'ritual', 'hit', 'save', 'dmg', 'desc']
    entries = []
    for spell in SRD['spells']:
        if spell['name'] in character.spells:
            entry = {'id': new_id('s')}
            for key in keys:
                entry[key] = spell[key]
            entries.append(entry)
    return entries


def feature(name, desc):
    """A Codex feature entry."""
    return {'id': new_id('f'), 'name': name, 'uses': None, 'desc': desc}


def notes_text(character, bank):
    """The text for the sheet's Notes tab: hero code and the Seven Trials tips."""
    lines = []
    if character.hero_code is not None:
        lines.append(f'Hero code: {character.hero_code}')
        lines.append('')
    if character.trial_results:
        lines.append('SEVEN TRIALS - beginner tips for ' + character.name)
        lines.append('')
        for number, (tag, correct) in enumerate(character.trial_results, 1):
            if correct is None:
                mark = 'skipped'
            elif correct:
                mark = 'passed'
            else:
                mark = 'review this'
            lines.append(f'{number}. [{mark}] ' + bank[tag]['tip'])
    return '\n'.join(lines).strip()


def build_sheet(character, bank):
    """Return one character sheet as a dictionary in the Codex format."""
    cls = character.class_data()
    grants = cls['grants']

    # Skills: 0 = not proficient, 1 = proficient, 2 = Expertise.
    skill_keys = {full: key for key, full in SKILLS.items()}
    skills = dict.fromkeys(SKILLS, 0)
    for name in character.skills:
        skills[skill_keys[name]] = 1
    for name in character.expertise:
        skills[skill_keys[name]] = 2

    actions = [unarmed_strike()]
    for name, info in character.weapons():
        actions.append(weapon_action(character, name, info))

    features = [feature('Walking Speed: ' + str(character.speed()) + ' ft.', '')]
    for item in character.species_data()['features'] + cls['features']:
        features.append(feature(item['name'], item['desc']))
    for label, choice in character.options.items():
        features.append(feature(label + ': ' + choice, 'Chosen in Character Forge.'))
    for feat in character.feats:
        features.append(feature(feat, SRD['feats'].get(feat, '')))
    if character.trial_results:
        features.append(feature('Beginner Guide (Seven Trials)', notes_text(character, bank)))

    spellcasting = None
    slots = {}
    if cls['caster']:
        pact = cls['caster'] == 'pact'
        spellcasting = {'ab': cls['castingAbility'], 'atk': 0, 'dc': 0, 'shortRest': pact}
        slots = {'1': {'max': 1 if pact else 2, 'used': 0}}

    items, gold = character.items()
    inventory = []
    for item in items:
        info = SRD['items'].get(item.get('srd') or '', {'wt': 0, 'cost': 0, 'desc': ''})
        inventory.append({'id': new_id('i'), 'qty': item['qty'], 'name': item['name'],
                          'wt': info['wt'], 'cost': info['cost'], 'rarity': '',
                          'attune': False, 'attuned': False, 'desc': info['desc'],
                          'cat': 'equipment'})

    tools = sorted(set(character.tools + grants.get('tools', [])))
    languages = list(character.languages)
    for language in grants.get('languages', []):
        if language not in languages:
            languages.append(language)

    abilities = {}
    for ability in ABILITIES:
        abilities[ability] = {'score': character.score(ability),
                              'save': ability in grants['saves']}

    hp = character.max_hp()
    return {
        'id': new_id('sh'),
        'kind': 'character',
        'rules': '2024',
        'name': character.name,
        'subtitle': character.subtitle(),
        'hp': {'cur': hp, 'max': hp, 'temp': 0},
        'ac': character.armor_class(),
        'prof': 2,
        'death': {'s': 0, 'f': 0},
        'abilities': abilities,
        'skills': skills,
        'actions': actions,
        'spellcasting': spellcasting,
        'slots': slots,
        'spells': spell_entries(character),
        'features': features,
        'proficiencies': {'armor': grants['armor'], 'weapons': grants['weapons'],
                          'tools': tools, 'languages': languages},
        'inventory': {
            'coins': {'cp': 0, 'sp': 0, 'ep': 0, 'gp': gold, 'pp': 0},
            'categories': [{'id': 'equipment', 'name': 'Equipment', 'collapsed': False},
                           {'id': 'backpack', 'name': 'Backpack', 'collapsed': False}],
            'items': inventory,
        },
        'background': {'name': character.background, 'feature': {'name': '', 'desc': ''}},
        'notes': notes_text(character, bank),
        'color': '#3d8bfd',
    }


def export_codex(character, bank, folder):
    """Write <folder>/<name>.codex.json (never overwriting a file) and return its path."""
    os.makedirs(folder, exist_ok=True)
    safe = re.sub(r'[^A-Za-z0-9_-]+', '-', character.name).strip('-').lower() or 'character'
    path = os.path.join(folder, safe + '.codex.json')
    number = 2
    while os.path.exists(path):
        path = os.path.join(folder, f'{safe}-{number}.codex.json')
        number += 1

    exported_at = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    data = {'format': 'valdurs-codex', 'schemaVersion': 1, 'exportedAt': exported_at,
            'sheets': [build_sheet(character, bank)]}
    with open(path, 'w', encoding='utf-8') as target:
        json.dump(data, target, indent=2, ensure_ascii=False)
    return path
