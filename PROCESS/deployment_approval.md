# 部署审批流程

## 审批节点
**每次正式部署前**必须获得刘总审批

## 审批内容
1. 本次部署变更内容
2. 构建版本号
3. 回滚方案
4. 影响范围

## 审批通知格式
```
【部署审批请求】
申请人：PM
变更内容：
- xxx
- xxx
版本号：engineering_system:20260407
影响范围：xxx
回滚方案：如有问题，执行 docker tag engineering_system:<旧版本> engineering_system:latest && docker-compose restart
请回复：确认 / 取消
```

## 审批超时
- 发出请求后 **30分钟**内无回复 → PM发送催办
- 超过 **2小时**无回复 → PM需电话联系刘总

## 审批通过格式
```
✅ 确认部署
版本：engineering_system:20260407
执行时间：预计 XX:XX
```

## 执行记录
每次部署必须记录到 `PROCESS/deployment_log.md`：
- 审批时间
- 审批人
- 部署时间
- 部署结果
