import pandas as pd
import re
from typing import List, Dict, Any, Tuple
from collections import defaultdict
import streamlit as st

class DataProcessor:
    def __init__(self):
        self.df = None
        self.processed_data = None
        self.excel_file_path = "excel_files_by_year_panta-new.xlsx"
        
        # کلیدواژه‌هایی که باید حذف شوند
        self.keywords_to_remove = [
            "مدیر فروش",
            "هزینه حمل",
            "توضیحات",
            "مدیر کارخانه",
            "کد کالا",
            "شرح کالا",
            "موجودی",
            "تاریخ ارسال",
            "مدیر عامل",
            "احتراما، دستور فرمایید درخواست جاری جهت خریدار ذیل ارسال گردد",
            "توزیع نسخ",
            "واحد فروش",
            "ردیف",
            "|",
            "توزیع نسخ",
            "گزارش زمان بندی ارسال"
        ]
    
    def unify_persian_chars(self, s: str) -> str:
        """یکسان‌سازی حروف عربی/فارسی"""
        if s is None:
            return ""
        s = str(s)
        s = s.replace("\u064A", "ی").replace("\u0643", "ک")
        return s
    
    def remove_keywords(self, text: str) -> str:
        """حذف کلیدواژه‌های مشخص شده از متن"""
        if pd.isna(text) or not isinstance(text, str):
            return ""
        
        cleaned_text = text
        for keyword in self.keywords_to_remove:
            # حذف دقیق کلیدواژه
            cleaned_text = cleaned_text.replace(keyword, "")
        
        # پاک‌سازی فضاهای اضافی
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
        return cleaned_text
    
    def normalize_status(self, s) -> str:
        """نرمال‌سازی وضعیت رسمی/غیررسمی با دقت بیشتر در تشخیص"""
        if pd.isna(s):
            return "نامشخص"
        
        st_text = self.unify_persian_chars(str(s)).strip()
        
        # حذف تمام فضاها، نیم‌فاصله‌ها و کاراکترهای اضافی
        st_nospace = re.sub(r"[\s\-\u200c\u200d_:،,\u00A0\u2000-\u200A\u202F\u205F\u3000]+", "", st_text)
        st_nospace = st_nospace.lower()
        
        # بررسی دقیق‌تر برای "غیر رسمی" و "غیررسمی"
        if re.search(r"غیر.*رسم", st_nospace) or re.search(r"غير.*رسم", st_nospace):
            return "غیررسمی"
        elif re.search(r"رسم", st_nospace) and not re.search(r"غیر|غير", st_nospace):
            return "رسمی"
        elif st_nospace == "" or "نامشخص" in st_nospace:
            return "نامشخص"
        
        return "نامشخص"
    
    def clean_text(self, text: str) -> str:
        """حذف اعداد و کاراکترهای غیرحروف فارسی"""
        if pd.isna(text):
            return ""
        txt = self.unify_persian_chars(str(text))
        return re.sub(r"[^آ-ی\s]", "", txt)
    
    def load_data(self, file_path: str = None) -> pd.DataFrame:
        """Load Excel data from file"""
        try:
            if file_path is None:
                file_path = self.excel_file_path
            
            # Read all sheets from Excel file
            excel_file = pd.ExcelFile(file_path)
            all_sheets_data = []
            
            st.info(f"📊 در حال خواندن {len(excel_file.sheet_names)} شیت از فایل اکسل...")
            
            for sheet_name in excel_file.sheet_names:
                try:
                    sheet_df = pd.read_excel(file_path, sheet_name=sheet_name)
                    sheet_df['sheet_name'] = sheet_name
                    
                    # Try to identify filename column
                    filename_col = None
                    for col in sheet_df.columns:
                        if any(keyword in str(col).lower() for keyword in ['filename', 'file', 'نام', 'فایل']):
                            filename_col = col
                            break
                    
                    if filename_col is None and len(sheet_df.columns) > 0:
                        filename_col = sheet_df.columns[0]
                    
                    if filename_col:
                        sheet_df['filename'] = sheet_df[filename_col]
                    else:
                        sheet_df['filename'] = f"Row_{sheet_df.index}"
                    
                    # Create file_content column by combining all text columns
                    text_columns = [col for col in sheet_df.columns if sheet_df[col].dtype == 'object']
                    sheet_df['file_content'] = sheet_df[text_columns].apply(
                        lambda row: ' '.join([str(val) for val in row if pd.notna(val)]), axis=1
                    )
                    
                    # اعمال حذف کلیدواژه‌ها به محتوای فایل
                    sheet_df['file_content'] = sheet_df['file_content'].apply(self.remove_keywords)
                    
                    all_sheets_data.append(sheet_df)
                    
                except Exception as e:
                    st.warning(f"خطا در خواندن شیت {sheet_name}: {str(e)}")
            
            if all_sheets_data:
                self.df = pd.concat(all_sheets_data, ignore_index=True)
                st.success(f"✅ فایل بارگذاری شد: {len(self.df)} رکورد از {len(excel_file.sheet_names)} شیت")
            else:
                st.error("هیچ شیت قابل خواندنی یافت نشد")
                return None
            
            # اضافه کردن ستون‌های مورد نیاز
            if "official_status" not in self.df.columns:
                self.df["official_status"] = None
            if "month" not in self.df.columns:
                self.df["month"] = None
            if "year" not in self.df.columns:
                self.df["year"] = None
            
            # نرمال‌سازی داده‌ها
            self.df["official_status"] = self.df["official_status"].apply(self.normalize_status)
            self.df["clean_name"] = self.df["filename"].apply(self.clean_text)
            self.df["month"] = self.df["month"].fillna("نامشخص")
            self.df["year_num"] = pd.to_numeric(self.df["year"], errors="coerce").astype("Int64")
            
            # استخراج شماره تلفن
            self.df["extracted_phones"] = self.df["file_content"].apply(self.extract_phone_numbers)
            self.df["phone_count"] = self.df["extracted_phones"].apply(len)
            self.df["phone_numbers_str"] = self.df["extracted_phones"].apply(lambda x: ', '.join(x) if x else 'یافت نشد')
            
            # نمایش آمار شیت‌ها
            sheet_stats = self.df['sheet_name'].value_counts().sort_index()
            st.info(f"📊 تفکیک داده‌ها بر اساس شیت:\n" + 
                   "\n".join([f"   - {sheet}: {count} رکورد" for sheet, count in sheet_stats.items()]))
            
            return self.df
        except Exception as e:
            st.error(f"خطا در بارگذاری داده‌ها: {str(e)}")
            return None
    
    def extract_phone_numbers(self, text: str) -> List[str]:
        """Extract phone numbers from text using regex patterns"""
        if pd.isna(text) or not isinstance(text, str):
            return []
        
        # Persian/Iranian phone number patterns
        patterns = [
            r'09\d{9}',  # Mobile numbers starting with 09
            r'\+989\d{9}',  # International format
            r'0\d{2,3}-?\d{7,8}',  # Landline numbers
            r'\b\d{11}\b',  # 11-digit numbers
            r'\b\d{4}-?\d{7}\b',  # Numbers with dash
        ]
        
        phone_numbers = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            phone_numbers.extend(matches)
        
        # Remove duplicates and return
        return list(set(phone_numbers))
    
    def extract_company_names(self, filename: str, content: str) -> List[str]:
        """Extract company names from filename and content"""
        companies = []
        
        # Extract from filename
        if filename:
            name_parts = str(filename).replace('.xlsm', '').replace('.xlsx', '')
            parts = [part.strip() for part in name_parts.split('-') if len(part.strip()) > 2]
            companies.extend(parts)
        
        # Extract from content
        if isinstance(content, str):
            buyer_pattern = r'خریدار\s*:?\s*([^,;\n]+)'
            buyer_matches = re.findall(buyer_pattern, content)
            companies.extend([match.strip() for match in buyer_matches if match.strip()])
        
        return list(set(companies))
    
    def extract_products(self, text: str) -> List[str]:
        """Extract product information from text"""
        if pd.isna(text) or not isinstance(text, str):
            return []
        
        # Product keywords in Persian
        product_keywords = [
            'محصول', 'کالا', 'جنس', 'اقلام', 'مواد', 'تجهیزات',
            'دستگاه', 'ماشین', 'قطعه', 'لوازم', 'ابزار', 'سیستم',
            'نرم افزار', 'برنامه', 'اپلیکیشن', 'پلتفرم', 'خدمات'
        ]
        
        products = []
        words = text.split()
        
        for i, word in enumerate(words):
            if any(keyword in word for keyword in product_keywords):
                context_start = max(0, i-2)
                context_end = min(len(words), i+3)
                context = ' '.join(words[context_start:context_end])
                products.append(context.strip())
        
        return list(set(products))
    
    def fuzzy_search_companies(self, query: str, threshold: int = 60) -> List[Tuple[str, int]]:
        """جستجوی فازی شرکت‌ها"""
        if not query or self.df is None:
            return []
        
        query_clean = self.clean_text(query).lower()
        companies = self.df["clean_name"].dropna().unique().tolist()
        
        matches = []
        for company in companies:
            company_clean = company.lower()
            
            if query_clean in company_clean:
                score = 100
            elif any(word in company_clean for word in query_clean.split()):
                score = 80
            else:
                common_chars = set(query_clean) & set(company_clean)
                score = int((len(common_chars) / max(len(query_clean), len(company_clean))) * 100)
            
            if score >= threshold:
                matches.append((company, score))
        
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches[:15]
    
    def process_data(self) -> pd.DataFrame:
        """Process the raw data and extract structured information"""
        if self.df is None:
            return None
        
        processed_rows = []
        
        for _, row in self.df.iterrows():
            # اعمال حذف کلیدواژه‌ها به محتوای فایل قبل از پردازش
            cleaned_content = self.remove_keywords(str(row.get('file_content', '')))
            
            phones = self.extract_phone_numbers(cleaned_content)
            companies = self.extract_company_names(
                str(row.get('filename', '')), 
                cleaned_content
            )
            products = self.extract_products(cleaned_content)
            
            processed_row = {
                'شماره_سند': str(row.get('filename', '')).split('-')[0] if '-' in str(row.get('filename', '')) else '',
                'نام_شرکت': ', '.join(companies) if companies else 'نامشخص',
                'نام_پاک': row.get('clean_name', ''),
                'سال': row.get('year', ''),
                'سال_عددی': row.get('year_num', ''),
                'ماه': row.get('month', ''),
                'وضعیت': row.get('official_status', 'نامشخص'),
                'شیت_منبع': row.get('sheet_name', ''),
                'شماره_تلفن': ', '.join(phones) if phones else 'یافت نشد',
                'تعداد_تلفن': len(phones),
                'محصولات': ', '.join(products) if products else 'یافت نشد',
                'تعداد_محصولات': len(products),
                'فایل_اصلی': row.get('filename', ''),
                'محتوای_کامل': cleaned_content  # محتوای پاک شده را ذخیره می‌کنیم
            }
            
            processed_rows.append(processed_row)
        
        self.processed_data = pd.DataFrame(processed_rows)
        return self.processed_data
    
    def search_company_detailed(self, company_name: str) -> Dict[str, Any]:
        """جستجوی تفصیلی یک شرکت"""
        if self.processed_data is None:
            return {}
        
        matches = self.fuzzy_search_companies(company_name)
        if not matches:
            return {"error": f"هیچ نتیجه‌ای برای '{company_name}' یافت نشد"}
        
        best_match = matches[0][0]
        best_score = matches[0][1]
        
        results = self.processed_data[
            self.processed_data["نام_پاک"].str.contains(re.escape(best_match), na=False)
        ]
        
        if results.empty:
            return {"error": f"هیچ فایلی برای '{best_match}' یافت نشد"}
        
        total_files = len(results)
        years_active = sorted(results["سال_عددی"].dropna().unique().astype(int).tolist())
        status_counts = results["وضعیت"].value_counts()
        sheet_distribution = results["شیت_منبع"].value_counts()
        
        yearly_stats = defaultdict(lambda: {"total": 0, "رسمی": 0, "غیررسمی": 0, "نامشخص": 0, "months": set(), "phones": 0})
        for _, row in results.iterrows():
            yr = row["سال_عددی"]
            if pd.isna(yr):
                continue
            yr = int(yr)
            st_status = row["وضعیت"]
            monthly = row["ماه"]
            yearly_stats[yr]["total"] += 1
            yearly_stats[yr][st_status] += 1
            yearly_stats[yr]["months"].add(str(monthly))
            yearly_stats[yr]["phones"] += row["تعداد_تلفن"]
        
        trend_analysis = "ثابت"
        if len(years_active) > 1:
            first = yearly_stats[years_active[0]]["total"]
            last = yearly_stats[years_active[-1]]["total"]
            if last > first:
                trend_analysis = "صعودی 📈"
            elif last < first:
                trend_analysis = "نزولی 📉"
            else:
                trend_analysis = "ثابت ➡️"
        
        return {
            "company_name": best_match,
            "match_score": best_score,
            "total_files": total_files,
            "years_active": years_active,
            "status_counts": status_counts.to_dict(),
            "sheet_distribution": sheet_distribution.to_dict(),
            "yearly_stats": dict(yearly_stats),
            "trend_analysis": trend_analysis,
            "recent_files": results.sort_values(["سال_عددی", "ماه"], ascending=[False, False]).head(15),
            "all_files": results
        }
    
    def get_all_years_report(self) -> Dict[str, Any]:
        """گزارش کلی همه سال‌ها"""
        if self.processed_data is None:
            return {}
        
        yearly_stats = defaultdict(lambda: {"total": 0, "رسمی": 0, "غیررسمی": 0, "نامشخص": 0, "phones": 0})
        
        for _, row in self.processed_data.iterrows():
            year = row["سال_عددی"]
            if pd.isna(year):
                continue
            year = int(year)
            status = row["وضعیت"]
            yearly_stats[year]["total"] += 1
            yearly_stats[year][status] += 1
            yearly_stats[year]["phones"] += row["تعداد_تلفن"]
        
        return dict(yearly_stats)
    
    def get_sheet_analysis(self) -> Dict[str, Any]:
        """تحلیل داده‌ها بر اساس شیت منبع"""
        if self.processed_data is None:
            return {}
        
        sheet_stats = {}
        for sheet_name in self.processed_data["شیت_منبع"].unique():
            sheet_data = self.processed_data[self.processed_data["شیت_منبع"] == sheet_name]
            
            sheet_stats[sheet_name] = {
                "total_files": len(sheet_data),
                "companies": len(sheet_data["نام_شرکت"].unique()),
                "files_with_phones": len(sheet_data[sheet_data["تعداد_تلفن"] > 0]),
                "phone_success_rate": len(sheet_data[sheet_data["تعداد_تلفن"] > 0]) / len(sheet_data) * 100,
                "status_distribution": sheet_data["وضعیت"].value_counts().to_dict()
            }
        
        return sheet_stats
    
    def search_data(self, query: str, search_fields: List[str] = None) -> pd.DataFrame:
        """Search data based on query and specified fields"""
        if self.processed_data is None:
            return pd.DataFrame()
        
        if not query:
            return self.processed_data
        
        if search_fields is None:
            search_fields = ['نام_شرکت', 'شماره_تلفن', 'محصولات', 'فایل_اصلی', 'نام_پاک']
        
        # Create boolean mask for search
        mask = pd.Series([False] * len(self.processed_data))
        
        for field in search_fields:
            if field in self.processed_data.columns:
                field_mask = self.processed_data[field].astype(str).str.contains(
                    query, case=False, na=False, regex=False
                )
                mask = mask | field_mask
        
        return self.processed_data[mask]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get basic statistics about the data"""
        if self.processed_data is None:
            return {}
        
        all_phones = []
        all_products = []
        
        for _, row in self.processed_data.iterrows():
            if row['شماره_تلفن'] != 'یافت نشد':
                phones = [p.strip() for p in str(row['شماره_تلفن']).split(',')]
                all_phones.extend(phones)
            
            if row['محصولات'] != 'یافت نشد':
                products = [p.strip() for p in str(row['محصولات']).split(',')]
                all_products.extend(products)
        
        stats = {
            'تعداد_کل_سندها': len(self.processed_data),
            'تعداد_شرکت_های_منحصر_به_فرد': len(self.processed_data['نام_شرکت'].unique()),
            'تعداد_سندهای_با_تلفن': len(self.processed_data[self.processed_data['تعداد_تلفن'] > 0]),
            'تعداد_کل_تلفن_ها': len(set(all_phones)),
            'تعداد_کل_محصولات': len(set(all_products)),
            'سال_های_موجود': sorted([int(x) for x in self.processed_data['سال_عددی'].dropna().unique() if not pd.isna(x)]),
            'ماه_های_موجود': sorted(self.processed_data['ماه'].unique().tolist()),
            'شیت_های_منبع': sorted(self.processed_data['شیت_منبع'].unique().tolist()),
            'all_phones': list(set(all_phones)),
            'all_products': list(set(all_products))
        }
        
        return stats
