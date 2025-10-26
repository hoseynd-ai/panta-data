"""
رابط کاربری Streamlit - سیستم تحلیل مشتریان
نویسنده: hoseynd-ai
تاریخ: 2025-01-23 (نسخه نهایی)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from data_processor import DataProcessor, SearchMode
import datetime
from pathlib import Path

# ==================== تنظیمات صفحه ====================
st.set_page_config(
    page_title="سیستم تحلیل مشتریان",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="📊"
)

# ==================== CSS سفارشی ====================
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .customer-card {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #667eea;
        margin: 10px 0;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
    }
    .formal-badge {
        background-color: #28a745;
        color: white;
        padding: 5px 10px;
        border-radius: 5px;
        font-size: 12px;
    }
    .informal-badge {
        background-color: #ffc107;
        color: black;
        padding: 5px 10px;
        border-radius: 5px;
        font-size: 12px;
    }
</style>
""", unsafe_allow_html=True)

# ==================== Session State ====================
if "dp" not in st.session_state:
    st.session_state.dp = DataProcessor()
    st.session_state.data_loaded = False

dp: DataProcessor = st.session_state.dp

# ==================== بارگذاری داده ====================
if not st.session_state.data_loaded:
    try:
        with st.spinner("در حال بارگذاری داده..."):
            dp.load_data()
            dp.process_data()
            st.session_state.data_loaded = True
    except Exception as e:
        st.error(f"خطا در بارگذاری: {e}")
        st.stop()

# ==================== Header ====================
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.title("📊 سیستم تحلیل و مدیریت مشتریان")
with col_h2:
    st.caption(f"👤 hoseynd-ai")
    st.caption(f"🕐 {datetime.datetime.now().strftime('%Y/%m/%d %H:%M')}")
    if st.button("🔄 بازخوانی داده"):
        dp.load_data()
        dp.process_data()
        st.rerun()

# ==================== Sidebar ====================
st.sidebar.title("🎯 منوی اصلی")
menu = st.sidebar.radio(
    "انتخاب بخش:",
    [
        "🏠 داشبورد",
        "🔍 جستجوی مشتری",
        "📊 تحلیل محصولات",
        "📈 تحلیل زمانی",
        "📋 تحلیل وضعیت سفارشات",
        "🔴 مشتریان از دست رفته",
        "👥 مدیریت CRM",
        "📥 گزارش‌گیری"
    ]
)

# ==================== 🏠 داشبورد ====================
if menu == "🏠 داشبورد":
    st.subheader("🏠 داشبورد اصلی")
    
    # KPI ها
    total_customers = dp.processed_data['customer_name'].nunique()
    total_orders = len(dp.processed_data)
    total_products = dp.processed_data['product_count'].sum()
    
    # آمار رسمی/غیررسمی
    formal_count = len(dp.processed_data[dp.processed_data['state_normalized'] == 'رسمی'])
    informal_count = len(dp.processed_data[dp.processed_data['state_normalized'] == 'غیررسمی'])
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("👥 تعداد مشتریان", f"{total_customers:,}")
    with col2:
        st.metric("🛒 کل سفارشات", f"{total_orders:,}")
        st.caption(f"🟢 رسمی: {formal_count:,} | 🟡 غیررسمی: {informal_count:,}")
    with col3:
        st.metric("📦 کل محصولات", f"{int(total_products):,}")
    with col4:
        formal_percentage = (formal_count / total_orders * 100) if total_orders > 0 else 0
        st.metric("نرخ رسمی", f"{formal_percentage:.1f}%")
    
    st.divider()
    
    # نمودارها
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        yearly_stats = dp.get_yearly_stats()
        
        fig1 = go.Figure()
        
        fig1.add_trace(go.Bar(
            name='سفارش رسمی',
            x=yearly_stats['سال'],
            y=yearly_stats['سفارش_رسمی'],
            marker_color='#28a745'
        ))
        
        fig1.add_trace(go.Bar(
            name='سفارش غیررسمی',
            x=yearly_stats['سال'],
            y=yearly_stats['سفارش_غیررسمی'],
            marker_color='#ffc107'
        ))
        
        fig1.update_layout(
            title='📊 سفارشات سالانه (رسمی/غیررسمی)',
            barmode='stack',
            xaxis_title='سال',
            yaxis_title='تعداد سفارش'
        )
        
        st.plotly_chart(fig1, use_container_width=True)
    
    with col_chart2:
        product_stats = dp.get_product_stats().head(10)
        fig2 = px.pie(
            product_stats,
            values='تعداد_فروش',
            names='محصول',
            title='🎯 10 محصول پرفروش',
            hole=0.4
        )
        st.plotly_chart(fig2, use_container_width=True)
    
    st.divider()
    
    st.markdown("### 📋 تحلیل وضعیت سفارشات")
    
    state_stats = dp.get_order_state_stats()
    
    col_state1, col_state2 = st.columns(2)
    
    with col_state1:
        fig3 = px.bar(
            state_stats,
            x='وضعیت',
            y='تعداد_سفارش',
            title='تعداد سفارشات بر اساس وضعیت',
            color='وضعیت',
            color_discrete_map={'رسمی': '#28a745', 'غیررسمی': '#ffc107'}
        )
        st.plotly_chart(fig3, use_container_width=True)
    
    with col_state2:
        st.dataframe(state_stats, use_container_width=True, height=200)

# ==================== 🔍 جستجوی مشتری ====================
elif menu == "🔍 جستجوی مشتری":
    st.subheader("🔍 جستجوی هوشمند مشتری")
    
    st.info("💡 می‌توانید با هر بخشی از نام مشتری جستجو کنید. مثلاً: 'ایرانیان' یا 'کریمان' یا 'آبادگران'")
    
    col_search1, col_search2 = st.columns([3, 1])
    
    with col_search1:
        query = st.text_input("🔎 نام مشتری:", placeholder="مثال: ایرانیان")
    
    with col_search2:
        search_mode = st.selectbox(
            "حالت:",
            [
                ("خودکار ⭐", SearchMode.AUTO),
                ("دقیق", SearchMode.EXACT),
                ("کلمات کلیدی", SearchMode.PARTIAL),
                ("فازی", SearchMode.FUZZY)
            ],
            format_func=lambda x: x[0]
        )[1]
    
    min_score = st.slider("حداقل امتیاز:", 0, 100, 60, 5)
    
    if query.strip():
        with st.spinner("در حال جستجو..."):
            results = dp.search_customer(query, mode=search_mode, min_score=min_score)
        
        if results:
            st.success(f"✅ {len(results)} مشتری یافت شد")
            
            for i, result in enumerate(results, 1):
                with st.expander(f"🏢 {i}. {result.customer_name} - امتیاز: {result.match_score}%", expanded=i==1):
                    
                    col_info1, col_info2, col_info3, col_info4 = st.columns(4)
                    
                    with col_info1:
                        st.metric("کل سفارشات", result.total_purchases)
                    with col_info2:
                        st.metric("🟢 سفارش رسمی", result.formal_purchases)
                    with col_info3:
                        st.metric("🟡 سفارش غیررسمی", result.informal_purchases)
                    with col_info4:
                        st.metric("تعداد محصول", result.total_products)
                    
                    col_time1, col_time2 = st.columns(2)
                    
                    with col_time1:
                        years_str = ", ".join(map(str, result.years_active))
                        st.info(f"📅 **سال‌های فعالیت:** {years_str}")
                    
                    with col_time2:
                        months_str = ", ".join(map(str, result.months_active))
                        st.info(f"📆 **ماه‌های فعالیت:** {months_str}")
                    
                    st.divider()
                    
                    tab1, tab2, tab3, tab4 = st.tabs(["📞 تماس", "🗺️ آدرس", "📦 محصولات", "📋 تاریخچه"])
                    
                    with tab1:
                        st.markdown("#### شماره‌های تماس")
                        
                        col_phone1, col_phone2 = st.columns(2)
                        
                        with col_phone1:
                            if result.mobile_numbers:
                                st.markdown("**📱 موبایل:**")
                                for mobile in result.mobile_numbers:
                                    if mobile:
                                        st.code(mobile)
                            else:
                                st.warning("شماره موبایل ثبت نشده")
                        
                        with col_phone2:
                            if result.phone_numbers:
                                st.markdown("**☎️ ثابت:**")
                                for phone in result.phone_numbers:
                                    if phone:
                                        st.code(phone)
                            else:
                                st.warning("شماره ثابت ثبت نشده")
                    
                    with tab2:
                        st.markdown("#### 🗺️ آدرس‌ها")
                        if result.addresses:
                            for idx, addr in enumerate(result.addresses, 1):
                                if addr and addr != 'nan':
                                    st.info(f"**آدرس {idx}:** {addr}")
                        else:
                            st.warning("آدرسی ثبت نشده")
                    
                    with tab3:
                        st.markdown("#### 📦 محصولات خریداری شده")
                        if result.products:
                            cols = st.columns(3)
                            for idx, product in enumerate(result.products):
                                with cols[idx % 3]:
                                    st.markdown(f"- {product}")
                        else:
                            st.warning("محصولی ثبت نشده")
                    
                    with tab4:
                        st.markdown("#### 📋 تاریخچه کامل خریدها")
                        details_df = dp.get_customer_details(result.customer_name)
                        
                        st.dataframe(
                            details_df[['year', 'month', 'state_normalized', 'products_list', 'mobile', 'address']],
                            use_container_width=True,
                            height=300
                        )
                        
                        csv = details_df.to_csv(index=False, encoding='utf-8-sig')
                        st.download_button(
                            f"📥 دانلود تاریخچه {result.customer_name}",
                            csv,
                            f"customer_{result.customer_name}.csv",
                            "text/csv"
                        )
        
        else:
            st.warning("❌ نتیجه‌ای یافت نشد. امتیاز را کاهش دهید یا حالت جستجو را تغییر دهید.")

# ==================== 📊 تحلیل محصولات ====================
elif menu == "📊 تحلیل محصولات":
    st.subheader("📊 تحلیل محصولات")
    
    product_stats = dp.get_product_stats()
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.metric("تعداد محصولات منحصر به فرد", len(product_stats))
    with col2:
        st.metric("مجموع فروش", int(product_stats['تعداد_فروش'].sum()))
    
    st.divider()
    
    top_n = st.slider("تعداد محصولات برتر:", 5, 50, 20)
    
    fig = px.bar(
        product_stats.head(top_n),
        x='محصول',
        y='تعداد_فروش',
        title=f'{top_n} محصول پرفروش',
        color='تعداد_فروش',
        color_continuous_scale='Viridis'
    )
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    st.markdown("### 📋 لیست کامل محصولات")
    st.dataframe(product_stats, use_container_width=True, height=400)
    
    csv = product_stats.to_csv(index=False, encoding='utf-8-sig')
    st.download_button(
        "📥 دانلود گزارش محصولات",
        csv,
        "product_report.csv",
        "text/csv"
    )

# ==================== 📈 تحلیل زمانی ====================
elif menu == "📈 تحلیل زمانی":
    st.subheader("📈 تحلیل زمانی مشتریان")
    
    st.markdown("### 📊 تحلیل سالانه")
    yearly_stats = dp.get_yearly_stats()
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig1 = px.line(
            yearly_stats,
            x='سال',
            y='تعداد_مشتری',
            title='روند تعداد مشتریان',
            markers=True
        )
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        fig2 = go.Figure()
        
        fig2.add_trace(go.Bar(
            name='رسمی',
            x=yearly_stats['سال'],
            y=yearly_stats['سفارش_رسمی'],
            marker_color='#28a745'
        ))
        
        fig2.add_trace(go.Bar(
            name='غیررسمی',
            x=yearly_stats['سال'],
            y=yearly_stats['سفارش_غیررسمی'],
            marker_color='#ffc107'
        ))
        
        fig2.update_layout(
            title='سفارشات رسمی و غیررسمی',
            barmode='group'
        )
        
        st.plotly_chart(fig2, use_container_width=True)
    
    st.dataframe(yearly_stats, use_container_width=True)
    
    st.divider()
    
    st.markdown("### 📅 تحلیل ماهانه (دسته‌بندی شده بر اساس سال)")
    
    available_years = sorted(dp.processed_data['year'].dropna().unique(), reverse=True)
    selected_year = st.selectbox(
        "📅 انتخاب سال:",
        available_years
    )
    
    if selected_year:
        monthly_stats = dp.get_monthly_stats(int(selected_year))
        
        if not monthly_stats.empty:
            fig3 = go.Figure()
            
            fig3.add_trace(go.Scatter(
                x=monthly_stats['ماه'],
                y=monthly_stats['تعداد_سفارش'],
                mode='lines+markers',
                name='کل سفارشات',
                line=dict(color='#667eea', width=3)
            ))
            
            fig3.add_trace(go.Scatter(
                x=monthly_stats['ماه'],
                y=monthly_stats['سفارش_رسمی'],
                mode='lines+markers',
                name='سفارش رسمی',
                line=dict(color='#28a745', width=2)
            ))
            
            fig3.add_trace(go.Scatter(
                x=monthly_stats['ماه'],
                y=monthly_stats['سفارش_غیررسمی'],
                mode='lines+markers',
                name='سفارش غیررسمی',
                line=dict(color='#ffc107', width=2)
            ))
            
            fig3.update_layout(
                title=f'📊 روند ماهانه سال {int(selected_year)}',
                xaxis_title='ماه',
                yaxis_title='تعداد سفارش',
                xaxis=dict(tickmode='linear', tick0=1, dtick=1)
            )
            
            st.plotly_chart(fig3, use_container_width=True)
            
            st.dataframe(monthly_stats, use_container_width=True)
        else:
            st.warning(f"❌ داده‌ای برای سال {int(selected_year)} یافت نشد")
    
    st.divider()
    
    with st.expander("🗓️ مشاهده تمام سال‌ها و ماه‌های آنها"):
        yearly_monthly_data = dp.get_yearly_monthly_grouped()
        
        for year, monthly_df in yearly_monthly_data.items():
            st.markdown(f"#### 📅 سال {year}")
            st.dataframe(monthly_df, use_container_width=True, height=200)

# ==================== 📋 تحلیل وضعیت سفارشات ====================
elif menu == "📋 تحلیل وضعیت سفارشات":
    st.subheader("📋 تحلیل وضعیت سفارشات (رسمی/غیررسمی)")
    
    state_stats = dp.get_order_state_stats()
    
    col1, col2, col3 = st.columns(3)
    
    formal_data = state_stats[state_stats['وضعیت'] == 'رسمی']
    informal_data = state_stats[state_stats['وضعیت'] == 'غیررسمی']
    
    with col1:
        formal_count = formal_data['تعداد_سفارش'].sum() if not formal_data.empty else 0
        st.metric("🟢 سفارشات رسمی", f"{int(formal_count):,}")
    
    with col2:
        informal_count = informal_data['تعداد_سفارش'].sum() if not informal_data.empty else 0
        st.metric("🟡 سفارشات غیررسمی", f"{int(informal_count):,}")
    
    with col3:
        total = formal_count + informal_count
        formal_percent = (formal_count / total * 100) if total > 0 else 0
        st.metric("نرخ رسمی‌سازی", f"{formal_percent:.1f}%")
    
    st.divider()
    
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        fig1 = px.pie(
            state_stats,
            values='تعداد_سفارش',
            names='وضعیت',
            title='توزیع سفارشات',
            color='وضعیت',
            color_discrete_map={'رسمی': '#28a745', 'غیررسمی': '#ffc107'},
            hole=0.4
        )
        st.plotly_chart(fig1, use_container_width=True)
    
    with col_chart2:
        fig2 = px.bar(
            state_stats,
            x='وضعیت',
            y=['تعداد_مشتری', 'تعداد_سفارش', 'تعداد_محصول'],
            title='مقایسه آماری',
            barmode='group'
        )
        st.plotly_chart(fig2, use_container_width=True)
    
    st.dataframe(state_stats, use_container_width=True)
    
    st.divider()
    
    st.markdown("### 📊 روند رسمی‌سازی در طول زمان")
    
    yearly_stats = dp.get_yearly_stats()
    
    fig3 = go.Figure()
    
    fig3.add_trace(go.Scatter(
        x=yearly_stats['سال'],
        y=yearly_stats['سفارش_رسمی'],
        mode='lines+markers',
        name='رسمی',
        fill='tonexty',
        line=dict(color='#28a745', width=3)
    ))
    
    fig3.add_trace(go.Scatter(
        x=yearly_stats['سال'],
        y=yearly_stats['سفارش_غیررسمی'],
        mode='lines+markers',
        name='غیررسمی',
        fill='tozeroy',
        line=dict(color='#ffc107', width=3)
    ))
    
    fig3.update_layout(
        title='روند سالانه سفارشات رسمی و غیررسمی',
        xaxis_title='سال',
        yaxis_title='تعداد سفارش'
    )
    
    st.plotly_chart(fig3, use_container_width=True)

# ==================== 🔴 مشتریان از دست رفته ====================
elif menu == "🔴 مشتریان از دست رفته":
    st.subheader("🔴 شناسایی مشتریان از دست رفته")
    
    st.markdown("""
    این بخش مشتریانی را شناسایی می‌کند که در گذشته از شما خرید داشتند 
    اما اخیراً خریدی انجام نداده‌اند.
    
    **🎯 منطق کار:**
    - مشتریانی که در بازه **سال‌های فعالیت** حداقل یک بار خرید کرده‌اند
    - اما در بازه **سال‌های سکوت** هیچ خریدی نداشته‌اند
    - تطبیق هوشمند نام‌ها (حداقل 2 از 3 کلمه مشترک یا شبیه)
    - محصولات نرمال‌سازی شده (Panflow 110 = panflow110)
    """)
    
    # تنظیمات
    with st.expander("⚙️ تنظیمات جستجو", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📅 دوره فعالیت")
            active_start = st.number_input(
                "شروع دوره فعالیت",
                min_value=1390,
                max_value=1404,
                value=1393,
                help="مشتریانی که از این سال به بعد خرید داشته‌اند"
            )
            
            active_end = st.number_input(
                "پایان دوره فعالیت",
                min_value=1390,
                max_value=1404,
                value=1402,
                help="تا این سال خرید داشته‌اند"
            )
            
            min_purchases = st.number_input(
                "حداقل تعداد خرید",
                min_value=1,
                max_value=50,
                value=1,
                help="فقط مشتریانی که حداقل این تعداد خرید داشته‌اند"
            )
        
        with col2:
            st.markdown("#### 🔇 دوره سکوت")
            silent_start = st.number_input(
                "شروع دوره سکوت",
                min_value=1390,
                max_value=1404,
                value=1403,
                help="از این سال به بعد خرید نداشته‌اند"
            )
            
            silent_end = st.number_input(
                "پایان دوره سکوت",
                min_value=1390,
                max_value=1404,
                value=1404,
                help="تا این سال هیچ خریدی نداشته‌اند"
            )
            
            similarity = st.slider(
                "درصد شباهت کلمات",
                min_value=70,
                max_value=100,
                value=85,
                help="برای تشخیص نام‌های شبیه (مثلاً آبادگران ≈ ابادگران)"
            )
    
    # دکمه جستجو
    if st.button("🔍 شناسایی مشتریان از دست رفته", type="primary", use_container_width=True):
        with st.spinner("در حال پردازش... این ممکن است چند ثانیه طول بکشد..."):
            try:
                lost_df = dp.find_lost_customers(
                    active_period_start=int(active_start),
                    active_period_end=int(active_end),
                    silent_period_start=int(silent_start),
                    silent_period_end=int(silent_end),
                    similarity_threshold=float(similarity),
                    min_purchase_count=int(min_purchases)
                )
                
                if len(lost_df) == 0:
                    st.success("🎉 هیچ مشتری از دست رفته‌ای یافت نشد!")
                    st.balloons()
                else:
                    # نمایش آمار
                    st.success(f"✅ {len(lost_df)} مشتری از دست رفته شناسایی شد!")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        high_priority = len(lost_df[lost_df['اولویت'] == '🔴 بالا'])
                        st.metric("🔴 اولویت بالا", high_priority)
                    
                    with col2:
                        medium_priority = len(lost_df[lost_df['اولویت'] == '🟡 متوسط'])
                        st.metric("🟡 اولویت متوسط", medium_priority)
                    
                    with col3:
                        low_priority = len(lost_df[lost_df['اولویت'] == '🟢 پایین'])
                        st.metric("🟢 اولویت پایین", low_priority)
                    
                    with col4:
                        total_purchases = lost_df['تعداد_خرید'].sum()
                        st.metric("📊 مجموع خریدها", f"{total_purchases:,}")
                    
                    st.divider()
                    
                    # فیلتر اولویت
                    st.subheader("📊 نتایج")
                    
                    priority_filter = st.multiselect(
                        "فیلتر بر اساس اولویت:",
                        options=['🔴 بالا', '🟡 متوسط', '🟢 پایین'],
                        default=['🔴 بالا', '🟡 متوسط', '🟢 پایین']
                    )
                    
                    filtered_df = lost_df[lost_df['اولویت'].isin(priority_filter)]
                    
                    # نمایش جدول
                    st.dataframe(
                        filtered_df,
                        use_container_width=True,
                        height=400,
                        column_config={
                            "نام_مشتری": st.column_config.TextColumn("نام مشتری", width="medium"),
                            "آخرین_سال": st.column_config.NumberColumn("آخرین سال", format="%d"),
                            "آخرین_ماه": st.column_config.NumberColumn("آخرین ماه", format="%d"),
                            "تعداد_خرید": st.column_config.NumberColumn("تعداد خرید", format="%d"),
                            "اولویت": st.column_config.TextColumn("اولویت", width="small"),
                        }
                    )
                    
                    st.divider()
                    
                    # دکمه دانلود
                    st.subheader("💾 خروجی اکسل")
                    
                    col_dl1, col_dl2 = st.columns([2, 1])
                    
                    with col_dl1:
                        st.info(f"📋 آماده دانلود: {len(filtered_df)} مشتری در فایل اکسل با 2 شیت (داده‌ها + آمار)")
                    
                    with col_dl2:
                        if st.button("📥 تولید و دانلود فایل اکسل", type="primary", use_container_width=True):
                            with st.spinner("در حال تولید فایل..."):
                                filepath = dp.export_lost_customers_to_excel(lost_df)
                                
                                with open(filepath, 'rb') as f:
                                    st.download_button(
                                        label="⬇️ دانلود فایل اکسل",
                                        data=f,
                                        file_name=Path(filepath).name,
                                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                        use_container_width=True
                                    )
                                
                                st.success(f"✅ فایل ذخیره شد در: `{filepath}`")
                    
                    # نمایش جزئیات برخی مشتریان
                    st.divider()
                    st.subheader("🔍 جزئیات مشتریان با اولویت بالا")
                    
                    high_priority_customers = filtered_df[filtered_df['اولویت'] == '🔴 بالا'].head(5)
                    
                    if len(high_priority_customers) > 0:
                        for idx, row in high_priority_customers.iterrows():
                            with st.expander(f"🏢 {row['نام_مشتری']} - {row['تعداد_خرید']} خرید"):
                                col_detail1, col_detail2 = st.columns(2)
                                
                                with col_detail1:
                                    st.markdown(f"**📅 آخرین خرید:** {int(row['آخرین_سال'])}/{int(row['آخرین_ماه'])}")
                                    st.markdown(f"**📊 {row['آمار_سفارشات']}**")
                                    st.markdown(f"**📱 موبایل:** {row['موبایل']}")
                                
                                with col_detail2:
                                    st.markdown(f"**☎️ تلفن:** {row['تلفن']}")
                                    st.markdown(f"**🗺️ آدرس:** {row['آدرس']}")
                                    st.markdown(f"**📦 محصولات:** {row['محصولات']}")
                    else:
                        st.info("مشتری با اولویت بالا یافت نشد")
                
            except Exception as e:
                st.error(f"❌ خطا در پردازش: {e}")
                st.exception(e)

# ==================== 👥 مدیریت CRM ====================
elif menu == "👥 مدیریت CRM":
    st.subheader("👥 مدیریت مشتریان (CRM)")
    
    tab1, tab2, tab3 = st.tabs(["➕ افزودن مشتری", "✏️ ویرایش", "📋 لیست کامل"])
    
    with tab1:
        st.markdown("### ➕ افزودن مشتری/سفارش جدید")
        
        with st.form("add_customer_form"):
            col_form1, col_form2 = st.columns(2)
            
            with col_form1:
                new_name = st.text_input("نام مشتری *", help="نام کامل شرکت یا شخص")
                new_year = st.number_input("سال *", min_value=1390, max_value=1410, value=1404)
                new_month = st.number_input("ماه *", min_value=1, max_value=12, value=1)
                new_state = st.selectbox(
                    "وضعیت سفارش *",
                    ["رسمی", "غیررسمی"],
                    help="آیا این سفارش رسمی است یا غیررسمی؟"
                )
            
            with col_form2:
                new_address = st.text_area("آدرس", help="آدرس کامل")
                new_mobile = st.text_input("شماره موبایل", placeholder="09123456789")
                new_phone = st.text_input("شماره ثابت", placeholder="02112345678")
                new_products = st.text_input(
                    "محصولات (با , جدا کنید)",
                    placeholder="محصول A، محصول B، محصول C",
                    help="نام محصولات را با کاما از هم جدا کنید"
                )
            
            submitted = st.form_submit_button("💾 ذخیره سفارش", type="primary", use_container_width=True)
            
            if submitted:
                if new_name and new_year and new_month and new_state:
                    success = dp.add_customer(
                        customer_name=new_name,
                        year=new_year,
                        month=new_month,
                        state=new_state,
                        address=new_address,
                        mobile=new_mobile,
                        phone=new_phone,
                        products=new_products
                    )
                    
                    if success:
                        st.success("✅ سفارش با موفقیت ثبت شد!")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error("❌ خطا در ثبت سفارش")
                else:
                    st.warning("⚠️ لطفاً فیلدهای ضروری (*) را پر کنید")
    
    with tab2:
        st.markdown("### ✏️ ویرایش سفارش مشتری")
        
        all_customers = sorted(dp.processed_data['customer_name'].unique())
        selected_customer = st.selectbox("🔍 انتخاب مشتری:", all_customers)
        
        if selected_customer:
            customer_records = dp.get_customer_details(selected_customer)
            
            st.markdown(f"#### 📋 سفارشات {selected_customer}")
            st.dataframe(
                customer_records[['year', 'month', 'state_normalized', 'mobile', 'products_list']],
                use_container_width=True
            )
            
            record_index = st.selectbox(
                "انتخاب رکورد برای ویرایش:",
                customer_records.index.tolist(),
                format_func=lambda x: f"ردیف {x} - سال {int(customer_records.loc[x, 'year'])} ماه {int(customer_records.loc[x, 'month'])}"
            )
            
            if record_index is not None:
                record = customer_records.loc[record_index]
                
                st.divider()
                
                with st.form("edit_form"):
                    st.markdown("#### ✏️ ویرایش اطلاعات")
                    
                    edit_name = st.text_input("نام", value=record['customer_name'])
                    
                    col_e1, col_e2, col_e3 = st.columns(3)
                    with col_e1:
                        edit_year = st.number_input("سال", value=int(record['year']))
                    with col_e2:
                        edit_month = st.number_input("ماه", value=int(record['month']))
                    with col_e3:
                        edit_state = st.selectbox(
                            "وضعیت",
                            ["رسمی", "غیررسمی"],
                            index=0 if record['state_normalized'] == 'رسمی' else 1
                        )
                    
                    edit_mobile = st.text_input("موبایل", value=record['mobile'])
                    edit_phone = st.text_input("ثابت", value=record['phone'])
                    edit_address = st.text_area("آدرس", value=record['address'])
                    edit_products = st.text_input("محصولات", value=", ".join(record['products_list']))
                    
                    col_btn1, col_btn2 = st.columns(2)
                    
                    with col_btn1:
                        if st.form_submit_button("💾 ذخیره تغییرات", type="primary", use_container_width=True):
                            dp.update_customer(
                                index=record_index,
                                customer_name=edit_name,
                                year=edit_year,
                                month=edit_month,
                                state=edit_state,
                                mobile=edit_mobile,
                                phone=edit_phone,
                                address=edit_address,
                                products=edit_products
                            )
                            st.success("✅ تغییرات ذخیره شد")
                            st.rerun()
                    
                    with col_btn2:
                        if st.form_submit_button("🗑️ حذف رکورد", type="secondary", use_container_width=True):
                            if st.session_state.get('confirm_delete', False):
                                dp.delete_customer(record_index)
                                st.success("✅ رکورد حذف شد")
                                st.session_state.confirm_delete = False
                                st.rerun()
                            else:
                                st.session_state.confirm_delete = True
                                st.warning("⚠️ برای تایید حذف، دوباره کلیک کنید")
    
    with tab3:
        st.markdown("### 📋 لیست کامل سفارشات")
        
        col_filter1, col_filter2, col_filter3 = st.columns(3)
        
        with col_filter1:
            filter_year = st.multiselect(
                "فیلتر سال:",
                sorted(dp.processed_data['year'].dropna().unique())
            )
        
        with col_filter2:
            filter_state = st.multiselect(
                "فیلتر وضعیت:",
                ['رسمی', 'غیررسمی']
            )
        
        with col_filter3:
            filter_customer = st.text_input("فیلتر نام مشتری:")
        
        filtered_df = dp.processed_data.copy()
        
        if filter_year:
            filtered_df = filtered_df[filtered_df['year'].isin(filter_year)]
        
        if filter_state:
            filtered_df = filtered_df[filtered_df['state_normalized'].isin(filter_state)]
        
        if filter_customer:
            filtered_df = filtered_df[
                filtered_df['customer_name'].str.contains(filter_customer, case=False, na=False)
            ]
        
        st.caption(f"نمایش {len(filtered_df):,} رکورد از {len(dp.processed_data):,}")
        
        st.dataframe(
            filtered_df[['customer_name', 'year', 'month', 'state_normalized', 'mobile', 'products_list']],
            use_container_width=True,
            height=500
        )
        
        csv = filtered_df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            "📥 دانلود لیست (CSV)",
            csv,
            "all_orders.csv",
            "text/csv",
            use_container_width=True
        )

# ==================== 📥 گزارش‌گیری ====================
elif menu == "📥 گزارش‌گیری":
    st.subheader("📥 گزارش‌گیری و خروجی")
    
    st.markdown("### 📊 گزارش‌های آماده")
    
    col_report1, col_report2, col_report3 = st.columns(3)
    
    with col_report1:
        if st.button("📊 گزارش سالانه", use_container_width=True):
            yearly = dp.get_yearly_stats()
            filename = f"yearly_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
            dp.export_to_excel(filename, yearly)
            
            with open(filename, 'rb') as f:
                st.download_button(
                    "⬇️ دانلود گزارش سالانه",
                    f,
                    filename,
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
    
    with col_report2:
        if st.button("📦 گزارش محصولات", use_container_width=True):
            products = dp.get_product_stats()
            filename = f"products_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
            dp.export_to_excel(filename, products)
            
            with open(filename, 'rb') as f:
                st.download_button(
                    "⬇️ دانلود گزارش محصولات",
                    f,
                    filename,
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
    
    with col_report3:
        if st.button("📋 گزارش وضعیت", use_container_width=True):
            states = dp.get_order_state_stats()
            filename = f"state_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
            dp.export_to_excel(filename, states)
            
            with open(filename, 'rb') as f:
                st.download_button(
                    "⬇️ دانلود گزارش وضعیت",
                    f,
                    filename,
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
    
    st.divider()
    
    st.markdown("### 🎯 گزارش سفارشی")
    
    report_type = st.selectbox(
        "نوع گزارش:",
        ["سالانه", "ماهانه", "محصولات", "وضعیت سفارشات", "همه داده‌ها"]
    )
    
    if report_type == "ماهانه":
        selected_year_report = st.selectbox(
            "انتخاب سال:",
            sorted(dp.processed_data['year'].dropna().unique(), reverse=True)
        )
    else:
        selected_year_report = None
    
    if st.button("📥 تولید گزارش", type="primary"):
        if report_type == "سالانه":
            data = dp.get_yearly_stats()
        elif report_type == "ماهانه":
            data = dp.get_monthly_stats(int(selected_year_report))
        elif report_type == "محصولات":
            data = dp.get_product_stats()
        elif report_type == "وضعیت سفارشات":
            data = dp.get_order_state_stats()
        else:
            data = dp.processed_data
        
        st.success("✅ گزارش آماده شد")
        st.dataframe(data, use_container_width=True, height=400)
        
        col_dl1, col_dl2 = st.columns(2)
        
        with col_dl1:
            csv = data.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                "⬇️ دانلود CSV",
                csv,
                f"report_{report_type}_{datetime.datetime.now().strftime('%Y%m%d')}.csv",
                "text/csv",
                use_container_width=True
            )
        
        with col_dl2:
            filename = f"report_{report_type}_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
            dp.export_to_excel(filename, data)
            
            with open(filename, 'rb') as f:
                st.download_button(
                    "⬇️ دانلود Excel",
                    f,
                    filename,
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

# ==================== Footer ====================
st.divider()
col_footer1, col_footer2 = st.columns([3, 1])

with col_footer1:
    st.caption("🔧 سیستم تحلیل و مدیریت مشتریان | طراحی شده توسط hoseynd-ai | 2025")

with col_footer2:
    st.caption(f"📊 کل داده‌ها: {len(dp.processed_data):,} رکورد")