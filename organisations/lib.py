from datetime import datetime, timedelta
from django.utils.timezone import utc
from django.db import connection

from .models import Organisation

# Return a clause summing the number of records in a table whose field meets a criteria
def _sum_clause(field, criteria):
    return "SUM(CASE WHEN issues_problem."+ field + " " + criteria + " THEN 1 ELSE 0 END)"

# Return the number of records created more recently than the date supplied
def _date_clause(alias):
    return _sum_clause('created', "> %s") + " AS " + alias

# Get fraction of true values over non-null values for boolean field
def _boolean_clause(field):
    clause = _sum_clause(field, "= %s")
    clause += " / "
    clause += "NULLIF(" + _sum_clause(field, "IS NOT NULL") + ", 0)::float" + " AS " + field
    return clause

# Return the count of non-null values for a boolean field
def _count_clause(field, alias):
    return _sum_clause(field, "IS NOT NULL") + " AS " + alias

# Return the average of non-null values in an integer field
def _average_value_clause(field, alias):
    clause = "AVG(issues_problem."+ field +") AS " + alias
    return clause

# Return problem counts for a set of organisations for the last week, four weeks
# and six months based on created date and problem and organisation filters.
# Filter values can be specified as a single value or a tuple of values. Possible problem_filters
# are: status, service_id, category, breach, service_code. Possible organisation_filters are
# organisation_type, ccg.
# A threshold can be expressed as a tuple of interval and value and only organisations
# where the number of issues reported in the interval equals or exceeds the value will be returned.
# By default, all organisations matching the organisation filters will be returned. To get only
# organisations that have at least one problem matching the problem filters, apply a threshold
# like ('all_time', 1).
# Possible list values for extra_organisation_data are 'coords' and 'type'.
def interval_counts(problem_filters={},
                    organisation_filters={},
                    threshold=None,
                    extra_organisation_data=[],
                    problem_data_intervals=['week', 'four_weeks', 'six_months', 'all_time']):
    cursor = connection.cursor()

    now = datetime.utcnow().replace(tzinfo=utc)
    intervals = {'week': now - timedelta(days=7),
                 'four_weeks': now - timedelta(days=28),
                 'six_months': now - timedelta(days=365/12*6)}

    boolean_counts = ['happy_service', 'happy_outcome']

    average_fields = ['time_to_acknowledge', 'time_to_address']

    organisation_id = organisation_filters.get('organisation_id')

    params = []
    tables = []

    # organisation identifying info
    select_clauses = ["""organisations_organisation.id AS id""",
                      """organisations_organisation.ods_code AS ods_code""",
                      """organisations_organisation.name AS name"""]

    # Group by clauses to go with the non-aggregate selects
    group_by_clauses = ["organisations_organisation.id",
                         "organisations_organisation.name",
                         "organisations_organisation.ods_code"]

    if 'coords' in extra_organisation_data:
        select_clauses.append("""ST_X(organisations_organisation.point) AS lon""")
        select_clauses.append("""ST_Y(organisations_organisation.point) AS lat""")
        group_by_clauses.append('lon')
        group_by_clauses.append('lat')
    if 'type' in extra_organisation_data:
        select_clauses.append("""(CASE WHEN organisations_organisation.organisation_type = 'gppractices'
                                  THEN 'GP'
                                  WHEN organisations_organisation.organisation_type = 'hospitals'
                                  THEN 'Hospital'
                                  ELSE 'Unknown' END) AS type""")
        group_by_clauses.append('type')

    # Generate the interval counting select values and params
    for interval in intervals.keys():
        if interval in problem_data_intervals:
            select_clauses.append(_date_clause(interval))
            params.append(intervals[interval])

    # Add an all time count
    if 'all_time' in problem_data_intervals:
        select_clauses.append("""count(issues_problem.id) as all_time""")


    # Get the True/False percentages and counts
    for field in boolean_counts:
        select_clauses.append(_boolean_clause(field))
        params.append(True)
        select_clauses.append(_count_clause(field, '%s_count' % field))

    # Get the averages
    for field in average_fields:
        select_clauses.append(_average_value_clause(field, "average_" + field))

    problem_filter_clauses = ["""organisations_organisation.id = issues_problem.organisation_id"""]
    organisation_filter_clauses = []

    # Apply problem filters to the issue table
    for criteria in ['status', 'service_id', 'category']:
        value = problem_filters.get(criteria)
        if value != None:
            if type(value) != tuple:
                value = (value,)
            problem_filter_clauses.append("issues_problem." + criteria + " in %s""")
            params.append(value)

    breach = problem_filters.get('breach')
    if breach != None:
        problem_filter_clauses.append("issues_problem.breach = %s""")
        params.append(breach)

    service_code = problem_filters.get('service_code')
    if service_code != None:
        if organisation_id:
            raise NotImplementedError("Filtering for service on a single organisation uses service_id, not service_code")
        else:
            if type(service_code) != tuple:
                service_code = (service_code,)
            problem_filter_clauses.append("""issues_problem.service_id in (select id from organisations_service where service_code in %s)""")
            params.append(service_code)

    # Apply organisation filters to the organisation table
    if organisation_id != None:
        organisation_filter_clauses.append("organisations_organisation.id = %s")
        params.append(organisation_filters['organisation_id'])

    organisation_type = organisation_filters.get('organisation_type')
    if organisation_type != None:
        if organisation_id:
             raise NotImplementedError("Filtering for an organisation type is unnecessary for a single organisation")
        else:
             if type(organisation_type) != tuple:
                organisation_type = (organisation_type,)
             organisation_filter_clauses.append("organisations_organisation.organisation_type in %s")
             params.append(organisation_type)


    ccg = organisation_filters.get('ccg')
    if ccg != None:
        if organisation_id:
             raise NotImplementedError("Filtering for a ccg is unnecessary for a single organisation")
        else:
            if type(ccg) != tuple:
                ccg = (ccg,)
            tables.append('organisations_organisation_ccgs')
            organisation_filter_clauses.append("organisations_organisation_ccgs.organisation_id = organisations_organisation.id")
            organisation_filter_clauses.append("organisations_organisation_ccgs.ccg_id in %s")
            params.append(ccg)


    # Having clauses to implement the threshold
    having_text = ''
    if threshold != None:
        if organisation_id:
            raise NotImplementedError("Threshold is not implemented for a single organisation")
        interval, cutoff = threshold
        allowed_intervals = intervals.keys() + ['all_time']
        if interval not in allowed_intervals:
            raise NotImplementedError("Threshold can only be set on the value of one of: %s" % allowed_intervals)

        if interval == 'all_time':
            having_clause = "count(issues_problem.id)"
        else:
            having_clause =  _sum_clause('created', "> %s")
            params.append(intervals[interval])
        having_text = "HAVING " + having_clause + " >= %s"
        params.append(cutoff)

    # Assemble the SQL
    select_text = "SELECT %s" % ', '.join(select_clauses)

    # The problem filter criteria go in a left join and the organisation filter
    # criteria are specified in the where clause
    tables.append("organisations_organisation")
    from_text = """FROM %s""" % ", ".join(tables)
    from_text += """ LEFT JOIN issues_problem"""
    criteria_text = "ON %s" % " AND ".join(problem_filter_clauses)
    if organisation_filter_clauses:
        criteria_text += " WHERE %s" % " AND ".join(organisation_filter_clauses)

    group_text = "GROUP BY %s" % ', '.join(group_by_clauses)
    sort_text = "ORDER BY name"
    query = "%s %s %s %s %s %s" % (select_text,
                                   from_text,
                                   criteria_text,
                                   group_text,
                                   having_text,
                                   sort_text)

    cursor.execute(query, params)
    desc = cursor.description
    # Return a list of dictionaries
    counts = [ dict(zip([col[0] for col in desc], row)) for row in cursor.fetchall() ]
    # Or for a single organisation, just one
    if organisation_id:
         counts = counts[0]
    return counts
