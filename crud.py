from database import get_db_connection
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta

# --- Issue Operations ---

def create_issue(title: str, description: str, area: str, latitude: Optional[str], longitude: Optional[str], image_filename: Optional[str]):
    conn = get_db_connection()
    conn.execute(
        '''INSERT INTO issues 
           (title, description, area, latitude, longitude, image_filename) 
           VALUES (?, ?, ?, ?, ?, ?)''',
        (title, description, area, latitude, longitude, image_filename)
    )
    conn.commit()
    conn.close()

def get_issues(area: Optional[str] = None, status: Optional[str] = None, search_query: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    query = "SELECT * FROM issues WHERE 1=1"
    params = []
    
    if area:
        query += " AND area = ?"
        params.append(area)
    if status:
        query += " AND status = ?"
        params.append(status)
    if search_query:
        query += " AND (title LIKE ? OR description LIKE ?)"
        search_term = f"%{search_query}%"
        params.append(search_term)
        params.append(search_term)

    query += " ORDER BY created_at DESC"
    
    issues = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(row) for row in issues]

def get_issue_by_id(issue_id: int) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    issue = conn.execute("SELECT * FROM issues WHERE id = ?", (issue_id,)).fetchone()
    conn.close()
    return dict(issue) if issue else None

def get_issues_with_location() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    issues = conn.execute("""
        SELECT id, title, latitude, longitude, status, area 
        FROM issues 
        WHERE latitude IS NOT NULL AND latitude != ''
    """).fetchall()
    conn.close()
    return [dict(row) for row in issues]

def update_issue_status(issue_id: int, status: str, resolved_image_filename: Optional[str] = None):
    conn = get_db_connection()
    if resolved_image_filename:
        conn.execute(
            "UPDATE issues SET status = ?, resolved_image_filename = ? WHERE id = ?", 
            (status, resolved_image_filename, issue_id)
        )
    else:
        conn.execute("UPDATE issues SET status = ? WHERE id = ?", (status, issue_id))
    conn.commit()
    conn.close()

def check_duplicate_issues(area: str, title: str) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    query = """
        SELECT id, title FROM issues 
        WHERE area = ? 
        AND title LIKE ? 
        AND status != 'Resolved'
    """
    search_term = f"%{title}%"
    duplicates = conn.execute(query, (area, search_term)).fetchall()
    conn.close()
    return [{"id": row["id"], "title": row["title"]} for row in duplicates]

# --- Vote Operations ---

def get_user_votes(user_id: str) -> List[int]:
    conn = get_db_connection()
    votes = conn.execute('SELECT issue_id FROM upvotes WHERE user_id = ?', (user_id,)).fetchall()
    conn.close()
    return [v['issue_id'] for v in votes]

def toggle_vote(user_id: str, issue_id: int):
    conn = get_db_connection()
    existing_vote = conn.execute(
        "SELECT * FROM upvotes WHERE user_id = ? AND issue_id = ?", 
        (user_id, issue_id)
    ).fetchone()
    
    if existing_vote:
        conn.execute("DELETE FROM upvotes WHERE user_id = ? AND issue_id = ?", (user_id, issue_id))
        conn.execute("UPDATE issues SET upvote_count = upvote_count - 1 WHERE id = ?", (issue_id,))
    else:
        conn.execute("INSERT INTO upvotes (user_id, issue_id) VALUES (?, ?)", (user_id, issue_id))
        conn.execute("UPDATE issues SET upvote_count = upvote_count + 1 WHERE id = ?", (issue_id,))
        
    conn.commit()
    conn.close()

# --- Analytics Operations ---

def get_total_issues_count() -> int:
    conn = get_db_connection()
    count = conn.execute("SELECT COUNT(*) FROM issues").fetchone()[0]
    conn.close()
    return count

def get_resolved_issues_count() -> int:
    conn = get_db_connection()
    count = conn.execute("SELECT COUNT(*) FROM issues WHERE status='Resolved'").fetchone()[0]
    conn.close()
    return count

def get_area_stats() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    area_data = conn.execute("""
        SELECT area, COUNT(*) as count 
        FROM issues 
        GROUP BY area 
        ORDER BY count DESC
    """).fetchall()
    conn.close()
    return [dict(row) for row in area_data]

def get_all_issues_for_analytics() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    rows = conn.execute("SELECT created_at, status FROM issues").fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_top_critical_issues(limit: int = 5) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    issues = conn.execute(f"SELECT * FROM issues WHERE status != 'Resolved' ORDER BY upvote_count DESC LIMIT {limit}").fetchall()
    conn.close()
    return [dict(row) for row in issues]

def get_top_issues_with_upvotes(limit: int = 3) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    issues = conn.execute(f'''
        SELECT id, title, area, upvote_count 
        FROM issues 
        WHERE status != 'Resolved' AND upvote_count > 0
        ORDER BY upvote_count DESC 
        LIMIT {limit}
    ''').fetchall()
    conn.close()
    return [dict(row) for row in issues]

def get_monthly_trend_data(limit: int = 6) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    trend_data = conn.execute(f'''
        SELECT strftime('%Y-%m', created_at) as month, 
               COUNT(*) as total_count,
               SUM(CASE WHEN status = 'Resolved' THEN 1 ELSE 0 END) as resolved_count
        FROM issues
        GROUP BY month
        ORDER BY month DESC
        LIMIT {limit}
    ''').fetchall()
    conn.close()
    return [dict(row) for row in trend_data]

def delete_old_resolved_issues(days: int = 60) -> int:
    conn = get_db_connection()
    # Calculate the cutoff date
    cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
    
    # Execute deletion
    cursor = conn.execute(
        "DELETE FROM issues WHERE status = 'Resolved' AND created_at < ?", 
        (cutoff_date,)
    )
    deleted_count = cursor.rowcount
    conn.commit()
    conn.close()
    return deleted_count
