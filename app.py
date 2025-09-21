import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from data_processor import DataProcessor
import os

# Page configuration
st.set_page_config(
    page_title="سیستم جستجوی کامل مشتریان پنتا (1393-1404)",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better RTL support and styling
st.markdown("""
<style>
    .main > div {
        direction: rtl;
        text-align: right;
    }
    .stDataFrame {
        direction: rtl;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .search-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 1rem;
        margin-bottom: 2rem;
        text-align: center;
    }
    .company-header {
        background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 0.8rem;
        margin: 1rem 0;
        text-align: center;
        font-size: 1.5rem;
        font-weight: bold;
    }
    .trend-up {
        color: #28a745;
        font-weight: bold;
    }
    .trend-down {
        color: #dc3545;
        font-weight: bold;
    }
    .trend-stable {
        color: #6c757d;
        font-weight: bold;
    }
    .sheet-info {
        background: linear-gradient(90deg, #ffecd2 0%, #fcb69f 100%);
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

def display_company_analysis(analysis_result):
    """نمایش تحلیل تفصیلی شرکت"""
    if "error" in analysis_result:
        st.error(analysis_result["error"])
        return
    
    company_name = analysis_result["company_name"]
    match_score = analysis_result["match_score"]
    
    # Header شرکت
    st.markdown(f"""
    <div class="company-header">
        🏢 {company_name.upper()} 
        <small>(تطبیق: {match_score}%)</small>
    </div>
    """, unsafe_allow_html=True)
    
    # آمار کلی
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("تعداد کل فایل‌ها", analysis_result["total_files"])
    with col2:
        st.metric("سال‌های فعال", len(analysis_result["years_active"]))
    with col3:
        years_range = f"{min(analysis_result['years_active'])}-{max(analysis_result['years_active'])}" if len(analysis_result['years_active']) > 1 else str(analysis_result['years_active'][0])
        st.metric("دوره فعالیت", years_range)
    with col4:
        trend = analysis_result["trend_analysis"]
        trend_class = "trend-up" if "صعودی" in trend else ("trend-down" if "نزولی" in trend else "trend-stable")
        st.markdown(f'<p class="{trend_class}">روند: {trend}</p>', unsafe_allow_html=True)
    with col5:
        total_phones = sum([stats["phones"] for stats in analysis_result["yearly_stats"].values()])
        st.metric("کل شماره تلفن", total_phones)
    
    # توزیع بر اساس شیت منبع
    st.subheader("📊 توزیع بر اساس شیت منبع")
    sheet_dist = analysis_result["sheet_distribution"]
    if sheet_dist:
        col1, col2 = st.columns(2)
        with col1:
            # نمودار دایره‌ای توزیع شیت‌ها
            fig_sheet = px.pie(
                values=list(sheet_dist.values()),
                names=list(sheet_dist.keys()),
                title="توزیع فایل‌ها بر اساس سال (شیت)"
            )
            st.plotly_chart(fig_sheet, use_container_width=True)
        
        with col2:
            # جدول توزیع شیت‌ها
            sheet_df = pd.DataFrame([
                {"سال (شیت)": sheet, "تعداد فایل": count, "درصد": f"{count/analysis_result['total_files']*100:.1f}%"}
                for sheet, count in sheet_dist.items()
            ])
            st.dataframe(sheet_df, use_container_width=True, hide_index=True)
    
    # آمار وضعیت
    st.subheader("📋 تفکیک بر اساس وضعیت")
    status_counts = analysis_result["status_counts"]
    total = analysis_result["total_files"]
    
    col1, col2, col3 = st.columns(3)
    with col1:
        formal_count = status_counts.get("رسمی", 0)
        formal_pct = (formal_count / total * 100) if total > 0 else 0
        st.metric("رسمی", f"{formal_count} ({formal_pct:.1f}%)")
    with col2:
        informal_count = status_counts.get("غیررسمی", 0)
        informal_pct = (informal_count / total * 100) if total > 0 else 0
        st.metric("غیررسمی", f"{informal_count} ({informal_pct:.1f}%)")
    with col3:
        unknown_count = status_counts.get("نامشخص", 0)
        unknown_pct = (unknown_count / total * 100) if total > 0 else 0
        st.metric("نامشخص", f"{unknown_count} ({unknown_pct:.1f}%)")
    
    # آمار سالانه تفصیلی
    st.subheader("📈 تحلیل سالانه تفصیلی")
    yearly_stats = analysis_result["yearly_stats"]
    
    if yearly_stats:
        years_data = []
        for year, stats in yearly_stats.items():
            months = ", ".join(sorted([m for m in stats["months"] if m != "نامشخص"]))
            years_data.append({
                "سال": year,
                "کل فایل‌ها": stats["total"],
                "رسمی": stats["رسمی"],
                "غیررسمی": stats["غیررسمی"],
                "نامشخص": stats["نامشخص"],
                "شماره تلفن": stats["phones"],
                "ماه‌های فعال": months
            })
        
        yearly_df = pd.DataFrame(years_data).sort_values("سال")
        st.dataframe(yearly_df, use_container_width=True, hide_index=True)
        
        # نمودارهای تحلیلی
        col1, col2 = st.columns(2)
        
        with col1:
            # نمودار روند فعالیت سالانه
            fig_trend = px.line(
                yearly_df,
                x="سال",
                y="کل فایل‌ها",
                title=f"روند فعالیت سالانه {company_name}",
                markers=True
            )
            fig_trend.update_layout(xaxis_title="سال", yaxis_title="تعداد فایل‌ها")
            st.plotly_chart(fig_trend, use_container_width=True)
        
        with col2:
            # نمودار تفکیک وضعیت
            fig_status = px.bar(
                yearly_df,
                x="سال",
                y=["رسمی", "غیررسمی", "نامشخص"],
                title=f"تفکیک وضعیت فایل‌های {company_name}",
                color_discrete_map={
                    "رسمی": "#28a745",
                    "غیررسمی": "#dc3545",
                    "نامشخص": "#6c757d"
                }
            )
            st.plotly_chart(fig_status, use_container_width=True)
    
    # فایل‌های اخیر
    st.subheader("📋 فایل‌های اخیر (15 مورد)")
    recent_files = analysis_result["recent_files"]
    display_columns = ['شماره_سند', 'سال', 'ماه', 'وضعیت', 'شیت_منبع', 'شماره_تلفن', 'فایل_اصلی']
    st.dataframe(
        recent_files[display_columns],
        use_container_width=True,
        hide_index=True
    )
    
    # دانلود تمام فایل‌های شرکت
    all_files = analysis_result["all_files"]
    csv_data = all_files.to_csv(index=False, encoding='utf-8-sig')
    st.download_button(
        label=f"📥 دانلود تمام فایل‌های {company_name} (CSV)",
        data=csv_data,
        file_name=f"{company_name}_files_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )

def display_all_years_report(yearly_stats):
    """نمایش گزارش کلی همه سال‌ها"""
    st.subheader("📊 گزارش کلی فعالیت مشتریان پنتا (1393-1404)")
    
    if not yearly_stats:
        st.warning("داده‌ای برای نمایش یافت نشد")
        return
    
    # تبدیل به DataFrame
    years_data = []
    for year, stats in yearly_stats.items():
        years_data.append({
            "سال": year,
            "کل فایل‌ها": stats["total"],
            "رسمی": stats["رسمی"],
            "غیررسمی": stats["غیررسمی"],
            "نامشخص": stats["نامشخص"],
            "شماره تلفن": stats["phones"]
        })
    
    yearly_df = pd.DataFrame(years_data).sort_values("سال")
    
    # نمایش جدول
    st.dataframe(yearly_df, use_container_width=True, hide_index=True)
    
    # نمودارها
    col1, col2 = st.columns(2)
    
    with col1:
        # نمودار کل فایل‌ها
        fig_total = px.bar(
            yearly_df,
            x="سال",
            y="کل فایل‌ها",
            title="تعداد کل فایل‌ها در هر سال",
            color="کل فایل‌ها",
            color_continuous_scale="viridis"
        )
        st.plotly_chart(fig_total, use_container_width=True)
    
    with col2:
        # نمودار تفکیک وضعیت
        fig_status = px.bar(
            yearly_df,
            x="سال",
            y=["رسمی", "غیررسمی", "نامشخص"],
            title="تفکیک وضعیت فایل‌ها",
            color_discrete_map={
                "رسمی": "#28a745",
                "غیررسمی": "#dc3545",
                "نامشخص": "#6c757d"
            }
        )
        st.plotly_chart(fig_status, use_container_width=True)
    
    # نمودار شماره تلفن‌ها
    fig_phones = px.line(
        yearly_df,
        x="سال",
        y="شماره تلفن",
        title="روند استخراج شماره تلفن در طول سال‌ها",
        markers=True
    )
    st.plotly_chart(fig_phones, use_container_width=True)
    
    # دانلود گزارش
    csv_data = yearly_df.to_csv(index=False, encoding='utf-8-sig')
    st.download_button(
        label="📥 دانلود گزارش کلی (CSV)",
        data=csv_data,
        file_name=f"all_years_report_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )

def display_sheet_analysis(sheet_stats):
    """نمایش تحلیل داده‌ها بر اساس شیت"""
    st.subheader("📊 تحلیل داده‌ها بر اساس شیت منبع")
    
    # تبدیل به DataFrame
    sheet_data = []
    for sheet_name, stats in sheet_stats.items():
        sheet_data.append({
            "شیت (سال)": sheet_name,
            "تعداد فایل": stats["total_files"],
            "تعداد شرکت": stats["companies"],
            "فایل با تلفن": stats["files_with_phones"],
            "درصد موفقیت تلفن": f"{stats['phone_success_rate']:.1f}%",
            "رسمی": stats["status_distribution"].get("رسمی", 0),
            "غیررسمی": stats["status_distribution"].get("غیررسمی", 0)
        })
    
    sheet_df = pd.DataFrame(sheet_data)
    st.dataframe(sheet_df, use_container_width=True, hide_index=True)
    
    # نمودار مقایسه شیت‌ها
    col1, col2 = st.columns(2)
    
    with col1:
        fig_files = px.bar(
            sheet_df,
            x="شیت (سال)",
            y="تعداد فایل",
            title="تعداد فایل در هر شیت",
            color="تعداد فایل",
            color_continuous_scale="blues"
        )
        st.plotly_chart(fig_files, use_container_width=True)
    
    with col2:
        fig_companies = px.bar(
            sheet_df,
            x="شیت (سال)",
            y="تعداد شرکت",
            title="تعداد شرکت در هر شیت",
            color="تعداد شرکت",
            color_continuous_scale="greens"
        )
        st.plotly_chart(fig_companies, use_container_width=True)

def main():
    # Header
    st.markdown("""
    <div class="search-header">
        <h1>🔍 سیستم جستجوی کامل مشتریان پنتا</h1>
        <p>جستجو و تحلیل هوشمند اطلاعات فایل‌های اکسل (1393-1404)</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize data processor
    if 'data_processor' not in st.session_state:
        st.session_state.data_processor = DataProcessor()
        st.session_state.data_loaded = False
    
    # Load data automatically
    if not st.session_state.data_loaded:
        with st.spinner("در حال بارگذاری و پردازش داده‌ها..."):
            df = st.session_state.data_processor.load_data()
            if df is not None:
                processed_df = st.session_state.data_processor.process_data()
                if processed_df is not None:
                    st.session_state.data_loaded = True
                    st.success("✅ داده‌ها با موفقیت پردازش شدند!")
                else:
                    st.error("❌ خطا در پردازش داده‌ها")
                    return
            else:
                st.error("❌ خطا در بارگذاری فایل اکسل")
                return
    
    # Sidebar for mode selection
    with st.sidebar:
        st.header("⚙️ تنظیمات")
        
        if st.session_state.data_loaded:
            # نمایش اطلاعات فایل
            stats = st.session_state.data_processor.get_statistics()
            st.markdown(f"""
            <div class="sheet-info">
                <h4>📁 اطلاعات فایل</h4>
                <p>✅ فایل بارگذاری شد</p>
                <p>📊 {stats.get('تعداد_کل_سندها', 0)} رکورد</p>
                <p>📅 {len(stats.get('شیت_های_منبع', []))} شیت</p>
                <p>🏢 {stats.get('تعداد_شرکت_های_منحصر_به_فرد', 0)} شرکت</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.header("🎯 حالت جستجو")
            search_mode = st.radio(
                "نوع جستجو را انتخاب کنید:",
                ["جستجوی شرکت خاص", "گزارش کلی همه سال‌ها", "تحلیل شیت‌ها", "جستجوی عمومی", "شماره تلفن‌ها", "محصولات"]
            )
        else:
            st.error("❌ خطا در بارگذاری داده‌ها")
            st.stop()
    
    # Main content
    if st.session_state.data_loaded:
        # Get statistics
        stats = st.session_state.data_processor.get_statistics()
        
        # Display statistics
        st.subheader("📊 آمار کلی سیستم")
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("تعداد کل اسناد", stats.get('تعداد_کل_سندها', 0))
        with col2:
            st.metric("تعداد شرکت‌ها", stats.get('تعداد_شرکت_های_منحصر_به_فرد', 0))
        with col3:
            st.metric("اسناد با شماره تلفن", stats.get('تعداد_سندهای_با_تلفن', 0))
        with col4:
            success_rate = (stats.get('تعداد_سندهای_با_تلفن', 0) / max(stats.get('تعداد_کل_سندها', 1), 1)) * 100
            st.metric("درصد موفقیت تلفن", f"{success_rate:.1f}%")
        with col5:
            st.metric("تعداد شیت‌ها", len(stats.get('شیت_های_منبع', [])))
        
        # Different modes
        if search_mode == "گزارش کلی همه سال‌ها":
            yearly_report = st.session_state.data_processor.get_all_years_report()
            display_all_years_report(yearly_report)
            
        elif search_mode == "تحلیل شیت‌ها":
            sheet_analysis = st.session_state.data_processor.get_sheet_analysis()
            display_sheet_analysis(sheet_analysis)
            
        elif search_mode == "جستجوی شرکت خاص":
            st.subheader("🔍 جستجوی تفصیلی شرکت")
            
            company_query = st.text_input(
                "نام شرکت را وارد کنید:",
                placeholder="نام شرکت یا بخشی از آن را بنویسید...",
                help="سیستم از جستجوی فازی استفاده می‌کند و نزدیک‌ترین تطبیق را پیدا می‌کند"
            )
            
            if company_query:
                with st.spinner("در حال جستجو و تحلیل..."):
                    analysis_result = st.session_state.data_processor.search_company_detailed(company_query)
                    display_company_analysis(analysis_result)
        
        elif search_mode == "شماره تلفن‌ها":
            st.subheader("📞 شماره تلفن‌های استخراج شده")
            
            all_phones = stats.get('all_phones', [])
            
            # Search functionality
            phone_search = st.text_input("🔍 جستجو در شماره تلفن‌ها:")
            
            filtered_phones = all_phones
            if phone_search:
                filtered_phones = [phone for phone in all_phones if phone_search in phone]
            
            st.metric("📞 تعداد کل شماره تلفن‌ها", len(all_phones))
            
            if filtered_phones:
                # Display in columns
                cols = st.columns(3)
                for i, phone in enumerate(filtered_phones[:60]):  # Show first 60
                    with cols[i % 3]:
                        st.code(phone)
                
                if len(filtered_phones) > 60:
                    st.info(f"تنها 60 مورد اول نمایش داده شد. کل: {len(filtered_phones)} مورد")
            else:
                st.info("شماره تلفنی یافت نشد.")
            
            # Download option
            if all_phones:
                phones_df = pd.DataFrame({'شماره_تلفن': all_phones})
                csv = phones_df.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="💾 دانلود شماره تلفن‌ها (CSV)",
                    data=csv,
                    file_name="phone_numbers.csv",
                    mime="text/csv"
                )
        
        elif search_mode == "محصولات":
            st.subheader("📦 محصولات استخراج شده")
            
            all_products = stats.get('all_products', [])
            
            # Search functionality
            product_search = st.text_input("🔍 جستجو در محصولات:")
            
            filtered_products = all_products
            if product_search:
                filtered_products = [product for product in all_products if product_search.lower() in product.lower()]
            
            st.metric("📦 تعداد کل محصولات", len(all_products))
            
            if filtered_products:
                for product in filtered_products[:50]:  # Show first 50
                    st.write(f"• {product}")
                
                if len(filtered_products) > 50:
                    st.info(f"تنها 50 مورد اول نمایش داده شد. کل: {len(filtered_products)} مورد")
            else:
                st.info("محصولی یافت نشد.")
            
            # Download option
            if all_products:
                products_df = pd.DataFrame({'محصول': all_products})
                csv = products_df.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="💾 دانلود محصولات (CSV)",
                    data=csv,
                    file_name="products.csv",
                    mime="text/csv"
                )
        
        else:  # جستجوی عمومی
            st.subheader("🔍 جستجوی عمومی")
            
            col1, col2 = st.columns([3, 1])
            with col1:
                search_query = st.text_input(
                    "جستجو در نام شرکت، شماره تلفن یا نام فایل:",
                    placeholder="کلمه کلیدی را وارد کنید..."
                )
            with col2:
                search_button = st.button("🔍 جستجو", type="primary")
            
            # Advanced filters
            with st.expander("🔧 فیلترهای پیشرفته"):
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    year_filter = st.selectbox(
                        "انتخاب سال:",
                        ["همه"] + [str(int(y)) for y in stats.get('سال_های_موجود', [])]
                    )
                with col2:
                    month_filter = st.selectbox(
                        "انتخاب ماه:",
                        ["همه"] + stats.get('ماه_های_موجود', [])
                    )
                with col3:
                    sheet_filter = st.selectbox(
                        "انتخاب شیت:",
                        ["همه"] + stats.get('شیت_های_منبع', [])
                    )
                with col4:
                    phone_filter = st.selectbox(
                        "وضعیت شماره تلفن:",
                        ["همه", "دارای شماره تلفن", "بدون شماره تلفن"]
                    )
            
            # Perform search
            if search_query or search_button:
                results = st.session_state.data_processor.search_data(search_query)
                
                # Apply filters
                if year_filter != "همه":
                    results = results[results['سال_عددی'] == int(year_filter)]
                if month_filter != "همه":
                    results = results[results['ماه'] == month_filter]
                if sheet_filter != "همه":
                    results = results[results['شیت_منبع'] == sheet_filter]
                if phone_filter == "دارای شماره تلفن":
                    results = results[results['تعداد_تلفن'] > 0]
                elif phone_filter == "بدون شماره تلفن":
                    results = results[results['تعداد_تلفن'] == 0]
                
                st.subheader(f"📋 نتایج جستجو ({len(results)} مورد)")
                
                if len(results) > 0:
                    # Display results
                    display_columns = ['شماره_سند', 'نام_شرکت', 'سال', 'ماه', 'وضعیت', 'شیت_منبع', 'شماره_تلفن', 'تعداد_تلفن']
                    st.dataframe(
                        results[display_columns],
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    # Download button
                    csv = results.to_csv(index=False, encoding='utf-8-sig')
                    st.download_button(
                        label="📥 دانلود نتایج (CSV)",
                        data=csv,
                        file_name=f"search_results_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                    
                    # Detailed view
                    if len(results) <= 50:  # فقط برای نتایج کم
                        st.subheader("🔍 مشاهده جزئیات")
                        selected_index = st.selectbox(
                            "انتخاب سند برای مشاهده جزئیات:",
                            range(len(results)),
                            format_func=lambda x: f"{results.iloc[x]['شماره_سند']} - {results.iloc[x]['نام_شرکت']}"
                        )
                        
                        if selected_index is not None:
                            selected_row = results.iloc[selected_index]
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write("**شماره سند:**", selected_row['شماره_سند'])
                                st.write("**نام شرکت:**", selected_row['نام_شرکت'])
                                st.write("**سال:**", selected_row['سال'])
                                st.write("**ماه:**", selected_row['ماه'])
                                st.write("**شیت منبع:**", selected_row['شیت_منبع'])
                            with col2:
                                st.write("**وضعیت:**", selected_row['وضعیت'])
                                st.write("**شماره تلفن:**", selected_row['شماره_تلفن'])
                                st.write("**تعداد تلفن:**", selected_row['تعداد_تلفن'])
                                st.write("**نام فایل:**", selected_row['فایل_اصلی'])
                            
                            # Show full content
                            with st.expander("📄 محتوای کامل سند"):
                                st.text_area(
                                    "محتوای کامل:",
                                    value=selected_row['محتوای_کامل'],
                                    height=300,
                                    disabled=True
                                )
                else:
                    st.warning("🔍 هیچ نتیجه‌ای یافت نشد. لطفاً کلمات کلیدی دیگری امتحان کنید.")

if __name__ == "__main__":
    main()
