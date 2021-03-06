import sys
import json
import pandas as pd
from selenium.webdriver.common.keys import Keys
import time
from selenium.webdriver.chrome.options import Options
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from os.path import join, dirname
import os
import datetime
from airflow import DAG
from airflow.operators.slack_operator import SlackAPIPostOperator


default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime.datetime(2019, 5, 31),
    'email': ['airflow@example.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 0,
    'retry_delay': datetime.timedelta(minutes=5),
}


sys.path.append('/Users/soojeong/DSS/github/Joongonara')
from id_pw import *
from slack_api import *
id = id()
pw = pw()
webhook_URL = api()


def crawling():
    """
    중고나라 페이지 크롤링
    """
    utc_time = datetime.datetime.utcnow()
    time_gap = datetime.timedelta(hours=9)
    kor_time = utc_time + time_gap
    today = kor_time.strftime("%Y.%m.%d.")

    naver_login_url = 'https://nid.naver.com/nidlogin.login'
    joonggonara_url = 'https://cafe.naver.com/joonggonara.cafe?iframe_url=/ArticleList.nhn%3Fsearch.clubid=10050146%26search.boardtype=L%26viewType=pc'
    keyword_list = [
        '노트북'
    ]
    result_dic = {}
    for keyword in keyword_list:
        result_dic[keyword] = {
            'title': [],
            'writer': [],
            'href': [],
            'date': []
        }

    options = webdriver.ChromeOptions()
    options.add_argument('headless')
    options.add_argument('window-size=1920x1080')
    options.add_argument("disable-gpu")

    driver = webdriver.Chrome(options=options)

    driver.get(naver_login_url)
    driver.implicitly_wait(1)

    driver.get('https://nid.naver.com/nidlogin.login')
    driver.execute_script(
        "document.getElementsByName('id')[0].value=\'" + id + "\'")
    driver.execute_script(
        "document.getElementsByName('pw')[0].value=\'" + pw + "\'")
    driver.find_element_by_xpath(
        '//*[@id="frmNIDLogin"]/fieldset/input').click()

    driver.get(joonggonara_url)
    driver.implicitly_wait(3)

    driver.get(joonggonara_url)
    driver.implicitly_wait(1)

    search_input = driver.find_element_by_css_selector(
        'input#topLayerQueryInput')
    search_input.send_keys(keyword)

    search_button = driver.find_element_by_css_selector(
        "form[name='frmBoardSearch'] > button")
    search_button.click()
    driver.implicitly_wait(1)

    iframe = driver.find_element_by_css_selector('iframe#cafe_main')
    driver.switch_to.frame(iframe)

    driver.find_element_by_xpath(
        '//*[@id="currentSearchByTop"]').click()

    driver.find_element_by_css_selector(
        'div.is_selected > ul.select_list > li:nth-child(2) > a').click()

    driver.find_element_by_css_selector('button.btn-search-green').click()

    req = driver.page_source
    html = BeautifulSoup(req, 'html.parser')
    title_list = []
    writer_list = []
    href_list = []
    date_list = []
    T_F = False

    for tag in html.select('div#content-area div#main-area table tbody tr'):
        if len(tag.select('div.inner_list > a.article')) < 1:
            continue

        title = tag.select('div.inner_list > a.article')[0].text.strip()
        number = tag.select('div.inner_number')[0].text.strip()
        writer = tag.select('td.p-nick > a.m-tcol-c')[0].text.strip()
        date = tag.select('td.td_date')[0].text.strip()
        if ':' in date:
            date = today + date
        else:
            date = date + "0:0"
        href = 'https://cafe.naver.com/joonggonara/'+number
        utc_time = datetime.datetime.utcnow()

        time_gap = datetime.timedelta(hours=9)
        kor_time = utc_time + time_gap
        twenty_min_ago = kor_time - datetime.timedelta(minutes=20)
        write_time = datetime.datetime.strptime(date, "%Y.%m.%d.%H:%M")
        if write_time > twenty_min_ago:
            T_F = True
            title_list.append(title)
            writer_list.append(writer)
            href_list.append(href)
            date_list.append(date)

        else:
            break
    result_dic[keyword]['title'] = title_list
    result_dic[keyword]['writer'] = writer_list
    result_dic[keyword]['href'] = href_list
    result_dic[keyword]['date'] = date_list

    driver.quit()
    if T_F:
        df = pd.DataFrame(result_dic[keyword])

        string = ""
        for i in range(len(df)):
            string += str(i+1)
            string += "\n"
            string += str(df['title'].iloc[i])
            string += "\n"
            string += str(df['href'].iloc[i])
            string += "\n \n"

        return string
    return None


def send_slack(msg, channel="#dss", username="중고나라봇"):
    payload = {
        "channel": '#dss',
        "username": "중고나라봇",
        "icon_emoji": ":smile:",
        "text": msg,
    }

    response = requests.post(
        webhook_URL,
        data=json.dumps(payload),
    )

    print(response)


dag = DAG(
    'send_slack', default_args=default_args, schedule_interval='*/20 * * * *', dagrun_timeout=datetime.timedelta(seconds=55), catchup=False)

task1 = PythonOperator(task_id='slack', python_callable=send_slack, op_kwargs={
                       'msg': crawling()}, dag=dag)
