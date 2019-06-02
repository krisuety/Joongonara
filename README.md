# Joongonara
[중고나라] 사고싶은 item과 관련된 글이 올라오면 slack message 받기


1. id_pw.py와 slack_api.py 수정
2. send_slack.py 를 실행해 최근 20분 사이에 올라온 새 글들이 slack message로 오는지 확인
3. airflow 디렉토리 안에 있는 airflow_send_slack.py 를 dag으로 추가하여 최근 20분 사이에 올라온 새 글들이 있을 때 message 받기

네이버 중고나라 카페의 경우 글을 올린 후 전체 검색 페이지에 올라오기까지 10분의 gap이 있으므로 검색 주기를 10분 미만으로 설정하지 않도록 주의.
