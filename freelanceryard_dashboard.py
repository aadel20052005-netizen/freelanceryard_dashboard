"""
داشبورد مبيعات شبين الكوم 2026
تشغيل:  streamlit run app.py
"""
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

# ----------------------------------------------------------------------------
# إعداد الصفحة
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="داشبورد مبيعات شبين الكوم",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_FILE = "shebin_sales_2026.xls"  # ضع الملف بجوار app.py
PRIMARY = "#4F46E5"
PALETTE = px.colors.qualitative.Set2

# ----------------------------------------------------------------------------
# تنسيق CSS (يدعم العربية RTL ويعمل مع الوضع الفاتح والداكن)
# ----------------------------------------------------------------------------
st.markdown(
    f"""
    <style>
    html, body, [data-testid="stAppViewContainer"], [data-testid="stSidebar"] {{
        direction: rtl;
        text-align: right;
    }}
    .block-container {{ padding-top: 2rem; padding-bottom: 2rem; }}
    .dash-title {{ font-size: 2rem; font-weight: 800; margin-bottom: 0; }}
    .dash-sub {{ opacity: .65; margin-bottom: 1.2rem; }}
    .kpi {{
        background: rgba(128,128,128,.08);
        border: 1px solid rgba(128,128,128,.2);
        border-right: 5px solid {PRIMARY};
        border-radius: 14px;
        padding: 1.1rem 1.3rem;
    }}
    .kpi .label {{ font-size: .95rem; opacity: .7; }}
    .kpi .value {{ font-size: 1.9rem; font-weight: 800; margin-top: .2rem; }}
    .kpi .unit  {{ font-size: .9rem; font-weight: 500; opacity: .7; }}
    h3 {{ margin-top: .5rem; }}
    /* Plotly والجداول تبقى LTR لسلامة الأرقام */
    [data-testid="stPlotlyChart"], [data-testid="stDataFrame"] {{ direction: ltr; }}
    </style>
    """,
    unsafe_allow_html=True,
)


# ----------------------------------------------------------------------------
# تحميل البيانات
# ----------------------------------------------------------------------------
@st.cache_data(show_spinner="جاري تحميل البيانات...")
def load_data(path: str) -> pd.DataFrame:
    # الملف CSV بامتداد xls، فنجرّب CSV أولاً ثم Excel كاحتياط
    try:
        df = pd.read_csv(path, encoding="utf-8-sig")
        if df.shape[1] < 2:
            raise ValueError("not csv")
    except Exception:
        df = pd.read_excel(path)

    df.columns = df.columns.str.strip()
    df["Order_Date"] = pd.to_datetime(df["Order_Date"], errors="coerce")
    for col in ["Quantity", "Unit_Price_EGP", "Total_Price_EGP"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["Order_Date", "Total_Price_EGP"])
    return df.sort_values("Order_Date").reset_index(drop=True)


def fmt(n: float) -> str:
    return f"{n:,.0f}"


def kpi(label: str, value: str, unit: str = "") -> str:
    return (
        f'<div class="kpi"><div class="label">{label}</div>'
        f'<div class="value">{value} <span class="unit">{unit}</span></div></div>'
    )


def style(fig, height=380):
    fig.update_layout(
        template="plotly_white",
        height=height,
        margin=dict(l=10, r=10, t=50, b=10),
        font=dict(family="Tahoma, Arial", size=13),
        title_font_size=17,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
    )
    return fig


if not Path(DATA_FILE).exists():
    st.error(f"لم أجد الملف «{DATA_FILE}». ضعه في نفس مجلد app.py ثم أعد التشغيل.")
    st.stop()

df = load_data(DATA_FILE)

# ----------------------------------------------------------------------------
# الشريط الجانبي: الفلاتر
# ----------------------------------------------------------------------------
st.sidebar.header("🎛️ الفلاتر")

categories = sorted(df["Category"].unique())
locations = sorted(df["Location"].unique())

sel_cat = st.sidebar.multiselect("الفئة", categories, default=categories)
sel_loc = st.sidebar.multiselect("المنطقة", locations, default=locations)

min_d, max_d = df["Order_Date"].min().date(), df["Order_Date"].max().date()
date_range = st.sidebar.date_input(
    "النطاق الزمني", value=(min_d, max_d), min_value=min_d, max_value=max_d
)
if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    start_d, end_d = date_range
else:  # المستخدم اختار تاريخاً واحداً فقط حتى الآن
    start_d = end_d = date_range[0] if isinstance(date_range, (tuple, list)) else date_range

mask = (
    df["Category"].isin(sel_cat)
    & df["Location"].isin(sel_loc)
    & df["Order_Date"].between(pd.Timestamp(start_d), pd.Timestamp(end_d))
)
fdf = df[mask]

st.sidebar.markdown("---")
st.sidebar.caption(f"عدد السجلات بعد التصفية: **{len(fdf):,}** من {len(df):,}")

# ----------------------------------------------------------------------------
# العنوان
# ----------------------------------------------------------------------------
st.markdown('<div class="dash-title">📊 داشبورد مبيعات شبين الكوم 2026</div>', unsafe_allow_html=True)
st.markdown('<div class="dash-sub">تحليل تفاعلي للإيرادات والطلبات والمنتجات</div>', unsafe_allow_html=True)

if fdf.empty:
    st.warning("لا توجد بيانات مطابقة للفلاتر المختارة. غيّر الفلاتر من الشريط الجانبي.")
    st.stop()

# ----------------------------------------------------------------------------
# KPIs
# ----------------------------------------------------------------------------
total_rev = fdf["Total_Price_EGP"].sum()
total_orders = fdf["Order_ID"].nunique()
aov = total_rev / total_orders

c1, c2, c3 = st.columns(3)
c1.markdown(kpi("💰 إجمالي المبيعات", fmt(total_rev), "ج.م"), unsafe_allow_html=True)
c2.markdown(kpi("🧾 إجمالي الطلبات", fmt(total_orders), "طلب"), unsafe_allow_html=True)
c3.markdown(kpi("🛒 متوسط قيمة الطلب", fmt(aov), "ج.م"), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# الرسوم البيانية
# ----------------------------------------------------------------------------
# 1) التطور الشهري
monthly = (
    fdf.groupby(fdf["Order_Date"].dt.to_period("M"))["Total_Price_EGP"].sum().reset_index()
)
monthly["Month"] = monthly["Order_Date"].dt.to_timestamp()
fig_month = px.line(
    monthly, x="Month", y="Total_Price_EGP", markers=True,
    title="📈 تطور المبيعات الشهرية",
    labels={"Month": "الشهر", "Total_Price_EGP": "المبيعات (ج.م)"},
)
fig_month.update_traces(line=dict(color=PRIMARY, width=3), marker=dict(size=9),
                        fill="tozeroy", fillcolor="rgba(79,70,229,.12)")
fig_month.update_xaxes(tickformat="%b %Y", dtick="M1")
st.plotly_chart(style(fig_month, 400), use_container_width=True)

col_a, col_b = st.columns(2)

# 2) المبيعات حسب الفئة
by_cat = (
    fdf.groupby("Category", as_index=False)["Total_Price_EGP"].sum()
    .sort_values("Total_Price_EGP", ascending=False)
)
fig_cat = px.bar(
    by_cat, x="Category", y="Total_Price_EGP", color="Category",
    color_discrete_sequence=PALETTE, text_auto=".3s",
    title="🗂️ المبيعات حسب الفئة",
    labels={"Category": "الفئة", "Total_Price_EGP": "المبيعات (ج.م)"},
)
fig_cat.update_xaxes(tickangle=-35)
col_a.plotly_chart(style(fig_cat, 430), use_container_width=True)

# 3) أعلى المناطق مبيعاً
by_loc = (
    fdf.groupby("Location", as_index=False)["Total_Price_EGP"].sum()
    .sort_values("Total_Price_EGP")
)
by_loc["Area"] = by_loc["Location"].str.replace("شبين الكوم - ", "", regex=False)
fig_loc = px.bar(
    by_loc, x="Total_Price_EGP", y="Area", orientation="h",
    color="Total_Price_EGP", color_continuous_scale="Blues", text_auto=".3s",
    title="📍 أعلى المناطق مبيعاً في شبين الكوم",
    labels={"Area": "المنطقة", "Total_Price_EGP": "المبيعات (ج.م)"},
)
fig_loc.update_coloraxes(showscale=False)
col_b.plotly_chart(style(fig_loc, 430), use_container_width=True)

# 4) أفضل 5 منتجات
top5 = (
    fdf.groupby("Product_Name", as_index=False)["Total_Price_EGP"].sum()
    .nlargest(5, "Total_Price_EGP").sort_values("Total_Price_EGP")
)
fig_top = px.bar(
    top5, x="Total_Price_EGP", y="Product_Name", orientation="h",
    color="Total_Price_EGP", color_continuous_scale="Purples", text_auto=".3s",
    title="🏆 أفضل 5 منتجات من حيث الإيرادات",
    labels={"Product_Name": "المنتج", "Total_Price_EGP": "الإيرادات (ج.م)"},
)
fig_top.update_coloraxes(showscale=False)
st.plotly_chart(style(fig_top, 360), use_container_width=True)

# ----------------------------------------------------------------------------
# الجدول التفصيلي
# ----------------------------------------------------------------------------
st.markdown("### 🔎 تفاصيل الطلبات")

s1, s2 = st.columns([3, 1])
query = s1.text_input("ابحث (اسم العميل، المنتج، رقم الطلب...)", placeholder="اكتب كلمة للبحث")
n_rows = s2.selectbox("عدد الصفوف", [50, 100, 250, 500, "الكل"], index=0)

table = fdf.sort_values("Order_Date", ascending=False)
if query:
    q = query.strip()
    text_cols = ["Order_ID", "Customer_Name", "Location", "Product_Name", "Category"]
    hit = table[text_cols].apply(lambda c: c.str.contains(q, case=False, na=False)).any(axis=1)
    table = table[hit]
if n_rows != "الكل":
    table = table.head(int(n_rows))

st.dataframe(
    table,
    use_container_width=True,
    hide_index=True,
    height=420,
    column_config={
        "Order_ID": "رقم الطلب",
        "Order_Date": st.column_config.DateColumn("التاريخ", format="YYYY-MM-DD"),
        "Customer_Name": "العميل",
        "Location": "المنطقة",
        "Product_Name": "المنتج",
        "Category": "الفئة",
        "Quantity": st.column_config.NumberColumn("الكمية", format="%d"),
        "Unit_Price_EGP": st.column_config.NumberColumn("سعر الوحدة", format="%d ج.م"),
        "Total_Price_EGP": st.column_config.NumberColumn("الإجمالي", format="%d ج.م"),
    },
)
st.caption(f"يعرض {len(table):,} صف")

st.download_button(
    "⬇️ تحميل البيانات المفلترة (CSV)",
    data=fdf.to_csv(index=False).encode("utf-8-sig"),
    file_name="filtered_sales.csv",
    mime="text/csv",
)