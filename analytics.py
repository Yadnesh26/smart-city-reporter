from database import get_db_connection
from datetime import datetime

def get_public_stats():
    conn = get_db_connection()
    
    # 1. KPI Cards (The Big Numbers)
    total = conn.execute("SELECT COUNT(*) FROM issues").fetchone()[0]
    resolved = conn.execute("SELECT COUNT(*) FROM issues WHERE status = 'Resolved'").fetchone()[0]
    
    # Avoid division by zero
    resolution_rate = round((resolved / total * 100), 1) if total > 0 else 0
    
    # 2. Priority List (Top 3 Unresolved by Upvotes)
    # We lower threshold to >2 upvotes for the demo so you actually see data
    top_issues = conn.execute('''
        SELECT id, title, area, upvote_count 
        FROM issues 
        WHERE status != 'Resolved' AND upvote_count > 0
        ORDER BY upvote_count DESC 
        LIMIT 3
    ''').fetchall()
    
    # 3. Monthly Trend (For the Graph)
    # SQLite trick to group by Month (YYYY-MM)
    trend_data = conn.execute('''
        SELECT strftime('%Y-%m', created_at) as month, 
               COUNT(*) as total_count,
               SUM(CASE WHEN status = 'Resolved' THEN 1 ELSE 0 END) as resolved_count
        FROM issues
        GROUP BY month
        ORDER BY month DESC
        LIMIT 6
    ''').fetchall()
    
    conn.close()
    
    # Format trend data for Chart.js (Arrays)
    # We reverse it so the chart goes Left(Old) -> Right(New)
    months = [row['month'] for row in trend_data][::-1]
    raised_counts = [row['total_count'] for row in trend_data][::-1]
    resolved_counts = [row['resolved_count'] for row in trend_data][::-1]
    
    return {
        "kpi": {"total": total, "resolved": resolved, "rate": resolution_rate},
        "top_issues": top_issues,
        "chart": {
            "labels": months,
            "raised": raised_counts,
            "resolved": resolved_counts
        }
    }