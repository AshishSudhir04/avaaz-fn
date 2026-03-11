## ISL Intro / Small-Talk Coverage Map

### Templates handled by explicit rules

- **Greeting / how-are-you**
  - \"Hello\" / \"Hi\" → `HELLO` (RuleGreeting)
  - \"Hello, how are you?\" / \"Hi, how are you?\" → `HELLO HOW YOU` (RuleGreetingHowAreYou)
  - \"How are you?\" → `HOW YOU` (RuleHowAreYou)

- **Name**
  - \"What is your name?\" / \"What is your good name?\" / \"What's your name?\" → `YOUR NAME WHAT` (RuleNameQuestion)
  - \"My name is X\" / \"I am X\" (intro context) → `ME NAME X` (RuleNameStatement)

- **Where from / where live**
  - \"Where are you from?\" / \"Where do you come from?\" → `YOU FROM WHERE` (RuleWhereLiveQuestion)
  - \"Where do you live?\" / \"Where you live?\" → `YOU LIVE WHERE` (RuleWhereLiveQuestion)
  - \"I live in Kochi/Delhi\" → `ME LIVE KOCHI/DELHI` (RuleWhereLiveStatement)

- **Feelings / state**
  - \"I am happy/sad/busy\" → `ME HAPPY/SAD/BUSY` (RuleFeelingStatement)

- **Thanks / bye**
  - \"Thank you\" / \"Thank you very much\" / \"Thanks\" → `THANK_YOU` (RuleThankYou)
  - \"Bye\" / \"Good bye\" → `BYE` (RuleBye)

### Templates currently using fallback mapping

- \"See you again\" → `SEE YOU AGAIN` (RuleFallbackLinear)
- \"I work\" / \"I work from home\" → `ME WORK`, `ME WORK HOME` (RuleFallbackLinear)
- \"I study\" / \"I study in college\" → `ME STUDY`, `ME STUDY COLLEGE` (RuleFallbackLinear)
- \"Welcome\" / \"You are welcome\" → `WELCOME`, `YOU WELCOME` (RuleFallbackLinear)

### Gloss tokens with video assets (from `isl_lexicon.json`)

- Core intro tokens used by rules:
  - `HELLO`, `HOW`, `YOU`, `ME`, `NAME`, `FROM`, `LIVE`, `KOCHI`, `DELHI`, `HAPPY`, `SAD`, `BUSY`, `THANK_YOU`, `BYE`.
- Additional intro/small-talk tokens available for future rules:
  - `WORK`, `STUDY`, `COLLEGE`, `AGAIN`, `WELCOME`, `WORLD`, `WE`, `OUR`, `US`, `SAFE`, `GOOD`, `GREAT`, `HOME`, `HERE`.

### Known gaps / future work

- Add more explicit rules for:
  - Work/study intros (\"I work at X\", \"I study language\", etc.).
  - Group introductions (\"We are from X\", \"Our home is here\").
- Decide how to treat city/country names consistently (currently handled as uppercase tokens via fallback).

