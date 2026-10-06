# 무숙녀 정산 도우미 (스마트스토어·쿠팡)

## 파일 구성 (파일 하나에 역할 하나)
| 파일 | 역할 | 단계 |
| --- | --- | --- |
| common.py | 공통 표 모양, 엑셀을 글자로 읽기, 금액·날짜 바꾸기 | 2 |
| smartstore.py, coupang.py | 쇼핑몰별 번역기 (위쪽 대응표만 다름) | 2 |
| master.py | 기준 정보 엑셀 읽기와 검사 | 3 |
| matching.py | 상품명 → 상품코드, 원가 연결, 짝 없음 추천 | 3 |
| profit.py | 순이익 계산 (계산 규칙 시트를 코드로) | 4 |
| reconcile.py | 주문과 정산 대조 (누락, 금액 오류) | 5 |
| verify.py | 정답 파일과 공식 검산 | 6 |
| engine.py | 부품을 순서대로 이어 한 번에 실행 | 7 |
| report.py | 보고서 엑셀 저장 | 7 |
| gui.py | 화면 | 7 |
| stepN_check.py | 단계별 확인용 시험 | 2~7 |

## 실행
    py gui.py

## exe 만들기 (처음 한 번 pyinstaller 설치)
    py -m pip install pyinstaller
    py -m PyInstaller --onefile --noconsole --name musooknyeo_settlement gui.py
dist 폴더에 musooknyeo_settlement.exe가 생겨요. 엑셀 파일들과 같은 폴더에 두고 실행하면 파일 칸이 자동으로 채워져요.
