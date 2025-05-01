"""Initial migration

Revision ID: initial_migration
Revises: 
Create Date: 2023-05-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import func
from passlib.context import CryptContext

# revision identifiers, used by Alembic.
revision = 'initial_migration'
down_revision = None
branch_labels = None
depends_on = None

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__ident="2b",
    crypt__disabled=True
)


def get_password_hash(password):
    return pwd_context.hash(password)


def upgrade():
    # Create users table
    op.create_table('users',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('email', sa.String(), nullable=False),
                    sa.Column('hashed_password', sa.String(), nullable=False),
                    sa.Column('full_name', sa.String(), nullable=False),
                    sa.Column('is_admin', sa.Boolean(), nullable=False,
                              default=False),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('email')
                    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)

    # Create accounts table
    op.create_table('accounts',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('user_id', sa.Integer(), nullable=False),
                    sa.Column('balance', sa.Float(), nullable=False,
                              default=0.0),
                    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_index(op.f('ix_accounts_id'), 'accounts', ['id'], unique=False)

    # Create payments table
    op.create_table('payments',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('transaction_id', sa.String(), nullable=False),
                    sa.Column('account_id', sa.Integer(), nullable=False),
                    sa.Column('user_id', sa.Integer(), nullable=False),
                    sa.Column('amount', sa.Float(), nullable=False),
                    sa.Column('created_at', sa.DateTime(timezone=True),
                              server_default=func.now(), nullable=False),
                    sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], ),
                    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('transaction_id')
                    )
    op.create_index(op.f('ix_payments_id'), 'payments', ['id'], unique=False)
    op.create_index(op.f('ix_payments_transaction_id'), 'payments',
                    ['transaction_id'], unique=True)

    # Insert test data
    # Test user
    op.execute(f"""
    INSERT INTO users (email, hashed_password, full_name, is_admin)
    VALUES ('user@example.com', '{get_password_hash("userpassword")}', 'Test User', false)
    """)

    # Test admin
    op.execute(f"""
    INSERT INTO users (email, hashed_password, full_name, is_admin)
    VALUES ('admin@example.com', '{get_password_hash("adminpassword")}', 'Test Admin', true)
    """)

    # Test account for test user
    op.execute("""
    INSERT INTO accounts (id, user_id, balance)
    VALUES (1, 1, 0.0)
    """)


def downgrade():
    op.drop_index(op.f('ix_payments_transaction_id'), table_name='payments')
    op.drop_index(op.f('ix_payments_id'), table_name='payments')
    op.drop_table('payments')
    op.drop_index(op.f('ix_accounts_id'), table_name='accounts')
    op.drop_table('accounts')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
