# Git Sentry

[![Deploy](https://www.herokucdn.com/deploy/button.png)](https://heroku.com/deploy?template=https://github.com/DandyDev/gitsentry)

To configure patterns to watch for, edit example.json and set the config in Heroku:
```bash
$ heroku config:set SENTRY_PATTERNS="$(cat example.json)"
```

The json should be according to the following pattern:

```json
{
  "regex_matching_repo_name(s)": [ 
    "regex_for_path1",
    "regex_for_path2"
  ],
  "regex_matching_another_repo_name(s)": [ 
    "regex_for_path1",
    "regex_for_path2"
  ]
}
```
