"""The personal wrong-problem list is a read-only view of OJ submissions."""
from django.db.models import Count, Exists, OuterRef, Subquery

from problem.models import Problem
from utils.api import APIView, serializers
from ..models import JudgeStatus, Submission


WRONG_RESULTS = (
    JudgeStatus.COMPILE_ERROR, JudgeStatus.WRONG_ANSWER,
    JudgeStatus.CPU_TIME_LIMIT_EXCEEDED, JudgeStatus.REAL_TIME_LIMIT_EXCEEDED,
    JudgeStatus.MEMORY_LIMIT_EXCEEDED, JudgeStatus.RUNTIME_ERROR,
    JudgeStatus.PARTIALLY_ACCEPTED,
)


class WrongProblemQuerySerializer(serializers.Serializer):
    offset = serializers.IntegerField(default=0, min_value=0)
    limit = serializers.IntegerField(default=20, min_value=1, max_value=100)


class WrongProblemSerializer(serializers.ModelSerializer):
    failure_count = serializers.IntegerField(read_only=True)
    last_failure_time = serializers.DateTimeField(read_only=True)
    last_failure_result = serializers.IntegerField(read_only=True)
    last_failure_submission_id = serializers.CharField(read_only=True)
    latest_result = serializers.IntegerField(read_only=True)
    latest_submission_id = serializers.CharField(read_only=True)

    class Meta:
        model = Problem
        fields = ("id", "_id", "title", "difficulty", "failure_count", "last_failure_time",
                  "last_failure_result", "last_failure_submission_id", "latest_result", "latest_submission_id")


class WrongProblemListAPI(APIView):
    def get(self, request):
        # Never accept user_id/username from the client, including for administrators.
        if not request.user.is_authenticated:
            return self.private_error("Please login first", "permission-denied")
        if request.user.is_disabled:
            return self.private_error("Your account is disabled", "permission-denied")
        query = WrongProblemQuerySerializer(data=request.GET)
        if not query.is_valid():
            return self.invalid_serializer(query)

        personal_submissions = Submission.objects.filter(
            user_id=request.user.id, contest_id__isnull=True, problem_id=OuterRef("pk"))
        failures = personal_submissions.filter(result__in=WRONG_RESULTS)
        failure_counts = failures.order_by().values("problem_id").annotate(total=Count("id")).values("total")
        latest_failure = failures.order_by("-create_time", "-id")
        latest_submission = personal_submissions.order_by("-create_time", "-id")

        # A problem appears once, even after multiple failures. Rejudges are reflected
        # immediately because no duplicate notebook table or synchronization job exists.
        problems = Problem.objects.filter(visible=True, contest_id__isnull=True).annotate(
            has_failure=Exists(failures)).filter(has_failure=True).annotate(
                failure_count=Subquery(failure_counts[:1]),
                last_failure_time=Subquery(latest_failure.values("create_time")[:1]),
                last_failure_result=Subquery(latest_failure.values("result")[:1]),
                last_failure_submission_id=Subquery(latest_failure.values("id")[:1]),
                latest_result=Subquery(latest_submission.values("result")[:1]),
                latest_submission_id=Subquery(latest_submission.values("id")[:1]),
        ).order_by("-last_failure_time", "-id")

        offset = query.validated_data["offset"]
        limit = query.validated_data["limit"]
        response = self.success({"total": problems.count(),
                                 "results": WrongProblemSerializer(problems[offset:offset + limit], many=True).data})
        response["Cache-Control"] = "no-store"
        return response

    def private_error(self, message, error):
        response = self.error(message, error)
        response["Cache-Control"] = "no-store"
        return response
