#!/usr/bin/env python3
"""
X402 Pipeline - Dune Analytics Data Pipeline
Fetches query results from Dune Analytics, stores them locally in SQLite,
and provides simple access functions with CLI interface.

Usage:
    # Set API key as environment variable
    export DUNE_API_KEY="your_api_key_here"
    
    # Fetch a single query
    python x402_pipeline.py fetch "num transactions"
    
    # Fetch all queries
    python x402_pipeline.py fetch-all
    
    # Get query results with pagination
    python x402_pipeline.py get "num transactions" --limit 10 --offset 0
    
    # Get last N results
    python x402_pipeline.py tail "num transactions" -n 5
    
    # List all available queries
    python x402_pipeline.py list

Programmatic Usage:
    from x402_pipeline import DuneDataPipeline
    
    # Initialize pipeline
    pipeline = DuneDataPipeline(api_key="your_key")
    
    # Fetch a query
    result = pipeline.fetch_query("num transactions")
    
    # Get query data
    data = pipeline.get_query("num transactions", limit=10)
    
    # Get last N rows
    tail_data = pipeline.tail("num transactions", n=5)
"""

import os
import sys
import sqlite3
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path
import argparse

try:
    from dune_client.client import DuneClient
    from dune_client.query import QueryBase
except ImportError:
    print("Error: dune-client library not installed.")
    print("Please run: pip install dune-client")
    sys.exit(1)

try:
    import pandas as pd
    import pyarrow as pa
    import pyarrow.parquet as pq
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False


# Query ID mappings
QUERY_IDS = {
    "num transactions": 6084845,
    "num transactions percent": 6084845,
    "x402 volume evm": 6094619,
    "volume by token evm": 6094619,
    "facilitators by chain": 6084891,
    "facilitators by chain percent": 6084891,
    "facilitators solana": 6084802,
    "x402 volume solana": 6094785,
    "volume by token solana": 6094785,
}


@dataclass
class QueryResult:
    """Represents a query result entry"""
    id: int
    logical_name: str
    query_id: int
    data: str  # JSON string
    timestamp: str
    row_count: int


class DuneDataPipeline:
    """
    X402 Pipeline - Main pipeline class for fetching and storing Dune Analytics query results.
    """
    
    def __init__(self, db_path: str = "data/databases/x402_data.db", api_key: Optional[str] = None):
        """
        Initialize the pipeline.
        
        Args:
            db_path: Path to SQLite database file
            api_key: Dune API key (if None, reads from DUNE_API_KEY env var)
        """
        self.db_path = db_path
        self.api_key = api_key or os.getenv("DUNE_API_KEY")
        
        if not self.api_key:
            raise ValueError(
                "Dune API key not found. Set DUNE_API_KEY environment variable "
                "or pass api_key parameter."
            )
        
        # Initialize Dune client
        self.client = DuneClient(self.api_key)
        
        # Initialize database
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create table for query results
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS query_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                logical_name TEXT NOT NULL,
                query_id INTEGER NOT NULL,
                data TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                row_count INTEGER NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_logical_name 
            ON query_results(logical_name)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp 
            ON query_results(timestamp DESC)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_query_id 
            ON query_results(query_id)
        """)
        
        conn.commit()
        conn.close()
    
    def _retry_with_backoff(self, func, max_retries: int = 3, base_delay: float = 1.0):
        """
        Retry a function with exponential backoff.
        
        Args:
            func: Function to retry
            max_retries: Maximum number of retries
            base_delay: Base delay in seconds for exponential backoff
            
        Returns:
            Result of the function call
        """
        for attempt in range(max_retries):
            try:
                return func()
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                
                delay = base_delay * (2 ** attempt)
                print(f"  Attempt {attempt + 1} failed: {e}")
                print(f"  Retrying in {delay:.1f} seconds...")
                time.sleep(delay)
        
        raise Exception("Max retries exceeded")
    
    def fetch_query(self, logical_name: str, wait_for_completion: bool = True) -> Optional[QueryResult]:
        """
        Fetch the latest result for a query by logical name.
        
        Args:
            logical_name: Logical name of the query
            wait_for_completion: Whether to wait for query execution to complete
            
        Returns:
            QueryResult object or None if query not found
        """
        if logical_name not in QUERY_IDS:
            print(f"Error: Unknown query name '{logical_name}'")
            print(f"Available queries: {', '.join(QUERY_IDS.keys())}")
            return None
        
        query_id = QUERY_IDS[logical_name]
        
        print(f"Fetching query: {logical_name} (ID: {query_id})...")
        
        try:
            # Create QueryBase object
            query = QueryBase(query_id=query_id, name=logical_name)
            
            if wait_for_completion:
                # Execute query and wait for completion (uses execution credits)
                def execute_query():
                    return self.client.run_query(query)
                
                results = self._retry_with_backoff(execute_query)
            else:
                # Get latest results without executing (doesn't use execution credits)
                def get_latest():
                    return self.client.get_latest_result(query)
                
                results = self._retry_with_backoff(get_latest)
            
            # Extract data from ResultsResponse
            if not results or not hasattr(results, 'result') or not results.result:
                print(f"  No results found for query {query_id}")
                return None
            
            rows = results.result.rows
            row_count = len(rows) if rows else 0
            
            # Store in database
            timestamp = datetime.now().isoformat()
            data_json = json.dumps(rows) if rows else "[]"
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO query_results 
                (logical_name, query_id, data, timestamp, row_count)
                VALUES (?, ?, ?, ?, ?)
            """, (logical_name, query_id, data_json, timestamp, row_count))
            conn.commit()
            conn.close()
            
            print(f"  [OK] Fetched {row_count} rows and stored in database")
            
            return QueryResult(
                id=cursor.lastrowid,
                logical_name=logical_name,
                query_id=query_id,
                data=data_json,
                timestamp=timestamp,
                row_count=row_count
            )
            
        except Exception as e:
            print(f"  [ERROR] Error fetching query: {e}")
            return None
    
    def fetch_all(self) -> Dict[str, Optional[QueryResult]]:
        """
        Fetch all queries defined in QUERY_IDS.
        
        Returns:
            Dictionary mapping logical names to QueryResult objects
        """
        print("Fetching all queries...")
        print(f"Total queries: {len(QUERY_IDS)}")
        print()
        
        results = {}
        for logical_name in QUERY_IDS.keys():
            results[logical_name] = self.fetch_query(logical_name)
            time.sleep(1)  # Rate limiting
        
        successful = sum(1 for r in results.values() if r is not None)
        print()
        print(f"Completed: {successful}/{len(QUERY_IDS)} queries fetched successfully")
        
        return results
    
    def get_query(self, logical_name: str, limit: int = 100, offset: int = 0) -> Optional[List[Dict[str, Any]]]:
        """
        Get query results by logical name with pagination.
        
        Args:
            logical_name: Logical name of the query
            limit: Maximum number of results to return
            offset: Number of results to skip (for pagination)
            
        Returns:
            List of result dictionaries, or None if query not found
        """
        if logical_name not in QUERY_IDS:
            print(f"Error: Unknown query name '{logical_name}'")
            return None
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get most recent result for this query
        cursor.execute("""
            SELECT data, timestamp, row_count
            FROM query_results
            WHERE logical_name = ?
            ORDER BY timestamp DESC
            LIMIT 1
        """, (logical_name,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            print(f"No data found for query '{logical_name}'")
            print("Run 'fetch' or 'fetch-all' first to populate data")
            return None
        
        data_json, timestamp, total_rows = row
        
        # Parse JSON data
        try:
            all_data = json.loads(data_json)
        except json.JSONDecodeError:
            print(f"Error parsing data for query '{logical_name}'")
            return None
        
        # Apply pagination
        paginated_data = all_data[offset:offset + limit]
        
        print(f"Query: {logical_name}")
        print(f"Total rows: {total_rows}")
        print(f"Showing: {len(paginated_data)} rows (offset: {offset}, limit: {limit})")
        print(f"Last updated: {timestamp}")
        
        return paginated_data
    
    def tail(self, logical_name: str, n: int = 10) -> Optional[List[Dict[str, Any]]]:
        """
        Get the last N results for a query.
        
        Args:
            logical_name: Logical name of the query
            n: Number of recent results to return
            
        Returns:
            List of result dictionaries, or None if query not found
        """
        if logical_name not in QUERY_IDS:
            print(f"Error: Unknown query name '{logical_name}'")
            return None
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get most recent result
        cursor.execute("""
            SELECT data, timestamp
            FROM query_results
            WHERE logical_name = ?
            ORDER BY timestamp DESC
            LIMIT 1
        """, (logical_name,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            print(f"No data found for query '{logical_name}'")
            return None
        
        data_json, timestamp = row
        
        try:
            all_data = json.loads(data_json)
        except json.JSONDecodeError:
            print(f"Error parsing data")
            return None
        
        # Get last N rows
        tail_data = all_data[-n:] if len(all_data) > n else all_data
        
        print(f"Query: {logical_name}")
        print(f"Last {len(tail_data)} rows (out of {len(all_data)} total)")
        print(f"Last updated: {timestamp}")
        
        return tail_data
    
    def list_queries(self) -> List[Dict[str, Any]]:
        """
        List all available queries with their latest fetch info.
        
        Returns:
            List of query information dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query_info = []
        for logical_name, query_id in QUERY_IDS.items():
            cursor.execute("""
                SELECT timestamp, row_count
                FROM query_results
                WHERE logical_name = ?
                ORDER BY timestamp DESC
                LIMIT 1
            """, (logical_name,))
            
            row = cursor.fetchone()
            last_fetch = row[0] if row else None
            row_count = row[1] if row else 0
            
            query_info.append({
                "logical_name": logical_name,
                "query_id": query_id,
                "last_fetch": last_fetch,
                "row_count": row_count
            })
        
        conn.close()
        return query_info
    
    def export_for_artemis(
        self, 
        output_dir: str = "data/exports",
        format: str = "both"
    ) -> Dict[str, Any]:
        """
        Export all query data in Artemis Analytics-ready format.
        
        Args:
            output_dir: Directory to save exported files
            format: Export format - "parquet", "csv", or "both" (default: "both")
            
        Returns:
            Dictionary with export summary
        """
        if not HAS_PANDAS:
            raise ImportError(
                "pandas and pyarrow are required for Artemis export. "
                "Install with: pip install pandas pyarrow"
            )
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        export_summary = {
            "timestamp": datetime.now().isoformat(),
            "queries_exported": [],
            "total_rows": 0,
            "files_created": []
        }
        
        print(f"Exporting data for Artemis Analytics to {output_dir}/...")
        print()
        
        # Collect all query data
        all_data = []
        
        for logical_name, query_id in QUERY_IDS.items():
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get most recent result
            cursor.execute("""
                SELECT data, timestamp, row_count
                FROM query_results
                WHERE logical_name = ?
                ORDER BY timestamp DESC
                LIMIT 1
            """, (logical_name,))
            
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                print(f"  [WARN] Skipping '{logical_name}' - no data found")
                continue
            
            data_json, timestamp, row_count = row
            
            try:
                rows = json.loads(data_json)
            except json.JSONDecodeError:
                print(f"  [WARN] Skipping '{logical_name}' - invalid JSON")
                continue
            
            if not rows:
                print(f"  [WARN] Skipping '{logical_name}' - empty result")
                continue
            
            # Add metadata to each row
            for row_data in rows:
                enriched_row = {
                    **row_data,
                    "_query_name": logical_name,
                    "_query_id": query_id,
                    "_fetched_at": timestamp,
                    "_exported_at": datetime.now().isoformat()
                }
                all_data.append(enriched_row)
            
            export_summary["queries_exported"].append({
                "logical_name": logical_name,
                "query_id": query_id,
                "row_count": row_count,
                "last_fetch": timestamp
            })
            export_summary["total_rows"] += row_count
            
            print(f"  [OK] '{logical_name}': {row_count} rows")
        
        if not all_data:
            print("\n[WARN] No data to export. Run 'fetch-all' first to populate data.")
            return export_summary
        
        # Create DataFrame
        df = pd.DataFrame(all_data)
        
        # Export based on format
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format in ["parquet", "both"]:
            parquet_path = output_path / f"artemis_x402_dune_data_{timestamp_str}.parquet"
            df.to_parquet(parquet_path, index=False, engine="pyarrow")
            export_summary["files_created"].append(str(parquet_path))
            print(f"\n[OK] Parquet file: {parquet_path}")
            print(f"  Rows: {len(df)}, Columns: {len(df.columns)}")
        
        if format in ["csv", "both"]:
            csv_path = output_path / f"artemis_x402_dune_data_{timestamp_str}.csv"
            df.to_csv(csv_path, index=False)
            export_summary["files_created"].append(str(csv_path))
            print(f"[OK] CSV file: {csv_path}")
            print(f"  Rows: {len(df)}, Columns: {len(df.columns)}")
        
        # Create schema metadata file
        schema_path = output_path / f"artemis_x402_dune_schema_{timestamp_str}.json"
        schema_info = {
            "dataset_name": "x402_dune_analytics",
            "description": "X402 Dune Analytics query results exported for Artemis Analytics",
            "export_timestamp": export_summary["timestamp"],
            "total_rows": int(len(df)),
            "columns": [
                {
                    "name": col,
                    "type": str(df[col].dtype),
                    "nullable": bool(df[col].isna().any())
                }
                for col in df.columns
            ],
            "queries": export_summary["queries_exported"],
            "artemis_integration": {
                "recommended_format": "parquet",
                "sheets_compatible": True,
                "terminal_compatible": True,
                "notes": [
                    "Data includes metadata columns prefixed with '_' for tracking",
                    "Each row includes query name, query ID, and fetch timestamp",
                    "Parquet format recommended for large datasets",
                    "CSV format provided for human readability and quick inspection"
                ]
            }
        }
        
        with open(schema_path, "w") as f:
            json.dump(schema_info, f, indent=2)
        
        export_summary["files_created"].append(str(schema_path))
        print(f"[OK] Schema metadata: {schema_path}")
        
        print("\n" + "="*60)
        print("EXPORT SUMMARY")
        print("="*60)
        print(f"Total queries exported: {len(export_summary['queries_exported'])}")
        print(f"Total rows: {export_summary['total_rows']}")
        print(f"Files created: {len(export_summary['files_created'])}")
        print("\n[OK] Ready for Artemis Analytics integration!")
        
        return export_summary
    
    def run_dbt_transforms(self, dbt_project_dir: str = ".", profiles_dir: str = "dbt", project_file: str = "config/dbt_project.yml"):
        """
        Run dbt transformations on the exported data.
        
        Args:
            dbt_project_dir: Directory containing dbt_project.yml
            profiles_dir: Directory containing profiles.yml
            
        Returns:
            True if successful, False otherwise
        """
        try:
            from dbt.cli.main import dbtRunner
            
            logger = logging.getLogger(__name__) if 'logging' in globals() else None
            
            if logger:
                logger.info("Running dbt transformations...")
            else:
                print("Running dbt transformations...")
            
            # Initialize dbt
            dbt = dbtRunner()
            
            # Copy dbt_project.yml to root if needed
            import shutil
            if not Path("dbt_project.yml").exists() and Path(project_file).exists():
                shutil.copy(project_file, "dbt_project.yml")
            
            # Run dbt models
            result = dbt.invoke(["run", "--project-dir", ".", "--profiles-dir", profiles_dir])
            
            if result.success:
                if logger:
                    logger.info("[OK] dbt transformations completed successfully")
                else:
                    print("[OK] dbt transformations completed successfully")
                return True
            else:
                if logger:
                    logger.error(f"[ERROR] dbt transformations failed: {result}")
                else:
                    print(f"[ERROR] dbt transformations failed: {result}")
                return False
                
        except ImportError:
            error_msg = "dbt-core not installed. Install with: pip install dbt-core dbt-sqlite"
            if 'logging' in globals():
                logging.getLogger(__name__).error(error_msg)
            else:
                print(f"Error: {error_msg}")
            return False
        except Exception as e:
            error_msg = f"Error running dbt: {e}"
            if 'logging' in globals():
                logging.getLogger(__name__).error(error_msg)
            else:
                print(f"Error: {error_msg}")
            return False


def main():
    """Command line interface"""
    parser = argparse.ArgumentParser(
        description="X402 Pipeline - Dune Analytics Data Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Available commands:
  fetch <name>     - Fetch latest result for a query
  fetch-all        - Fetch all queries
  get <name>       - Get query results (with pagination)
  tail <name>      - Get last N results for a query
  list             - List all available queries
  export           - Export all data in Artemis Analytics-ready format
        """
    )
    
    parser.add_argument(
        "command",
        choices=["fetch", "fetch-all", "get", "tail", "list", "export"],
        help="Command to execute"
    )
    
    parser.add_argument(
        "name",
        nargs="?",
        help="Logical query name (required for fetch, get, tail)"
    )
    
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Limit for get command (default: 100)"
    )
    
    parser.add_argument(
        "--offset",
        type=int,
        default=0,
        help="Offset for get command (default: 0)"
    )
    
    parser.add_argument(
        "-n",
        type=int,
        default=10,
        help="Number of rows for tail command (default: 10)"
    )
    
    parser.add_argument(
        "--db",
        default="data/databases/x402_data.db",
        help="Path to SQLite database (default: data/databases/x402_data.db)"
    )
    
    parser.add_argument(
        "--api-key",
        help="Dune API key (overrides DUNE_API_KEY env var)"
    )
    
    parser.add_argument(
        "--output-dir",
        default="data/exports",
        help="Output directory for export command (default: data/exports)"
    )
    
    parser.add_argument(
        "--format",
        choices=["parquet", "csv", "both"],
        default="both",
        help="Export format for export command (default: both)"
    )
    
    args = parser.parse_args()
    
    # Initialize pipeline
    try:
        pipeline = DuneDataPipeline(db_path=args.db, api_key=args.api_key)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    # Execute command
    if args.command == "fetch":
        if not args.name:
            print("Error: Query name required for 'fetch' command")
            print(f"Available queries: {', '.join(QUERY_IDS.keys())}")
            sys.exit(1)
        
        result = pipeline.fetch_query(args.name)
        if result:
            print(f"\n[OK] Successfully fetched and stored query: {args.name}")
            print(f"  Rows: {result.row_count}")
            print(f"  Timestamp: {result.timestamp}")
    
    elif args.command == "fetch-all":
        results = pipeline.fetch_all()
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        for name, result in results.items():
            status = "[OK]" if result else "[ERROR]"
            row_count = result.row_count if result else 0
            print(f"{status} {name}: {row_count} rows")
    
    elif args.command == "get":
        if not args.name:
            print("Error: Query name required for 'get' command")
            sys.exit(1)
        
        data = pipeline.get_query(args.name, limit=args.limit, offset=args.offset)
        if data:
            print("\nResults:")
            print(json.dumps(data, indent=2))
    
    elif args.command == "tail":
        if not args.name:
            print("Error: Query name required for 'tail' command")
            sys.exit(1)
        
        data = pipeline.tail(args.name, n=args.n)
        if data:
            print("\nResults:")
            print(json.dumps(data, indent=2))
    
    elif args.command == "list":
        queries = pipeline.list_queries()
        print("\n" + "="*80)
        print("AVAILABLE QUERIES")
        print("="*80)
        print(f"{'Query Name':<40} {'Query ID':<12} {'Last Fetch':<20} {'Rows':<10}")
        print("-" * 80)
        for q in queries:
            last_fetch = q["last_fetch"][:19] if q["last_fetch"] else "Never"
            print(f"{q['logical_name']:<40} {q['query_id']:<12} {last_fetch:<20} {q['row_count']:<10}")
    
    elif args.command == "export":
        try:
            summary = pipeline.export_for_artemis(
                output_dir=args.output_dir,
                format=args.format
            )
        except ImportError as e:
            print(f"Error: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"Error during export: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()

