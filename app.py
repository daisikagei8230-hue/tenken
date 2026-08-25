import streamlit as st

from common import STATUS_LABELS, compute_status, init_db, load_machines, load_records, require_login

st.set_page_config(page_title="機械整備・点検記録", page_icon="🔧", layout="wide")

require_login()
init_db()

st.title("🔧 機械整備・点検記録")
st.caption("搾乳機・パーラー設備などの点検スケジュールをまとめて管理します")

machines = load_machines()
records = load_records()
status_df = compute_status(machines, records)

if machines.empty:
    st.info("まだ機械・設備が登録されていません。左のメニューから「機械設備の登録」で追加してください。")
else:
    overdue = status_df[status_df["status"] == "overdue"]
    due_soon = status_df[status_df["status"] == "due_soon"]

    col1, col2, col3 = st.columns(3)
    col1.metric("登録台数", len(status_df))
    col2.metric("期限超過", len(overdue))
    col3.metric("まもなく点検(7日以内)", len(due_soon))

    if len(overdue) > 0:
        st.error("⚠️ 期限を過ぎている機械があります")
        for _, r in overdue.iterrows():
            st.write(f"- **{r['name']}**({r['location'] or '場所未設定'}) — 予定日: {r['next_due_date']}")

    if len(due_soon) > 0:
        st.warning("まもなく点検予定です")
        for _, r in due_soon.iterrows():
            st.write(
                f"- **{r['name']}**({r['location'] or '場所未設定'}) — 予定日: {r['next_due_date']}(あと{r['days_until_due']}日)"
            )

    st.divider()
    st.subheader("機械・設備の一覧")

    display_df = status_df[
        ["name", "category", "location", "last_record_date", "next_due_date", "status"]
    ].copy()
    display_df["status"] = display_df["status"].map(STATUS_LABELS)
    display_df = display_df.sort_values(
        by="next_due_date", na_position="last"
    ).rename(
        columns={
            "name": "名称",
            "category": "種別",
            "location": "設置場所",
            "last_record_date": "前回点検日",
            "next_due_date": "次回予定日",
            "status": "状態",
        }
    )
    st.dataframe(display_df, use_container_width=True, hide_index=True)
