from slacker import Slacker


def send_msg(text, token, username=None, channel=None, icon=None):
    """
    Send a message to Slack
    """

    if not token:
        raise ValueError("You must provide a Slack token in your configuration!")
    if not channel:
        raise ValueError("You must provide a channel to send the Slack message to!")

    slack = Slacker(token)

    if not channel.startswith("#"):
        channel = "#" + channel
    icon_url = None
    icon_emoji = None
    if icon and icon.startswith(":") and icon.endswith(":"):
        icon_emoji = icon
    else:
        icon_url = icon

    response = slack.chat.post_message(channel, text, username=username, icon_url=icon_url, icon_emoji=icon_emoji)
    return response


def send_githook_trigger(service, repo_name, commit, token, username, channel, icon):
    file_messages = []
    file_messages.extend(["\t- *{}* has been _added_".format(x) for x in commit.added])
    file_messages.extend(["\t- *{}* has been _modifed_".format(x) for x in commit.modified])
    file_messages.extend(["\t- *{}* has been _removed_".format(x) for x in commit.removed])
    msg = """
Some of the files you asked me to watch have changed in the *{}* repository on {}:
{}
    """.format(repo_name, service, "\n".join(file_messages))
    send_msg(msg, token, username, channel, icon)

