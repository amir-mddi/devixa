from django_filters import rest_framework as django_filters


class CommonTimeFilter(django_filters.FilterSet):
    start_time = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    end_time = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    from_id = django_filters.NumberFilter(field_name='id', lookup_expr='gte')

    class Meta:
        fields = ['start_time', 'end_time', 'from_id']
