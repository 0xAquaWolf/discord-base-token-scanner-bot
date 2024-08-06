import asyncpg
from asyncpg import Connection
from typing import Dict, Any, List
import json
from utils.logger import setup_logger

logger = setup_logger(__name__)


class Database:
    def __init__(self, config):
        self.config = config
        self.pool = None

    async def connect(self):
        try:
            self.pool = await asyncpg.create_pool(
                host=self.config["DB_HOST"],
                port=self.config["DB_PORT"],
                user=self.config["DB_USER"],
                password=self.config["DB_PASSWORD"],
                database=self.config["DB_NAME"],
            )
            logger.info("Connected to the database")
        except Exception as e:
            logger.error(f"Error connecting to the database: {e}")
            raise

    async def close(self):
        if self.pool:
            await self.pool.close()
            logger.info("Closed database connection")

    async def insert_new_token(self, token_info: Dict[str, Any]):
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO tokens (name, symbol, total_supply, decimals, deployer_address, deployer_tx_hash, basescan_token_url, basescan_deployer_url, dexscreener_url)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """,
                token_info["name"],
                token_info["symbol"],
                token_info["total_supply"],
                token_info["decimals"],
                token_info["deployer_addy"],
                token_info["deployer_txHash"],
                token_info["basescan_token_url"],
                token_info["basescan_deployer_url"],
                token_info["dexscreener_url"],
            )
            await conn.execute("NOTIFY new_token, $1", json.dumps(token_info))
            logger.info(f"Inserted new token: {token_info['name']}")

    async def insert_liquidity_event(self, event_type: str, event_data: Dict[str, Any]):
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO liquidity_events (event_type, token_name, token_symbol, eth_amount, token_amount, liquidity, token_min, eth_min, to_address, deadline, tx_hash)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            """,
                event_type,
                event_data["token_name"],
                event_data["token_symbol"],
                event_data.get("eth_amount"),
                event_data.get("token_amount"),
                event_data.get("liquidity"),
                event_data["token_min"],
                event_data["eth_min"],
                event_data["to_address"],
                event_data["deadline"],
                event_data["tx_hash"],
            )
            await conn.execute(
                "NOTIFY liquidity_event, $1",
                json.dumps({"event_type": event_type, **event_data}),
            )
            logger.info(f"Inserted {event_type} event for {event_data['token_name']}")

    async def update_token_price(self, token_address: str, price: float):
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE tokens SET price = $1, last_updated = NOW()
                WHERE address = $2
            """,
                price,
                token_address,
            )
            logger.info(f"Updated price for token {token_address}: {price}")

    async def update_token_activity(self, token_address: str, activity: Dict[str, Any]):
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE tokens SET 
                    last_transaction = $1,
                    transaction_count = $2,
                    holder_count = $3,
                    last_updated = NOW()
                WHERE address = $4
            """,
                activity["last_transaction"],
                activity["transaction_count"],
                activity["holder_count"],
                token_address,
            )
            logger.info(f"Updated activity for token {token_address}")

    async def save_market_trends(self, trends: Dict[str, Any]):
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO market_trends (trend_data, created_at)
                VALUES ($1, NOW())
            """,
                json.dumps(trends),
            )
            logger.info("Saved market trends")

    async def get_token_info(self, token_address: str) -> Dict[str, Any]:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT * FROM tokens WHERE address = $1
            """,
                token_address,
            )
            return dict(row) if row else None

    async def get_recent_liquidity_events(
        self, limit: int = 10
    ) -> List[Dict[str, Any]]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM liquidity_events
                ORDER BY created_at DESC
                LIMIT $1
            """,
                limit,
            )
            return [dict(row) for row in rows]

    async def get_latest_market_trend(self) -> Dict[str, Any]:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT * FROM market_trends
                ORDER BY created_at DESC
                LIMIT 1
            """)
            return dict(row) if row else None
