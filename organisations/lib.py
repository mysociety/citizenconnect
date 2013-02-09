from datetime import datetime, timedelta

# Return counts for a model queryset for the last week, four week and six months
# based on created date
def interval_counts(queryset):
    counts = {}
    now = datetime.now()
    intervals = {'week': 7,
                 'four_weeks': 28,
                 'six_months': 365/12*6}
    for interval_name, days_ago in intervals.items():
        lower_bound = now - timedelta(days_ago)
        counts[interval_name] = queryset.filter(created__gte=lower_bound).count
    return counts
