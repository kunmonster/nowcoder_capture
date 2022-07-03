import json

with open("info.json", 'r', encoding='utf-8') as f:
    all_info = json.load(f)
    f.close()
new_all_test = []

for every_test in all_info:
    new_every_test = every_test
    testDetail = []
    for every_question in new_every_test["testDetail"]:
        new_every_question = every_question
        new_every_question["detail"] = every_question["detail"].replace(u"\xa0", "").lstrip()
        if not every_question["select"]:
            # 非选择题
            new_every_question["answers"]["detail"] = new_every_question["answers"]["detail"].replace(u"\xa0",
                                                                                                    "").lstrip()
        new_review = []
        for every_review in new_every_question["review"]:
            new_every_review = every_review
            new_every_review["detail"] = new_every_review["detail"].replace(u"\xa0", "").lstrip()
            new_review.append(new_every_review)
        new_every_question["review"] = new_review
        testDetail.append(new_every_question)
        new_every_test["testDetail"] = testDetail
    new_all_test.append(new_every_test)
with open("deal_info.json", 'w', encoding='utf-8') as f:
    f.write(json.dumps(new_all_test,ensure_ascii=False))
    f.close()
