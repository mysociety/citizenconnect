from datetime import datetime, timedelta
from django.utils.timezone import utc
from django.db import connection

from issues.models import Problem


# Return a clause summing the number of records in a table whose field meets a criteria
def _sum_clause(table, field, criteria):
    return "SUM(CASE WHEN " + table + "." + field + " " + criteria + " THEN 1 ELSE 0 END)"


# Return the number of records created more recently than the date supplied
def _date_clause(table, field, alias):
    return _sum_clause(table, field, "> %s") + " AS " + alias


# Get fraction of true values over non-null values for boolean field
def _boolean_clause(table, field):
    clause = _sum_clause(table, field, "= %s")
    clause += " / "
    clause += "NULLIF(" + _sum_clause(table, field, "IS NOT NULL") + ", 0)::float" + " AS " + field
    return clause


# Return the average of non-null values in an integer field
def _average_value_clause(table, field, alias):
    clause = "AVG(" + table + "." + field + ") AS " + alias
    return clause


# Generate the interval counting select values and params for problems
def _create_problem_selects(intervals, data_intervals, boolean_fields, average_fields, select_clauses, params):
    for interval in intervals.keys():
        if interval in data_intervals:
            select_clauses.append(_date_clause('issues_problem', 'created', interval))
            params.append(intervals[interval])

    # Add a problem all time count
    if 'all_time' in data_intervals:
        select_clauses.append("""count(issues_problem.id) as all_time""")

    if 'all_time_open' in data_intervals:
        select_clauses.append(_sum_clause('issues_problem', 'status', "in %s") + """ as all_time_open""")
        params.append(tuple(Problem.OPEN_STATUSES))

    if 'all_time_closed' in data_intervals:
        select_clauses.append(_sum_clause('issues_problem', 'status', "in %s") + """ as all_time_closed""")
        params.append(tuple(Problem.CLOSED_STATUSES))

    # Get the True/False percentages and counts
    for field in boolean_fields:
        select_clauses.append(_boolean_clause('issues_problem', field))
        params.append(True)

    # Get the averages
    for field in average_fields:
        select_clauses.append(_average_value_clause('issues_problem', field, "average_" + field))


def _apply_problem_filters(problem_filters, problem_filter_clauses, organisation_id, params):

    # Filter out any REJECTED problems.
    problem_filter_clauses.append("issues_problem.publication_status != %s")
    params.append(Problem.REJECTED)

    # Apply problem filters to the issue table
    for criteria in ['status', 'service_id', 'category', 'moderated', 'publication_status']:
        value = problem_filters.get(criteria)
        if value is not None:
            if type(value) != tuple:
                value = (value,)
            problem_filter_clauses.append("issues_problem." + criteria + " in %s""")
            params.append(value)

    breach = problem_filters.get('breach')
    if breach is not None:
        problem_filter_clauses.append("issues_problem.breach = %s""")
        params.append(breach)

    formal_complaint = problem_filters.get('formal_complaint')
    if formal_complaint is not None:
        problem_filter_clauses.append("issues_problem.formal_complaint = %s""")
        params.append(formal_complaint)

    service_code = problem_filters.get('service_code')
    if service_code is not None:
        if organisation_id:
            raise NotImplementedError("Filtering for service on a single organisation uses service_id, not service_code")
        else:
            if type(service_code) != tuple:
                service_code = (service_code,)
            problem_filter_clauses.append("""issues_problem.service_id in (select id from organisations_service where service_code in %s)""")
            params.append(service_code)


# Generate the interval counting select values and params for reviews
def _create_review_selects(intervals, data_intervals, select_clauses, params):

    for interval in intervals.keys():
        if interval in data_intervals:
            select_clauses.append(_date_clause('reviews_display_review',
                                               'api_published',
                                               'reviews_' + interval))
            params.append(intervals[interval])

    # Add a review all time count
    if 'all_time' in data_intervals:
        select_clauses.append("""count(reviews_display_review) as reviews_all_time""")


def _apply_organisation_filters(organisation_filters,
                                organisation_filter_clauses,
                                organisation_id,
                                tables,
                                params):
    # Apply organisation filters to the organisation table
    if organisation_id is not None:
        organisation_filter_clauses.append("organisations_organisation.id = %s")
        params.append(organisation_filters['organisation_id'])

    organisation_ids = organisation_filters.get('organisation_ids')
    if organisation_ids is not None:
        if len(organisation_ids) == 0:
            raise ValueError("To filter by organisations, at least one organisation id must be supplied")
        organisation_filter_clauses.append("organisations_organisation.id in %s")
        params.append(organisation_ids)

    organisation_type = organisation_filters.get('organisation_type')
    if organisation_type is not None:
        if organisation_id:
            raise NotImplementedError("Filtering for an organisation type is unnecessary for a single organisation")
        else:
            if type(organisation_type) != tuple:
                organisation_type = (organisation_type,)
            organisation_filter_clauses.append("organisations_organisation.organisation_type in %s")
            params.append(organisation_type)

    ccg = organisation_filters.get('ccg')
    if ccg is not None:
        if organisation_id:
            raise NotImplementedError("Filtering for a ccg is unnecessary for a single organisation")
        else:
            if type(ccg) != tuple:
                ccg = (ccg,)
            # Filtering by CCG requires joining to the Organisation Parent tables
            # Because Organisation Parent are connected to CCGs
            tables.append('organisations_organisationparent_ccgs')
            organisation_filter_clauses.append("organisations_organisationparent_ccgs.organisationparent_id = organisations_organisation.parent_id")
            organisation_filter_clauses.append("organisations_organisationparent_ccgs.ccg_id in %s")
            params.append(ccg)


# Return problem or review counts for a set of organisations for the last week, four weeks
# and six months based on created date and problem and organisation filters.
# The filter_type parameter can be set to 'problems' or 'reviews' to return each type of data.
# Filter values can be specified as a single value or a tuple of values. Possible problem_filters
# are: status, service_id, category, breach, service_code, moderated and publication_status.
# Possible organisation_filters are organisation_type, ccg.
# A threshold can be expressed as a tuple of interval and value and only organisations
# where the number of issues reported in the interval equals or exceeds the value will be returned.
# By default, all organisations matching the organisation filters will be returned. To get only
# organisations that have at least one problem matching the problem filters, apply a threshold
# like ('all_time', 1).
# Possible list values for extra_organisation_data are 'coords', 'type' and 'average_recommendation_rating'.
# Possible data_intervals are 'week', 'four_weeks', 'six_months', 'all_time'. For problems only,
# there are also 'all_time_open', and 'all_time_closed'.
# Possible values for average_fields are 'time_to_acknowledge', 'time_to_address' - returned dicts will
# include a key 'average_time_to_acknowledge' or 'average_time_to_address, whose value will be
# the average time in minutes.
# Possible values for boolean_fields are 'happy_service' and 'happy_outcome' - returned dicts will include
# a key 'happy_service' or 'happy_outcome' whose value will be the fraction of issues for which the measure
# is true.
def interval_counts(problem_filters={},
                    organisation_filters={},
                    threshold=None,
                    extra_organisation_data=[],
                    data_intervals=['week', 'four_weeks', 'six_months', 'all_time'],
                    average_fields=['time_to_acknowledge', 'time_to_address'],
                    boolean_fields=['happy_service', 'happy_outcome'],
                    data_type='problems'):
    cursor = connection.cursor()

    now = datetime.utcnow().replace(tzinfo=utc)
    intervals = {'week': now - timedelta(days=7),
                 'four_weeks': now - timedelta(days=28),
                 'six_months': now - timedelta(days=365/12*6)}

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
                                  WHEN organisations_organisation.organisation_type = 'clinics'
                                  THEN 'Clinic'
                                  ELSE 'Unknown' END) AS type""")
        group_by_clauses.append('type')
    if 'average_recommendation_rating' in extra_organisation_data:
        select_clauses.append("""organisations_organisation.average_recommendation_rating as average_recommendation_rating""")
        group_by_clauses.append("organisations_organisation.average_recommendation_rating")

    if data_type == 'problems':
        _create_problem_selects(intervals,
                                data_intervals,
                                boolean_fields,
                                average_fields,
                                select_clauses,
                                params)

        problem_filter_clauses = ["""organisations_organisation.id = issues_problem.organisation_id"""]
        _apply_problem_filters(problem_filters, problem_filter_clauses, organisation_id, params)

    elif data_type == 'reviews':
        _create_review_selects(intervals, data_intervals, select_clauses, params)
        # We'll manually add a join to reviews_display_review_organisations below
        review_filter_clauses = ["""reviews_display_review_organisations.review_id = reviews_display_review.id"""]
        # We don't want any "replies" to show up in these counts
        review_filter_clauses.append("""reviews_display_review.in_reply_to_id IS NULL""")

    else:
        raise "Unknown data_type: %s" % data_type

    organisation_filter_clauses = []

    _apply_organisation_filters(organisation_filters,
                                organisation_filter_clauses,
                                organisation_id,
                                tables,
                                params)

    # Having clauses to implement the threshold
    having_text = ''
    if threshold is not None:
        if data_type == 'problems':
            table = 'issues_problem'
        else:
            table = 'reviews_display_review'

        if organisation_id:
            raise NotImplementedError("Threshold is not implemented for a single organisation")
        interval, cutoff = threshold
        allowed_intervals = intervals.keys() + ['all_time']
        if interval not in allowed_intervals:
            raise NotImplementedError("Threshold can only be set on the value of one of: %s" % allowed_intervals)

        if interval == 'all_time':
            having_clause = "count(" + table + ".id)"
        else:
            having_clause = _sum_clause(table, 'created', "> %s")
            params.append(intervals[interval])
        having_text = "HAVING " + having_clause + " >= %s"
        params.append(cutoff)

    # Assemble the SQL
    select_text = "SELECT %s" % ', '.join(select_clauses)

    # The problem or review filter criteria go in a left join and the organisation filter
    # criteria are specified in the where clause
    tables.append("organisations_organisation")
    from_text = """FROM %s""" % ", ".join(tables)
    criteria_text = ''
    if data_type == 'problems':
        from_text += """ LEFT JOIN issues_problem"""
        criteria_text = "ON %s" % " AND ".join(problem_filter_clauses)
    elif data_type == 'reviews':
        # This is a bit hacky, but we need to join to reviews via an interim table
        from_text += """ LEFT JOIN reviews_display_review_organisations ON organisations_organisation.id = reviews_display_review_organisations.organisation_id"""
        from_text += """ LEFT JOIN reviews_display_review"""
        criteria_text += " ON %s" % " AND ".join(review_filter_clauses)

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
    counts = [dict(zip([col[0] for col in desc], row)) for row in cursor.fetchall()]
    # Or for a single organisation, just one
    if organisation_id:
        counts = counts[0]
    return counts
