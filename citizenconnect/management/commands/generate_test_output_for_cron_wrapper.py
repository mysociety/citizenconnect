import sys

from django.core.management.base import NoArgsCommand



class Command(NoArgsCommand):
    """
    This test command generates output to stdout, and stderr, and throws an
    exception. This lets us test how the cron wrapper script behaves.
    """

    help = "Send some output to stdout and stderr, for testing the cron wrapper"

    def handle_noargs(self, *args, **options):

        sys.stderr.write("This is to STDERR\n");
        sys.stdout.write("This is to STDOUT\n");
        sys.stderr.write("This is to STDERR again\n");

        raise Exception("Boom - exception raised")
