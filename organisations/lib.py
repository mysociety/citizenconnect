from datetime import datetime, timedelta
from django.utils.timezone import utc
from django.db import connection

from .models import Organisation

# Return a clause summing the number of records in a table whose field meets a criteria
def _sum_clause(table, field, criteria):
    return "SUM(CASE WHEN "+ table +"."+ field + " " + criteria + " THEN 1 ELSE 0 END)"

# Return the number of records created more recently than the date supplied
def _date_clause(issue_table, alias):
    return _sum_clause(issue_table, 'created', "> %s") + " AS " + alias

# Get fraction of true values over non-null values for boolean field
def _boolean_clause(issue_table, field):
    clause = _sum_clause(issue_table, field, "= %s")
    clause += " / "
    clause += "NULLIF(" + _sum_clause(issue_table, field, "IS NOT NULL") + ", 0)::float" + " AS " + field
    return clause

# Return the count of non-null values for a boolean field
def _count_clause(issue_table, field, alias):
    return _sum_clause(issue_table, field, "IS NOT NULL") + " AS " + alias

# Return the average of non-null values in an integer field
def _average_value_clause(issue_table, field, alias):
    clause = "AVG("+ issue_table +"."+ field +") AS " + alias
    return clause

# Return counts for an organisation or a set of organisations for the last week, four week
# and six months based on created date and filters. Filter values can be specified as a single value
# or a tuple of values. For a set of organisations, a threshold can be expressed as a tuple of interval
# and value and only organisations where the number of issues reported in the interval equals or exceeds
# the value will be returned.
def interval_counts(issue_type, filters={}, sort='name', organisation_id=None, threshold=None):
    cursor = connection.cursor()
    issue_table = issue_type._meta.db_table

    now = datetime.utcnow().replace(tzinfo=utc)
    intervals = {'week': now - timedelta(days=7),
                 'four_weeks': now - timedelta(days=28),
                 'six_months': now - timedelta(days=365/12*6)}

    boolean_counts = ['happy_service', 'happy_outcome']

    average_fields = ['time_to_acknowledge', 'time_to_address']

    params = []
    extra_tables = []

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

    # Get the True/False percentages and counts
    for field in boolean_counts:
        select_clauses.append(_boolean_clause(issue_table,  field))
        params.append(True)
        select_clauses.append(_count_clause(issue_table, field, '%s_count' % field))

    # Get the averages
    for field in average_fields:
        select_clauses.append(_average_value_clause(issue_table, field, "average_" + field))

    criteria_clauses = ["""organisations_organisation.id = %s.organisation_id""" % issue_table]

    # Apply simple filters to the issue table
    for criteria in ['status', 'service_id', 'category']:
        value = filters.get(criteria)
        if value != None:
            if type(value) != tuple:
                value = (value,)
            criteria_clauses.append(issue_table + "." + criteria + " in %s""")
            params.append(value)

    service_code = filters.get('service_code')
    if service_code != None:
        if organisation_id:
            raise NotImplementedError("Filtering for service on a single organisation uses service_id, not service_code")
        else:
            if type(service_code) != tuple:
                service_code = (service_code,)
            extra_tables.append('organisations_service')
            criteria_clauses.append("organisations_service.id = %s.service_id" % issue_table)
            criteria_clauses.append("organisations_service.service_code in %s")
            params.append(service_code)

    organisation_type = filters.get('organisation_type')
    if organisation_type != None:
        if organisation_id:
             raise NotImplementedError("Filtering for an organisation type is unnecessary for a single organisation")
        else:
             if type(organisation_type) != tuple:
                organisation_type = (organisation_type,)
             criteria_clauses.append("organisations_organisation.organisation_type in %s")
             params.append(organisation_type)

    # Group by clauses to go with the non-aggregate selects
    group_by_clauses = ["""organisations_organisation.id""",
                        """organisations_organisation.name""",
                        """organisations_organisation.ods_code"""]

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
            having_clause = "count("+ issue_table + ".id)"
        else:
            having_clause =  _sum_clause(issue_table, 'created', "> %s")
            params.append(intervals[interval])
        having_text = "HAVING " + having_clause + " >= %s"
        params.append(cutoff)

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
        from_text = "FROM organisations_organisation, %s " % issue_table
        if extra_tables:
            from_text += ", " + ", ".join(extra_tables)
        criteria_text = "WHERE %s" % " AND ".join(criteria_clauses)

    group_text = "GROUP BY %s" % ', '.join(group_by_clauses)
    sort_text = "ORDER BY %s" % sort
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
