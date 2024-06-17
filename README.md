# CE-Assistant (v2)
An object oriented version of [CE-Assistant](https://github.com/andykasen13/CE-Assistant), a discord bot coded using `discord.py`. This bot serves two main purposes for the online community [Challenge Enthusiasts](https://cedb.me).

### Challenge Enthusiasts
Challenge Enthusiasts is an online community made to curate and categorize video games in a point-based system. Each game is given certain "objectives" based on tasks to be completed in the game.

## Purpose 1: Game Updates
This bot will send detailed updates to the [Discord server](https://discord.gg/spKdVZTZ6c) whenever a game on the site is added, updated, or removed.

![Screenshot of a game, Battletoads, being added to Challenge Enthusiasts](https://imgur.com/rXGjnuc.png)

When a game is updated, the bot gives a run down of everything that was changed.

![Screenshot of a game, Terra Ferminarium, being updated on Challenge Enthusiasts](https://imgur.com/ME18Ja5.png)

When a game has a longer amount of objectives (five or more), the bot will screenshot just the specific objective that was changed.

![Screenshot of the 'Challenge Enthusiasts' game on the Challenge Enthusiasts site, used for keeping track of badges, having a singular objective update.](https://imgur.com/pbDCyJ1.png)

## Purpose 2: Casino
This bot allows users in the [Discord server](https://discord.gg/spKdVZTZ6c) to participate in roll events. Users who participate in these will have a set number of games that fit certain parameters (difficulty, category, etc.) randomly selected for them, depending on the event. Once they complete these events (usually within a time limit, but some events go on forever), they're awarded a badge on the site, and the bot sends an update to the server.

![Screenshot of a user, Kyara, completing the roll event 'Never Lucky'.](https://imgur.com/XNCDYDn.png)

The bot keeps track of all previously completed rolls as well, so anyone can view their previous accomplishments.

This gets a lot trickier, as some rolls are Co-Op or PvP. You can view a spreadsheet with all of the roll events [here](https://docs.google.com/spreadsheets/d/1jvYRLshEu65s15NKLNmVxUeTFh-y73Ftd1Quy2uLs3M/edit?usp=sharing).

## How this gets done
