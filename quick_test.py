import sys
sys.path.insert(0, '.')
from src.core.config import get_track_label, get_city_level_label, get_nature_label

print('赛道标签测试:')
print(get_track_label('工：新工科和数学'))
print(get_track_label('工：生化环材食药'))
print(get_track_label('医：临床口腔'))
print(get_track_label('农：农学植物'))

print('城市级别测试:')
print(get_city_level_label('一线城市/省会城市'))
print(get_city_level_label('新一线城市'))

print('办学性质测试:')
print(get_nature_label('公办'))
print(get_nature_label('独立学院'))
print(get_nature_label('中外合作'))

print('全部测试通过!')
