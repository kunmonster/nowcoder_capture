# - * - coding: utf - 8 -*-
import json
import logging

import bs4.element
import requests as req
from bs4 import BeautifulSoup
from selenium import webdriver
from time import sleep

from selenium.webdriver.common.by import By

hostUrl = "https://www.nowcoder.com"


header = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36',
    'cookie': cookie
}


# 将cookie字符串转换成字典,返回字典数组
def cookieToDict(cookieStr):
    cookie_dict = []
    first_deal = cookieStr.split(';')
    for i in first_deal:
        second_deal = i.split("=")
        cookie_dict.append(
            {'name': second_deal[0].lstrip(), 'value': second_deal[1].lstrip()})
    return cookie_dict


# 获取所有地址
def getAllAddr(host_url, header_array):
    text = req.get(host_url + "/kaoyan", headers=header_array).text
    dom_obj = BeautifulSoup(text, 'html.parser')
    a_dict = dom_obj.findAll("a", "js-go-summary")
    # 获取链资源地址
    allPaperAddre = []

    for i in a_dict:
        allPaperAddre.append(i.get("data-href"))

    return allPaperAddre


# 返回所有试卷的基本信息
# {'uuid','pid','tid',, 'first_qid','quest_num','last_qid'}
def gerALlTestInfo(host_url, allPageAddre):
    allTestInfo = []
    browser = webdriver.Chrome(executable_path='chromedriver.exe')
    cookies = cookieToDict(cookie)
    browser.get("https://www.nowcoder.com")
    for i in cookies:
        browser.add_cookie(i)
    for item in allPageAddre:
        browser.get(host_url + item)
        sleep(2)
        next_btn = browser.find_element(By.ID, 'next')
        next_btn.submit()

        # 获取当前test的网页==>uuid,pid,tid

        long_site = browser.current_url
        quest_ul = browser.find_elements(By.XPATH, '/html/body/div[1]/div/div[1]/div/div[4]/ul/*')
        quest_num = len(quest_ul)
        rawInfo = long_site.split('/')[-1].split('?')
        uuid_v = rawInfo[0].strip()
        pid_tid = rawInfo[1].split('&')
        pid_v = pid_tid[0].split('=')[1].strip()
        tid_v = pid_tid[1].split('=')[1].strip()

        browser.find_element(By.ID, 'next').submit()

        quest_ID_site = browser.current_url
        title_v = browser.find_element(By.CLASS_NAME, 'com-subject-title').text
        quest_ID = int(quest_ID_site.split('&')[1].split('=')[1]) - 1
        allTestInfo.append({'title': title_v, 'uuid': uuid_v, 'pid': pid_v, 'tid': tid_v, 'first_qid': quest_ID,
                            'quest_num': quest_num,
                            'last_qid': quest_ID + quest_num - 1})
        sleep(2)
    # 关闭浏览器
    browser.close()

    str_json = json.dumps(allTestInfo)
    with open('./a.json', 'w') as f:
        f.write(str_json)
        f.close()

    return allTestInfo


# request site = "https://www.nowcoder.com/question/next?pid=26371575&qid=1085975&tid=57538512"
def getTestDetails(allTestInfo):
    if len(allTestInfo) == 0:
        exit(-1)
    else:
        # everyTest
        TestArray = []
        for item in allTestInfo:
            # everyQuestion
            first = int(item['first_qid'])
            quest_Num = int(item['quest_num'])
            i = 1
            everyTestArray = []
            # quest_id = first
            quest_id = first
            while i <= quest_Num:
                quest_id += 1
                i = i + 1
                text_html = req.get(
                    hostUrl + "/test/question/done?tid=" + item['tid'] + "&qid=" + str(quest_id) + "#summary",
                    headers=header).text
                soup_obj = BeautifulSoup(text_html, 'html.parser')
                # 获取题目信息,这是一个元素数组,每个题目的数组长度应该是五,其中第一个和第三个为空
                question_str_arr = soup_obj.find('div', 'subject-question').contents

                '''第四个子元素,题目的信息'''
                question_detail_Arr = question_str_arr[3].contents

                question = {
                    'info':""
                }
                for dire_child in question_detail_Arr:
                    print(dire_child.name)
                    recur_element(dire_child, question)
                    print("finish===="+question['info'])
                    # if isinstance(dire_child, str) | (dire_child.name == 'p'):
                    #     '''为字符串'''
                    #     if not dire_child == ' ':
                    #         question += str(dire_child)
                    #     else:
                    #         pass
                    # else:
                    #     '''遍历子元素'''
                    #     for sub_child in dire_child.contents:
                    #         '''元素不为NavaString'''
                    #         if not isinstance(sub_child, str):
                    #             '''题目出现图片'''
                    #             print(sub_child.name)
                    #             if sub_child.name == 'img':
                    #                 '''需要在题目里面打上一个标记,使用@打上标记'''
                    #                 src = sub_child['src']
                    #                 question = question + '@' + src + '@'
                    #             if (sub_child.name == 'p') | (sub_child.name == 'div'):
                    #                 print(sub_child.string)
                    #                 if sub_child.string is not None:
                    #                     question += sub_child.string
                    #             else:
                    #                 pass
                    #         else:
                    #             '''字符串'''
                    #             if sub_child.string is not None:
                    #                 question += str(sub_child.string)

                '''答案'''
                '''判断数组长度'''

                answers = soup_obj.find_all('div', 'result-subject-item result-subject-answer')[0]

                '''选择题'''
                if len(answers) >= 15:
                    '''注意特殊格式'''

                    right_answer = answers.contents[1].contents[0]
                    case_a = answers.contents[3].contents[1].contents[0]
                    case_b = answers.contents[5].contents[1].contents[0]
                    case_c = answers.contents[7].contents[1].contents[0]
                    case_d = answers.contents[9].contents[1].contents[0]
                '''非选择题=直接去找答案'''
                if len(answers) <= 11:
                    non_selection_answer_arr = soup_obj.find_all('div', 'design-answer-box')
                    print(non_selection_answer_arr)

                if i >= 48:
                    break
                sleep(0.2)


def recur_element(element, question):
    print(question['info'])
    if element is None:
        return
    elif isinstance(element, bs4.element.NavigableString):
        # print("isStr==="+element.name)
        if element.string is not None:
            question['info'] += element.string
    elif element.name == "img":
        question['info'] += ('@' + element['src'] + '@')
    else:
        print("isNoStr====:" + element.name)
        try:
            sub_arr = element.contents
            if sub_arr is not None:
                for item in sub_arr:
                    recur_element(item, question)
            else:
                return question
        except AttributeError:
            logging.WARN("没有contents属性")
            pass


# gerALlTestInfo(hostUrl,getAllAddr(hostUrl,header))
with open('./a.json', 'r') as f:
    all_info = json.load(f)
    f.close()
    # print(all_info)
# gerALlTestInfo(hostUrl, getAllAddr(hostUrl, header))

js_data = [{
    "uuid": "4ad7f6bcede24456847f1be5a15c657b",
    "pid": "26371464",
    "tid": "57544235",
    "first_qid": 1085690,
    "quest_num": 47,
    "last_qid": 1085736
}]

getTestDetails(allTestInfo=js_data)
