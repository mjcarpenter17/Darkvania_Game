Please review the codebase and documentation to get an understanding of where we are at with building out our little MetroidVania game, **Darkvania**.

### Current Progress

- **Player Character**
    - Animations: idle, walk, jump, transition, fall, two attacks, dash, hit, death
- **Enemy**
    - Assassin: idle, walk, hit, death animations; moves back and forth with edge detection
- **Map Editor**
    - Create levels from a sprite tile sheet
    - Place objects
    - Export levels to `.json` format
- **Gameplay**
    - Player has health
    - Collision detection with enemy

We are in a good spot to proceed with a few advancements.

---

## Next Features & Controls

### Player Controls

- [ ] Add double jump
- [ ] Add ledge hold (using "Ledge Grab" animation)
- [ ] Add wall hold (hold against wall with no ground, hold shift; uses "Wall Hold" animation)
- [ ] Add wall slide (press down/S while holding wall; uses "Wall Transition" and "Wall Slide" animations; stops when player stops pressing down but still holds wall; plays "Wall Slide Stop" animation)

### Advanced Player Actions

- [ ] Add player roll (invincible while rolling; uses "Roll" animation)
- [ ] Add downward attack (falling, press down/S + attack/F; uses "Fall Attack" animation)
- [ ] Add slam attack (hold attack/F for >1 sec, release for powerful slam; uses "Slam" animation)

### After Controls & Testing

- [ ] Add interactable objects
    - [ ] Chests
    - [ ] Doors
- [ ] Add more enemies
    - [ ] Archer (`Assets/enemies/archer/Archer.json`, `Assets/enemies/archer/Archer.png`)
    - [ ] Wasp (`Assets/enemies/wasp/Wasp.json`, `Assets/enemies/wasp/Wasp.png`)

---

## Next Steps

When you have a good understanding of the project, please create a new task list that breaks all the desired next items into a phased task list.

---

## Feedback

I would love to hear your thoughts on the project:
- Where you think it's at
- Where you think it can go
- Anything we should add to the task list (UI/UX improvements, polish, refactors, etc.)
- Anything we may not have considered yet
lease review the codebase and documentation to get an understanding of were we are at with building out our little MetroidVania game, Darkvania.
We have a player character with idle, walk, jump, transition, fall, Two attacks, dash, hit and death animtions
We have a single enmy right no, the assassin, that has idle, walk, hit and death animations and moves back and forth, with edge detection.
we have a map editor to create out levels from a sprite tile sheet, and can place objects, and that exports levels to .json format
Our player has health and caan detect collison with our enemy
i feel like we're in a good spot to proceed with a few advancemenets
The next thing I want to do is add a few more features and controls to out player
I want to
 - Add a double jump
 - add a ledge hold ( using the "Ledge Grab" animation)
 - Add a Wall hold. maybe controls are being against a wall, with no ground under player, and holding shift (using "Wall hold" animation, holding on to the side of a wall without sliding)
 - add a wall slide if the player presses down (or S) while holding a wall (using the "Wall Transition" animation to transition from wall hold to wall slide, then use "Wall Slide" animation) and stoping when player stops pressing down but still holding wall (and playing the "Wall slide Stop" animation)
Then After adding the double jump and wall controls I would like to;
 - add a player roll (using the "Roll" animation) where the player is invincible while rolling
 - add a downward attack (using the "Fall Attack" animation) so that if the player is falling, presses down (or S) and presses attack (F) the trigger the Down attack
 - add a slam attack (using the "Slam" animation) where after the player presses the attack (F) and holds the 2nd attack for longer than 1 sec, and then releases, the do a powerful slam attack.

and, after adding all those player controls, and doing testing to fine tune the controls, then I want to 
 - add interactable objects like
	- Chests
	- Doors
 - add more enemies such as 
	- the Archer (using \Assests\enemies\archer\Archer.json and \Assests\enemies\archer\Archer.png)
 	- the Wasp (using Assests\enemies\wasp\Wasp.json and Assests\enemies\wasp\Wasp.png)
When you think you have a good understanding of the project, please cerate a new tasklist that break all the desired next items to a phased tasklist.
Also, I would love to hear your thoughts on the project, where you think it's at, where you think it can go, and any thing you think we should add to the task list such as UI or UX improvemnts, polish, refactors, anything we may not have considered yet, etc.
