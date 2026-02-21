# SVT Swedish Tutor — Claude Skill

A Claude skill that turns any [SVT Play](https://www.svtplay.se) episode into a personalized Swedish learning session. Instead of generic vocabulary lists, you practice with real language from content you actually watched.

## What it does

Share an SVT Play URL with Claude and it becomes your conversational Swedish tutor for that episode. It automatically fetches the Swedish subtitles via a hosted API, builds a study brief, and guides you through comprehension and vocabulary practice — all anchored to the specific episode you watched. No scripts to run, no setup beyond installing the skill.

**The flow:**
1. Share an SVT Play URL
2. Claude asks if you've watched it
3. You get a context summary + key vocabulary brief
4. If you haven't watched yet — go watch, ask questions mid-episode anytime
5. After watching — comprehension check, vocabulary drilling, idioms in context

## Why this works

Generic Swedish apps teach you words in isolation. This skill teaches you words you encountered in a real story you care about, in the exact sentences they appeared in. That context is what makes vocabulary stick.

## Installation

No technical setup required.

1. Download or clone this repo
2. Zip the `svt-swedish-tutor/` folder
3. Open Claude.ai → Settings → Capabilities → Skills
4. Upload the zip file
5. Enable the skill

## Usage

Simply paste any SVT Play episode URL into Claude:

```
https://www.svtplay.se/video/jXvkPLJ/sa-byggdes-sverige/6-fororten-nar-framtiden-kommer-till-stan
```

Claude will handle the rest.

**Note:** SVT Play subtitles are available on most SVT content. The skill works best with factual, documentary, or drama content that uses clear spoken Swedish.

## What's inside

```
svt-swedish-tutor/
├── SKILL.md                   — Claude's instructions
├── vercel.json                — Vercel deployment config
├── api/
│   └── transcript.py          — Hosted serverless function (SVT → transcript)
└── scripts/
    └── extract_subtitles.py   — Local version for testing and development
```

## For maintainers — deploying the API

The skill calls a hosted API to fetch transcripts. If you're forking this for your own use, you'll need to deploy the API yourself:

1. Create a free account at [vercel.com](https://vercel.com)
2. Push this repo to GitHub
3. Import the repo in Vercel — it auto-detects the configuration
4. After deployment, copy your Vercel URL (e.g. `svt-transcript-api.vercel.app`)
5. Replace `your-api.vercel.app` in `SKILL.md` with your actual URL
6. Repackage and redistribute the skill zip

The API accepts:
```
GET /api/transcript?url=https://www.svtplay.se/video/...
GET /api/transcript?id=jXvkPLJ
```

## Best suited for

Swedish learners at A2–B2 level who are watching Swedish TV to improve comprehension. Works especially well if you watch with Swedish subtitles on.

## Author

Built by Hercules Reyes. Contributions welcome.

## License

MIT
