import logging
import os
import re
import json
from flask import Flask, request, Response
from slack import send_githook_trigger

log = logging.Logger(__name__)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
log.addHandler(handler)

SENTRY_PATTERNS = json.loads(os.environ.get('SENTRY_PATTERNS', '{".*": [".*"]}'))
SLACK_TOKEN = os.environ.get('SLACK_TOKEN', None)
SLACK_CHANNEL = os.environ.get('SLACK_CHANNEL', None)
SLACK_USERNAME = os.environ.get('SLACK_USERNAME', 'GitSentry')
SLACK_ICON = os.environ.get('SLACK_ICON', ':warning:')

app = Flask(__name__)
app.debug = True


@app.route('/gh', methods=['POST'])
def gh():
    log.info("Github hook triggered:")
    data = request.json
    log.info(request.data)
    repo_name = data['repository']['full_name']
    commit = process_gh_resp(data, repo_name)
    if commit:
        log.info("Added files: {}".format(",".join(commit.added)))
        log.info("Removed files: {}".format(",".join(commit.removed)))
        log.info("Modified files: {}".format(",".join(commit.modified)))
        send_githook_trigger("GitHub", repo_name, commit, SLACK_TOKEN, SLACK_USERNAME, SLACK_CHANNEL, SLACK_ICON)
    else:
        log.info("Nothing to report")
    return Response(status=202)

@app.route('/bb', methods=['POST'])
def bb():
    log.info("Bitbucket hook triggered:")
    data = json.loads(request.form['payload'])
    repo_name = data['repository']['absolute_url'][1:-1]
    commit = process_bb_resp(data, repo_name)
    if commit:
        log.info("Added files: {}".format(",".join(commit.added)))
        log.info("Removed files: {}".format(",".join(commit.removed)))
        log.info("Modified files: {}".format(",".join(commit.modified)))
        send_githook_trigger("BitBucket", repo_name, commit, SLACK_TOKEN, SLACK_USERNAME, SLACK_CHANNEL, SLACK_ICON)
    else:
        log.info("Nothing to report")
    return Response(status=202)


def get_valid_path_patterns(repo_name):
    patterns = set()
    for repo_pat in SENTRY_PATTERNS.iterkeys():
        if re.match(repo_pat, repo_name, re.IGNORECASE):
            for path_pat in SENTRY_PATTERNS[repo_pat]:
                patterns.add(path_pat)
    compiled_patterns = {re.compile(p, re.IGNORECASE) for p in patterns}
    return compiled_patterns


def process_gh_resp(data, repo_name):
    patterns = get_valid_path_patterns(repo_name)
    if not patterns:
        return None

    commits = [Commit.from_gh(c) for c in data['commits']]
    return get_merged_commit(commits, patterns)


def process_bb_resp(data, repo_name):
    patterns = get_valid_path_patterns(repo_name)
    if not patterns:
        return None

    commits = [Commit.from_bb(c) for c in data['commits']]
    return get_merged_commit(commits, patterns)


def get_merged_commit(commits, patterns):
    merged_commit = reduce(lambda c1, c2: c1.update(c2), commits)
    merged_commit.filter(patterns)
    if merged_commit.is_empty():
        return None
    else:
        return merged_commit


class Commit(object):
    def __init__(self, added=None, modified=None, removed=None):
        if not removed:
            removed = set()
        if not modified:
            modified = set()
        if not added:
            added = set()
        self.added = added
        self.modified = modified
        self.removed = removed

    def update(self, commit):
        self.added.update(commit.added)
        self.removed.update(commit.removed)
        self.modified.update(commit.modified)
        return self

    def filter(self, patterns):
        self.added = {path for path in self.added if any([p.match(path) for p in patterns])}
        self.removed = {path for path in self.removed if any([p.match(path) for p in patterns])}
        self.modified = {path for path in self.modified if any([p.match(path) for p in patterns])}

    def is_empty(self):
        return not self.added and not self.removed and not self.modified

    @staticmethod
    def from_gh(commit):
        return Commit(added=set(commit['added']), modified=set(commit['modified']), removed=set(commit['removed']))

    @staticmethod
    def from_bb(commit):
        a = {f['file'] for f in commit['files'] if f['type'] == "added"}
        m = {f['file'] for f in commit['files'] if f['type'] == "modified"}
        r = {f['file'] for f in commit['files'] if f['type'] == "removed"}
        return Commit(added=a, modified=m, removed=r)