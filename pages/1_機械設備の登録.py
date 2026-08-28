from datetime import date

import streamlit as st

from common import add_machine, delete_machine, init_db, inject_pwa_meta, load_machines, require_login, update_machine

st.set_page_config(page_title="機械設備の登録", page_icon="🔧", layout="wide")
inject_pwa_meta()
require_login()
init_db()

st.title("機械・設備の登録")

with st.form("add_machine_form", clear_on_submit=True):
    st.subheader("新しい機械・設備を追加")
    name = st.text_input("名称(例: 搾乳機1号機)")
    category = st.text_input("種別(例: 搾乳機・パーラー設備・冷却設備など、任意)")
    location = st.text_input("設置場所(任意)")
    interval_days = st.number_input("点検周期(日数)", min_value=1, value=30, step=1)
    initial_due_date = st.date_input("次回点検予定日(まだ点検記録がない場合の初期値)", value=date.today())
    notes = st.text_area("メモ(任意)")
    submitted = st.form_submit_button("追加する")

    if submitted:
        if not name:
            st.error("名称は必須です")
        else:
            add_machine(
                name, category, location, int(interval_days), initial_due_date.isoformat(), notes
            )
            st.success(f"「{name}」を追加しました")
            st.rerun()

st.divider()
st.subheader("登録済みの機械・設備")

machines = load_machines()

if machines.empty:
    st.info("まだ登録がありません。")
else:
    for _, m in machines.iterrows():
        with st.expander(f"{m['name']}({m['location'] or '場所未設定'})"):
            with st.form(f"edit_form_{m['id']}"):
                e_name = st.text_input("名称", value=m["name"], key=f"name_{m['id']}")
                e_category = st.text_input("種別", value=m["category"] or "", key=f"cat_{m['id']}")
                e_location = st.text_input("設置場所", value=m["location"] or "", key=f"loc_{m['id']}")
                e_interval = st.number_input(
                    "点検周期(日数)",
                    min_value=1,
                    value=int(m["interval_days"]),
                    step=1,
                    key=f"interval_{m['id']}",
                )
                e_initial_due = st.date_input(
                    "次回点検予定日(点検記録がまだない場合に使う値)",
                    value=date.fromisoformat(m["initial_due_date"]) if m["initial_due_date"] else date.today(),
                    key=f"due_{m['id']}",
                )
                e_notes = st.text_area("メモ", value=m["notes"] or "", key=f"notes_{m['id']}")

                col1, col2 = st.columns(2)
                update_clicked = col1.form_submit_button("更新する")
                delete_clicked = col2.form_submit_button("削除する", type="secondary")

                if update_clicked:
                    update_machine(
                        m["id"],
                        e_name,
                        e_category,
                        e_location,
                        int(e_interval),
                        e_initial_due.isoformat(),
                        e_notes,
                    )
                    st.success("更新しました")
                    st.rerun()

                if delete_clicked:
                    delete_machine(m["id"])
                    st.success(f"「{m['name']}」を削除しました(点検記録も削除されます)")
                    st.rerun()
