from datetime import timedelta

from django.utils import timezone

from contest.models import Contest
from contest.tests import DEFAULT_CONTEST_DATA
from problem.tests import DEFAULT_PROBLEM_DATA, ProblemCreateTestBase
from utils.api.tests import APITestCase
from .models import JudgeStatus, Submission
from .views.wrong_problem import WRONG_RESULTS


class WrongProblemListTests(APITestCase):
    def setUp(self):
        self.user = self.create_user("notebook-user", "test-pass")
        self.other = self.create_user("other-user", "test-pass", login=False)
        self.problem = self.make_problem("1000")
        self.url = self.reverse("wrong_problem_list_api")

    def make_problem(self, display_id):
        return ProblemCreateTestBase.add_problem(dict(DEFAULT_PROBLEM_DATA, _id=display_id), self.user)

    def submit(self, result, problem=None, user=None, contest=None):
        owner = user or self.user
        return Submission.objects.create(user_id=owner.id, username=owner.username, problem=problem or self.problem,
                                         result=result, language="C++", code="private-code", contest=contest)

    def get_list(self, **params):
        response = self.client.get(self.url, params)
        self.assertSuccess(response)
        self.assertEqual(response["Cache-Control"], "no-store")
        return response.data["data"]

    def test_empty_without_submissions(self):
        self.assertEqual(self.get_list(), {"total": 0, "results": []})

    def test_excluded_results_do_not_create_wrong_problems(self):
        for result in (JudgeStatus.ACCEPTED, JudgeStatus.PENDING, JudgeStatus.JUDGING, JudgeStatus.SYSTEM_ERROR):
            self.submit(result)
        self.assertEqual(self.get_list(), {"total": 0, "results": []})

    def test_all_effective_failures_are_included_and_deduplicated(self):
        for result in WRONG_RESULTS:
            self.submit(result)
        data = self.get_list()
        self.assertEqual(data["total"], 1)
        self.assertEqual(data["results"][0]["failure_count"], len(WRONG_RESULTS))
        self.assertEqual(data["results"][0]["_id"], "1000")

    def test_accepted_after_failure_retains_history_and_shows_latest_result(self):
        wrong = self.submit(JudgeStatus.WRONG_ANSWER)
        accepted = self.submit(JudgeStatus.ACCEPTED)
        row = self.get_list()["results"][0]
        self.assertEqual(row["last_failure_submission_id"], wrong.id)
        self.assertEqual(row["last_failure_result"], JudgeStatus.WRONG_ANSWER)
        self.assertEqual(row["latest_submission_id"], accepted.id)
        self.assertEqual(row["latest_result"], JudgeStatus.ACCEPTED)

    def test_other_users_and_forged_owner_parameters_do_not_leak(self):
        self.submit(JudgeStatus.WRONG_ANSWER, user=self.other)
        self.assertEqual(self.get_list(user_id=self.other.id, username=self.other.username)["total"], 0)
        self.submit(JudgeStatus.RUNTIME_ERROR)
        self.assertEqual(self.get_list()["results"][0]["failure_count"], 1)

    def test_administrator_still_only_sees_own_wrong_problems(self):
        self.submit(JudgeStatus.WRONG_ANSWER)
        self.create_super_admin()
        self.assertEqual(self.get_list(user_id=self.user.id)["total"], 0)

    def test_anonymous_and_disabled_accounts_are_rejected(self):
        self.client.logout()
        self.assertFailed(self.client.get(self.url))
        self.client.force_login(self.user)
        self.user.is_disabled = True
        self.user.save()
        self.assertFailed(self.client.get(self.url))

    def test_hidden_problem_is_excluded(self):
        self.submit(JudgeStatus.WRONG_ANSWER)
        self.problem.visible = False
        self.problem.save()
        self.assertEqual(self.get_list()["total"], 0)

    def test_contest_submissions_and_contest_problems_are_excluded(self):
        contest = Contest.objects.create(**dict(DEFAULT_CONTEST_DATA, created_by=self.user))
        self.submit(JudgeStatus.WRONG_ANSWER, contest=contest)
        contest_problem = self.make_problem("A")
        contest_problem.contest = contest
        contest_problem.save()
        self.submit(JudgeStatus.WRONG_ANSWER, problem=contest_problem)
        self.assertEqual(self.get_list()["total"], 0)

    def test_rejudge_updates_counts_and_removes_last_failure(self):
        first = self.submit(JudgeStatus.WRONG_ANSWER)
        second = self.submit(JudgeStatus.RUNTIME_ERROR)
        Submission.objects.filter(pk=first.id).update(result=JudgeStatus.ACCEPTED)
        self.assertEqual(self.get_list()["results"][0]["failure_count"], 1)
        Submission.objects.filter(pk=second.id).update(result=JudgeStatus.ACCEPTED)
        self.assertEqual(self.get_list()["total"], 0)

    def test_deleted_problem_is_excluded(self):
        self.submit(JudgeStatus.WRONG_ANSWER)
        self.problem.delete()
        self.assertEqual(self.get_list()["total"], 0)

    def test_created_time_determines_latest_even_for_late_results(self):
        newer = self.submit(JudgeStatus.ACCEPTED)
        older = self.submit(JudgeStatus.WRONG_ANSWER)
        Submission.objects.filter(pk=older.id).update(create_time=newer.create_time - timedelta(hours=1))
        self.assertEqual(self.get_list()["results"][0]["latest_result"], JudgeStatus.ACCEPTED)

    def test_pagination_is_stable_and_total_counts_problems(self):
        same_time = timezone.now()
        for i in range(3):
            submission = self.submit(JudgeStatus.WRONG_ANSWER, problem=self.make_problem(str(2000 + i)))
            Submission.objects.filter(pk=submission.pk).update(create_time=same_time)
        first = self.get_list(limit=2)
        second = self.get_list(limit=2, offset=2)
        self.assertEqual(first["total"], 3)
        ids = [p["id"] for p in first["results"] + second["results"]]
        self.assertEqual(len(set(ids)), 3)
        self.assertEqual(ids, sorted(ids, reverse=True))

    def test_invalid_pagination_is_rejected(self):
        for params in ({"limit": 0}, {"limit": 101}, {"offset": -1}, {"offset": "bad"}, {"limit": "1.5"}):
            self.assertFailed(self.client.get(self.url, params))

    def test_no_source_code_or_problem_content_in_list(self):
        self.submit(JudgeStatus.WRONG_ANSWER)
        row = self.get_list()["results"][0]
        self.assertNotIn("code", row)
        self.assertNotIn("description", row)
        self.assertNotIn("info", row)
