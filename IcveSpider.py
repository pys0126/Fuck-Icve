import time
import requests
import random                                                                                                                                                                                                                                                                                                       
import json
from pprint import pprint
from typing import List
from lxml import etree

session = requests.Session()
header = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36 Edg/96.0.1054.62"
}
headers = {
    "Content-Type": "application/x-www-form-urlencoded",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36 Edg/96.0.1054.62"
}


def get_check_img():
    # result = execjs.eval("Math.random()") 等同于 random.random()
    url = f"https://zjy2.icve.com.cn/api/common/VerifyCode/index?t={str(random.random())}"
    gci_res = session.get(url=url, headers=header)
    with open("verifycode.png", mode="wb") as f:
        f.write(gci_res.content)
    vcode = input("请输入验证码: ")
    return vcode


def login(username: str = None, password: str = None):
    """
    return:
        'code': 1,
        'displayName': 'xxx',
        'firstUserName': 'xxxxxx',
        'hrefUrl': '/student/studio/studio.html',
        'isEmail': 0,
        'isForceUpdatePwdToSecurity': 0,
        'isGameTea': 0,
        'isInitialPwd': 0,
        'isNeedConfirmUserName': 0,
        'isSecurityLowPwd': 0,
        'isValid': 1,
        'lateCode': 0,
        'mgdCount': 0,
        'schoolCategory': 0,
        'schoolCode': 'cqhgzy',
        'schoolId': '0bmeauooybbgjbrm-ikicg',
        'schoolLogo': '/common/images/logo.png',
        'schoolName': '重庆xx学院',
        'schoolUrl': '',
        'secondUserName': '',
        'token': 'rpjtaqwufz5nx56ya8h4g',
        'userId': 'vfejaews3yzpr15ncii4ag',
        'userName': 'xx',
        'userType': 1,
        'versionMode': 1,
        'versionType': '2.0'
    """
    url = "https://zjy2.icve.com.cn/api/common/login/login"
    payload = {
        "userName": username,
        "userPwd": password,
        "verifyCode": get_check_img()
    }
    login_res = session.post(url=url, data=payload, headers=headers)
    return login_res.json()


def get_homework_list():
    url = "https://zjy2.icve.com.cn/api/student/myHomework/getMyHomeworkList"
    payload = {
        "unprocessed": 1
    }
    gcl_res = session.post(url=url, data=payload, headers=headers)
    all_homework = []
    for course_list in gcl_res.json()["list"]:
        course_name = course_list["courseName"]
        homeworks = []
        for homework_list in course_list["homeworkList"]:
            homeworks.append({
                "homework_name": homework_list["Title"],
                "courseOpenId": homework_list["courseOpenId"],
                "openClassId": homework_list["openClassId"],
                "homeWorkId": homework_list["homeworkId"],
                "activityId": "",
                "hkTermTimeId": homework_list["hkTermTimeId"],
                "faceType": ""
            })
        all_homework.append({
            "course_name": course_name,
            "homework_list": homeworks
        })
    return all_homework


def get_homework_preview(all_homework: list):
    course_name = [homework_course["course_name"] for homework_course in all_homework]
    pprint(course_name)
    course_index = int(input(f"输入序号1-{str(len(course_name))}：")) - 1
    homework_name = [homework_list["homework_name"] for homework_list in all_homework[course_index]["homework_list"]]
    pprint(homework_name)
    homework_index = int(input(f"输入序号1-{str(len(homework_name))}：")) - 1
    del all_homework[course_index]["homework_list"][homework_index]["homework_name"]
    homework_payload = all_homework[course_index]["homework_list"][homework_index]
    url = "https://security.zjy2.icve.com.cn/api/study/homework/preview"
    ghp_res = session.post(url=url, data=homework_payload, headers=headers)
    course_homework_list = json.loads(ghp_res.json()["redisData"])["questions"]
    homework_title_dict = {
        "title": [questions["Title"] for questions in course_homework_list]  # 只获取题目
    }
    return homework_title_dict


def get_answer(homework_title_list: List[str], cookie: str):
    chatiba_q_list = []  # 答案列表，最终返回
    for homework_title in homework_title_list:
        chatiba_url = "http://chatiba.com/s?key=" + homework_title.replace('\n', '')
        while True:
            chatiba_res = requests.get(url=chatiba_url, headers=header)
            chatiba_lxml = etree.HTML(chatiba_res.text)
            if not chatiba_lxml.xpath('//div[@class="ctb_tm_list"]/a/@href'):
                time.sleep(0.5)
            else:
                break
        # chatiba_res = requests.get(url=chatiba_url, headers=header)
        # chatiba_lxml = etree.HTML(chatiba_res.text)
        chatiba_q_payload_url = chatiba_lxml.xpath('//div[@class="ctb_tm_list"]/a/@href')[0]
        chatiba_q_payload = {
            "id": chatiba_q_payload_url.split("/")[-1].split(".")[0],
            "index": chatiba_q_payload_url.split("/")[-2],
            "type": "getda"
        }
        chatiba_q_url = "http://chatiba.com/q"
        headers["Cookie"] = cookie
        chatiba_q_res = requests.post(url=chatiba_q_url, data=chatiba_q_payload, headers=headers)
        while True:
            chatiba_q_res = requests.post(url=chatiba_q_url, data=chatiba_q_payload, headers=headers)
            if chatiba_q_res.json()["status"] == -2:
                time.sleep(0.5)
            else:
                break
        chatiba_q_list.append({
            "title": homework_title,
            "da": chatiba_q_res.json()["da"]
        })
        print(homework_title.replace("\n", "") + "： " + chatiba_q_res.json()["da"])
    return chatiba_q_list


# 自动答题（未完成）
def auto_da():
    '''
    /api/study/homework/newStuSubmitHomework（提交做的题）
    useTime=1665(秒)
    uniqueId=(/api/study/homework/preview能获取)
    timestamp=time.time()
    sourceType=1
    openClassId=(/api/study/homework/preview能获取)
    isDraft=0
    homeworkTermTimeId=(/api/study/homework/preview能获取)
    homeworkId=(/api/study/homework/preview能获取)
    data=[{"questionId":"2cxnajwsbqjeldm0eqzsg",
            "sourceType":1,
            "questionType":1, # (/api/study/homework/preview的questions能获取)
            "questionScore":1,
            "answerTime":1640180201998, # time.time()
            "stuAnswer":"3", # 0: A/对, 1: B/错, 2: C, 3: D
            "sortOrder":1,   # (/api/study/homework/preview的questions能获取)
            "paperStuQuestionId":"kjdaqauaolcjflrjyg7sw_0"  # uniqueId + "_0"
    }]
    '''
    sub_url = "https://security.zjy2.icve.com.cn/api/study/homework/newStuSubmitHomework"


# 根据题目.TXT查询答案并保存为TXT
def txt_search_da(fname: str, cookie: str):
    with open(fname, "r", encoding="u8") as f:
        chatiba_q_list = get_answer(homework_title_list=f.readlines()[:int(input("请输入查询多少题[数字]："))], cookie=cookie)
    for chatiba_q in chatiba_q_list:
        with open("答案.txt", "a", encoding="u8") as f2:
            f2.write(chatiba_q["title"].replace("\n", "") + "： " + chatiba_q["da"] + "\n")


# 只保存题目
def save_homework_title(k_user: str, k_pwd: str):
    login(username=k_user, password=k_pwd)  # 登录
    htd = get_homework_preview(all_homework=get_homework_list())
    for homework_title in htd["title"]:
        with open("题目.txt", "a", encoding="u8") as f:
            print(homework_title)
            f.write(homework_title + "\n")


# 保存答案为json
def save_json(k_user: str, k_pwd: str, chatiba_cookie: str):
    login(username=k_user, password=k_pwd)  # 登录
    homework_title_list = get_homework_preview(all_homework=get_homework_list())["title"]  # 获取所选课程的题目
    chatiba_q_list = get_answer(homework_title_list=homework_title_list, cookie=chatiba_cookie)  # 获取所有题目答案
    with open("答案.json", mode="w", encoding="u8") as f:  # 保存为json文件
        f.write(json.dumps({"data": chatiba_q_list}, ensure_ascii=False))


# 保存答案为txt
def save_txt(k_user: str, k_pwd: str, chatiba_cookie: str):
    login(username=k_user, password=k_pwd)  # 登录
    homework_title_list = get_homework_preview(all_homework=get_homework_list())["title"]  # 获取所选课程的题目
    chatiba_q_list = get_answer(homework_title_list=homework_title_list, cookie=chatiba_cookie)  # 获取所有题目答案
    i = 0
    for chatiba_q in chatiba_q_list:
        i += 1
        with open("答案.txt", "a", encoding="u8") as f:
            f.write(str(i) + "." + chatiba_q["title"] + ": " + chatiba_q["da"] + "\n")


# 题答案的主函数
def search_homework(cookie: str, k_user: str, k_pwd: str):
    save_type = input("请输入保存答案的格式[txt/json]: ")
    if save_type == "txt":
        save_txt(k_user, k_pwd, cookie)
    elif save_type == "json":
        save_json(k_user, k_pwd, cookie)
    else:
        print("输入错误")


def skip_ppt():
    '''
        "courseOpenId"
        "openClassId"
        "cellId"
        "cellLogId"
        "picNum"
        "studyNewlyTime"
        "studyNewlyPicNum"
        "token"
    '''
    login(username=k_user, password=k_pwd)
    courselist_url = "https://zjy2.icve.com.cn/api/student/learning/getLearnningCourseList"
    courselist_res = session.post(url=courselist_url, data={"type": 1}, headers=headers)
    courselist = courselist_res.json()["courseList"]
    for course_info in courselist:
        coursename = course_info["courseName"]
        pprint(coursename)
    course_index = int(input(f"请选择课程[1-{len(courselist)}]: "))

    courseopenid = courselist[course_index - 1]["courseOpenId"]
    openclassid = courselist[course_index - 1]["openClassId"]
    getprocesslist_url = "https://zjy2.icve.com.cn/api/study/process/getProcessList"
    getprocesslist_res = session.post(url=getprocesslist_url, data={
        "courseOpenId": courseopenid,
        "openClassId": openclassid
    }, headers=headers)

    for modulelist in getprocesslist_res.json()["progress"]["moduleList"]:
        moduleid = modulelist["id"]
        module_name = modulelist["name"]
        print("\n" + "进行：" + module_name)
        gettopicbymoduleid_url = "https://zjy2.icve.com.cn/api/study/process/getTopicByModuleId"
        gettopicbymoduleid_re = session.post(url=gettopicbymoduleid_url, data={
            "courseOpenId": courseopenid,
            "moduleId": moduleid
        }, headers=headers)

        topiclist = gettopicbymoduleid_re.json()["topicList"]
        for topic in topiclist:
            topicid = topic["id"]
            getcellbytopicid_url = "https://zjy2.icve.com.cn/api/study/process/getCellByTopicId"
            getcellbytopicid_res = session.post(url=getcellbytopicid_url, data={
                "courseOpenId": courseopenid,
                "openClassId": openclassid,
                "topicId": topicid
            }, headers=headers)
            celllist = getcellbytopicid_res.json()["cellList"]

            for cell in celllist:
                cellid = cell["Id"]
                categoryname = cell["categoryName"]
                if categoryname == "ppt":
                    viewdirectory_url = "https://zjy2.icve.com.cn/api/common/Directory/viewDirectory"
                    viewdirectory_res = session.post(url=viewdirectory_url, data={
                        "courseOpenId": courseopenid,
                        "openClassId": openclassid,
                        "cellId": cellid,
                        "flag": "s",
                        "moduleId": moduleid
                    }, headers=headers)
                    token = viewdirectory_res.json()["guIdToken"]
                    pagecount = viewdirectory_res.json()["pageCount"]

                    # 跳过ppt关键
                    stuprocesscellLog = session.post(
                        url="https://zjy2.icve.com.cn/api/common/Directory/stuProcessCellLog",
                        data={
                            "courseOpenId": courseopenid,
                            "openClassId": openclassid,
                            "cellId": cellid,
                            "cellLogId": "",
                            "picNum": pagecount,
                            "studyNewlyTime": 0,
                            "studyNewlyPicNum": pagecount,
                            "token": token,
                        }, headers=headers)
                    print({
                        "courseOpenId": courseopenid,
                        "openClassId": openclassid,
                        "cellId": cellid,
                        "cellLogId": "",
                        "picNum": pagecount,
                        "studyNewlyTime": 0,
                        "studyNewlyPicNum": pagecount,
                        "token": token,
                    })
                    print("已完成：" + viewdirectory_res.json()["cellName"])
                    time.sleep(random.randint(1, 3))
                else:
                    break


if __name__ == "__main__":
    # 查题吧cookie，去http://chatiba.com/注册一个账号，然后获取cookie
    chatiba_cookie = "你的cookie"
    # 云职教用户名和密码
    k_user = "填你的用户名"
    k_pwd = "填你的密码"

    # 自动保存查询答案
    search_homework(cookie=chatiba_cookie, k_user=k_user, k_pwd=k_pwd)

    # 过PPT，能过大部分
    # skip_ppt()

    # 只保存题目
    # save_homework_title(k_user=k_user, k_pwd=k_pwd)

    # 根据导出的题目查询
    # txt_search_da(fname="题目.txt", cookie=chatiba_cookie)
