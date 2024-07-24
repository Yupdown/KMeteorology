import requests  # requests 모듈 임포트


url = 'https://apihub.kma.go.kr/api/typ01/url/stn_inf.php?inf=AWS&stn=&tm=202211300900&help=1&authKey=Ud0jPfajTAWdIz32o5wFcg'

with open('aws_info.txt', 'wb') as f:  # 저장할 파일을 바이너리 쓰기 모드로 열기
    response = requests.get(url)  # 파일 URL에 GET 요청 보내기
    f.write(response.content)  # 응답의 내용을 파일에 쓰기