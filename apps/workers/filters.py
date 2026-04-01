from django_filters import FilterSet, rest_framework as filters
from .models import Worker, WorkerGroup, Project


class WorkerFilter(FilterSet):
    """人员过滤器"""
    name = filters.CharFilter(lookup_expr="icontains")
    id_card = filters.CharFilter()
    phone = filters.CharFilter()
    work_type = filters.ChoiceFilter(choices=Worker.WORK_TYPE_CHOICES)
    skill_level = filters.ChoiceFilter(choices=Worker.SKILL_LEVEL_CHOICES)
    status = filters.ChoiceFilter(choices=Worker.STATUS_CHOICES)
    group = filters.NumberFilter()
    entry_date_from = filters.DateFilter(field_name="entry_date", lookup_expr="gte")
    entry_date_to = filters.DateFilter(field_name="entry_date", lookup_expr="lte")

    class Meta:
        model = Worker
        fields = ["name", "id_card", "phone", "work_type", "skill_level", "status", "group"]


class WorkerGroupFilter(FilterSet):
    """班组过滤器"""
    name = filters.CharFilter(lookup_expr="icontains")
    project = filters.NumberFilter()

    class Meta:
        model = WorkerGroup
        fields = ["name", "project"]


class ProjectFilter(FilterSet):
    """项目过滤器"""
    name = filters.CharFilter(lookup_expr="icontains")
    code = filters.CharFilter()
    status = filters.ChoiceFilter(choices=Project.STATUS_CHOICES)
    start_date_from = filters.DateFilter(field_name="start_date", lookup_expr="gte")
    start_date_to = filters.DateFilter(field_name="start_date", lookup_expr="lte")

    class Meta:
        model = Project
        fields = ["name", "code", "status", "start_date_from", "start_date_to"]
