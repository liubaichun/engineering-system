"""
飞书通知服务
使用飞书机器人 Webhook 发送通知
"""
import json
import urllib.request
import urllib.error

# 飞书机器人 Webhook URL
FEISHU_WEBHOOK_URL = "https://open.feishu.cn/open-apis/bot/v2/hook/55b83d27-6629-4115-a851-c2aea9dba19b"


def send_feishu_notification(user_id, title, content):
    """
    发送飞书消息给指定用户
    
    Args:
        user_id: 用户ID (int) - 注意：飞书机器人不支持user_id直接发送，需要使用openid或email
        title: 消息标题
        content: 消息内容
    """
    try:
        payload = {
            "msg_type": "text",
            "content": {"text": f"【{title}】\n{content}"}
        }
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            FEISHU_WEBHOOK_URL,
            data=data,
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            result = json.loads(response.read().decode('utf-8'))
            if result.get('code') == 0:
                return True, "发送成功"
            else:
                return False, f"发送失败: {result.get('msg')}"
    except urllib.error.HTTPError as e:
        return False, f"HTTP错误: {e.code}"
    except urllib.error.URLError as e:
        return False, f"网络错误: {e.reason}"
    except TimeoutError:
        return False, "发送超时"
    except Exception as e:
        return False, f"未知错误: {str(e)}"


def send_approval_notification(applicant_id, approver_name, flow_type, action, remark=''):
    """
    发送审批结果通知给申请人
    
    Args:
        applicant_id: 申请人ID
        approver_name: 审批人名称
        flow_type: 流程类型 (expense/leave/overtime等)
        action: 操作 (approved/rejected)
        remark: 审批意见
    """
    action_text = "已通过" if action == "approved" else "已拒绝"
    content = f"您的{_flow_type_name(flow_type)}申请{action_text}，审批人：{approver_name}"
    if remark:
        content += f"，意见：{remark}"
    
    title = f"审批{action_text}"
    return send_feishu_notification(applicant_id, title, content)


def _flow_type_name(flow_type):
    """获取流程类型的中文名称"""
    names = {
        'expense': '费用报销',
        'leave': '请假',
        'overtime': '加班',
        'general': '一般审批',
        'user_registration': '用户注册',
        'role_change': '角色变更',
    }
    return names.get(flow_type, flow_type)
