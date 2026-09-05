from pydantic import BaseModel


class BackupFileSummary(BaseModel):
    file_name: str | None = None
    size_bytes: int = 0
    encrypted: bool = False


class BackupRetentionSummary(BaseModel):
    daily_keep: int = 0
    weekly_keep: int = 0
    monthly_keep: int = 0
    daily_count: int = 0
    weekly_count: int = 0
    monthly_count: int = 0


class BackupTaskSummary(BaseModel):
    installed: bool = False
    next_run_time: str | None = None
    last_run_time: str | None = None
    last_task_result: int | None = None
    healthy: bool = False


class RestoreTestSummary(BaseModel):
    available: bool = False
    success: bool | None = None
    finished_at: str | None = None
    message: str | None = None


class BackupRecoveryStatus(BaseModel):
    backup_configured: bool
    backup_success: bool | None = None
    database: str | None = None
    finished_at: str | None = None
    duration_seconds: float | None = None
    message: str | None = None

    latest_backup: BackupFileSummary
    cloud_enabled: bool
    cloud_status: str
    encryption_enabled: bool

    retention: BackupRetentionSummary
    scheduled_task: BackupTaskSummary
    restore_test: RestoreTestSummary

    viewer_can_run_actions: bool
