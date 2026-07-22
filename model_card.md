# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name

**VibeCheck 1.0**

It's a small music recommender that tries to match songs to your vibe.

---

## 2. Intended Use

**What it does:** You tell it what you like. A favorite genre, a favorite mood,
how much energy you want, and whether you like acoustic songs. It looks at a
list of songs and gives you back the top 5 that fit you best. It also tells you
why it picked each one.

**Who it's for:** This is a school project. It's made for learning how
recommenders work. It is not for real users or a real app.

**What it should not be used for:** Don't use it to actually pick music for
people. The song list is tiny and the rules are simple, so it misses a lot. It
also should not be used to judge anyone's taste or to make any real decision.
It's a demo, not a real product.

---

## 3. How the Model Works

I don't use any fancy machine learning. It's just a points system.

Every song starts at 0 points. Then I add points based on how well it matches you:

- Same genre as your favorite: **+5 points**
- Same mood as your favorite: **+4 points**
- Close to your energy level: **up to +2 points** (the closer it is, the more
  points it gets)
- You like acoustic songs and this song is pretty acoustic: **+1 point**

After that I add up all the points for each song and sort them from highest to
lowest. The top 5 are your recommendations.

The one thing I changed from the starter is that I put all the point values in
one spot (called `DEFAULT_WEIGHTS`). That made it easy to run experiments later
without messing with the actual logic.

---

## 4. Data

The catalog is really small. It's just **20 songs** in a CSV file
(`data/songs.csv`).

Each song has a genre, a mood, and some numbers: energy, tempo (bpm), valence
(how happy it sounds), danceability, and acousticness.

**Limits I noticed in the data:**

- 20 songs is tiny. A real app has millions.
- Most genres only have **one song**. 11 of the 15 genres are just a single song.
- There is **no "sad" mood** in the data at all. The moods are chill, intense,
  relaxed, happy, moody, focused, and confident.
- The songs lean **high energy**. 9 of the 20 are high energy and only 5 are calm.

These limits end up causing most of the biases below.

---

## 5. Strengths

- **It works great for normal, clear tastes.** If you ask for pop and happy, you
  get the pop happy song at the top. If you ask for lofi and chill, you get the
  calm lofi songs. The obvious cases feel right.
- **It explains itself.** Every pick shows the reasons and how many points each
  one gave, like `genre match (+5.0), mood match (+4.0), energy match (+1.84)`.
  So you can always see why a song got picked.
- **It's fast and simple.** The rules are easy to read, so it's easy to change a
  weight and see what happens.

---

## 6. Limitations and Bias

The **biggest problem is the tiny catalog**. 11 of the 15 genres only have one
song. And genre is worth the most points (+5). So if your favorite genre is
rock, you get the one rock song at the top pretty much every time, and there is
no other rock song it could ever show you. You get zero variety in the music you
actually like. (Small note: it's not 100% locked. If your mood and energy don't
match that one song, a song from another genre can sometimes beat it. But most
of the time you're stuck with the same pick.)

A few other biases I found while testing:

- **Genre beats mood, and that feels wrong sometimes.** Genre is +5 but mood is
  only +4. So a song can win just for being the right genre even if the mood is
  off. A pop fan who wants *happy* music gets "Gym Hero" (a pop song that is
  actually *intense*, like a gym workout song) pushed up to #2, ahead of songs
  that are actually happy. If you care about the mood more than the label, it
  lets you down.
- **It favors people who like loud music.** The songs lean high energy. So a
  person who wants loud music finds about 8 songs that are a really close energy
  match, but a person who wants calm music only finds about 3. Just because of
  which songs are in the list, calm-music fans get worse energy matches. That's
  not fair to them.
- **It never says "I found nothing."** If you ask for something the catalog can't
  do (like a sad mood, which isn't even in the data), it doesn't warn you. It
  just quietly ranks songs by energy and still hands you a full top 5, like it
  found a real match. So the people it helps the least get the most
  confident-looking wrong answers.

---

## 7. Evaluation

I tested the recommender with 5 different profiles in `src/main.py`. Three are
normal listeners and two are "trick" profiles I made on purpose to try to break
it. All the outputs below are the real results from `python -m src.main`.

### Normal profiles

**High-Energy Pop** (`genre=pop, mood=happy, energy=0.9, acoustic=False`)

```
1. Sunrise City - Neon Echo
   Score:   10.84
   Reasons: genre match (+5.0), mood match (+4.0), energy match (+1.84)
2. Gym Hero - Max Pulse
   Score:   6.94
   Reasons: genre match (+5.0), energy match (+1.94)
3. Rooftop Lights - Indigo Parade
   Score:   5.72
   Reasons: mood match (+4.0), energy match (+1.72)
4. Island Time - Palm Fever
   Score:   5.36
   Reasons: mood match (+4.0), energy match (+1.36)
5. Storm Runner - Voltline
   Score:   1.98
   Reasons: energy match (+1.98)
```

**Chill Lofi** (`genre=lofi, mood=chill, energy=0.35, acoustic=True`)

```
1. Library Rain - Paper Lanterns
   Score:   12.00
   Reasons: genre match (+5.0), mood match (+4.0), energy match (+2.00), acoustic match (+1.0)
2. Midnight Coding - LoRoom
   Score:   11.86
   Reasons: genre match (+5.0), mood match (+4.0), energy match (+1.86), acoustic match (+1.0)
3. Focus Flow - LoRoom
   Score:   7.90
   Reasons: genre match (+5.0), energy match (+1.90), acoustic match (+1.0)
4. Cathedral Skies - Aurelia
   Score:   6.90
   Reasons: mood match (+4.0), energy match (+1.90), acoustic match (+1.0)
5. Spacewalk Thoughts - Orbit Bloom
   Score:   6.86
   Reasons: mood match (+4.0), energy match (+1.86), acoustic match (+1.0)
```

**Deep Intense Rock** (`genre=rock, mood=intense, energy=0.9, acoustic=False`)

```
1. Storm Runner - Voltline
   Score:   10.98
   Reasons: genre match (+5.0), mood match (+4.0), energy match (+1.98)
2. Breakwater - Tidal Frame
   Score:   5.96
   Reasons: mood match (+4.0), energy match (+1.96)
3. Gym Hero - Max Pulse
   Score:   5.94
   Reasons: mood match (+4.0), energy match (+1.94)
4. Riot in the Pit - Blackout Signal
   Score:   5.88
   Reasons: mood match (+4.0), energy match (+1.88)
5. Sunrise City - Neon Echo
   Score:   1.84
   Reasons: energy match (+1.84)
```

### Trick profiles

**Conflicting Vibes** (`genre=jazz, mood=sad, energy=0.9, acoustic=True`) — I
asked for loud (energy 0.9) but also sad, jazzy, and acoustic. No song has the
mood "sad", so that rule never fires.

```
1. Velvet Midnight - Blue Room Trio
   Score:   6.98
   Reasons: genre match (+5.0), energy match (+0.98), acoustic match (+1.0)
2. Coffee Shop Stories - Slow Stereo
   Score:   6.94
   Reasons: genre match (+5.0), energy match (+0.94), acoustic match (+1.0)
3. Old Porch Song - Willow Hollow
   Score:   2.12
   Reasons: energy match (+1.12), acoustic match (+1.0)
4. Desert Mirage - Sahara Strings
   Score:   2.08
   Reasons: energy match (+1.08), acoustic match (+1.0)
5. Midnight Coding - LoRoom
   Score:   2.04
   Reasons: energy match (+1.04), acoustic match (+1.0)
```

**Impossible Taste** (`genre=reggaeton, mood=euphoric, energy=0.5, acoustic=False`)
— a genre and a mood that aren't in the data at all, so only the energy rule can
score.

```
1. Sunday Soul - Ruby Mae
   Score:   1.96
   Reasons: energy match (+1.96)
2. Old Porch Song - Willow Hollow
   Score:   1.92
   Reasons: energy match (+1.92)
3. Desert Mirage - Sahara Strings
   Score:   1.88
   Reasons: energy match (+1.88)
4. Island Time - Palm Fever
   Score:   1.84
   Reasons: energy match (+1.84)
5. Midnight Coding - LoRoom
   Score:   1.84
   Reasons: energy match (+1.84)
```

### Comparing the profiles

Here is how many songs each pair of profiles shares in its top 5:

| Profile pair | Shared top-5 songs |
|--------------|:------------------:|
| High-Energy Pop  vs  Chill Lofi | 0 |
| High-Energy Pop  vs  Deep Intense Rock | 3 |
| High-Energy Pop  vs  Conflicting Vibes | 0 |
| High-Energy Pop  vs  Impossible Taste | 1 |
| Chill Lofi  vs  Deep Intense Rock | 0 |
| Chill Lofi  vs  Conflicting Vibes | 1 |
| Chill Lofi  vs  Impossible Taste | 1 |
| Deep Intense Rock  vs  Conflicting Vibes | 0 |
| Deep Intense Rock  vs  Impossible Taste | 0 |
| Conflicting Vibes  vs  Impossible Taste | 3 |

What that tells me, in plain words:

- **High-Energy Pop vs Chill Lofi: 0 shared.** These two want the opposite genre,
  the opposite mood, and the opposite energy. So they have nothing in common. The
  pop person gets loud upbeat songs and the lofi person gets quiet calm ones.
  That's the system doing exactly what it should.
- **High-Energy Pop vs Deep Intense Rock: 3 shared.** Both want high energy, so
  the loud songs (Gym Hero, Storm Runner, Sunrise City) show up on both lists.
  The only real difference is #1: the pop fan gets Sunrise City and the rock fan
  gets Storm Runner. Makes sense that two "loud music" people see similar stuff.
- **Chill Lofi vs Deep Intense Rock: 0 shared.** This one is all about energy.
  0.35 vs 0.9 splits them completely. One list is all calm, the other all loud.
  It shows the energy rule really is doing work, not just the genre.
- **Conflicting Vibes vs Impossible Taste: 3 shared.** Both of these are broken
  profiles that the catalog can't really match. So both of them fall back to the
  same few middle-of-the-road songs. That's a bad sign. It means when the system
  can't find a real match, two totally different people get almost the same list.

### What surprised me

- The normal profiles all worked and put the right song at #1. That part felt
  good.
- The "Gym Hero" thing surprised me the most. It's a pop song but its mood is
  intense, not happy. When I turned off the mood rule in my experiment, Gym Hero
  jumped all the way to #1 for a "happy pop" person. That showed me how much the
  mood rule was actually holding it back, and how genre can take over.
- I did not expect the two broken profiles to end up with the same songs. That
  made the "it never says I found nothing" problem really obvious.

I didn't use any accuracy numbers. I just checked if the top songs matched what
I would expect for each profile.

---

## 8. Future Work

If I kept working on this, here's what I'd change:

1. **Add way more songs.** This fixes the biggest problem. If every genre had a
   bunch of songs, people would actually get variety instead of the same one pick.
2. **Rebalance genre vs mood.** Maybe make them worth the same, or let the user
   choose what matters more to them. Right now genre quietly wins too often.
3. **Add a "no good match" message.** If the top score is really low, it should
   just say it couldn't find anything good instead of faking a confident list.

---

## 9. Personal Reflection

**My biggest learning moment** was seeing that the recommendations are really
just points and sorting. There is no magic. Once I saw the score breakdown next
to each song, the whole thing clicked. It also hit me that the *data* matters way
more than I thought. Most of the bias wasn't from my code, it was from the tiny
song list. A whole genre having one song broke variety no matter how good my
rules were.

**Using AI tools** helped me a lot with the coding part. It helped me write the
functions and explained stuff I didn't fully get, like the difference between
`.sort()` and `sorted()`. But I did have to double check it. One time it changed
an import and it broke the run button, and I had to catch that. I also checked
the actual recommendation results by hand to make sure they made sense, instead
of just trusting the output.

**What surprised me** is how a really simple algorithm can still "feel" like a
real recommendation. It's just adding points, but when it shows you a good song
with the reasons, it feels smart. That made me realize apps like Spotify are
probably doing a fancier version of the same basic idea: score things, sort them,
show the top ones.

**If I extended this**, I'd add more songs first, then try to make it explain the
recommendations in full sentences instead of short tags, and maybe let a user
give feedback (like or skip) so it could learn over time instead of just using a
fixed profile.
