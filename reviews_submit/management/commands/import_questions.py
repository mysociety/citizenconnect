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
            api_question_id = int(entry.find('{http://www.w3.org/2005/Atom}id').text)
            title = entry.find('{http://www.w3.org/2005/Atom}title').text

            try:
                question = Question.objects.get(api_question_id=api_question_id)
            except Question.DoesNotExist:
                question = Question(api_question_id=api_question_id)

            question.title = title
            question.save()

            for answer in entry.findall('{http://syndication.nhschoices.nhs.uk/schemas/answer}Answer'):
                answer_id = answer.get('id')

                try:
                    answer_model = question.answer_set.get(api_answer_id=answer_id)
                except Answer.DoesNotExist:
                    answer_model = Answer(api_answer_id=answer_id)

                answer_model.text = answer.text
                question.answer_set.add(answer_model)
