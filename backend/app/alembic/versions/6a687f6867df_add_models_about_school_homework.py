"""add models about school homework

Revision ID: 6a687f6867df
Revises: e090aa701634
Create Date: 2021-10-08 16:17:04.370004

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '6a687f6867df'
down_revision = 'e090aa701634'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('group_member',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False, comment='主键'),
    sa.Column('group_id', sa.BigInteger(), nullable=False, comment='所属小组id'),
    sa.Column('name', sa.String(), nullable=False, comment='学生姓名'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('group_id', 'name')
    )
    op.create_index('group_member_group_id_idx', 'group_member', ['group_id'], unique=False)
    op.create_index('group_member_name_idx', 'group_member', ['name'], unique=False)
    op.create_table('homework',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False, comment='id，主键'),
    sa.Column('publisher_id', sa.BigInteger(), nullable=False, comment='发布者用户id'),
    sa.Column('subject_id', sa.Integer(), nullable=False, comment='学科id'),
    sa.Column('pub_time', sa.TIMESTAMP(), nullable=False, comment='发布时间'),
    sa.Column('end_time', sa.TIMESTAMP(), nullable=False, comment='截止时间'),
    sa.Column('title', sa.String(length=20), nullable=False, comment='作业标题'),
    sa.Column('desc', sa.Text(), nullable=False, comment='作业描述'),
    sa.Column('images', sa.String(), nullable=True, comment='图片'),
    sa.Column('videos', sa.String(), nullable=True, comment='视频'),
    sa.Column('audios', sa.String(), nullable=True, comment='声音'),
    sa.Column('docs', sa.String(), nullable=True, comment='文档'),
    sa.Column('is_delete', sa.Boolean(), server_default=sa.text('False'), nullable=False, comment='是否删除'),
    sa.Column('create_time', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='创建时间'),
    sa.Column('update_time', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True, comment='最后修改时间'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('homework_end_time_idx', 'homework', ['end_time'], unique=False)
    op.create_index('homework_pub_time_idx', 'homework', ['pub_time'], unique=False)
    op.create_index('homework_publisher_id_idx', 'homework', ['publisher_id'], unique=False)
    op.create_table('homework_answer',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False, comment='id，主键'),
    sa.Column('submitter_member_id', sa.BigInteger(), nullable=False, comment='提交人成员id'),
    sa.Column('homework_id', sa.BigInteger(), nullable=False, comment='作业id'),
    sa.Column('images', sa.String(), nullable=True, comment='图片'),
    sa.Column('videos', sa.String(), nullable=True, comment='视频'),
    sa.Column('audios', sa.String(), nullable=True, comment='声音'),
    sa.Column('docs', sa.String(), nullable=True, comment='文档'),
    sa.Column('create_time', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='创建时间'),
    sa.Column('update_time', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True, comment='最后修改时间'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('homework_answer_submitter_member_id_idx', 'homework_answer', ['submitter_member_id'], unique=False)
    op.create_table('homework_answer_status',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False, comment='id，主键'),
    sa.Column('homework_id', sa.BigInteger(), nullable=False, comment='作业id'),
    sa.Column('student_class_id', sa.BigInteger(), nullable=False, comment='学生所属班级id'),
    sa.Column('student_name', sa.String(), nullable=False, comment='学生姓名'),
    sa.Column('score', sa.String(length=1), server_default='0', nullable=False, comment='作业评分: 1-A 2-B 3-C 4-D'),
    sa.Column('status', sa.String(length=2), server_default='1', nullable=False, comment='作业状态'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('homework_answer_status_homework_id_idx', 'homework_answer_status', ['homework_id'], unique=False)
    op.create_index('homework_answer_status_status_idx', 'homework_answer_status', ['status'], unique=False)
    op.create_index('homework_answer_status_student_class_id_idx', 'homework_answer_status', ['student_class_id'], unique=False)
    op.create_index('homework_answer_status_student_name_idx', 'homework_answer_status', ['student_name'], unique=False)
    op.create_table('homework_assign',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False, comment='id，主键'),
    sa.Column('homework_id', sa.BigInteger(), nullable=False, comment='作业id'),
    sa.Column('class_id', sa.BigInteger(), nullable=False, comment='班级id'),
    sa.Column('group_id', sa.BigInteger(), nullable=False, comment='小组id，0 表示全班'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('homework_id', 'class_id', 'group_id')
    )
    op.create_index('homework_assign_class_id_idx', 'homework_assign', ['class_id'], unique=False)
    op.create_index('homework_assign_group_id_idx', 'homework_assign', ['group_id'], unique=False)
    op.create_index('homework_assign_homework_id_idx', 'homework_assign', ['homework_id'], unique=False)
    op.create_table('message',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False, comment='id，主键'),
    sa.Column('sender_member_id', sa.BigInteger(), nullable=False, comment='消息发送人的成员id，0 表示系统发送'),
    sa.Column('category', sa.String(length=2), nullable=False, comment='类型: 1-校本作业提示 2-校本作业评论'),
    sa.Column('receiver_class_id', sa.BigInteger(), nullable=False, comment='消息接收人班级id'),
    sa.Column('receiver', sa.String(), nullable=False, comment='消息接收人姓名'),
    sa.Column('context', sa.String(), nullable=True, comment='内容'),
    sa.Column('is_delete', sa.Boolean(), server_default=sa.text('False'), nullable=False, comment='是否删除'),
    sa.Column('create_time', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='创建时间'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('message_receiver_class_id_idx', 'message', ['receiver_class_id'], unique=False)
    op.create_index('message_receiver_idx', 'message', ['receiver'], unique=False)
    op.create_index('message_sender_member_id_idx', 'message', ['sender_member_id'], unique=False)
    op.drop_index('class_group_member_group_id_idx', table_name='class_group_member')
    op.drop_index('class_group_member_member_id_idx', table_name='class_group_member')
    op.drop_table('class_group_member')
    op.alter_column('apply4class', 'family_relation',
               existing_type=sa.VARCHAR(length=2),
               comment='亲属关系',
               existing_comment='亲属关系: 1-本人 2-爸爸 3-妈妈 4-爷爷 5-奶奶 6-外公 7-外婆 8-哥哥 9-姐姐',
               existing_nullable=True)
    op.alter_column('class_member', 'family_relation',
               existing_type=sa.VARCHAR(length=2),
               comment='亲属关系id',
               existing_comment='亲属关系id: 1-本人 2-爸爸 3-妈妈 4-爷爷 5-奶奶 6-外公 7-外婆 8-哥哥 9-姐姐',
               existing_nullable=True)
    op.drop_column('group', 'create_time')
    op.drop_column('group', 'update_time')
    op.drop_column('sys_config', 'create_time')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('sys_config', sa.Column('create_time', postgresql.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), autoincrement=False, nullable=False, comment='创建时间'))
    op.add_column('group', sa.Column('update_time', postgresql.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), autoincrement=False, nullable=True, comment='最后修改时间'))
    op.add_column('group', sa.Column('create_time', postgresql.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), autoincrement=False, nullable=False, comment='创建时间'))
    op.alter_column('class_member', 'family_relation',
               existing_type=sa.VARCHAR(length=2),
               comment='亲属关系id: 1-本人 2-爸爸 3-妈妈 4-爷爷 5-奶奶 6-外公 7-外婆 8-哥哥 9-姐姐',
               existing_comment='亲属关系id',
               existing_nullable=True)
    op.alter_column('apply4class', 'family_relation',
               existing_type=sa.VARCHAR(length=2),
               comment='亲属关系: 1-本人 2-爸爸 3-妈妈 4-爷爷 5-奶奶 6-外公 7-外婆 8-哥哥 9-姐姐',
               existing_comment='亲属关系',
               existing_nullable=True)
    op.create_table('class_group_member',
    sa.Column('id', sa.BIGINT(), autoincrement=True, nullable=False, comment='主键'),
    sa.Column('group_id', sa.BIGINT(), autoincrement=False, nullable=False, comment='所属小组id'),
    sa.Column('member_id', sa.BIGINT(), autoincrement=False, nullable=False, comment='成员id'),
    sa.Column('create_time', postgresql.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), autoincrement=False, nullable=False, comment='创建时间'),
    sa.Column('update_time', postgresql.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), autoincrement=False, nullable=True, comment='最后修改时间'),
    sa.PrimaryKeyConstraint('id', name='class_group_member_pkey'),
    sa.UniqueConstraint('group_id', 'member_id', name='class_group_member_group_id_member_id_key')
    )
    op.create_index('class_group_member_member_id_idx', 'class_group_member', ['member_id'], unique=False)
    op.create_index('class_group_member_group_id_idx', 'class_group_member', ['group_id'], unique=False)
    op.drop_index('message_sender_member_id_idx', table_name='message')
    op.drop_index('message_receiver_idx', table_name='message')
    op.drop_index('message_receiver_class_id_idx', table_name='message')
    op.drop_table('message')
    op.drop_index('homework_assign_homework_id_idx', table_name='homework_assign')
    op.drop_index('homework_assign_group_id_idx', table_name='homework_assign')
    op.drop_index('homework_assign_class_id_idx', table_name='homework_assign')
    op.drop_table('homework_assign')
    op.drop_index('homework_answer_status_student_name_idx', table_name='homework_answer_status')
    op.drop_index('homework_answer_status_student_class_id_idx', table_name='homework_answer_status')
    op.drop_index('homework_answer_status_status_idx', table_name='homework_answer_status')
    op.drop_index('homework_answer_status_homework_id_idx', table_name='homework_answer_status')
    op.drop_table('homework_answer_status')
    op.drop_index('homework_answer_submitter_member_id_idx', table_name='homework_answer')
    op.drop_table('homework_answer')
    op.drop_index('homework_publisher_id_idx', table_name='homework')
    op.drop_index('homework_pub_time_idx', table_name='homework')
    op.drop_index('homework_end_time_idx', table_name='homework')
    op.drop_table('homework')
    op.drop_index('group_member_name_idx', table_name='group_member')
    op.drop_index('group_member_group_id_idx', table_name='group_member')
    op.drop_table('group_member')
    # ### end Alembic commands ###
