"""create datasets and emails
Revision ID: 0001
"""
from alembic import op
import sqlalchemy as sa
revision="0001"; down_revision=None; branch_labels=None; depends_on=None
def upgrade():
    op.create_table("datasets",sa.Column("id",sa.String(36),primary_key=True),sa.Column("name",sa.String(255),nullable=False),sa.Column("source_filename",sa.String(255),nullable=False),sa.Column("source_format",sa.String(16),nullable=False),sa.Column("total_records",sa.Integer(),nullable=False),sa.Column("columns",sa.JSON(),nullable=False),sa.Column("subject_column",sa.String(255),nullable=False),sa.Column("body_column",sa.String(255),nullable=False),sa.Column("ground_truth_columns",sa.JSON(),nullable=False),sa.Column("file_size",sa.Integer(),nullable=False),sa.Column("status",sa.String(32),nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),sa.Column("updated_at",sa.DateTime(timezone=True),nullable=False))
    op.create_table("emails",sa.Column("id",sa.String(80),primary_key=True),sa.Column("dataset_id",sa.String(36),sa.ForeignKey("datasets.id",ondelete="CASCADE"),nullable=False),sa.Column("external_id",sa.String(255),nullable=False),sa.Column("subject",sa.Text(),nullable=False),sa.Column("body",sa.Text(),nullable=False),sa.Column("ground_truth",sa.JSON(),nullable=False),sa.Column("metadata",sa.JSON(),nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False))
    op.create_index("ix_datasets_name","datasets",["name"]); op.create_index("ix_datasets_status","datasets",["status"]); op.create_index("ix_emails_dataset_id","emails",["dataset_id"]); op.create_index("ix_emails_dataset_external_id","emails",["dataset_id","external_id"])
def downgrade(): op.drop_table("emails"); op.drop_table("datasets")
