from unittest.mock import MagicMock

from app.models.content import CalendarItemStatus, ContentCalendarItem, GeneratedPost
from app.models.publishing import PublishingJob, PublishingJobStatus
from app.services.calendar import delete_calendar_item


def test_delete_calendar_item_removes_publishing_jobs():
    item = ContentCalendarItem(
        id=10,
        company_id=1,
        generated_post_id=20,
        platform="linkedin",
        post_type="professional",
        status=CalendarItemStatus.queued,
    )
    post = GeneratedPost(
        id=20,
        company_id=1,
        platform="linkedin",
        post_type="professional",
        content_json='{"hook":"Hi","body":"Body","hashtags":[],"platform":"linkedin","post_type":"professional"}',
        model="test",
    )
    job = PublishingJob(
        id=99,
        company_id=1,
        calendar_item_id=10,
        connected_account_id=1,
        status=PublishingJobStatus.failed,
    )

    session = MagicMock()
    get_row = MagicMock()
    get_row.first.return_value = (item, post)
    jobs_row = MagicMock()
    jobs_row.all.return_value = [job]
    versions_row = MagicMock()
    versions_row.all.return_value = []
    session.exec.side_effect = [get_row, jobs_row, versions_row]

    delete_calendar_item(session, 1, 10)

    session.delete.assert_any_call(job)
    session.delete.assert_any_call(item)
    session.delete.assert_any_call(post)
    session.commit.assert_called_once()
