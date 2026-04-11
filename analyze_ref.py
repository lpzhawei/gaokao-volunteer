import pandas as pd

df = pd.read_excel('../河北-2025高报数据参考.xlsx', sheet_name='Sheet1', header=1)
print('总行数:', len(df))
print()

# 只看2025年物理类
df_phy = df[df['科类'] == '物理']
print('2025物理行数:', len(df_phy))

# 查看关键字段
print('\n专业备注含色盲的示例:')
mask = df_phy['专业备注'].str.contains('色盲|色弱|视力|身高|体重', na=False)
print(df_phy[mask][['院校名称', '专业名称', '专业备注']].head(15).to_string())

print('\n学费字段唯一值:')
print(df_phy['学费'].unique()[:30])

print('\n专业版块唯一值:')
print(df_phy['专业版块'].unique())

print('\n城市水平标签分布(物理):')
print(df_phy['城市水平标签'].value_counts())

print('\n体检限制关键词示例:')
print(df_phy[df_phy['专业备注'].notna()]['专业备注'].str[:100].head(20).tolist())
