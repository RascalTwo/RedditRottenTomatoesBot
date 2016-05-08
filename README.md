# Reddit /r/RottenTomatoes Top Box Office Poster

Made for /u/MasterLawlz to post all movies that enter the Top Box office and have been out for at least one weekend to /r/RottenTomatoes.

Requires `username`, `password`, `client_id`, and `client_secret` for the Reddit account the bot will run under.

Also requires the account to have moderator status in the subreddit of which the sidebar will be updated, as the bot must approve it's own posts.

# Dependencies

- [Python 3](https://www.python.org/download/releases/3.0/)
- [Requests](http://docs.python-requests.org/en/master/)

You can have the dependencies automatically installed by executing `pip install -r requirements.txt`, although there is only one dependency. You will obviously have to obtain Python and pip manually.

# Setup

## Reddit Account

Go the `Apps` tab of your reddit account preferences.

![reddit-prefs](https://i.imgur.com/fA33kDv.png)

Give it a name of whatever you want - you can change this later - and a redirect URL of `http://127.0.0.1:6504/authorize_callback`. You won't need to use this for this bot, it just requires this field to be filled out. Also make sure to mark it as a `Script`.

![app-creating](https://i.imgur.com/s44fMdw.png)

You'll then see the ID and secret of the application. You enter these in the `client_id` and `client_secret` fields. They are marked red and green respectively.

![app-details](https://i.imgur.com/hydS5CT.png)

You will also need to fill out the empty fields in the `config.json` accordinly. You should have text before the forward slash & version number in the `user_agent` field be the same as the app name you created.

![config-filled-out](https://i.imgur.com/LKw0Kq0.png)

That's all the setup required for the app. You can now exeute the script and it should work.

## Configuration

The configuration file - `config.json` looks like this:

```json
{
    "client_id": "",
    "client_secret": "",
    "user_agent": "SomethingUnique/1.0 by /u/Rascal_Two for /u/MasterLawlz running under /u/tomatometerbot at /r/RottenTomatoes",
    "username": "",
    "password": "",
    "subreddit": "RottenTomatoes",
    "check_rate": 3600,
    "post_title_format": "{movie_title} - {tomato_score}%",
    "post_flairs": {
        "enabled": true,
        "flairs": [
            {
                "min": 0,
                "max": 59,
                "text": "Rotten",
                "class": "rotten"
            },
            {
                "min": 60,
                "max": 100,
                "text": "Fresh",
                "class": "fresh"
            }
        ]
    }
}
```

- `client_id` is the client ID of the reddit application setup above.
- `client_secret` is the cllicne secret of the reddit application setup above.
- `user_agent` is what reddit identifies the bot as. The more unique this is the better, as common user agents have their rates limited.
- `username` is the username of the Reddit account the bot will run under.
- `password` is the password of the Reddit account the bot will run under.
- `subreddit` is the name of the subreddit sidebar that's being updated.
- `check_rate` is the rate - in seconds - that the bot will check and make posts.
- `post_title_format` is the format of which the post titles are. `{movie_title}` gets replaced with the title of the movie, and `{tomato_score}` gets replaced with the rotten tomatoe score for that movie.
- `post_flairs`
    - `enabled` - Determines if posts are even given flairs.
    - `flairs` - List of all possible flairs.

*****

A flair has four properties:

- `min` is the minimum value the tomato score can be for the flair to be applied.
- `max` is the maximum value the tomato score can be for the flair to be applied.
- `text` is the text of the flair assigned to the post.
- `class` is the class of the flair assigned to the post.

The `text` and `class` must match that of your alreay created flairs on the subreddit. It's not making a flair with these two attributes, it's getting the flair from the subreddit with these two attributes.

Be careful, they are case sensitive.

## Subreddit

You need to do two things to the subreddit to get the flairs to work. You can ignore this if you have `post_flairs` `enabled` set to false.

The first of which is the stylesheet.

![sample-stylesheet](https://i.imgur.com/stNobTN.png)

You need to simply add your flairs. This technically is not required, but that's how you do it.

Next you need to define the flairs in the flair section:

![flairs-set](https://i.imgur.com/qBQHa25.png)

You're *defining* the text and css class here. You need to match the flair `text` and `class` to these values, not the other way around.

Be careful, they are case sensitive.

*****

# Explanation

When the bot is first created it loads the configuration data from the `config.json` file. It then sends the `username`, `password`, `client_id`, and `client_secret` to the Reddit API to get a access token. This access token lasts 60 minutes, and is used to do actions as the reddit account.

This access token is automatically refreshed, so the bot can run for a very long time.

Every minute it outputs a message stating it's uptime. It also checks if it's time to check for new valid movies. If it it, then it scrapes the backend of the rotten tomatoes API - `https://d2a5cgar23scu2.cloudfront.net/api/private/v1.0/m/list/find?page=1&limit=10&type=in-theaters&sortBy=popularity`.

I won't bore you by explaining every attribute of the GET request, it's human readable.

*****

The top ten movies fetched are cycled through, and each is checked to see if it's in the `data.json` file. The entire premiere date is then fetched from the movie page, and it is calculated if two weekends have passed since it's premiere.

If so, then the movie is added to the list of movies to post.

*****

For every movie that is approved to be posted, they're first posted. Then the flair is calculated based on the the tomato score, and the flair is assigned to the post.

*****

# TODO

> I may do some of these, I may do none of these. Depends on how worth-it said feature would be.

- Convert to [PRAW](https://praw.readthedocs.io/en/stable/)

- Logging to file.