import hmac
from datetime import date, timedelta

import pandas as pd
import psycopg2
import streamlit as st

DUE_SOON_DAYS = 7


def get_conn():
    return psycopg2.connect(st.secrets["DB_URL"], connect_timeout=8)


def require_login():
    """共通パスワードでのログインゲート。認証済みでなければ入力画面を表示して停止する。"""
    if st.session_state.get("authenticated"):
        return

    st.title("🔧 機械整備・点検記録")
    password = st.text_input("パスワード", type="password")
    if st.button("ログイン"):
        if hmac.compare_digest(password, st.secrets["APP_PASSWORD"]):
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("パスワードが違います")
    st.stop()


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS machines (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT,
            location TEXT,
            interval_days INTEGER NOT NULL,
            initial_due_date TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS maintenance_records (
            id SERIAL PRIMARY KEY,
            machine_id INTEGER NOT NULL REFERENCES machines(id) ON DELETE CASCADE,
            record_date TEXT NOT NULL,
            performed_by TEXT,
            description TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        )
        """
    )
    conn.commit()
    cur.close()
    conn.close()


def load_machines():
    conn = get_conn()
    df = pd.read_sql_query("SELECT * FROM machines ORDER BY id", conn)
    conn.close()
    return df


def add_machine(name, category, location, interval_days, initial_due_date, notes):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO machines (name, category, location, interval_days, initial_due_date, notes)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (name, category, location, interval_days, initial_due_date, notes),
    )
    conn.commit()
    cur.close()
    conn.close()


def update_machine(machine_id, name, category, location, interval_days, initial_due_date, notes):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE machines
        SET name = %s, category = %s, location = %s, interval_days = %s, initial_due_date = %s, notes = %s
        WHERE id = %s
        """,
        (name, category, location, interval_days, initial_due_date, notes, machine_id),
    )
    conn.commit()
    cur.close()
    conn.close()


def delete_machine(machine_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM machines WHERE id = %s", (machine_id,))
    conn.commit()
    cur.close()
    conn.close()


def load_records(machine_id=None):
    conn = get_conn()
    if machine_id is None:
        df = pd.read_sql_query(
            "SELECT * FROM maintenance_records ORDER BY record_date DESC, id DESC", conn
        )
    else:
        df = pd.read_sql_query(
            "SELECT * FROM maintenance_records WHERE machine_id = %(machine_id)s ORDER BY record_date DESC, id DESC",
            conn,
            params={"machine_id": machine_id},
        )
    conn.close()
    return df


def add_record(machine_id, record_date, performed_by, description):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO maintenance_records (machine_id, record_date, performed_by, description)
        VALUES (%s, %s, %s, %s)
        """,
        (machine_id, record_date, performed_by, description),
    )
    conn.commit()
    cur.close()
    conn.close()


def delete_record(record_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM maintenance_records WHERE id = %s", (record_id,))
    conn.commit()
    cur.close()
    conn.close()


def compute_status(machines_df, records_df):
    """機械ごとに最終点検日・次回予定日・状態(overdue/due_soon/ok/unknown)を算出する。"""
    if machines_df.empty:
        return machines_df.assign(
            last_record_date=None, next_due_date=None, status=None, days_until_due=None
        )

    last_dates = (
        records_df.groupby("machine_id")["record_date"].max()
        if not records_df.empty
        else pd.Series(dtype=str)
    )

    rows = []
    today = date.today()
    for _, m in machines_df.iterrows():
        last_date_str = last_dates.get(m["id"])
        if last_date_str:
            last_date = date.fromisoformat(last_date_str)
            next_due = last_date + timedelta(days=int(m["interval_days"]))
        elif m["initial_due_date"]:
            last_date = None
            next_due = date.fromisoformat(m["initial_due_date"])
        else:
            last_date = None
            next_due = None

        if next_due is None:
            status = "unknown"
            days_until = None
        else:
            days_until = (next_due - today).days
            if days_until < 0:
                status = "overdue"
            elif days_until <= DUE_SOON_DAYS:
                status = "due_soon"
            else:
                status = "ok"

        rows.append(
            {
                **m.to_dict(),
                "last_record_date": last_date.isoformat() if last_date else None,
                "next_due_date": next_due.isoformat() if next_due else None,
                "status": status,
                "days_until_due": days_until,
            }
        )

    return pd.DataFrame(rows)


STATUS_LABELS = {
    "overdue": "🔴 期限超過",
    "due_soon": "🟡 まもなく点検",
    "ok": "🟢 予定内",
    "unknown": "⚪ 予定未設定",
}
