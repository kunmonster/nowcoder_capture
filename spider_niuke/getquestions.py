# - * - coding: utf - 8 -*-
import json
import logging
import re

import bs4.element
import requests as req
from bs4 import BeautifulSoup
from selenium import webdriver
from time import sleep

from selenium.webdriver.common.by import By

hostUrl = "https://www.nowcoder.com"
cookie = ''
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
    with open('./a.json', 'w', encoding='utf-8') as json_file:
        json_file.write(str_json)
        json_file.close()

    return allTestInfo


# request site = "https://www.nowcoder.com/question/next?pid=26371575&qid=1085975&tid=57538512"
def getTestDetails(allTestInfo):
    if len(allTestInfo) == 0:
        exit(-1)
    else:
        # everyTest
        AllTestArray = []
        for item in allTestInfo:
            # everyQuestion
            first = int(item['first_qid'])
            quest_Num = int(item['quest_num'])
            i = 1
            everyTestArray = []
            # quest_id = first
            quest_id = first
            QuestionArray = []
            while i <= quest_Num:
                quest_id += 1
                text_html = req.get(
                    hostUrl + "/test/question/done?tid=" + item['tid'] + "&qid=" + str(quest_id) + "#summary",
                    headers=header).text
                soup_obj = BeautifulSoup(text_html, 'html.parser')
                # 获取题目信息,这是一个元素数组,每个题目的数组长度应该是五,其中第一个和第三个为空
                question_str_arr = soup_obj.find('div', 'subject-question').contents

                # 第四个子元素,题目的信息
                question_detail_Arr = question_str_arr[3].contents

                question = {
                    # 题目序号#
                    'id': i,
                    # 题目类型
                    # '1'表示选择题,'0'表示非选择题
                    'select': bool,
                    # 题目详情
                    'detail': "",
                    # 答案
                    'answers': object,
                    'review': object
                }
                for dire_child in question_detail_Arr:
                    recur_element(dire_child, question)

                # 答案
                # 判断数组长度

                answers_arr = soup_obj.find_all('div', 'result-subject-item result-subject-answer')[0]

                # 选择题
                selection_answer = {"RightAnswer": "", "A": "", "B": "", "C": "", "D": ""}
                if len(answers_arr) >= 15:
                    # 注意特殊格式

                    right_answer = str(answers_arr.contents[1].contents[0]).replace(r"/\n", "").strip()
                    right_answer = re.sub(u'([^\u0041-\u007a])', '', right_answer)[0]
                    selection_answer["RightAnswer"] = right_answer
                    selection_answer["A"] = answers_arr.contents[3].contents[1].contents[0].text
                    selection_answer["B"] = answers_arr.contents[5].contents[1].contents[0].text
                    selection_answer["C"] = answers_arr.contents[7].contents[1].contents[0].text
                    selection_answer["D"] = answers_arr.contents[9].contents[1].contents[0].text
                    question['select'] = True
                    question['answers'] = selection_answer

                # 非选择题===>直接去找答案
                if len(answers_arr) <= 11:
                    non_selection_answer = {
                        'detail': ''
                    }
                    question['select'] = False
                    non_selection_answer_arr = soup_obj.find_all('div', 'design-answer-box')
                    if isinstance(non_selection_answer_arr, bs4.element.ResultSet):
                        for answer_item in non_selection_answer_arr:
                            recur_element(answer_item, non_selection_answer)
                    else:
                        recur_element(non_selection_answer_arr, non_selection_answer)
                    question['answers'] = non_selection_answer
                if i >= 48:
                    break

                # 爬取用户评论(用户评论包含答案)
                user_answers = soup_obj.find_all('div', 'answer-brief')
                # 用户评论存放数组
                user_answers_all_info = []

                for user in user_answers:
                    every_user_ans = dict({
                        'detail': ""
                    })
                    recur_element(user, every_user_ans)
                    user_answers_all_info.append(every_user_ans)
                question['review'] = user_answers_all_info
                QuestionArray.append(question)
                i = i + 1
                sleep(0.1)
            AllTestArray.append({"title":item['title'],"testDetail":QuestionArray})
        json_detail = json.dumps(AllTestArray, ensure_ascii=False)
        with open('info.json', 'w', encoding='utf-8') as f:
            f.write(json_detail)
        f.close()


# 递归遍历子元素,传参传引用
def recur_element(element: object, question: object) -> object:
    print(question['detail'])
    if element is None:
        return
    elif isinstance(element, bs4.element.NavigableString):
        # print("isStr==="+element.name)
        if element.string is not None:
            question['detail'] += element.string
    elif element.name == "img":
        question['detail'] += ('@' + element['src'] + '@')
    else:
        # print("isNoStr====:" + element.name)
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
with open('./a.json', 'r', encoding='utf-8') as f:
    all_info = json.load(f)
    f.close()
    # print(all_info)
# gerALlTestInfo(hostUrl, getAllAddr(hostUrl, header))

# js_data = [{
#     "uuid": "4ad7f6bcede24456847f1be5a15c657b",
#     "pid": "26371464",
#     "tid": "57544235",
#     "first_qid": 1085690,
#     "quest_num": 47,
#     "last_qid": 1085736
# }]

getTestDetails(allTestInfo=all_info)
