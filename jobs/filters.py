import django_filters

from .models import Job


class JobFilter(django_filters.FilterSet):
    location = django_filters.CharFilter(field_name='location', lookup_expr='icontains')
    job_type = django_filters.ChoiceFilter(choices=Job.JOB_TYPE_CHOICES)
    salary_min = django_filters.NumberFilter(field_name='salary_min', lookup_expr='gte')
    salary_max = django_filters.NumberFilter(field_name='salary_max', lookup_expr='lte')
    company = django_filters.NumberFilter(field_name='company_id')
    is_active = django_filters.BooleanFilter(field_name='is_active')
    skills = django_filters.CharFilter(method='filter_by_skills')

    class Meta:
        model = Job
        fields = ['location', 'job_type', 'salary_min', 'salary_max', 'company', 'is_active', 'skills']

    def filter_by_skills(self, queryset, name, value):
        """
        Supports filtering by comma-separated skill names or IDs:
        e.g. ?skills=django,sql or ?skills=Python
        """
        if not value:
            return queryset
        skill_names = [s.strip() for s in value.split(',') if s.strip()]
        for skill_name in skill_names:
            if skill_name.isdigit():
                queryset = queryset.filter(skills__id=int(skill_name))
            else:
                queryset = queryset.filter(skills__name__icontains=skill_name)
        return queryset.distinct()
