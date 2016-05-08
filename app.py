#!/usr/bin/env python3

# The MIT License (MIT)

# Copyright (c) 2016 RascalTwo @ therealrascaltwo@gmail.com

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
import json
import time
import re
import requests
from datetime import datetime
from datetime import timedelta

class HTTPException(Exception):
    """Whenever there is a non-200 response code returned."""


class RedditAPIException(Exception):
    """Reddit itself returned a error based on our POST/GET request."""


def handle_response(response_expected):
    """Decorator to catch errors within request responses."""
    def wrap(function):
        def function_wrapper(*args, **kwargs):
            """Function wrapper."""
            response = function(*args, **kwargs)

            if response.status_code != 200:
                raise HTTPException("'{}' returned a status code of {}"
                                    .format(function.__name__,
                                            response.status_code))
            if response_expected == "json":
                data = response.json()
                if "errors" in data and len(data["errors"]) != 0:
                    raise RedditAPIException("\n".join("'{0}' error {1[0]}: {1[1]}"
                                                       .format(function.__name__, error)
                                                       for error in data["errors"]))

                if "error" in data:
                    raise RedditAPIException("'{}' error: {}"
                                             .format(function.__name__,
                                                     data["error"]))

                if "json" in data:
                    if "errors" in data["json"] and len(data["json"]["errors"]) != 0:
                        raise RedditAPIException("\n".join("'{0}' error {1[0]}: {1[1]}"
                                                           .format(function.__name__, error)
                                                           for error in data["json"]["errors"]))

                    if "error" in data["json"]:
                        raise RedditAPIException("'{}' error: {}"
                                                 .format(function.__name__,
                                                         data["json"]["error"]))


                return response.json()
            return response.text
        return function_wrapper
    return wrap


class RedditRottenTomatoesPoster(object):

    def __init__(self):
        """Create bot and import 'config.json'."""
        with open("config.json", "r") as config_file:
            self.config = json.loads(config_file.read())

        try:
            with open("data.json", "r") as data_file:
                self.data = json.loads(data_file.read())
        except:
            self.data = []
            self._save_data()

        self.token = None

    def _headers(self, auth=True):
        """Header(s) to send to Reddit.

        Keyword Arguments:
        `auth` (bool(true)) -- Should the 'Authorization' header be
                               included. Default is true. Options is provided
                               because '_get_token' must have this false.

        Returns:
        `dict` -- With keys as headers, and values as header contents.

        """
        if auth:
            return {
                "User-Agent": self.config["user_agent"],
                "Authorization": "{} {}".format(self.token["token_type"],
                                                self.token["access_token"])
            }
        return {
            "User-Agent": self.config["user_agent"]
        }

    @handle_response("json")
    def _get_token(self):
        """Return the access_token for this session.

        Returns:
        `dict` -- contains 'access_token', 'refresh_token', and 'token_type'.

        May throw a 'HTTPException' or 'RedditAPIException'.

        """
        client_auth = requests.auth.HTTPBasicAuth(self.config["client_id"],
                                                  self.config["client_secret"])
        post_data = {
            "grant_type": "password",
            "username": self.config["username"],
            "password": self.config["password"]
        }
        return requests.post("https://www.reddit.com/api/v1/access_token",
                             auth=client_auth,
                             data=post_data,
                             headers=self._headers(False))

    def _save_data(self):
        with open("data.json", "w") as data_file:
            data_file.write(json.dumps(self.data))

    def refresh_token(self):
        """Attempt to refresh the access token."""
        try:
            self.token = self._get_token()
        except (HTTPException, RedditAPIException) as token_exception:
            self.token = None
            print("Could not get access token from the Reddit API.\n"
                  "This can be caused by mutiple things, such as:\n"
                  "  Reddit not being accessable\n"
                  "  Username and/or password being incorrect.\n"
                  "  'client_id' and/or 'client_secret' being incorrect.\n"
                  "  Applicaiton on Reddit not created as a 'script'.\n\n"
                  "Raw Error: {}".format(token_exception))

    def run(self):
        """Start the loop for the bot to run in."""
        self.refresh_token()

        uptime = 0

        while True:
            print("Uptime: {}s".format(uptime))

            if self.token["expires_in"] <= 60:
                print("Refreshing access token...", end="")
                self.refresh_token()
                print("Access token refreshed.")

            if uptime % self.config["check_rate"] == 0:
                print("Updating...", end="")
                try:

                    for movie in self.get_movies_to_post():
                        post_made = self.make_post(self.config["post_title_format"]
                                                   .format(movie_title=movie["title"],
                                                           tomato_score=movie["tomatoScore"]),
                                                   "https://rottentomatoes.com{}"
                                                   .format(movie["url"]))

                        post_made = post_made["json"]["data"]["name"]

                        if self.config["post_flairs"]["enabled"]:

                            try:
                                my_flair = [flair for flair in self.config["post_flairs"]["flairs"] if flair["min"] <= movie["tomatoScore"] and movie["tomatoScore"] <= flair["max"]][0]
                            except Exception as exception:
                                print("Something went wrong.\n"
                                      "Attempted to get the flair for a post with a tomato score of '{}'\n\n"
                                      "Raw Error: {}"
                                      .format(movie["tomatoScore"],
                                              exception))

                            flair_options = self.get_flair_options(post_made)

                            try:
                                flair_id = [flair["flair_template_id"] for flair in flair_options["choices"] if flair["flair_text"] == my_flair["text"] and flair["flair_css_class"] == my_flair["class"]][0]
                            except Exception as exception:
                                print("Something went wrong.\n"
                                      "Attempted to get the flair id.\n"
                                      "Was unable to find a flair with text of '{}' and class of '{}'\n\n"
                                      "Raw Error: {}"
                                      .format(flair["text"],
                                              flair["class"],
                                              exception))

                            my_flair["id"] = flair_id

                            self.set_post_flair(post_made, my_flair)

                        self.approve_post(post_made)

                        del movie["tomatoScore"]

                        self.data.append(movie)

                        self._save_data()

                    print("Updated.")

                except(HTTPException, RedditAPIException) as exception:
                    print("There was an error making a post.\n"
                          "{}".format(exception))

            uptime += 60
            self.token["expires_in"] -= 60
            time.sleep(60)

    @handle_response("json")
    def get_top_box_office(self):
        response = requests.get("https://d2a5cgar23scu2.cloudfront.net/api/private/v1.0/m/list/find?page=1&limit=10&type=in-theaters&sortBy=popularity",
                                headers=self._headers())
        return response

    @handle_response("html")
    def get_movie_page(self, url):
        response = requests.get("https://rottentomatoes.com{}".format(url))

        return response

    def get_movies_to_post(self):
        results = self.get_top_box_office()["results"]

        keys = ["id", "title", "url"]

        movies_to_post = []
        for movie in results:
            score = movie["tomatoScore"]
            movie = {
                "id": movie["id"],
                "title": movie["title"],
                "url": movie["url"]
            }
            if movie in self.data:
                continue

            premiere_date = self.get_movie_page(movie["url"]).split('itemprop="datePublished" content="')[1].split('"')[0]

            date_object = datetime.strptime(premiere_date, "%Y-%m-%d")

            if (date_object.weekday() >= 5):
                wait_days = (date_object.weekday() - 14) * -1
            else:
                wait_days = (date_object.weekday() - 7) * -1

            if ((date_object + timedelta(days=wait_days) - datetime.now()).total_seconds() < 0):
                movies_to_post.append({
                    "id": movie["id"],
                    "title": movie["title"],
                    "url": movie["url"],
                    "tomatoScore": score
                })
        return movies_to_post

    @handle_response("json")
    def get_flair_options(self, name):
        post_data = {
            "link": name
        }
        return requests.post("https://oauth.reddit.com/r/{}/api/flairselector"
                             .format(self.config["subreddit"]),
                             data=post_data,
                             headers=self._headers())

    @handle_response("json")
    def set_post_flair(self, name, flair):
        post_data = {
            "api_type": "json",
            "flair_template_id": flair["id"],
            "link": name,
            "text": flair["text"]

        }
        return requests.post("https://oauth.reddit.com/r/{}/api/selectflair"
                             .format(self.config["subreddit"]),
                             data=post_data,
                             headers=self._headers())

    @handle_response("json")
    def make_post(self, title, link):
        post_data = {
            "api_type": "json",
            "kind": "link",
            "extension": "json",
            "resubmit": True,
            "sendreplies": True,
            "sr": self.config["subreddit"],
            "title": title,
            "url": link
        }
        return requests.post("https://oauth.reddit.com/api/submit",
                               data=post_data,
                               headers=self._headers(True))

    @handle_response("json")
    def approve_post(self, id):
        post_data = {
            "id": id
        }
        return requests.post("https://oauth.reddit.com/api/approve",
                               data=post_data,
                               headers=self._headers(True))


if __name__ == "__main__":
    RedditRottenTomatoesPoster().run()
