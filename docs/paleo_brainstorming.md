**Goal:**

I want to explore having AI look at my screen while I am playing a game and have agents represent the characters in the game, so that one character owns one agent for itself. These agents think about what is going on to them and around them. Then, they can think about what actions they would take next. I do not know if I can get my agents embedded in the game itself to control the characters as “AI” in the sense of smart NPCs that move around that you can interact with, since I am merely playing the game, but this idea that agents can control characters instead of having AI that beelines to follow you has been something in my mind ever since I learned about the agentic space.

The game I would like to focus on is a dinosaur survival game called **Path of Titans** that involves PvE and PvP elements. I would like agents to be a dinosaur. They should act like a dinosaur, think like a dinosaur. This realism aspect would be really cool, along with having the context of the game itself. Realism means that they act like animals, they drink when thirsty, they wander around their territory, they search for food, they hunt, they battle over disputes, and they only kill when they need to. The agents should know the controls of the game and what abilities their dinosaur has equipped to “use” as if playing the game, when attacking, for example, or when moving around. They should take note of their surroundings and the UI (health, status effects like buffs or nerfs, stamina, hunger, thirst, etc). They should know the risks in mechanics, like that resting or sleeping means you will take more damage. They should also know what dinosaur they are, and what other dinosaurs are. It should be able to determine if that species of dinosaur is a threat or not based on size, diet, and more. The agents should have a full context of the game and its mechanics. This includes the emote wheel, where the dinosaur can roar with a certain call (broadcast, friendly, threaten, and help) or play an animation / emote (some dinosaurs have shakes, stretches, alt threatens, and many more). A lot of mechanics in the game are only on certain dinosaurs, and the agent should thoroughly know the game and all the dinosaurs, abilities, mechanics, and status effects. The main thing I want from this project is to simulate agents acting like realistic dinosaurs, like real animals, with an inner thinking chain but unable to speak, but having access to body language, emotes, calls, and more. One huge mechanic in the game is growth, so sometimes there will be baby dinosaurs running around. In real life, some animals will actively seek out and kill the offspring of competitor species. Does it make sense for a certain species of dinosaur to do the same? Or perhaps that species is small and prefers to hunt juveniles for their size? The realism aspect also goes into how animals react; they have fight, flight, and freeze, among other responses to external stimuli. When a dinosaur gets too injured or gets scared by a large hit, maybe it will immediately flee. But if the dinosaur gets cornered or runs out of stamina, it would be in fight mode. There are so many aspects that can be considered and accomplished via agentic AI.

**Questions:**

1. What is the best way to give the agent context of the game? Obviously, I do not want to write out everything myself, so would I just refer the agent to websites from the game’s wiki to fill out memory blocks? These wiki pages also include helpful information, like a guide on each playable species and what abilities they have available. It could be cool to explore with the agent their ability to infer (knowing what species is approaching, the agent knows what abilities are available for that species, and can guess what the dinosaur actually has equipped based on seeing it use abilities that would take up slot real estate). I can use LLMs to brainstorm even more about possible things to consider with the context of the game itself.  
2. Would a dataset apply to this project? Would that be the wikis on the game? I assume that the LLM used would know what animal-like behavior is like.  
3. Is this Machine Learning? Or Computer Vision?  
4. I would like to use Letta Bot instead of Open Claw. Is that fine?  
5. Can I use Letta as my agent interface? With GLM-5 as the model?  
6. Is it impossible to actually embed the agents inside the game, since I did not make the game?  
7. Even if I cannot implement agents controlling various characters in the game at once, is it possible to allow one agent control my character? This way, the agent can see the screen, think about what to do next, and actually provide the inputs while I am playing the game, as if the agent is using my own hands and fingers.  
8. Is it possible for the agent to view my screen live instead of being sent an image manually as a frame?  
9. How can this system work and be locally installed so someone else can try it on their dinosaur?  
10. I need a name for this. Something related to “Path” is cool, but PATH already exists as the very well-known system variable on your computer. Then “Titan” does not really fit this vibe of smart agents looking at the screen and controlling dinosaurs as their AI system, as well as the humble animal aspect of these agents representing real creatures. I feel like a name related to dinosaurs is going to stick best. Any suggestions? Or at least words that can get me thinking about names related to any of these aspects?  
    1. **Ideas:**  
       1. [PALEO.ai](http://PALEO.ai)  
       2. [Hatchling.ai](http://Hatchling.ai)  
       3. [Instinct.ai](http://Instinct.ai) **DOMAIN USED**  
       4. [PATH.ai](http://PATH.ai) **DOMAIN USED**  
       5. [TITAN.ai](http://TITAN.ai) **DOMAIN USED**  
       6. [HATCH.ai](http://HATCH.ai) **DOMAIN USED**

**Additional Ideas:**

Agentic Personality:
- Mood
- Morality
- Agressiveness
- Friendliness
- Curiosity
- Braveness