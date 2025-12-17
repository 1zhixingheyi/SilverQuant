"""
钉钉消息通知工具

提供基于钉钉机器人的消息推送功能：
- 安全签名验证：支持HMAC-SHA256签名认证机制
- 多种消息格式：文本消息、Markdown富文本消息
- @全体功能：支持群组@全体成员的通知
- 错误处理：网络异常和发送失败的容错处理
- 抽象接口：与飞书工具统一的接口设计

消息推送架构：
- 抽象基类：BaseMessager定义统一的消息推送接口
- 钉钉实现：DingMessager实现钉钉机器人推送
- 安全机制：时间戳和签名的动态生成验证
- 配置检查：完整的配置验证和错误提示

核心功能特性：
- 实时通知：交易信号、策略状态、异常告警推送
- 富文本支持：Markdown格式的文本和链接
- @全体功能：支持群组@全体成员的通知
- 引用格式：自动转换分隔符为引用样式
- 发送状态：详细的发送结果反馈和错误信息

安全认证机制：
- HMAC-SHA256签名：确保消息来源的合法性
- 时间戳验证：防止重放攻击的时效性控制
- 签名算法：timestamp + secret组合的安全签名
- URL编码：Base64编码和URL安全编码

消息格式支持：
- 纯文本消息：简单的文字信息推送
- Markdown消息：支持富文本格式和链接
- 交互式消息：支持@特定用户和@全体成员
- 引用样式：自动转换格式为钉钉引用样式

与其他模块的关系：
- tools/utils_feishu.py: 继承统一的消息推送基类
- tools/constants.py: 使用消息格式分隔符常量
- 全局通知：被所有策略模块调用发送通知
- delegate/*: 交易委托状态和结果通知
- trader/*: 交易信号和持仓变化通知
"""

import abc
import base64
import hashlib
import hmac
import json
import time
import requests
import traceback
import urllib.parse
import urllib.request


class BaseMessager:
    @abc.abstractmethod
    def send_message(self, data) -> dict:
        return {}

    @abc.abstractmethod
    def send_text(self, text: str, output: str = '', alert: bool = False) -> bool:
        return False

    @abc.abstractmethod
    def send_text_as_md(self, text: str, output: str = '', alert: bool = False) -> bool:
        return False

    @abc.abstractmethod
    def send_markdown(self, title: str, text: str, output: str = '', alert: bool = False) -> bool:
        return False


class DingMessager(BaseMessager):
    def __init__(self, secret: str = None, url: str = None):
        """
        https://open.dingtalk.com/document/orgapp/custom-robots-send-group-messages
        :param secret: 安全设置的加签秘钥
        :param url: 机器人没有加签的WebHook_url
        """
        self.secret = secret
        self.url = url
        self.webhook_url = ''
        self.refresh_webhook()

    def refresh_webhook(self):
        if self.secret is None or self.url is None:
            print('请先在钉钉申请secret')
            print('格式:SECa0ab7f3ba9742c0*********')
            print('请先在钉钉申请token')
            print('格式:https://oapi.dingtalk.com/robot/send?access_token=1554a3dd1e748*********')
            return False

        timestamp = round(time.time() * 1000)  # 时间戳
        secret_enc = self.secret.encode('utf-8')
        string_to_sign = '{}\n{}'.format(timestamp, self.secret)
        string_to_sign_enc = string_to_sign.encode('utf-8')
        hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))  # 最终签名
        self.webhook_url = self.url + '&timestamp={}&sign={}'.format(timestamp, sign)  # 最终url，url+时间戳+签名
        return True

    def send_message(self, data) -> dict:
        """
        发送消息至机器人对应的群
        :param data: 发送的内容
        :return:
        """
        try:
            if self.refresh_webhook():
                header = {
                    "Content-Type": "application/json",
                    "Charset": "UTF-8"
                }
                send_data = json.dumps(data)
                send_data = send_data.encode("utf-8")

                response = requests.post(url=self.webhook_url, data=send_data, headers=header)
                return json.loads(response.text)
        except Exception as e:
            traceback.print_exc()
            return {'errmsg': str(e)}

    def send_text(self, text: str, output: str = '', alert: bool = False) -> bool:
        res = self.send_message(data={
            "msgtype": "text",
            "text": {
                "content": text,
            },
            "at": {
                "isAtAll": alert,
            },
        })

        if res['errmsg'] == 'ok':
            if len(output) > 0:
                print(output, end='')
            else:
                print('Ding message send success!')
            return True
        else:
            print('Ding message send failed: ', res['errmsg'])
            return False

    def send_text_as_md(self, text: str, output: str = '', alert: bool = False) -> bool:
        title = text.split('\n')[0]
        text = text.replace('\n\n ', '\n\n> ')
        text = text.replace('\n \n', '\n>\n> ')

        return self.send_markdown(title, text, output, alert)

    def send_markdown(self, title: str, text: str, output: str = '', alert: bool = False) -> bool:
        # my_data = {
        #     "msgtype": "markdown",
        #     "markdown": {
        #         "title": "测试markdown样式",
        #         "text": "# 一级标题 \n## 二级标题 \n> 引用文本  \n**加粗**  \n*斜体*  \n[百度链接](https://www.baidu.com) "
        #             "\n![草莓](https://dss0.bdstatic.com/70cFuHSh_Q1YnxGkpoWK1HF6hhy/it/u=1906469856,4113625838&fm=26&gp=0.jpg)"
        #             "\n- 无序列表 \n1.有序列表  \n@某手机号主 @18688889999"},
        #     "at": {
        #         "atMobiles": [""],
        #         "isAtAll": False}  # 是否@所有人
        # }

        my_data = {
            'msgtype': 'markdown',
            'markdown': {
                'title': title,
                'text': text,
            },
            'at': {
                'isAtAll': alert,
            }
        }

        res = self.send_message(data=my_data)

        if res['errmsg'] == 'ok':
            if len(output) > 0:
                print(output, end='')
            else:
                print('Ding markdown send success!')
            return True
        else:
            print('Ding markdown send failed: ', res['errmsg'])
            return False
