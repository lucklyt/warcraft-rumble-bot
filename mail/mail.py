# cython: language_level=3

from conf.conf import log
from email.mime.text import MIMEText
from smtplib import SMTP_SSL


def send_email(subject, message, reviver,code):
    try:
        user = reviver
        password = code
        # 邮件内容
        msg = MIMEText(message, 'plain', _charset="utf-8")
        # 邮件主题描述
        msg["Subject"] = subject
        msg['from'] = "{} <{}>".format("arclight", user)
        with SMTP_SSL(host="smtp.qq.com", port=465) as smtp:
            # 登录发邮件服务器
            smtp.login(user=user, password=password)
            # 实际发送、接收邮件配置
            smtp.sendmail(from_addr=user, to_addrs=[reviver], msg=msg.as_string())
            smtp.quit()
    except Exception as e:
        log.error("send email failed {}".format(e))
