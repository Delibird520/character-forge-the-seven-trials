# Character Forge: The Seven Trials

A beginner-friendly D&D character builder for COMP9001, using the free SRD 5.2 (2024) rules.

Character Forge builds a level-1 hero, quizzes the player on **their own character's strengths and weaknesses** (the *Seven Trials*), and exports a `.codex.json` file. The file is imported into **Valdur's Heroic Codex** in **Owlbear Rodeo** and linked to a token, ready to play with a DM.

**Why I made it:** when my friends and I built our first characters for a tabletop game, we used an Excel sheet. The layout was cluttered, we did not know where to start, and changing one choice did not update everything that depended on it. Character Forge turns that process into clear steps, works out the numbers for you, and helps new players understand their character and get curious about the world.

**Who it is for:** players who have never played D&D. Beginners often don't know that a wizard should stay out of melee, that a fighter without Darkvision needs a torch, or that an elf can't be put to sleep by magic. Character Forge teaches exactly these things.

---

## 1. Run the program

Requirements: Python 3.9 or later. Only the standard library is used.

Open a terminal in this folder and run:

```
python main.py           # start the program
python main.py --test    # run the assertion tests
```

- The main file is `main.py`.
- Keep the `data` folder next to the Python files.

---

## 2. Use the program

The main menu has four options:

| Menu | What it does |
| --- | --- |
| `1` Create a new character | Build a hero by hand or from a lucky number |
| `2` View character | Show the character summary |
| `3` Take the Seven Trials | The beginner quiz |
| `4` Export .codex.json | Save the file for Owlbear Rodeo |

### 2.1 Create a character (menu 1)

After entering a name, choose how to create the hero:

- **Build it yourself:** press **Enter**. You choose every option: class, species, background, languages, ability increases, skills, equipment and spells.
- **Random hero:** type an **8-digit lucky number**, for example your birth date (`20010412` or `2001-04-12`). The program makes every choice for you and always takes the ready-made gear package. See section 3.

While building by hand:

- At any list, press **Enter** to let the program pick one option at random.
- Every choice says where it comes from, for example `Fiendish Legacy [Tiefling species]` or `Skill proficiencies [Rogue class]`.
- Classes and species are listed with a one-line description for beginners.
- Before a skill, tool, feat or Expertise choice, a one-line hint explains what it means.

**Ability scores:** the program rolls five sets (4d6, drop the lowest die) and recommends the set with the highest total in the class's three key abilities. Press **Enter** to take it, or type `1`–`5`.

**Spells:** spellcasters choose level-1 cantrips and prepared spells (2024 rules):

| Class | Cantrips | Level-1 spells |
| --- | --- | --- |
| Bard | 2 | 4 |
| Cleric | 3 | 4 |
| Druid | 2 | 4 |
| Paladin | 0 | 2 |
| Ranger | 0 | 2 + Hunter's Mark |
| Sorcerer | 4 | 2 |
| Warlock | 2 | 2 |
| Wizard | 3 | 4 |

Spells from species options (for example High Elf *Prestidigitation*, Tiefling *Thaumaturgy*) are added automatically.

### 2.2 The Seven Trials (menu 3)

1. The program describes the character with *tags*, such as `no_darkvision`, `fragile`, `sleep_immune` or `rage`.
2. It randomly picks seven tags. Each tag has one question in `data/trials.json`.
3. If the character has fewer than seven tags, general rules questions fill the gap.
4. After each answer, a tip explains the rule. A title is awarded for the final score.

Press **Enter** to skip a question (useful for a short demo). Skipped questions are marked `[skipped]` in the exported Notes. If you export without taking the trials, all seven tips are saved as `[skipped]`.

### 2.3 Export (menu 4)

The file is saved as `exports/<name>.codex.json`. The seven tips are saved in the sheet's **Notes** tab and as a **Beginner Guide (Seven Trials)** feature, so the player can reread them during play.

---

## 3. How the lucky number works

Python's `random` module is *pseudo-random*: started from the same **seed** number, it always produces the same sequence of choices. Character Forge builds the seed from the lucky number and five dice (see `lucky.py`):

| Step | Operation |
| --- | --- |
| 1 | Roll d4, d6, d8, d10 and d20 |
| 2 | Lucky number **+ d4** |
| 3 | **× d6** |
| 4 | **// d8** (floor division, so the result stays a whole number) |
| 5 | **Squared** |
| 6 | Remove every copy of the ones digit of the five dice's total (e.g. 2 + 2 + 8 + 10 + 18 = 40 → remove every `0`) |
| 7 | Keep the **last 8 digits** (`% 100000000`) → the **hero code** |

Every step is printed on screen. The hero code is used as the seed for all random choices and is saved in the sheet's Notes. Because the dice change every time, the same lucky number gives a different hero on each run.

---

## 4. Import the character into Owlbear Rodeo

### 4.1 Install the Heroic Codex extension (first time only)

1. Open [Owlbear Rodeo](https://www.owlbear.rodeo/) and click **Sign up / Log in** at the top right. After logging in, your **Profile** page opens.
2. Scroll down to **Extensions** and click **MANAGE**.
3. Click **+** at the top right, paste `https://owlbear.vald.io/manifest.json` and click **ADD**.

### 4.2 Create a room

1. On the Profile page, click **CREATE A NEW ROOM**.
2. Tick **Valdur's Heroic Codex** in the room's extension list, then create the room.
3. Add a map so tokens have somewhere to stand: open **Scenes** in the bottom Dock → **Asset Manager** → **Add → New**, drop in any map image, click **IMPORT**, then **Open** the scene.

### 4.3 Import the character sheet

1. Click the **book icon** at the top left to open Heroic Codex.
2. Click **`...`** → **Import a sheet file**.
3. Choose the `.codex.json` file from the `exports` folder. The character appears as a new sheet.

### 4.4 Add a token and link it to the sheet

1. Open **Characters** in the bottom Dock → **Asset Manager** → **Add → Starter Sets**, and add the **Characters and Monsters** set.
2. Drag a character token onto the map.
3. Click the token to select it.
4. In Heroic Codex, with your character's sheet open, click **`...`** → **Link to selected token**.

A chain icon appears next to the sheet name and the token shows the character's HP. The character is now ready for the DM to run a game.

> **Note:** the message "Dice+ not found: using built-in dice" is not an error. The Codex rolls its own dice.

---

## 5. Optional: a first fight against a goblin

This short test shows the character in action and was used to play-test the project.

1. **Add a goblin sheet:** in Heroic Codex, click the arrow next to the sheet name → **New creature**. Name it `Goblin`, set **AC 15** and **HP 7**, then click **Done**.
2. **Link the goblin:** drag the **Goblin** token from the Characters and Monsters set onto the map, select it, and choose **`...`** → **Link to selected token** while the goblin sheet is open.
3. **Attack:** switch back to your hero's sheet and click an action (for example *Dagger*) or a spell. Results appear in **Table rolls**. Hold **Shift** for Advantage or **Ctrl/Cmd** for Disadvantage.
4. **Apply damage:** if the *to hit* total is 15 or more, the attack hits. Open the goblin's sheet, click its HP, enter the damage and press **Damage**.

Rolls never change a target's HP by themselves: the DM decides whether an attack hits and applies the damage.

---

## 6. What the exported sheet contains

- Name, species, class and level
- HP and AC (best of worn armor and shield, or Unarmored Defense)
- Ability scores and saving throw proficiencies
- Skills and level-1 Expertise
- Weapon attacks from the starting weapons, plus Unarmed Strike
- Species traits, level-1 class features, origin feats and chosen lineage/ancestry options
- Armor, weapon and tool proficiencies, and languages
- Starting equipment and gold
- Spellcasting ability, level-1 spell slots and chosen spells
- The Seven Trials tips and the hero code

The Codex calculates modifiers, proficiency, spell attack bonus and save DC itself.

### Limits

To keep the project small:

- **Level 1 only.**
- **Four backgrounds** (Acolyte, Criminal, Sage, Soldier): these are the only backgrounds in the free SRD 5.2. The other 2024 backgrounds are not open-licensed.
- **Wizards** choose their 4 prepared spells. Other spellbook entries and Magic Initiate spells can be added from the Codex's SRD spell list.
- **Sub-options inside class features** (Fighting Style, Divine Order, Weapon Mastery weapons) are listed with their rules text and chosen in the Codex.
- **Size** is not tracked.
- The class ability priorities, the five-set recommendation and the lucky-number generator are project features, not official rules.

---

## 7. Files

| File | Purpose |
| --- | --- |
| `main.py` | Menus, input validation, character creation steps, assertion tests |
| `forge.py` | `Character` class, HP/AC/weapon/tag calculations, `.codex.json` export |
| `trials.py` | The Seven Trials quiz |
| `lucky.py` | Lucky number + five dice → hero code |
| `data/srd52.json` | SRD 5.2 species, classes, backgrounds, origin feats, items and level 0–1 spells |
| `data/trials.json` | Question bank: one question and tip per tag |
| `examples/demo-hero.codex.json` | A sample export to test importing |

---

## 8. Course concepts used

| Advanced topic | Where |
| --- | --- |
| Classes and objects (Lab 7) | `Character` in `forge.py`, with methods such as `armor_class()`, `max_hp()` and `tags()` |
| Files (Lab 9) | `load_json()` reads the rule data and question bank; `export_codex()` writes the `.codex.json` |
| Exceptions: `raise`, `try`/`except` (Lab 8) | Custom `DataFileError` for missing or damaged data files; `ValueError`/`OSError` handled in the menu; input loops reject bad input |
| Testing (Lab 10) | `python main.py --test`: assertion tests, including all 432 class/species/background combinations |
| Recursion (Lab 11) | `strip_digit()` in `lucky.py` removes a digit from the hero code recursively |

Also used: variables and arithmetic operators, conditionals, lists, dictionaries and sets, loops and functions.

---

## 9. Sources and attribution

This work includes material from the System Reference Document 5.2 ("SRD 5.2") by Wizards of the Coast LLC, available at <https://www.dndbeyond.com/srd>. The SRD 5.2 is licensed under the Creative Commons Attribution 4.0 International License, <https://creativecommons.org/licenses/by/4.0/legalcode>.

- `data/srd52.json` was extracted from the SRD 5.2 data bundled with [Valdur's Heroic Codex](https://github.com/purvaldur/owlbear-charactersheet-5e), which obtains it from Open5e. The export format follows that project's sheet schema.
- [Owlbear Rodeo](https://www.owlbear.rodeo/) and its [documentation](https://docs.owlbear.rodeo/).
- Goblin Ambush battle map used in play-testing: [The Fateful Force](https://thefatefulforce.com/battle-resources/battle-maps/) (free for personal use; not included).
- The Seven Trials questions and tips were written for this project from the SRD 5.2 rules.

See `AI_ASSISTANCE.md` for the AI-use disclosure.
