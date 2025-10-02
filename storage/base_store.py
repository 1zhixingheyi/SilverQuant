"""
BaseDataStore Interface Contract

This defines the unified data storage interface that all storage backends must implement.
Used for:
- File storage (current implementation)
- Redis storage (HOT layer)
- MySQL storage (WARM layer)
- ClickHouse storage (COOL layer)
- Hybrid storage (multi-backend with fallback)

Contract Testing: All implementations must pass tests in tests/contract/test_base_store_contract.py
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, List, Tuple
from datetime import datetime
import pandas as pd


class BaseDataStore(ABC):
    """
    Unified data storage interface for SilverQuant project.

    Design principles:
    - Backward compatibility: Strategy code doesn't need to know storage backend
    - Performance goals: Position queries <1ms, Trade queries <100ms
    - Reliability: Auto-fallback when primary storage fails
    """

    # ===== Position State Operations (HOT layer) =====

    @abstractmethod
    def get_held_days(self, code: str, account_id: str) -> Optional[int]:
        """
        Query holding days for a stock position.

        Args:
            code: Stock code (e.g., 'SH600000')
            account_id: Account ID (e.g., '55009728')

        Returns:
            Holding days (int) or None if not found

        Performance:
            - Target: <1ms (from spec FR-001)
            - Redis: <1ms (hash lookup)
            - File: <10ms (JSON file read)

        Example:
            >>> store.get_held_days('SH600000', '55009728')
            5
        """
        pass

    @abstractmethod
    def update_held_days(self, code: str, days: int, account_id: str) -> None:
        """
        Update holding days for a stock position.

        Args:
            code: Stock code
            days: New holding days value
            account_id: Account ID

        Raises:
            ValueError: If days < 0

        Example:
            >>> store.update_held_days('SH600000', 5, '55009728')
        """
        pass

    @abstractmethod
    def all_held_inc(self, account_id: str) -> bool:
        """
        Increment all holding days by 1 (daily task before market opens).

        Args:
            account_id: Account ID

        Returns:
            True if incremented successfully, False if already incremented today

        Atomicity:
            - Must be atomic operation (from spec FR-005)
            - Redis: Use Lua script for atomicity
            - File: Use file lock

        Example:
            >>> store.all_held_inc('55009728')
            True  # First call today
            >>> store.all_held_inc('55009728')
            False  # Already incremented today
        """
        pass

    @abstractmethod
    def delete_held_days(self, code: str, account_id: str) -> None:
        """
        Delete holding record (when position is closed).

        Args:
            code: Stock code
            account_id: Account ID

        Example:
            >>> store.delete_held_days('SH600000', '55009728')
        """
        pass

    @abstractmethod
    def get_max_price(self, code: str, account_id: str) -> Optional[float]:
        """
        Query historical highest price since opening position.

        Args:
            code: Stock code
            account_id: Account ID

        Returns:
            Max price (float) or None if not found

        Example:
            >>> store.get_max_price('SH600000', '55009728')
            10.85
        """
        pass

    @abstractmethod
    def update_max_price(self, code: str, price: float, account_id: str) -> None:
        """
        Update historical highest price.

        Args:
            code: Stock code
            price: New max price
            account_id: Account ID

        Raises:
            ValueError: If price <= 0

        Example:
            >>> store.update_max_price('SH600000', 10.85, '55009728')
        """
        pass

    @abstractmethod
    def get_min_price(self, code: str, account_id: str) -> Optional[float]:
        """
        Query historical lowest price since opening position.

        Args:
            code: Stock code
            account_id: Account ID

        Returns:
            Min price (float) or None if not found

        Example:
            >>> store.get_min_price('SH600000', '55009728')
            9.50
        """
        pass

    @abstractmethod
    def update_min_price(self, code: str, price: float, account_id: str) -> None:
        """
        Update historical lowest price.

        Args:
            code: Stock code
            price: New min price
            account_id: Account ID

        Raises:
            ValueError: If price <= 0

        Example:
            >>> store.update_min_price('SH600000', 9.50, '55009728')
        """
        pass

    # ===== Trade Record Operations (COOL layer) =====

    @abstractmethod
    def record_trade(
        self,
        account_id: str,
        timestamp: str,
        code: str,
        name: str,
        order_type: str,
        remark: str,
        price: float,
        volume: int,
        strategy_name: str = ''
    ) -> None:
        """
        Record a trade transaction.

        Args:
            account_id: Account ID
            timestamp: Unix timestamp string
            code: Stock code
            name: Stock name
            order_type: Order type ('buy_order', 'sell_order', 'buy_trade', 'sell_trade', 'cancel')
            remark: Trade remark
            price: Trade price (yuan)
            volume: Trade volume (shares)
            strategy_name: Strategy name (optional)

        Consistency (from spec FR-006):
            - Must complete within 1 second after trade execution
            - Position state, trade record must be updated atomically

        Example:
            >>> store.record_trade(
            ...     account_id='55009728',
            ...     timestamp='1696118400',
            ...     code='SH600000',
            ...     name='浦发银行',
            ...     order_type='buy_trade',
            ...     remark='开仓',
            ...     price=10.50,
            ...     volume=1000,
            ...     strategy_name='问财选股V1'
            ... )
        """
        pass

    @abstractmethod
    def query_trades(
        self,
        account_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        code: Optional[str] = None,
        strategy_name: Optional[str] = None,
        limit: int = 1000
    ) -> List[Dict]:
        """
        Query trade records with filters.

        Args:
            account_id: Account ID
            start_date: Start date (YYYY-MM-DD), None for no limit
            end_date: End date (YYYY-MM-DD), None for no limit
            code: Stock code filter, None for all stocks
            strategy_name: Strategy name filter, None for all strategies
            limit: Max records to return

        Returns:
            List of trade dicts, sorted by timestamp DESC

        Performance (from spec FR-002):
            - Target: <100ms for 1 year data (~10k records)
            - ClickHouse: <50ms with date partition
            - File (CSV): <200ms (full scan)

        Example:
            >>> trades = store.query_trades(
            ...     account_id='55009728',
            ...     start_date='2024-01-01',
            ...     end_date='2024-12-31',
            ...     code='SH600000'
            ... )
            >>> len(trades)
            125
        """
        pass

    @abstractmethod
    def aggregate_trades(
        self,
        account_id: str,
        start_date: str,
        end_date: str,
        group_by: str = 'month'
    ) -> List[Dict]:
        """
        Aggregate trade statistics.

        Args:
            account_id: Account ID
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            group_by: Aggregation level ('day', 'month', 'year')

        Returns:
            List of aggregation results, each dict contains:
            - period: Period key (e.g., '2024-01' for month)
            - trade_count: Number of trades
            - total_amount: Total trade amount (yuan)
            - profit: Total profit (yuan, calculated from buy/sell pairs)

        Performance (from spec FR-023):
            - Target: <500ms for 3 years data

        Example:
            >>> stats = store.aggregate_trades(
            ...     account_id='55009728',
            ...     start_date='2024-01-01',
            ...     end_date='2024-12-31',
            ...     group_by='month'
            ... )
            >>> stats[0]
            {'period': '2024-01', 'trade_count': 45, 'total_amount': 125000.0, 'profit': 5200.0}
        """
        pass

    # ===== Kline Data Operations (COOL layer) =====

    @abstractmethod
    def get_kline(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        days: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Query daily kline data.

        Args:
            code: Stock code
            start_date: Start date (YYYYMMDD or YYYY-MM-DD), None for no limit
            end_date: End date (YYYYMMDD or YYYY-MM-DD), None for today
            days: Recent N days, overrides start_date if provided

        Returns:
            DataFrame with columns: datetime, open, high, low, close, volume, amount

        Performance (from spec FR-003):
            - Target: <20ms for 60 days data
            - ClickHouse: <20ms with (code, date) index
            - CSV + Memory cache: <5ms (already in memory)

        Example:
            >>> df = store.get_kline('SH600000', days=60)
            >>> len(df)
            60
            >>> df.columns.tolist()
            ['datetime', 'open', 'high', 'low', 'close', 'volume', 'amount']
        """
        pass

    @abstractmethod
    def batch_get_kline(
        self,
        codes: List[str],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        days: Optional[int] = None
    ) -> Dict[str, pd.DataFrame]:
        """
        Batch query kline data for multiple stocks.

        Args:
            codes: List of stock codes (max 100 from spec FR-027)
            start_date: Start date
            end_date: End date
            days: Recent N days

        Returns:
            Dict mapping code to DataFrame

        Raises:
            ValueError: If len(codes) > 100

        Example:
            >>> dfs = store.batch_get_kline(['SH600000', 'SZ000001'], days=60)
            >>> len(dfs)
            2
            >>> len(dfs['SH600000'])
            60
        """
        pass

    # ===== Account Management (WARM layer) =====

    @abstractmethod
    def create_account(
        self,
        account_id: str,
        account_name: str,
        broker: str,
        initial_capital: float
    ) -> int:
        """
        Create a new trading account.

        Args:
            account_id: Unique account ID (e.g., '55009728')
            account_name: Account name (e.g., '生产账户')
            broker: Broker name ('QMT', 'GM', 'TDX')
            initial_capital: Initial capital (yuan)

        Returns:
            Internal account ID (database primary key)

        Raises:
            ValueError: If account_id already exists (from spec FR-010)
            ValueError: If initial_capital <= 0
            ValueError: If broker not in ['QMT', 'GM', 'TDX']

        Example:
            >>> internal_id = store.create_account(
            ...     account_id='55009728',
            ...     account_name='生产账户',
            ...     broker='QMT',
            ...     initial_capital=100000.0
            ... )
            >>> internal_id
            1
        """
        pass

    @abstractmethod
    def get_account(self, account_id: str) -> Optional[Dict]:
        """
        Query account information.

        Args:
            account_id: Account ID

        Returns:
            Account dict or None if not found, dict contains:
            - id: Internal ID
            - account_id: Account ID
            - account_name: Account name
            - broker: Broker
            - initial_capital: Initial capital
            - current_capital: Current capital
            - total_assets: Total assets
            - position_value: Position market value
            - status: Status ('active', 'inactive', 'suspended')

        Example:
            >>> account = store.get_account('55009728')
            >>> account['account_name']
            '生产账户'
        """
        pass

    @abstractmethod
    def update_account_capital(
        self,
        account_id: str,
        current_capital: float,
        total_assets: float,
        position_value: float
    ) -> None:
        """
        Update account capital information (daily task).

        Args:
            account_id: Account ID
            current_capital: Available capital
            total_assets: Total assets
            position_value: Position market value

        Validation:
            - total_assets = current_capital + position_value

        Example:
            >>> store.update_account_capital(
            ...     account_id='55009728',
            ...     current_capital=50000.0,
            ...     total_assets=110000.0,
            ...     position_value=60000.0
            ... )
        """
        pass

    # ===== Strategy Management (WARM layer) =====

    @abstractmethod
    def create_strategy(
        self,
        strategy_name: str,
        strategy_code: str,
        strategy_type: str,
        version: str,
        description: str = ''
    ) -> int:
        """
        Create a new trading strategy.

        Args:
            strategy_name: Strategy name (e.g., '问财选股V1')
            strategy_code: Strategy code (e.g., 'wencai_v1')
            strategy_type: Strategy type ('wencai', 'remote', 'technical')
            version: Version (e.g., '1.0.0')
            description: Strategy description

        Returns:
            Internal strategy ID

        Raises:
            ValueError: If strategy_name already exists
            ValueError: If strategy_code already exists
            ValueError: If strategy_type not in ['wencai', 'remote', 'technical']

        Example:
            >>> strategy_id = store.create_strategy(
            ...     strategy_name='问财选股V1',
            ...     strategy_code='wencai_v1',
            ...     strategy_type='wencai',
            ...     version='1.0.0'
            ... )
        """
        pass

    @abstractmethod
    def get_strategy_params(
        self,
        strategy_name: str,
        version: Optional[int] = None
    ) -> Dict[str, any]:
        """
        Query strategy parameters.

        Args:
            strategy_name: Strategy name
            version: Parameter version, None for active version

        Returns:
            Dict mapping param_key to param_value

        Performance (from spec FR-018):
            - Target: <50ms (MySQL query + deserialization)

        Example:
            >>> params = store.get_strategy_params('问财选股V1')
            >>> params['slot_count']
            10
            >>> params['slot_capacity']
            10000
        """
        pass

    @abstractmethod
    def save_strategy_params(
        self,
        strategy_name: str,
        params: Dict[str, any],
        remark: str = ''
    ) -> int:
        """
        Save strategy parameters as new version.

        Args:
            strategy_name: Strategy name
            params: Dict mapping param_key to param_value
            remark: Version remark (e.g., '提高仓位测试')

        Returns:
            New version number

        Behavior (from spec FR-020):
            - Automatically increments version number
            - Sets new version as active
            - Deactivates old active version (is_active=False)

        Example:
            >>> new_version = store.save_strategy_params(
            ...     strategy_name='问财选股V1',
            ...     params={'slot_count': 12, 'slot_capacity': 15000},
            ...     remark='提高仓位测试'
            ... )
            >>> new_version
            6
        """
        pass

    @abstractmethod
    def compare_strategy_params(
        self,
        strategy_name: str,
        version_a: int,
        version_b: int
    ) -> Dict[str, Tuple[any, any]]:
        """
        Compare two parameter versions.

        Args:
            strategy_name: Strategy name
            version_a: First version
            version_b: Second version

        Returns:
            Dict mapping param_key to (value_a, value_b) tuple
            Only includes params with different values

        Performance (from spec FR-019):
            - Target: <100ms for version comparison

        Example:
            >>> diff = store.compare_strategy_params('问财选股V1', 1, 2)
            >>> diff
            {'slot_count': (10, 12), 'slot_capacity': (10000, 15000)}
        """
        pass

    # ===== Health Check =====

    @abstractmethod
    def health_check(self) -> Dict[str, str]:
        """
        Check storage backend health status.

        Returns:
            Dict mapping component to status ('ok', 'degraded', 'down')

        Example:
            >>> status = store.health_check()
            >>> status
            {'redis': 'ok', 'mysql': 'ok', 'clickhouse': 'ok', 'file': 'ok'}
        """
        pass

    # ===== Connection Management =====

    @abstractmethod
    def close(self) -> None:
        """
        Close all database connections.

        Example:
            >>> store.close()
        """
        pass
