import streamlit as st
import pandas as pd
from datetime import date, timedelta
import io

# --- Config ---
MONTHLY_INCOME = 4100
PAY_PER_CHECK = MONTHLY_INCOME / 2  # $2050
START_PAYDAY = date(2025, 9, 18)  # first paycheck

EXPENSES = {
    "Rent": 1900,
    "Car Payment": 700,
    "Utilities": 30,
    "Insurance": 160,
    "Gym Membership": 15,
}

GROCERY_TEMPLATE = [
    {"Item": "Chicken Breast", "Category": "Meat", "Size": "5 lb bulk", "Cost": 12},
    {"Item": "Steak Cuts", "Category": "Meat", "Size": "3 lb pack", "Cost": 20},
    {"Item": "Rice", "Category": "Grains", "Size": "10 lb bag", "Cost": 15, "Freq": "bi-monthly"},
    {"Item": "Broccoli", "Category": "Produce", "Size": "4 crowns", "Cost": 6},
    {"Item": "Mushrooms", "Category": "Produce", "Size": "2 packs", "Cost": 4},
    {"Item": "Granola Bars", "Category": "Snacks", "Size": "2 boxes", "Cost": 8},
    {"Item": "Chips", "Category": "Snacks", "Size": "3 bags", "Cost": 6},
    {"Item": "Protein Bars", "Category": "Snacks/Protein", "Size": "1 box", "Cost": 10},
    {"Item": "Protein Shakes", "Category": "Snacks/Protein", "Size": "4-pack", "Cost": 8},
    {"Item": "Coffee", "Category": "Beverages", "Size": "1 can", "Cost": 12},
    {"Item": "Soda/Water", "Category": "Beverages", "Size": "12-pack", "Cost": 10},
    {"Item": "Assorted Cheese Tray", "Category": "Charcuterie", "Size": "1 tray", "Cost": 4},
    {"Item": "Cured Meats", "Category": "Charcuterie", "Size": "Salami/Prosciutto", "Cost": 10},
    {"Item": "Olives", "Category": "Charcuterie", "Size": "1 jar", "Cost": 4},
    {"Item": "Crackers", "Category": "Charcuterie", "Size": "2 boxes", "Cost": 6},
    {"Item": "Grapes/Seasonal Fruit", "Category": "Charcuterie", "Size": "2 lb", "Cost": 5},
]

# --- Functions ---
def generate_paydays(start, end_year=2025):
    paydays = []
    d = start
    while d.year == end_year:
        paydays.append(d)
        d += timedelta(days=14)
    return paydays

def build_schedule():
    schedule = []
    for pd in generate_paydays(START_PAYDAY):
        is_first_half = pd.day <= 15

        if is_first_half:
            expenses = [
                {"Name": "Rent", "Amount": EXPENSES["Rent"]},
                {"Name": "Utilities", "Amount": EXPENSES["Utilities"]},
                {"Name": "Food & Snacks (Half)", "Amount": 300},
            ]
        else:
            expenses = [
                {"Name": "Car Payment", "Amount": EXPENSES["Car Payment"]},
                {"Name": "Insurance", "Amount": EXPENSES["Insurance"]},
                {"Name": "Gym Membership", "Amount": EXPENSES["Gym Membership"]},
                {"Name": "Food & Snacks (Half)", "Amount": 300},
            ]

        # build breakdown
        running = PAY_PER_CHECK
        breakdown = []
        for e in expenses:
            running -= e["Amount"]
            breakdown.append({**e, "Remaining After": running})

        # grocery plan
        grocery = []
        for g in GROCERY_TEMPLATE:
            if g.get("Item") == "Rice":
                if pd.month % 2 == 1:  # odd months only
                    grocery.append(g)
            else:
                grocery.append(g)

        grocery_total = sum(g["Cost"] for g in grocery)

        schedule.append({
            "Date": pd,
            "Breakdown": breakdown,
            "Final Remaining": running,
            "Grocery": grocery,
            "Grocery Total": grocery_total,
        })
    return schedule

def export_to_excel(schedule):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        # Paycheck breakdowns
        rows = []
        for p in schedule:
            for b in p["Breakdown"]:
                rows.append({
                    "Paycheck Date": p["Date"],
                    "Category": b["Name"],
                    "Amount": b["Amount"],
                    "Remaining After": b["Remaining After"]
                })
        df = pd.DataFrame(rows)
        df.to_excel(writer, sheet_name="Paychecks", index=False)

        # Grocery plan
        rows = []
        for p in schedule:
            for g in p["Grocery"]:
                rows.append({
                    "Paycheck Date": p["Date"],
                    "Item": g["Item"],
                    "Category": g["Category"],
                    "Size": g["Size"],
                    "Cost": g["Cost"],
                })
        df = pd.DataFrame(rows)
        df.to_excel(writer, sheet_name="Grocery Plan", index=False)

    return output.getvalue()

# --- UI ---
st.title("💰 Biweekly Budget & Aldi Grocery Planner")
st.caption("Single income household, $4,100 monthly income, biweekly pay")

tabs = st.tabs(["Paychecks", "Grocery Plan", "Summary"])

schedule = build_schedule()

with tabs[0]:
    st.subheader("Paycheck Breakdown")
    for p in schedule:
        st.markdown(f"**📅 {p['Date']} — Paycheck: ${PAY_PER_CHECK:.2f}**")
        df = pd.DataFrame(p["Breakdown"])
        st.table(df)
        st.success(f"Final Leftover: ${p['Final Remaining']:.2f}")

with tabs[1]:
    st.subheader("Aldi Grocery Lists")
    for p in schedule:
        st.markdown(f"**📅 {p['Date']} — Total: ${p['Grocery Total']}**")
        df = pd.DataFrame(p["Grocery"])
        st.table(df[["Item", "Category", "Size", "Cost"]])

with tabs[2]:
    total_leftover = sum(p["Final Remaining"] for p in schedule)
    total_grocery = sum(p["Grocery Total"] for p in schedule)

    st.metric("💵 Total Leftover (2025)", f"${total_leftover:.2f}")
    st.metric("🛒 Estimated Grocery Spend (2025)", f"${total_grocery:.2f}")
    st.info("Tip: Run this on your phone and **Add to Home Screen** for an app-like experience.")

    # Download button
    excel_data = export_to_excel(schedule)
    st.download_button(
        label="⬇️ Download Budget & Grocery Excel",
        data=excel_data,
        file_name="budget_grocery_plan.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

