
from organisations.choices_api import ChoicesAPI


class ReviewsAPI(object):

    """
    Abstraction around the Choices API that hides the pagination and parsing
    of the XML and lets us use an iterator to access the reviews.
    """

    def __init__(self):
        self.api = ChoicesAPI()

        self.current_page = 0
        self.has_next_page = False
        self.reviews = []

    def __iter__(self):
        return	 self

    def next(self):

        try:
            return self.reviews.pop(0)
        except IndexError:
            raise StopIteration
