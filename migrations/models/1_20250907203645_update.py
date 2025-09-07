from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "company" ADD "status" VARCHAR(255) NOT NULL DEFAULT 'active' /* ACTIVE: active\nINACTIVE: inactive */;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "company" DROP COLUMN "status";"""
