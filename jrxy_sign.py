#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import hashlib
import inspect
import os
import sys
import time
import re
import json
import traceback
from datetime import datetime
from notify import wecom_bot

import requests

text = ""
class JRXY_SIGN:
    def __init__(self, _config):
        """
        初始化函数
        @param config: 传入的配置信息
        """
        self.text = ""
        self.config = _config
        self.token_url = "https://mobile.campushoy.com/v6/config/tenant/config?oick=4152a541"
        self.wid_url = "https://messageapi.campusphere.net/message_pocket_web/V5/mp/restful/mobile/message/extend/get"
        self.detail_url = "https://cqcs.campusphere.net/wec-counselor-sign-apps/stu/sign/detailSignInstance"
        self.server_url = self.config['server_url'] if self.config['server_url'] else "http://api.5700.gq/jrxy"
        self.sign_url = "https://cqcs.campusphere.net/wec-counselor-sign-apps/stu/sign/submitSign"
        self.headers = {
            'User-Agent': "Mozilla/5.0 (Linux; Android 9; LLD-TL10 Build/HONORLLD-TL10; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/79.0.3945.116 Mobile Safari/537.36 cpdaily/9.5.0 wisedu/9.5.0",
            'Connection': "Keep-Alive",
            'Content-Type': "application/json",
            'appId': "amp-ios-12758"
        }
        self.config['task_logs'] = []
        if not os.path.exists("./log"):
            os.mkdir("./log")

    @staticmethod
    def md5(_str=None):
        """
        md5加密函数
        @param _str: 需要加密的字符串
        @return: 加密后的字符串
        """
        _md5 = hashlib.md5()
        _md5.update(_str.encode())
        return _md5.hexdigest()

    @staticmethod
    def exception_capture(_exception_method):
        """
        异常装饰器
        @param _exception_method: 捕获异常的方法
        @return: 内部函数名
        """

        def capture(func):
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    _exception_method(func, e, args, kwargs)

            return wrapper

        return capture

    @staticmethod
    def exception_method(_func, e, args, kwargs):
        """
        获取捕获的异常信息
        @param _func: 函数签名
        @param e: 异常
        @param args: 参数
        @param kwargs: 其他参数
        @return:
        """
        task_log = {
            "Function:": _func.__name__,
            "Exception:": e,
            "Traceback": traceback.format_exc(),
            "Parameters:": [param.name for param in list(inspect.signature(_func).parameters.values())],
            "Docstring:": inspect.getdoc(_func),
            "args": args,
            "kwargs": kwargs,
        }
        print(task_log)
        now = str(datetime.now()).replace(" ", "_").replace(":", "-")[:-7]
        with open("./log/jrxy_sign.logs", mode='a', encoding="utf-8") as f:
            f.write(f"{now} | error | {'; '.join([f'{key}: {task_log[key]}' for key in task_log])}\n\n")
        sys.exit()

    @exception_capture(exception_method)
    def log(self, s=None):
        global text
        content = f"【{self.config['userId']}】{s}"
        text += content
        print(content)

    @exception_capture(exception_method)
    def send(self, url, method='post', params=None, data=None, json=None, proxies=None, headers=None):
        """
        发送请求函数
        @param url: 请求的链接地址
        @param method: 请求的方法
        @param params: 请求的参数
        @param data: 请求的body数据
        @param json: 请求的json数据
        @param proxies: 请求代理
        @param headers: 请求头
        @return: 请求的响应体
        """
        response = None
        if method.lower() == "post":
            response = requests.post(url=url, params=params, data=data, json=json, headers=headers, proxies=proxies)
        elif method.lower() == "get":
            response = requests.get(url=url, params=params, data=data, json=json, headers=headers, proxies=proxies)
        return response

    @exception_capture(exception_method)
    def get_token(self):
        """
        获取msgAccessToken
        @return:
        """
        response = self.send(
            self.token_url,
            method='get',
            headers={
                'User-Agent': "Mozilla/5.0 (Linux; Android 9; LLD-TL10 Build/HONORLLD-TL10; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/79.0.3945.116 Mobile Safari/537.36 cpdaily/9.5.0 wisedu/9.5.0",
                'Cookie': f"sessionToken={self.config['sessionToken']}"
            })
        self.config['msgAccessToken'] = response.json()["data"]["tenantConfigVo"]["msgAccessToken"]

    @exception_capture(exception_method)
    def get_wid(self, day=2):
        """
        获取近两天的两个wid
        @param day: 获取的天数
        @return:
        """
        data = {
            "userId": self.config['userId'],
            "schoolCode": self.config['schoolCode'] if self.config['schoolCode'] else "12758",
            "timestamp": str(int(time.time()) - 86400 * day),
            "page": {
                "start": "0",
                "size": "200",
                "total": ""
            }
        }
        data['sign'] = JRXY_SIGN.md5(self.config['msgAccessToken'] + data['schoolCode'] + data['userId'])
        response = self.send(
            self.wid_url,
            json=data,
            headers={
                'User-Agent': "Mozilla/5.0 (Linux; Android 9; LLD-TL10 Build/HONORLLD-TL10; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/79.0.3945.116 Mobile Safari/537.36 cpdaily/9.5.0 wisedu/9.5.0",
                'Content-Type': "application/json",
                'appId': "amp-ios-12758",
                'accessToken': self.config['msgAccessToken']
            })
        if response.json()['page']['size'] == 2:
            msg = response.json()['msgsNew']
            msgsNew = {
                "yesterday": {
                    "date": re.findall("签到截止时间：(.*?)</p>", msg[-2]['content'])[0],
                    "wid": {
                        "signInstanceWid": re.findall("&signInstanceWid=(.*?)&from=push", msg[-2]['mobileUrl'])[0],
                        "signWid": re.findall("&signWid=(.*?)&signInstanceWid", msg[-2]['mobileUrl'])[0],
                    },
                    "isHandled": msg[-2]['isHandled'],
                },
                "today": {
                    "date": re.findall("签到截止时间：(.*?)</p>", msg[-1]['content'])[0],
                    "wid": {
                        "signInstanceWid": re.findall("&signInstanceWid=(.*?)&from=push", msg[-1]['mobileUrl'])[0],
                        "signWid": re.findall("&signWid=(.*?)&signInstanceWid", msg[-1]['mobileUrl'])[0],
                    },
                    "isHandled": msg[-1]['isHandled'],
                }
            }
            self.config['msgsNew'] = msgsNew
        else:
            time.sleep(600)
            self.get_wid()

    @exception_capture(exception_method)
    def enc_data(self):
        """
        加密数据, 并构建签到的json数据
        @return:
        """
        response = self.send(
            self.server_url,
            data={
                "data": json.dumps(self.config['bodyJson'], separators=(",", ":"), ensure_ascii=False),
                "type": "encrypt",
                "isnews": "true"
            })
        self.config['submit'] = {
            "bodyString": response.json()['data'],
            "lon": self.config['bodyJson']['longitude'],
            "calVersion": "firstv",
            "deviceId": self.config['deviceId'],
            "userId": self.config['userId'],
            "lat": self.config['bodyJson']['latitude']
        }

    @exception_capture(exception_method)
    def get_detail(self, markings="before"):
        """
        获取签到的详情信息
        @param markings: after: 获取签到前的信息; before: 获取签到后的信息
        @return:
        """
        response = self.send(
            self.detail_url,
            json=self.config['msgsNew']['yesterday']['wid'],
            headers={
                'User-Agent': "Mozilla/5.0 (Linux; Android 9; LLD-TL10 Build/HONORLLD-TL10; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/79.0.3945.116 Mobile Safari/537.36 cpdaily/9.5.0 wisedu/9.5.0",
                'Content-Type': "application/json",
                'Cookie': f"MOD_AUTH_CAS={self.config['MOD_AUTH_CAS']}"
            })
        if response.status_code == 200:
            json_data = response.json()
            if markings in "before":
                signedStuInfo = {
                    "userWid": json_data['datas']['signedStuInfo']['userWid'],
                    "userId": json_data['datas']['signedStuInfo']['userId'],
                    "userName": json_data['datas']['signedStuInfo']['userName'],
                    "sex": json_data['datas']['signedStuInfo']['sex'],
                    "schoolName": json_data['datas']['signedStuInfo']['schoolName'],
                    "grade": json_data['datas']['signedStuInfo']['grade'],
                    "dept": json_data['datas']['signedStuInfo']['dept'],
                    "major": json_data['datas']['signedStuInfo']['major'],
                    "cls": json_data['datas']['signedStuInfo']['cls'],
                    "stuDormitoryVo": {
                        "area": json_data['datas']['signedStuInfo']['stuDormitoryVo']['area'],
                        "building": json_data['datas']['signedStuInfo']['stuDormitoryVo']['building'],
                        "room": json_data['datas']['signedStuInfo']['stuDormitoryVo']['room'],
                    },
                }
                self.config['signedStuInfo'] = signedStuInfo
                bodyJson = {
                    "longitude": json_data["datas"]["longitude"],
                    "latitude": json_data["datas"]["latitude"],
                    "isMalposition": json_data["datas"]["isMalposition"],
                    "abnormalReason": "",
                    "signPhotoUrl": json_data["datas"]["signPhotoUrl"],
                    "isNeedExtra": json_data["datas"]["isNeedExtra"],
                    "position": json_data["datas"]["signAddress"],
                    "ticket": "",
                    "uaIsCpadaily": True,
                    "signInstanceWid": self.config['msgsNew']['today']['wid']['signInstanceWid'],
                    "extraFieldItems": [{
                        "extraFieldItemValue": extra["extraFieldItem"],
                        "extraFieldItemWid": extra["extraFieldItemWid"],
                    } for extra in json_data["datas"]["signedStuInfo"]["extraFieldItemVos"]]
                }
                self.config['bodyJson'] = bodyJson
            elif markings in "after":
                json_data = response.json()
                sign_info = {
                    "rateSignDate": json_data['datas']['rateSignDate'],
                    "rateTaskBeginTime": json_data['datas']['rateTaskBeginTime'],
                    "rateTaskEndTime": json_data['datas']['rateTaskEndTime'],
                    "signTime": json_data['datas']['signTime'],
                    "signType": json_data['datas']['signType'],
                    "changeTime": json_data['datas']['changeTime'],
                    "changeActorName": json_data['datas']['changeActorName'],
                }
                self.config['sign_info'] = sign_info

    @exception_capture(exception_method)
    def submit(self):
        """
        提交签到信息
        @return:
        """
        response = self.send(
            self.sign_url,
            json=self.config['submit'],
            headers={
                'User-Agent': "Mozilla/5.0 (Linux; Android 9; LLD-TL10 Build/HONORLLD-TL10; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/79.0.3945.116 Mobile Safari/537.36 cpdaily/9.5.0 wisedu/9.5.0",
                'Connection': "Keep-Alive",
                'Content-Type': "application/json",
                'Cookie': f"MOD_AUTH_CAS={self.config['MOD_AUTH_CAS']}"
            })
        if response.json()['message']:
            self.log("{" + "; ".join([f"{key}: {response.json()[key]}" for key in response.json()]) + "}")

    @exception_capture(exception_method)
    def main(self):
        self.get_token()
        self.get_wid()
        self.get_detail()
        self.enc_data()
        self.submit()
        self.get_detail(markings="after")
        now = str(datetime.now()).replace(" ", "_").replace(":", "-")[:-7]
        with open("./log/jrxy_sign.logs", mode="a") as f:
            f.write(f"{now} | info | {json.dumps(self.config)} \n\n")


if __name__ == '__main__':
    config = [{
        # 必填项,
        "userId": "",
        "deviceId": "",
        "sessionToken": "",
        "MOD_AUTH_CAS": "",
        # 选填项
        "server_url": "",
        "schoolCode": "",
    }]
    # print(json.dumps(config))
    for conf in config:
        JRXY_SIGN(conf).main()
    wecom_bot("今日校园-签到", text)
