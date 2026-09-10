import sqlite3
from pathlib import Path
from typing import List, Dict, Optional, Any

DB_PATH = Path("/home/appuser/data/nexus.db")

class Database:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Connections table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS connections (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    host TEXT NOT NULL,
                    port INTEGER DEFAULT 3389,
                    group_path TEXT DEFAULT '',
                    username TEXT DEFAULT '',
                    domain TEXT DEFAULT '',
                    password TEXT DEFAULT '',
                    credential_id TEXT DEFAULT '',
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Credential Vault table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS vault_credentials (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    username TEXT NOT NULL,
                    domain TEXT DEFAULT '',
                    password TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.commit()

    # ---------------- CONNECTION OPERATIONS ----------------

    def insert_or_update(self, record: Dict[str, Any]):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO connections (id, name, host, port, group_path, username, domain, password, credential_id, updated_at)
                VALUES (:id, :name, :host, :port, :group_path, :username, :domain, :password, :credential_id, CURRENT_TIMESTAMP)
                ON CONFLICT(id) DO UPDATE SET
                    name = excluded.name,
                    host = excluded.host,
                    port = excluded.port,
                    group_path = excluded.group_path,
                    username = excluded.username,
                    domain = excluded.domain,
                    password = excluded.password,
                    credential_id = excluded.credential_id,
                    updated_at = CURRENT_TIMESTAMP
            """, {
                "id": record["id"],
                "name": record["name"],
                "host": record["host"],
                "port": record.get("port", 3389),
                "group_path": record.get("group_path", ""),
                "username": record.get("username", ""),
                "domain": record.get("domain", ""),
                "password": record.get("password", ""),
                "credential_id": record.get("credential_id", "")
            })
            conn.commit()

    def fetch_all(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM connections ORDER BY group_path ASC, name ASC")
            return [dict(row) for row in cursor.fetchall()]

    def get_by_id(self, conn_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM connections WHERE id = ?", (conn_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def delete_connection(self, conn_id: str) -> bool:
        """Deletes a single connection entry by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM connections WHERE id = ?", (conn_id,))
            conn.commit()
            return cursor.rowcount > 0

    def delete_folder(self, folder_path: str) -> int:
        """Deletes all connections under a specific group path prefix."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM connections WHERE group_path = ? OR group_path LIKE ?",
                (folder_path, f"{folder_path}/%")
            )
            conn.commit()
            return cursor.rowcount

    def get_unique_folders(self) -> List[str]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT group_path FROM connections WHERE group_path != '' ORDER BY group_path ASC")
            return [row["group_path"] for row in cursor.fetchall()]

    def record_session_launch(self, conn_id: str):
        """Updates last connected timestamp and increments connection counter."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE connections 
                SET updated_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            """, (conn_id,))
            conn.commit()

    def fetch_recent_connections(self, limit: int = 6) -> List[Dict[str, Any]]:
        """Returns the most recently accessed sessions."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT c.*, v.name as vault_name 
                FROM connections c
                LEFT JOIN vault_credentials v ON c.credential_id = v.id
                ORDER BY c.updated_at DESC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_stats(self) -> Dict[str, int]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as total_nodes FROM connections")
            nodes = cursor.fetchone()["total_nodes"]

            cursor.execute("SELECT COUNT(DISTINCT group_path) as total_groups FROM connections WHERE group_path != ''")
            groups = cursor.fetchone()["total_groups"]

            cursor.execute("SELECT COUNT(*) as total_vaults FROM vault_credentials")
            vaults = cursor.fetchone()["total_vaults"]

            return {
                "nodes": nodes,
                "groups": groups,
                "vaults": vaults
            }

    def get_security_audit(self) -> Dict[str, int]:
        """Audits credential protection status across nodes."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as total FROM connections")
            total = cursor.fetchone()["total"]

            cursor.execute("SELECT COUNT(*) as vaulted FROM connections WHERE credential_id != ''")
            vaulted = cursor.fetchone()["vaulted"]

            cursor.execute("SELECT COUNT(*) as unassigned FROM connections WHERE credential_id = '' AND password = ''")
            unassigned = cursor.fetchone()["unassigned"]

            return {
                "total": total,
                "vaulted": vaulted,
                "unassigned": unassigned,
                "coverage_pct": int((vaulted / total * 100)) if total > 0 else 0
            }

    # ---------------- CREDENTIAL VAULT OPERATIONS ----------------

    def insert_or_update_vault_cred(self, cred: Dict[str, Any]):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO vault_credentials (id, name, username, domain, password, created_at)
                VALUES (:id, :name, :username, :domain, :password, CURRENT_TIMESTAMP)
                ON CONFLICT(id) DO UPDATE SET
                    name = excluded.name,
                    username = excluded.username,
                    domain = excluded.domain,
                    password = excluded.password
            """, {
                "id": cred["id"],
                "name": cred["name"],
                "username": cred["username"],
                "domain": cred.get("domain", ""),
                "password": cred["password"]
            })
            conn.commit()

    def fetch_all_vault_creds(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM vault_credentials ORDER BY name ASC")
            return [dict(row) for row in cursor.fetchall()]

    def get_vault_cred(self, cred_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM vault_credentials WHERE id = ?", (cred_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def delete_vault_cred(self, cred_id: str) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM vault_credentials WHERE id = ?", (cred_id,))
            cursor.execute("UPDATE connections SET credential_id = '' WHERE credential_id = ?", (cred_id,))
            conn.commit()
            return cursor.rowcount > 0

    def apply_credential_to_all(self, cred_id: str) -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE connections SET credential_id = ?", (cred_id,))
            conn.commit()
            return cursor.rowcount

    def apply_credential_to_folder(self, folder_path: str, cred_id: str) -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE connections SET credential_id = ? WHERE group_path = ? OR group_path LIKE ?",
                (cred_id, folder_path, f"{folder_path}/%")
            )
            conn.commit()
            return cursor.rowcount
