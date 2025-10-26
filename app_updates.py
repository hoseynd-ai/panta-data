# ==================== فقط بخش‌های نیاز به تغییر ====================

# در تمام جاهایی که از "سال_از_فایل" استفاده شده، به "سال_نهایی" تغییر دهید:

# مثال 1: در بخش جستجوی شرکت
years = sorted(df["سال_نهایی"].dropna().unique(), reverse=True)  # ⭐ تغییر

# مثال 2: در بخش جستجوی محتوا
years = sorted(df["سال_نهایی"].dropna().unique(), reverse=True)  # ⭐ تغییر

# مثال 3: در مدیریت مشتریان - تاریخچه
company_data = df[df["نام_شرکت"] == company]
latest_year = company_data["سال_نهایی"].max()  # ⭐ تغییر

# مثال 4: در نمایش داده‌ها
st.dataframe(
    unique_phones[["شماره_تلفن", "نام_شرکت", "سال_نهایی", "sheet_name", "filename"]],  # ⭐ تغییر
    use_container_width=True,
    height=500
)

# مثال 5: در بخش محصولات
st.dataframe(
    prods_df[["نام_شرکت", "محصولات", "سال_نهایی", "sheet_name", "filename"]],  # ⭐ تغییر
    use_container_width=True,
    height=500
)