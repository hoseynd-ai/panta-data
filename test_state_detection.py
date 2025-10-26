from data_processor import DataProcessor

dp = DataProcessor()
dp.load_data()
dp.process_data()

print("\n" + "="*60)
print("🔍 تست شناسایی رسمی/غیررسمی")
print("="*60)

# نمایش مقادیر اصلی
print("\n📊 مقادیر اصلی در ستون 'state':")
original_states = dp.df['state'].value_counts()
print(original_states)

print("\n✅ مقادیر نرمال شده 'state_normalized':")
normalized_states = dp.processed_data['state_normalized'].value_counts()
print(normalized_states)

print("\n🔍 نمونه‌هایی از تبدیل:")
sample = dp.processed_data[['customer_name', 'state_original', 'state_normalized']].head(30)
print(sample)

print("\n" + "="*60)