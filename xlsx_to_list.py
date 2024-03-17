import pandas as pd

# 엑셀 파일 경로 설정
file_path = '20240317거래량이상종목.xlsx'

# 엑셀 파일 읽기
df = pd.read_excel(file_path)

# 2열의 데이터를 리스트로 변환 (열 인덱스는 0부터 시작하므로 1을 사용)
column_values = df.iloc[:, 1].tolist()

formatted_data = [str(num).zfill(6) for num in column_values]

# 결과 출력
print(formatted_data)