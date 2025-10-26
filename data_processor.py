"""
سیستم پردازش و تحلیل داده‌های اکسل
نویسنده: hoseynd-ai
تاریخ: 2025-01-23 (نسخه نهایی - بدون خطا)
"""

import pandas as pd
import re
from typing import List, Tuple, Any, Dict, Optional
from rapidfuzz import fuzz, process
import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import json
from pathlib import Path


# ==================== Enums ====================
class SearchMode(Enum):
    """حالت‌های جستجو"""
    EXACT = "exact"
    FUZZY = "fuzzy"
    PARTIAL = "partial"
    AUTO = "auto"


# ==================== Data Classes ====================
@dataclass
class SearchResult:
    """نتیجه جستجو"""
    customer_name: str
    match_score: float
    total_purchases: int
    formal_purchases: int
    informal_purchases: int
    years_active: List[int]
    months_active: List[int]
    mobile_numbers: List[str]
    phone_numbers: List[str]
    addresses: List[str]
    products: List[str]
    total_products: int
    
    def to_dict(self):
        return asdict(self)


class DataProcessor:
    """کلاس اصلی پردازش داده"""
    
    def __init__(self, excel_file: str = "temp_excel_files_by_year_panta-new.xlsx"):
        self.excel_file = excel_file
        self.df = None
        self.processed_data = None
        
        # مسیرهای ذخیره‌سازی
        self.data_dir = Path("crm_data")
        self.data_dir.mkdir(exist_ok=True)
        
        # کش برای جستجوی سریع‌تر
        self.customer_index = {}
    
    # ==================== بارگذاری ====================
    
    def load_data(self, file_path: str = None) -> pd.DataFrame:
        """بارگذاری فایل اکسل"""
        try:
            file_path = file_path or self.excel_file
            
            xls = pd.ExcelFile(file_path)
            frames = []
            
            for sheet_name in xls.sheet_names:
                df_sheet = pd.read_excel(file_path, sheet_name=sheet_name)
                df_sheet['sheet_name'] = sheet_name
                frames.append(df_sheet)
            
            self.df = pd.concat(frames, ignore_index=True)
            self.df.columns = self.df.columns.str.strip()
            
            return self.df
            
        except Exception as e:
            raise Exception(f"خطا در بارگذاری فایل: {e}")
    
    # ==================== پردازش ====================
    
    def process_data(self, df: pd.DataFrame = None) -> pd.DataFrame:
        """پردازش و پاکسازی داده"""
        if df is not None:
            self.df = df
        
        if self.df is None:
            raise Exception("ابتدا فایل را بارگذاری کنید.")
        
        out = self.df.copy()
        
        # پاکسازی نام مشتری
        out['customer_name'] = out['customer name'].astype(str).str.strip()
        out['customer_name_normalized'] = out['customer_name'].apply(self._normalize_text)
        
        # پاکسازی سال و ماه
        out['year'] = pd.to_numeric(out['year'], errors='coerce')
        out['month'] = pd.to_numeric(out['month'], errors='coerce')
        
        # پاکسازی وضعیت سفارش
        out['state_original'] = out['state'].astype(str).str.strip()
        out['state_normalized'] = out['state_original'].apply(self._normalize_state)
        
        # پاکسازی آدرس
        out['address'] = out['address'].astype(str).str.strip()
        
        # پاکسازی تلفن‌ها
        out['mobile'] = out['شماره موبایل'].astype(str).apply(self._clean_phone)
        out['phone'] = out['شماره ثابت'].astype(str).apply(self._clean_phone)
        
        # پاکسازی محصولات (با کاما جدا شده)
        out['products_list'] = out['نام محصول'].apply(self._parse_products)
        out['products_list_normalized'] = out['products_list'].apply(
            lambda x: [self._normalize_product_name(p) for p in x]
        )
        out['product_count'] = out['products_list'].apply(len)
        
        # حذف ردیف‌های خالی
        out = out.dropna(subset=['customer_name'])
        out = out[out['customer_name'] != 'nan']
        out = out[out['customer_name'] != '']
        
        self.processed_data = out
        self._build_customer_index()
        
        return out
    
    # ==================== توابع کمکی ====================
    
    @staticmethod
    def _normalize_text(text: str) -> str:
        """نرمال‌سازی متن فارسی"""
        if not isinstance(text, str) or text == 'nan':
            return ""
        
        text = text.replace("ي", "ی").replace("ك", "ک")
        text = text.replace("\u200c", " ")
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip().lower()
    
    @staticmethod
    def _normalize_state(state: str) -> str:
        """نرمال‌سازی وضعیت سفارش"""
        if not isinstance(state, str) or state == 'nan' or state.strip() == '':
            return "نامشخص"
        
        s = state.strip()
        s = s.replace("ي", "ی").replace("ك", "ک")
        s_no_space = s.replace(" ", "").replace("\u200c", "").replace("\t", "").replace("\n", "").replace("\r", "")
        s_lower = s_no_space.lower()
        
        formal_keywords = ['رسمی', 'رسمي', 'formal', 'official', 'فاکتور', 'invoice']
        informal_keywords = ['غیررسمی', 'غیررسمي', 'غیرّسمی', 'غیرسمی', 'informal', 'unofficial', 'پیشفاکتور', 'پیش‌فاکتور', 'proforma']
        
        formal_normalized = [k.replace(" ", "").replace("\u200c", "").lower() for k in formal_keywords]
        informal_normalized = [k.replace(" ", "").replace("\u200c", "").lower() for k in informal_keywords]
        
        for keyword in informal_normalized:
            if keyword in s_lower:
                return "غیررسمی"
        
        for keyword in formal_normalized:
            if keyword in s_lower:
                return "رسمی"
        
        return s if s else "نامشخص"
    
    @staticmethod
    def _normalize_product_name(product: str) -> str:
        """
        نرمال‌سازی نام محصولات
        
        تبدیل تمام حالت‌های مختلف یک محصول به یک نام استاندارد
        
        مثال:
            "Panflow 110" → "panflow110"
            "P.N-Coat" → "pncoat"
            "PNR 2" → "pnr2"
        """
        if not isinstance(product, str) or product == 'nan' or product.strip() == '':
            return ""
        
        # تبدیل به حروف کوچک
        normalized = product.lower()
        
        # تبدیل حروف عربی به فارسی
        normalized = normalized.replace("ي", "ی").replace("ك", "ک")
        
        # حذف تمام کاراکترهای غیرحرف و غیرعدد (فقط حروف و اعداد باقی بماند)
        normalized = re.sub(r'[^a-zA-Z0-9آ-ی]', '', normalized)
        
        # حذف فاصله‌های اضافی
        normalized = normalized.strip()
        
        return normalized
    
    @staticmethod
    def _clean_phone(phone: str) -> str:
        """پاکسازی شماره تلفن"""
        if not isinstance(phone, str) or phone == 'nan':
            return ""
        
        phone = re.sub(r'[^\d]', '', phone)
        
        if phone.startswith('98') and len(phone) >= 10:
            phone = '0' + phone[2:]
        
        return phone
    
    def _parse_products(self, products_str: str) -> List[str]:
        """تجزیه محصولات با کاما"""
        if not isinstance(products_str, str) or products_str == 'nan':
            return []
        
        products = re.split(r'[,،]', products_str)
        products = [p.strip() for p in products if p.strip()]
        
        return products
    
    # ==================== ایندکس ====================
    
    def _build_customer_index(self):
        """ساخت ایندکس برای جستجوی سریع"""
        if self.processed_data is None:
            return
        
        self.customer_index = {}
        
        for customer_name in self.processed_data['customer_name'].unique():
            customer_data = self.processed_data[
                self.processed_data['customer_name'] == customer_name
            ]
            
            years = sorted(customer_data['year'].dropna().unique().tolist())
            months = sorted(customer_data['month'].dropna().unique().tolist())
            
            formal_count = len(customer_data[customer_data['state_normalized'] == 'رسمی'])
            informal_count = len(customer_data[customer_data['state_normalized'] == 'غیررسمی'])
            
            mobiles = customer_data['mobile'].unique().tolist()
            phones = customer_data['phone'].unique().tolist()
            addresses = customer_data['address'].unique().tolist()
            
            all_products = []
            for products_list in customer_data['products_list']:
                all_products.extend(products_list)
            all_products = list(set(all_products))
            
            normalized_name = self._normalize_text(customer_name)
            keywords = normalized_name.split()
            
            self.customer_index[customer_name] = {
                'normalized_name': normalized_name,
                'keywords': keywords,
                'total_purchases': len(customer_data),
                'formal_purchases': formal_count,
                'informal_purchases': informal_count,
                'years_active': years,
                'months_active': months,
                'mobile_numbers': [m for m in mobiles if m],
                'phone_numbers': [p for p in phones if p],
                'addresses': [a for a in addresses if a and a != 'nan'],
                'products': all_products,
                'total_products': len(all_products)
            }
    
    # ==================== جستجو ====================
    
    def search_customer(
        self,
        query: str,
        mode: SearchMode = SearchMode.AUTO,
        min_score: int = 60
    ) -> List[SearchResult]:
        """جستجوی هوشمند مشتری"""
        if not query.strip():
            return []
        
        query_normalized = self._normalize_text(query)
        query_keywords = query_normalized.split()
        
        results = []
        
        for customer_name, info in self.customer_index.items():
            score = 0
            
            if mode == SearchMode.EXACT:
                if info['normalized_name'] == query_normalized:
                    score = 100
            
            elif mode == SearchMode.PARTIAL:
                matches = 0
                for q_word in query_keywords:
                    if any(q_word in keyword for keyword in info['keywords']):
                        matches += 1
                
                if matches > 0:
                    score = (matches / len(query_keywords)) * 100
            
            elif mode == SearchMode.FUZZY:
                score = fuzz.token_set_ratio(query_normalized, info['normalized_name'])
            
            else:  # AUTO
                if info['normalized_name'] == query_normalized:
                    score = 100
                elif query_normalized in info['normalized_name']:
                    score = 95
                else:
                    matches = 0
                    for q_word in query_keywords:
                        for keyword in info['keywords']:
                            if q_word in keyword:
                                matches += 1
                                break
                            elif fuzz.ratio(q_word, keyword) > 85:
                                matches += 0.8
                                break
                    
                    if matches > 0:
                        score = (matches / len(query_keywords)) * 90
                    else:
                        score = fuzz.token_set_ratio(query_normalized, info['normalized_name']) * 0.8
            
            if score >= min_score:
                results.append(SearchResult(
                    customer_name=customer_name,
                    match_score=round(score, 2),
                    total_purchases=info['total_purchases'],
                    formal_purchases=info['formal_purchases'],
                    informal_purchases=info['informal_purchases'],
                    years_active=info['years_active'],
                    months_active=info['months_active'],
                    mobile_numbers=info['mobile_numbers'],
                    phone_numbers=info['phone_numbers'],
                    addresses=info['addresses'],
                    products=info['products'],
                    total_products=info['total_products']
                ))
        
        results.sort(key=lambda x: x.match_score, reverse=True)
        
        return results
    
    # ==================== تحلیل ====================
    
    def get_yearly_stats(self) -> pd.DataFrame:
        """آمار سالانه"""
        if self.processed_data is None:
            return pd.DataFrame()
        
        stats = self.processed_data.groupby('year').agg({
            'customer_name': 'nunique',
            'mobile': 'count',
            'product_count': 'sum'
        }).reset_index()
        
        stats.columns = ['سال', 'تعداد_مشتری', 'تعداد_سفارش', 'تعداد_محصول']
        
        formal = self.processed_data[
            self.processed_data['state_normalized'] == 'رسمی'
        ].groupby('year').size().reset_index(name='سفارش_رسمی')
        
        informal = self.processed_data[
            self.processed_data['state_normalized'] == 'غیررسمی'
        ].groupby('year').size().reset_index(name='سفارش_غیررسمی')
        
        stats = stats.merge(formal, left_on='سال', right_on='year', how='left')
        stats = stats.merge(informal, left_on='سال', right_on='year', how='left')
        stats = stats.drop(columns=['year_x', 'year_y'], errors='ignore')
        
        stats['سفارش_رسمی'] = stats['سفارش_رسمی'].fillna(0).astype(int)
        stats['سفارش_غیررسمی'] = stats['سفارش_غیررسمی'].fillna(0).astype(int)
        
        return stats.sort_values('سال')
    
    def get_monthly_stats(self, year: int = None) -> pd.DataFrame:
        """آمار ماهانه"""
        if self.processed_data is None:
            return pd.DataFrame()
        
        df = self.processed_data.copy()
        
        if year:
            df = df[df['year'] == year]
        
        stats = df.groupby(['year', 'month']).agg({
            'customer_name': 'nunique',
            'mobile': 'count'
        }).reset_index()
        
        stats.columns = ['سال', 'ماه', 'تعداد_مشتری', 'تعداد_سفارش']
        
        formal = df[df['state_normalized'] == 'رسمی'].groupby(['year', 'month']).size()
        informal = df[df['state_normalized'] == 'غیررسمی'].groupby(['year', 'month']).size()
        
        stats['سفارش_رسمی'] = stats.apply(
            lambda row: formal.get((row['سال'], row['ماه']), 0), axis=1
        )
        stats['سفارش_غیررسمی'] = stats.apply(
            lambda row: informal.get((row['سال'], row['ماه']), 0), axis=1
        )
        
        return stats.sort_values(['سال', 'ماه'])
    
    def get_yearly_monthly_grouped(self) -> Dict[int, pd.DataFrame]:
        """دسته‌بندی ماه‌ها بر اساس سال"""
        if self.processed_data is None:
            return {}
        
        years = sorted(self.processed_data['year'].dropna().unique())
        result = {}
        
        for year in years:
            year_int = int(year)
            monthly_data = self.get_monthly_stats(year_int)
            result[year_int] = monthly_data
        
        return result
    
    def get_product_stats(self) -> pd.DataFrame:
        """آمار محصولات (با نرمال‌سازی)"""
        if self.processed_data is None:
            return pd.DataFrame()
        
        # دیکشنری برای نگهداری محصولات نرمال شده و نام اصلی‌شان
        product_mapping = {}
        
        for idx, row in self.processed_data.iterrows():
            original_products = row['products_list']
            normalized_products = row['products_list_normalized']
            
            for orig, norm in zip(original_products, normalized_products):
                if norm and norm not in product_mapping:
                    product_mapping[norm] = orig
        
        # شمارش محصولات نرمال شده
        all_normalized_products = []
        for products_list in self.processed_data['products_list_normalized']:
            all_normalized_products.extend(products_list)
        
        all_normalized_products = [p for p in all_normalized_products if p]
        
        if not all_normalized_products:
            return pd.DataFrame(columns=['محصول', 'تعداد_فروش'])
        
        product_counts = pd.Series(all_normalized_products).value_counts().reset_index()
        product_counts.columns = ['محصول_نرمال', 'تعداد_فروش']
        
        product_counts['محصول'] = product_counts['محصول_نرمال'].map(product_mapping)
        
        product_counts = product_counts[['محصول', 'تعداد_فروش']].sort_values('تعداد_فروش', ascending=False)
        
        return product_counts
    
    def get_order_state_stats(self) -> pd.DataFrame:
        """آمار وضعیت سفارشات"""
        if self.processed_data is None:
            return pd.DataFrame()
        
        stats = self.processed_data.groupby('state_normalized').agg({
            'customer_name': 'nunique',
            'mobile': 'count',
            'product_count': 'sum'
        }).reset_index()
        
        stats.columns = ['وضعیت', 'تعداد_مشتری', 'تعداد_سفارش', 'تعداد_محصول']
        
        return stats
    
    def get_customer_details(self, customer_name: str) -> pd.DataFrame:
        """جزئیات کامل یک مشتری"""
        if self.processed_data is None:
            return pd.DataFrame()
        
        return self.processed_data[
            self.processed_data['customer_name'] == customer_name
        ].copy()
    
    # ==================== مشتریان از دست رفته ====================
    
    def find_lost_customers(
        self,
        active_period_start: int = 1393,
        active_period_end: int = 1402,
        silent_period_start: int = 1403,
        silent_period_end: int = 1404,
        min_keyword_match: int = 2,
        similarity_threshold: float = 85.0,
        min_purchase_count: int = 1
    ) -> pd.DataFrame:
        """شناسایی مشتریان از دست رفته"""
        if self.processed_data is None:
            raise Exception("ابتدا داده‌ها را پردازش کنید.")
        
        active_customers = self.processed_data[
            (self.processed_data['year'] >= active_period_start) &
            (self.processed_data['year'] <= active_period_end)
        ].copy()
        
        recent_customers = self.processed_data[
            (self.processed_data['year'] >= silent_period_start) &
            (self.processed_data['year'] <= silent_period_end)
        ].copy()
        
        # جمع‌آوری اطلاعات مشتریان دوره فعالیت
        active_groups = []
        
        for customer_name, group in active_customers.groupby('customer_name'):
            last_year = group['year'].max()
            last_month_series = group['month'].dropna()
            last_month = int(last_month_series.iloc[-1]) if len(last_month_series) > 0 else 0
            
            mobiles = ', '.join(set(filter(None, group['mobile'].unique())))
            phones = ', '.join(set(filter(None, group['phone'].unique())))
            address = group['address'].iloc[-1] if len(group) > 0 else ''
            
            all_products = []
            for products_list in group['products_list']:
                all_products.extend(products_list)
            all_products = list(set(all_products))
            
            formal_count = len(group[group['state_normalized'] == 'رسمی'])
            informal_count = len(group[group['state_normalized'] == 'غیررسمی'])
            order_stats = f"رسمی: {formal_count}, غیررسمی: {informal_count}"
            
            active_groups.append({
                'customer_name': customer_name,
                'last_year': int(last_year) if pd.notna(last_year) else 0,
                'last_month': last_month,
                'total_purchases': len(group),
                'mobiles': mobiles,
                'phones': phones,
                'address': address,
                'products': all_products,
                'order_stats': order_stats
            })
        
        active_unique = pd.DataFrame(active_groups)
        
        if len(active_unique) == 0:
            return pd.DataFrame(columns=[
                'نام_مشتری', 'آخرین_سال', 'آخرین_ماه', 'تعداد_خرید',
                'موبایل', 'تلفن', 'آدرس', 'محصولات', 'آمار_سفارشات', 'اولویت'
            ])
        
        active_unique = active_unique[active_unique['total_purchases'] >= min_purchase_count]
        
        recent_names = recent_customers['customer_name'].unique()
        
        lost_customers = []
        
        for _, row in active_unique.iterrows():
            old_name = row['customer_name']
            old_keywords = self._extract_keywords(old_name)
            
            is_found = False
            
            for new_name in recent_names:
                new_keywords = self._extract_keywords(new_name)
                
                match_score = self._calculate_keyword_match(
                    old_keywords, 
                    new_keywords, 
                    similarity_threshold
                )
                
                if match_score >= min_keyword_match:
                    is_found = True
                    break
            
            if not is_found:
                lost_customers.append(row)
        
        if not lost_customers:
            return pd.DataFrame(columns=[
                'نام_مشتری', 'آخرین_سال', 'آخرین_ماه', 'تعداد_خرید',
                'موبایل', 'تلفن', 'آدرس', 'محصولات', 'آمار_سفارشات', 'اولویت'
            ])
        
        result_df = pd.DataFrame(lost_customers)
        result_df = result_df[[
            'customer_name', 'last_year', 'last_month', 'total_purchases',
            'mobiles', 'phones', 'address', 'products', 'order_stats'
        ]]
        
        result_df.columns = [
            'نام_مشتری', 'آخرین_سال', 'آخرین_ماه', 'تعداد_خرید',
            'موبایل', 'تلفن', 'آدرس', 'محصولات', 'آمار_سفارشات'
        ]
        
        result_df = result_df.sort_values('تعداد_خرید', ascending=False).reset_index(drop=True)
        
        result_df['اولویت'] = result_df.apply(self._calculate_priority, axis=1)
        
        result_df['محصولات'] = result_df['محصولات'].apply(
            lambda x: ', '.join(x[:5]) + ('...' if len(x) > 5 else '') if isinstance(x, list) else str(x)
        )
        
        return result_df
    
    def _extract_keywords(self, name: str) -> List[str]:
        """استخراج کلمات کلیدی از نام (با حذف کلمات پرتکرار)"""
        stopwords = {
            'شرکت', 'موسسه', 'گروه', 'سازمان', 'مجموعه',
            'مهندسی', 'پیمانکاری', 'ساختمانی', 'عمرانی',
            'تجاری', 'صنعتی', 'خدماتی', 'فنی', 'تولیدی',
            'بازرگانی', 'پروژه', 'سهامی', 'خاص', 'عام',
            'محدود', 'و', 'در', 'به', 'از', 'با'
        }
        
        normalized = self._normalize_text(name)
        words = normalized.split()
        keywords = [word for word in words if word not in stopwords and len(word) > 2]
        
        return keywords
    
    def _calculate_keyword_match(
        self, 
        keywords1: List[str], 
        keywords2: List[str],
        threshold: float = 85.0
    ) -> float:
        """محاسبه تعداد کلمات مشترک یا شبیه"""
        match_count = 0.0
        used_keywords2 = set()
        
        for kw1 in keywords1:
            best_match = 0.0
            best_kw2 = None
            
            for kw2 in keywords2:
                if kw2 in used_keywords2:
                    continue
                
                if kw1 == kw2:
                    best_match = 1.0
                    best_kw2 = kw2
                    break
                
                similarity = fuzz.ratio(kw1, kw2)
                if similarity >= threshold and similarity > best_match * 100:
                    best_match = similarity / 100.0
                    best_kw2 = kw2
            
            if best_kw2:
                match_count += best_match
                used_keywords2.add(best_kw2)
        
        return match_count
    
    def _calculate_priority(self, row) -> str:
        """محاسبه اولویت مشتری"""
        purchases = row['تعداد_خرید']
        last_year = row['آخرین_سال']
        
        if purchases >= 10 and last_year >= 1402:
            return '🔴 بالا'
        elif purchases >= 5 and last_year >= 1401:
            return '🟡 متوسط'
        else:
            return '🟢 پایین'
    
    def export_lost_customers_to_excel(
        self, 
        lost_df: pd.DataFrame, 
        filename: str = None
    ) -> str:
        """خروجی اکسل مشتریان از دست رفته"""
        if filename is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"lost_customers_{timestamp}.xlsx"
        
        output_dir = Path("exports")
        output_dir.mkdir(exist_ok=True)
        
        filepath = output_dir / filename
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            lost_df.to_excel(writer, sheet_name='مشتریان از دست رفته', index=False)
            
            stats_data = {
                'شاخص': [
                    'تعداد کل مشتریان از دست رفته',
                    'مشتریان با اولویت بالا',
                    'مشتریان با اولویت متوسط',
                    'مشتریان با اولویت پایین',
                    'میانگین تعداد خرید',
                    'مجموع خریدهای از دست رفته'
                ],
                'مقدار': [
                    len(lost_df),
                    len(lost_df[lost_df['اولویت'] == '🔴 بالا']),
                    len(lost_df[lost_df['اولویت'] == '🟡 متوسط']),
                    len(lost_df[lost_df['اولویت'] == '🟢 پایین']),
                    round(lost_df['تعداد_خرید'].mean(), 2) if len(lost_df) > 0 else 0,
                    lost_df['تعداد_خرید'].sum()
                ]
            }
            
            stats_df = pd.DataFrame(stats_data)
            stats_df.to_excel(writer, sheet_name='آمار', index=False)
            
            workbook = writer.book
            worksheet = writer.sheets['مشتریان از دست رفته']
            
            worksheet.column_dimensions['A'].width = 35
            worksheet.column_dimensions['B'].width = 12
            worksheet.column_dimensions['C'].width = 12
            worksheet.column_dimensions['D'].width = 15
            worksheet.column_dimensions['E'].width = 25
            worksheet.column_dimensions['F'].width = 25
            worksheet.column_dimensions['G'].width = 50
            worksheet.column_dimensions['H'].width = 50
            worksheet.column_dimensions['I'].width = 30
            worksheet.column_dimensions['J'].width = 15
        
        return str(filepath)
    
    # ==================== CRM ====================
    
    def add_customer(
        self,
        customer_name: str,
        year: int,
        month: int,
        state: str,
        address: str,
        mobile: str,
        phone: str,
        products: str
    ) -> bool:
        """افزودن سفارش جدید"""
        try:
            new_row = {
                'customer name': customer_name,
                'year': year,
                'month': month,
                'state': state,
                'address': address,
                'شماره موبایل': mobile,
                'شماره ثابت': phone,
                'نام محصول': products,
                'sheet_name': f'Added_{datetime.datetime.now().strftime("%Y%m%d")}'
            }
            
            self.df = pd.concat([self.df, pd.DataFrame([new_row])], ignore_index=True)
            self.process_data()
            self.save_to_excel()
            
            return True
            
        except Exception as e:
            print(f"خطا: {e}")
            return False
    
    def update_customer(
        self,
        index: int,
        customer_name: str = None,
        year: int = None,
        month: int = None,
        state: str = None,
        address: str = None,
        mobile: str = None,
        phone: str = None,
        products: str = None
    ) -> bool:
        """ویرایش سفارش"""
        try:
            if customer_name:
                self.df.at[index, 'customer name'] = customer_name
            if year:
                self.df.at[index, 'year'] = year
            if month:
                self.df.at[index, 'month'] = month
            if state:
                self.df.at[index, 'state'] = state
            if address:
                self.df.at[index, 'address'] = address
            if mobile:
                self.df.at[index, 'شماره موبایل'] = mobile
            if phone:
                self.df.at[index, 'شماره ثابت'] = phone
            if products:
                self.df.at[index, 'نام محصول'] = products
            
            self.process_data()
            self.save_to_excel()
            
            return True
            
        except Exception as e:
            print(f"خطا: {e}")
            return False
    
    def delete_customer(self, index: int) -> bool:
        """حذف سفارش"""
        try:
            self.df = self.df.drop(index).reset_index(drop=True)
            self.process_data()
            self.save_to_excel()
            return True
        except Exception as e:
            print(f"خطا: {e}")
            return False
    
    # ==================== ذخیره ====================
    
    def save_to_excel(self, output_file: str = None):
        """ذخیره فایل اکسل"""
        output_file = output_file or self.excel_file
        
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            for sheet_name in self.df['sheet_name'].unique():
                sheet_df = self.df[self.df['sheet_name'] == sheet_name]
                sheet_df = sheet_df.drop(columns=['sheet_name'])
                sheet_df.to_excel(writer, sheet_name=str(sheet_name), index=False)
    
    def export_to_excel(self, filename: str, data: pd.DataFrame):
        """خروجی اکسل"""
        data.to_excel(filename, index=False, engine='openpyxl')