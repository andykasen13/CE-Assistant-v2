# CE-Assistant-v2
Object-based version of andykasen13/CE-Assistant

## little notes
- consider having `CEGame` hold an array of just `CEObjectives` instead of two different ones for `Primary` and `Community`. Keep the `get_primary_objectives()` and `get_community_objectives()` and it'll sort it within the class (wait im so smart!)
- look into schmole's idea of rerolling a specific game in a roll in the event of country-lock. Example:
  - admin runs /change-roll-game(event_name : str, user : discord.User)
  - spits out a dropdown of all currently rolled games and admin selects the game to reroll
  - manually change this game to a newly rerolled game.
- show role if a game uses one

## Classes
### CEUser
```
- private int discord_id
- private String ce_id
- private int casino_score
- private CE-Roll[] current_rolls
- private CE-Roll[] completed_rolls
- private CE-Roll[] pending_rolls
- private CE-Roll[] cooldowns
```

### CERoll
```
- private String roll_name
- private String init_time
- private String end_time
- private CE-Game[] games
- private String partner_id
- private int cooldown_days
- private int rerolls
```

### CEGame
```
- private String ce_id
- private String game_name
- private String platform
- private String platform_id
- private String point_value
- private boolean is_special // denotes whether the game is a special T0 or not
- private CE-Objective[] primary_objectives
- private CE-Objective[] community_objectives
- private int last_updated
```

### CEUserGame
```
- private int user_points
- private CE-User-Objective[] user_objective
```

### CEObjective
```
- private String ce_id
- private boolean is_community
- private String description
- private int point_value
- private int point_value_partial
- private String name
- private String requirements
- private String[] achievement_ce_ids // this will just be an array of ce-ids
```

### CEUserObjective
```
- private int user_points
```

### ideas
- "other classes" - steamdata, completiondata
- "other exceptions" - FailedUserUpdateException, FailedGameUpdateException
- do we want to have it update users stuff once a day (like have one big message per day outlining what happened that day) or do it every 30 minutes with casino
- /show-rolls (or something) to see all available rolls 
  - maybe /see-available-rolls?


### version 2 changelog
- huge backend changes, entirely object-oriented now.
- #game-additions posts now have links to their games.
- user updates!! messages will be sent in the new #user-log channel for any of the following:
  - a user ranks up
  - a user clears a t4 or higher
  - a user unlocks a new discord role (category/tier related)
  - open to more suggestions here!! submit them in #assistant-feedback
- rolling to return soon...
  - thank you folkius for covering in the meantime :)
  - #casino-log messages will be more detailed
  - Winner Takes All now accepts tier and category options.
  - /check-rolls will be much more concise.