from datetime import date

import streamlit as st

from common import add_record, delete_record, init_db, inject_pwa_meta, load_machines, load_records, require_login

st.set_page_config(page_title="点検・整備記録", page_icon="📝", layout="wide")
inject_pwa_meta()
require_login()
init_db()

st.title("点検・整備記録")

machines = load_machines()

if machines.empty:
    st.info("先に「機械設備の登録」で機械・設備を登録してください。")
    st.stop()

machine_options = {row["name"]: row["id"] for _, row in machines.iterrows()}

with st.form("add_record_form", clear_on_submit=True):
    st.subheader("点検・整備を記録する")
    selected_name = st.selectbox("機械・設備", list(machine_options.keys()))
    record_date = st.date_input("実施日", value=date.today())
    performed_by = st.text_input("担当者(任意)")
    description = st.text_area("内容(任意、例: 定期点検・部品交換など)")
    submitted = st.form_submit_button("記録する")

    if submitted:
        add_record(machine_options[selected_name], record_date.isoformat(), performed_by, description)
        st.success(f"「{selected_name}」の記録を追加しました")
        st.rerun()

st.divider()
st.subheader("記録の一覧")

filter_name = st.selectbox("機械・設備で絞り込み", ["すべて"] + list(machine_options.keys()))
machine_id_filter = None if filter_name == "すべて" else machine_options[filter_name]

records = load_records(machine_id_filter)

if records.empty:
    st.info("記録がありません。")
else:
    id_to_name = {v: k for k, v in machine_options.items()}
    display_df = records.copy()
    display_df["machine_name"] = display_df["machine_id"].map(id_to_name)
    display_df = display_df[["record_date", "machine_name", "performed_by", "description"]].rename(
        columns={
            "record_date": "実施日",
            "machine_name": "機械・設備",
            "performed_by": "担当者",
            "description": "内容",
        }
    )
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    st.caption("記録を削除する場合")
    del_options = {
        f"{r['record_date']} / {id_to_name.get(r['machine_id'], '?')} / {r['description'] or ''}": r["id"]
        for _, r in records.iterrows()
    }
    to_delete = st.selectbox("削除する記録を選択", ["選択してください"] + list(del_options.keys()))
    if to_delete != "選択してください" and st.button("この記録を削除する"):
        delete_record(del_options[to_delete])
        st.success("削除しました")
        st.rerun()
