# Git Sentry

[![Deploy](https://www.herokucdn.com/deploy/button.png)](https://heroku.com/deploy?template=https://github.com/DandyDev/gitsentry)

To configure patterns to watch for, edit example.json and set the config in Heroku:
```bash
$ heroku config:set SENTRY_PATTERNS="$(cat example.json)"
```