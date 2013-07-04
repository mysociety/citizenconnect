import xml.etree.ElementTree as ET

from django.core.management.base import BaseCommand, CommandError

from reviews_submit.models import Question, Answer


class Command(BaseCommand):
    args = '<org_type> <xml_file>'
    help = 'Import questions from the provided XML file'

    def handle(self, *args, **options):
        if len(args) < 2:
            raise CommandError("Usage: ./manage.py import_questions <org_type> </path/to/questions.xml>")

        org_type, xml_file = args[:2]
        try:
            tree = ET.parse(xml_file)
        except IOError:
            raise CommandError("File does not exist: %s" % xml_file)

        root = tree.getroot()

        for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
            api_question_id = int(entry.find('{http://www.w3.org/2005/Atom}id').text)
            title = entry.find('{http://www.w3.org/2005/Atom}title').text

            try:
                question = Question.objects.get(api_question_id=api_question_id, org_type=org_type)
            except Question.DoesNotExist:
                question = Question(api_question_id=api_question_id, org_type=org_type)

            question.title = title
            question.save()

            for answer in entry.findall('{http://syndication.nhschoices.nhs.uk/schemas/answer}Answer'):
                answer_id = answer.get('id')

                try:
                    answer_model = question.answers.get(api_answer_id=answer_id)
                except Answer.DoesNotExist:
                    answer_model = Answer(api_answer_id=answer_id)

                answer_model.text = answer.text
                question.answers.add(answer_model)
