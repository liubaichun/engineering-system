from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q
from .models import Project, WorkerGroup, Worker
from .serializers import (
    ProjectSerializer,
    WorkerGroupListSerializer,
    WorkerGroupDetailSerializer,
    WorkerGroupWriteSerializer,
    WorkerListSerializer,
    WorkerDetailSerializer,
    WorkerWriteSerializer,
)


class ProjectViewSet(viewsets.ModelViewSet):
    """
    项目管理
    list   : GET  /api/v1/projects/
    create : POST /api/v1/projects/
    retrieve: GET /api/v1/projects/{id}/
    update : PUT  /api/v1/projects/{id}/
    partial: PATCH/api/v1/projects/{id}/
    destroy: DELETE /api/v1/projects/{id}/
    """
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "code", "address"]
    ordering_fields = ["created_at", "start_date", "name"]


class WorkerGroupViewSet(viewsets.ModelViewSet):
    """
    班组管理
    list                : GET  /api/v1/groups/
    create              : POST /api/v1/groups/
    retrieve (详情含成员): GET  /api/v1/groups/{id}/
    update/patch        : PUT/PATCH /api/v1/groups/{id}/
    destroy             : DELETE /api/v1/groups/{id}/

    Extra Actions:
    GET /api/v1/groups/{id}/workers/  - 获取班组人员列表
    """
    queryset = WorkerGroup.objects.annotate(
        _worker_count=Count("workers", filter=Q(workers__status="active"))
    )
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "phone"]
    ordering_fields = ["name", "created_at"]

    def get_serializer_class(self):
        if self.action == "list":
            return WorkerGroupListSerializer
        if self.action == "retrieve":
            return WorkerGroupDetailSerializer
        return WorkerGroupWriteSerializer

    # ---------- 自定义动作 ----------

    @action(detail=True, methods=["get"])
    def workers(self, request, pk=None):
        """获取某班组下的人员列表"""
        group = self.get_object()
        workers = group.workers.all()
        page = self.paginate_queryset(workers)
        if page is not None:
            serializer = WorkerListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = WorkerListSerializer(workers, many=True)
        return Response(serializer.data)


class WorkerViewSet(viewsets.ModelViewSet):
    """
    施工人员管理
    list   : GET  /api/v1/workers/
    create : POST /api/v1/workers/
    retrieve: GET /api/v1/workers/{id}/
    update : PUT  /api/v1/workers/{id}/
    partial: PATCH/api/v1/workers/{id}/
    destroy: DELETE /api/v1/workers/{id}/

    Extra Actions:
    GET /api/v1/workers/group/{group_id}/ - 按班组筛选
    GET /api/v1/workers/stats/            - 人员统计
    """
    queryset = Worker.objects.select_related("group").all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["status", "work_type", "skill_level", "group"]
    search_fields = ["name", "id_card", "phone"]
    ordering_fields = ["name", "created_at", "entry_date"]

    def get_serializer_class(self):
        if self.action == "list":
            return WorkerListSerializer
        if self.action == "retrieve":
            return WorkerDetailSerializer
        return WorkerWriteSerializer

    # ---------- 自定义动作 ----------

    @action(detail=False, methods=["get"], url_path="group/(?P<group_id>[^/.]+)")
    def by_group(self, request, group_id=None):
        """按班组 ID 筛选人员"""
        workers = self.get_queryset().filter(group_id=group_id)
        page = self.paginate_queryset(workers)
        if page is not None:
            serializer = WorkerListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = WorkerListSerializer(workers, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def stats(self, request):
        """人员统计概览"""
        total = Worker.objects.count()
        active = Worker.objects.filter(status="active").count()
        inactive = Worker.objects.filter(status="inactive").count()
        paused = Worker.objects.filter(status="paused").count()

        # 按工种统计
        by_work_type = (
            Worker.objects
            .values("work_type")
            .annotate(count=Count("id"))
            .order_by("-count")
        )
        work_type_map = dict(Worker.WORK_TYPE_CHOICES)
        for item in by_work_type:
            item["work_type_display"] = work_type_map.get(item["work_type"], item["work_type"])

        # 按班组统计
        by_group = (
            WorkerGroup.objects
            .annotate(count=Count("workers", filter=Q(workers__status="active")))
            .values("id", "name", "count")
            .order_by("-count")
        )

        return Response({
            "total": total,
            "active": active,
            "inactive": inactive,
            "paused": paused,
            "by_work_type": list(by_work_type),
            "by_group": list(by_group),
        })
