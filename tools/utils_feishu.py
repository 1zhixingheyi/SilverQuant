"""
飞书消息通知工具

提供基于飞书机器人的消息推送功能：
- 安全签名验证：支持HMAC-SHA256签名认证机制
- 多种消息格式：文本消息、Markdown富文本卡片
- 交互式卡片：支持@全体成员和富文本展示
- 错误处理：网络异常和发送失败的容错处理
- 抽象接口：与钉钉工具统一的接口设计

消息推送架构：
- 抽象基类：继承BaseMessager统一消息推送接口
- 飞书实现：FeishuMessager实现飞书机器人推送
- 卡片模板：标准化的交互式卡片模板设计
- 安全机制：时间戳和签名的动态生成验证

核心功能特性：
- 实时通知：交易信号、策略状态、异常告警推送
- 富文本支持：Markdown格式的文本和交互式卡片
- @全体功能：支持群组@全体成员的通知
- 颜色适配：自动转换Markdown颜色为飞书支持的格式
- 发送状态：详细的发送结果反馈和错误信息

安全认证机制：
- HMAC-SHA256签名：确保消息来源的合法性
- 时间戳验证：防止重放攻击的时效性控制
- 签名算法：timestamp + secret组合的安全签名
- 配置检查：完整的配置验证和错误提示

消息格式支持：
- 纯文本消息：简单的文字信息推送
- Markdown卡片：支持富文本格式和代码块
- 交互式卡片：2.0版本的卡片模板结构
- 引用格式：自动转换分隔符为引用样式

卡片设计特性：
- 蓝色主题：专业的金融信息展示风格
- 响应式布局：PC和移动端的适配显示
- 文本大小：分层的文字大小配置
- 内边距控制：优化的视觉间距设计

与其他模块的关系：
- tools/utils_ding.py: 继承统一的消息推送基类
- tools/constants.py: 使用消息格式分隔符常量
- 全局通知：被所有策略模块调用发送通知
- delegate/*: 交易委托状态和结果通知
- trader/*: 交易信号和持仓变化通知
"""

import base64
import hashlib
import hmac
import json
import requests
import time
import traceback
from typing import Dict, Any

from tools.constants import MSG_INNER_SEPARATOR, MSG_OUTER_SEPARATOR
from tools.utils_ding import BaseMessager


def get_feishu_markdown_card(title, text):
    """
    生成飞书富文本卡片 (JSON 2.0 结构)
    """
    card_style = {
        "schema": "2.0",
        "config": {
            "update_multi": True,
            "style": {
                "text_size": {
                    "normal_v2": {
                        "default": "normal",
                        "pc": "normal",
                        "mobile": "heading"
                    }
                }
            }
        },
        "body": {
            "direction": "vertical",
            "padding": "12px 12px 12px 12px",
            "elements": [
                {
                    "tag": "markdown",
                    "content": text,
                    "text_align": "left",
                    "text_size": "normal_v2",
                    "margin": "0px 0px 0px 0px"
                }
            ]
        },
        "header": {
            "title": {
                "tag": "plain_text",
                "content": title
            },
            "template": "blue",
            "padding": "12px 12px 12px 12px"
        }
    }
    return card_style


class FeishuMessager(BaseMessager):
    def __init__(self, secret: str = None, webhook_url: str = None):
        """
        https://open.feishu.cn/document/client-docs/bot-v3/add-custom-bot?lang=zh-CN
        :param secret: 安全设置的签名
        :param url: 机器人的WebHook_url
        """
        self.secret = secret
        self.webhook_url = webhook_url
        self.refresh_webhook()

    def refresh_webhook(self) -> bool:
        """检查配置是否完整，并在缺少时打印提示"""
        if self.secret is None or self.webhook_url is None:
            print('--- FeishuMessager 配置提示 ---')
            if self.secret is None:
                print('请先在飞书申请secret')
                print('格式:SECa0ab7f3ba9742c0*********')
            if self.webhook_url is None:
                print('请先在飞书申请webhook')
                print('格式:https://open.feishu.cn/open-apis/bot/v2/hook/****************')
            print('------------------------------------')
            return False
        return True

    def gen_sign(self, timestamp: int) -> str:
        """
        生成签名
        :param timestamp: 时间戳 (必须与消息体中的 timestamp 一致)
        :return: sign
        """
        # 拼接 timestamp 和 secret
        string_to_sign = '{}\n{}'.format(timestamp, self.secret)
        hmac_code = hmac.new(string_to_sign.encode(
            "utf-8"), digestmod=hashlib.sha256).digest()
        # 对结果进行 Base64 处理
        sign = base64.b64encode(hmac_code).decode('utf-8')
        return sign

    def send_message(self, data: Dict[str, Any]) -> dict:
        """
        发送消息至机器人对应的群
        :param data: 发送的内容
        :return: 飞书服务器的响应字典
        """
        try:
            if not self.refresh_webhook():
                return {'msg': 'ConfigurationError', 'code': -1}

            header = {
                "Content-Type": "application/json",
                "Charset": "UTF-8"
            }

            send_data = json.dumps(data)
            send_data = send_data.encode("utf-8")

            response = requests.post(
                url=self.webhook_url, data=send_data, headers=header)
            return json.loads(response.text)
        except Exception:
            traceback.print_exc()
            return {'msg': 'Exception!', 'code': -99}

    def send_text(self, text: str, output: str = '', alert: bool = False) -> bool:
        """发送普通文本消息"""
        timestamp = round(time.time())
        sign = self.gen_sign(timestamp)

        content_elements = [
            {
                "tag": "text",
                "text": text,
            }
        ]
        if alert:
            content_elements.append({
                "tag": "at",
                "user_id": "all"
            })

        res = self.send_message(data={
            "timestamp": timestamp,
            "sign": sign,
            "msg_type": "post",
            "content": {"post":
                {"zh_cn":
                    {
                        "title": "",
                        "content": [content_elements]
                    }
                }
            }
        }
        )



        #{'StatusCode': 0, 'StatusMessage': 'success', 'code': 0, 'data': {}, 'msg': 'success'}

        if res.get('code') == 0 or res.get('StatusCode') == 0:
            if len(output) > 0:
                print(output, end='')
            else:
                print('Feishu message send success!')
            return True
        else:
            print('Feishu message send failed: ', {res})
            return False

    def send_text_as_md(self, text: str, output: str = '', alert: bool = False) -> bool:
        """将多行文本格式化为 Markdown 引用样式发送"""
        title = text.split('\n')[0]
        text = text.replace(MSG_OUTER_SEPARATOR, '\n\n>')
        text = text.replace(MSG_INNER_SEPARATOR, '\n')
        return self.send_markdown(title, text, output, alert)

    def send_markdown(self, title: str, text: str, output: str = '', alert: bool = False) -> bool:
        """发送 Markdown (交互式卡片) 消息"""
        #飞书 markdown 颜色替换
        color_replace_dic = {"#DC2832": "red", "#16BC50": "green"}
        for a, b in color_replace_dic.items():
            text = text.replace(a, b)
            
        text += "\n<at id=all></at>" if alert else ""
        timestamp = round(time.time())
        sign = self.gen_sign(timestamp)

        my_data = {
            "timestamp": timestamp,
            "sign": sign,
            'msg_type': 'interactive',
            "card": get_feishu_markdown_card(title, text)
        }

        res = self.send_message(data=my_data)
        if res.get('code') == 0 or res.get('StatusCode') == 0:
            if len(output) > 0:
                print(output, end='')
            else:
                print('Feishu markdown send success!')
            return True
        else:
            print(f'Feishu markdown send failed: {res}')
            return False