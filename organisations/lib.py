from datetime import datetime, timedelta
from django.utils.timezone import utc
from django.db import connection

from .models import Organisation

def _date_clause(issue_table, alias):
    return "sum(CASE WHEN "+ issue_table +".created > %s THEN 1 ELSE 0 END) as " + alias

# Return counts for an organisation or a set of organisations for the last week, four week
# and six months based on created date and filters
def interval_counts(issue_type, filters={}, sort='name', organisation_id=None):
    cursor = connection.cursor()
    issue_table = issue_type._meta.db_table

    now = datetime.utcnow().replace(tzinfo=utc)
    intervals = {'week': now - timedelta(7),
                 'four_weeks': now - timedelta(28),
                 'six_months': now - timedelta(365/12*6)}
    params = []

    # organisation identifying info
    select_clauses = ["""organisations_organisation.id as id""",
                      """organisations_organisation.ods_code as ods_code""",
                      """organisations_organisation.name as name"""]

    # Generate the interval counting select values and params
    for interval in intervals.keys():
        select_clauses.append(_date_clause(issue_table, interval))
        params.append(intervals[interval])
    # Add an all time count
    select_clauses.append("""count(%s.id) as all_time""" % issue_table)

    criteria_clauses = ["""organisations_organisation.id = %s.organisation_id""" % issue_table]

    # Apply filters to the issue table
    status = filters.get('status')
    if status != None:
        criteria_clauses.append(issue_table + """.status = %s""")
        params.append(status)

    service_id = filters.get('service_id')
    if service_id != None:
        criteria_clauses.append(issue_table + """.service_id = %s""")
        params.append(service_id)

    category = filters.get('category')
    if category != None:
        criteria_clauses.append(issue_table + """.category = %s""")
        params.append(category)

    # Group by clauses to go with the non-aggregate selects
    group_by_clauses = ["""organisations_organisation.id""",
                        """organisations_organisation.name""",
                        """organisations_organisation.ods_code"""]

    # Assemble the SQL
    select_text = "SELECT %s" % ', '.join(select_clauses)

    # For a single organisation, we always want a row returned, so the filter criteria
    # go in a left join and the organisation is specified in the where clause
    if organisation_id != None:
        from_text = """FROM organisations_organisation LEFT JOIN %s""" % issue_table
        criteria_text = "ON %s" % " AND ".join(criteria_clauses)
        criteria_text += " WHERE organisations_organisation.id = %s"
        params.append(organisation_id)
    # For multiple organisations we want whatever meets the filter criteria
    else:
        from_text = "FROM organisations_organisation, %s" % issue_table
        criteria_text = "WHERE %s" % " AND ".join(criteria_clauses)

    group_text = "GROUP BY %s" % ', '.join(group_by_clauses)
    sort_text = "ORDER BY %s" % sort
    query = "%s %s %s %s %s" % (select_text, from_text, criteria_text, group_text, sort_text)
    cursor.execute(query, params)

    desc = cursor.description
    # Return a list of dictionaries
    counts = [ dict(zip([col[0] for col in desc], row)) for row in cursor.fetchall() ]
    # Or for a single organisation, just one
    if organisation_id:
         counts = counts[0]
    return counts
