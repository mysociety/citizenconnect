import xml.etree.ElementTree as ET
from django.core.management.base import BaseCommand, CommandError

from reviews_submit.models import Question, Answer

class Command(BaseCommand):
    args = '<file>'
    help = 'Import questions from the provided XML file'

    def handle(self, *args, **options):
        if len(args) < 1:
            raise CommandError("Usage: ./manage.py import_questions ./path/to/questions.xml")

        tree = ET.parse(args[0])
        root = tree.getroot()

        for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
            title = entry.find('{http://www.w3.org/2005/Atom}title').text
            question = Question(title=title)
            question.save()

            for answer in entry.findall('{http://syndication.nhschoices.nhs.uk/schemas/answer}Answer'):
                question.answer_set.create(text=answer.text, value=answer.get('id'))
