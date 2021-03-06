"""Dealership review analyzer."""

import re
import requests
from bs4 import BeautifulSoup
from textblob import TextBlob


class CarReviewAnalyzer:
    """Car review analyzer class."""

    def __init__(self, num_reviews_print=0, url_list=[]):
        """Car Review Analyzer constructor."""
        self.num_reviews_print = num_reviews_print
        self.url_list = url_list
        self.reviews = {}
        self.top_users = []

    def find_rating(self, rating_element):
        """Find rating of dealership."""
        rating_string = rating_element["class"][4].split('-')[1]
        rating = int(rating_string) / 10
        return rating

    def parse_username(self, usertext):
        """Find username of reviewer."""
        list1 = usertext.split('-')
        if len(list1) > 2:
            temp = "-".join(list1[1:])
        else:
            temp = list1[1]
        user = temp.strip()
        return user

    def parse_html(self, textpage):
        """Parse HTML."""
        soup = BeautifulSoup(textpage, "html.parser")
        for review in soup.findAll('div', attrs={'class': 'review-entry'}):
            user_element = review.find('span', attrs={'class': 'italic'})
            user = self.parse_username(user_element.text)
            rating_element = review.find('div',
                                         attrs={'class': 'rating-static'})
            rating = self.find_rating(rating_element)
            content = review.find('p',
                                  attrs={'class': 'review-content'}).text
            recommend = review.find('div',
                                    attrs={'class': 'boldest'}).text.strip()
            date = review.find('div', attrs={'class': 'font-20'}).text
            title = review.find('h3').text
            # only save reviews that are consistent
            high_rating_consistent = rating >= 2.5 and recommend == "Yes"
            low_rating_consistent = rating < 2.5 and recommend == "No"
            if high_rating_consistent or low_rating_consistent:
                if user not in self.reviews:
                    self.reviews[user] = {"review": content, "rating": rating,
                                          "recommend": recommend,
                                          "date": date, "title": title}

    def get_reviews(self):
        """Scrapes pages and puts reveiws into dictionary."""
        for url in self.url_list:
            # try to scrape each page
            try:
                page = requests.get(url)
            except requests.exceptions.ConnectionError:
                print("CONNECTION ERROR: Connection was refused."
                      + " Double-check that you have the correct URL.")
            except requests.exceptions.Timeout:
                print("TIMEOUT ERROR: The request timed out."
                      + " Re-run program to try again.")
            except requests.exceptions.TooManyRedirects:
                print("TOO MANY REDIRECTS ERROR: This URL is most "
                      + "likely bad. Try a new one.")
            except requests.exceptions.RequestException as error:
                print(error)

            # put data into a dictionary
            self.parse_html(page.text)

    def clean_review(self, review):
        """Remove handles, special characters and links."""
        pattern = r'(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)'
        new_string = re.sub(pattern, " ", review).split()
        return ' '.join(new_string)

    def get_review_sentiment(self):
        """Calculate sentiment score of each review."""
        for user in self.reviews:
            cleaned = self.clean_review(self.reviews[user]['review'])
            analysis = TextBlob(cleaned)
            score = analysis.sentiment.polarity
            self.top_users.append({"user": user,
                                   "rating": self.reviews[user]["rating"],
                                   "sentiment": score})

    def sort_results(self):
        """Sort results by rating and then by polarity score."""
        self.top_users = sorted(self.top_users,
                                key=lambda i: (-i['rating'], -i['sentiment']))

    def print_results(self):
        """Print results."""
        # sort
        self.sort_results()
        # print
        print("TOP " + str(self.num_reviews_print) +
              " OVERLY POSITIVE REVIEWS")
        print("-----------------------------------------------------"
              + "---------------")
        for i in range(self.num_reviews_print):
            print(self.reviews[self.top_users[i]["user"]]["date"])
            print("rating: " + str(self.top_users[i]["rating"]) + "/5.0")
            print(self.top_users[i]["user"] + ": " +
                  self.reviews[self.top_users[i]["user"]]["title"])
            print(self.reviews[self.top_users[i]["user"]]["review"])
            print("-------------------------------------------------"
                  + "-------------------")


def main():
    """Run program."""
    num_reviews_print = 3
    url_list = ["https://www.dealerrater.com/dealer/McKaig-Chevrolet-Buick-A"
                + "-Dealer-For-The-People-dealer-reviews-23685/page1/?filter"
                + "=ALL_REVIEWS#link",
                "https://www.dealerrater.com/dealer/McKaig-Chevrolet-Buick-A"
                + "-Dealer-For-The-People-dealer-reviews-23685/page2/?filter"
                + "=ALL_REVIEWS#link",
                "https://www.dealerrater.com/dealer/McKaig-Chevrolet-Buick-A"
                + "-Dealer-For-The-People-dealer-reviews-23685/page3/?filter"
                + "=ALL_REVIEWS#link",
                "https://www.dealerrater.com/dealer/McKaig-Chevrolet-Buick-A"
                + "-Dealer-For-The-People-dealer-reviews-23685/page4/?filter"
                + "=ALL_REVIEWS#link",
                "https://www.dealerrater.com/dealer/McKaig-Chevrolet-Buick-A"
                + "-Dealer-For-The-People-dealer-reviews-23685/page5/?filter"
                + "=ALL_REVIEWS#link"]

    # scrape reviews, clean them, and get sentiment score
    # then sort based off of rating, then sentiment score
    analyzer = CarReviewAnalyzer(num_reviews_print, url_list)
    analyzer.get_reviews()
    analyzer.get_review_sentiment()
    analyzer.print_results()


if __name__ == "__main__":
    main()
