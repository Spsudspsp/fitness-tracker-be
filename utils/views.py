from django.contrib.postgres.aggregates import ArrayAgg
from django.core.exceptions import ImproperlyConfigured
from django.db.models import Max, Min
from rest_framework.decorators import action
from rest_framework.response import Response


class FilterValuesViewSetMixin:
    """
    Adds GET /filter-values/

    Supported filter metadata types:
    - ranges: returns the minimum and maximum database values for the fields
    - lists: returns lists of distinct values for the fields
    """

    filter_values_fields = {}
    supported_filter_types = ['ranges', 'lists']
    custom_filter_types = []

    def get_filter_values_fields(self):
        filter_values_fields = {**self.filter_values_fields}

        unknown_filter_types = (
            set(filter_values_fields) - set(self.supported_filter_types) - set(self.custom_filter_types)
        )

        if unknown_filter_types:
            raise ImproperlyConfigured(
                f'{self.__class__.__name__} has unsupported filter value types: '
                f'{", ".join(sorted(unknown_filter_types))}.'
            )

        for filter_type in self.supported_filter_types:
            if filter_type not in filter_values_fields:
                filter_values_fields[filter_type] = []
        return filter_values_fields

    def _get_ranges_aggregates(self):
        fields = self.get_filter_values_fields()['ranges']
        aggregations = {}

        for field in fields:
            aggregations.update({f'min_{field}': Min(field), f'max_{field}': Max(field)})

        return aggregations

    def _get_lists_aggregates(self):
        fields = self.get_filter_values_fields()['lists']
        aggregations = {}

        for field in fields:
            aggregations[field] = ArrayAgg(field, distinct=True, ordering=field)

        return aggregations

    def _get_custom_aggregates(self):
        aggregations = {}

        for filter_type in self.custom_filter_types:
            get_aggregates = getattr(self, f'get_{filter_type}_aggregates', None)

            if not callable(get_aggregates):
                raise ImproperlyConfigured(
                    f'{self.__class__.__name__} lists custom filter type '
                    f'"{filter_type}" but does not define get_{filter_type}_aggregates().'
                )

            current_aggregations = get_aggregates()

            if not isinstance(current_aggregations, dict):
                raise ImproperlyConfigured(f'get_{filter_type}_aggregates() is not a dict.')

            aggregations.update(current_aggregations)

        return aggregations

    def get_filter_values(self, qs):
        return qs.aggregate(
            **self._get_ranges_aggregates(), **self._get_lists_aggregates(), **self._get_custom_aggregates()
        )

    @action(detail=False, methods=['get'], url_path='filter-values')
    def filter_values(self, request, *args, **kwargs):
        qs = self.get_queryset()

        if request.query_params.get('apply_filters') == 'true':
            qs = self.filter_queryset(qs)

        data = self.get_filter_values(qs)

        return Response(data)
