import os
import requests
import re
import uuid
import time


def get_messages(url: str, post_id: str):
    response=requests.get(url + "?per_page=100&post=" + post_id)
    if response.status_code != 200:
        print("Http response error, code is: " + response.status_code)
        return []
    
    data = response.json()
    data = [item for item in data if item.get('post') == int(post_id)]
    
    msg_dict={}

    sys_content=[
        "你的回答需要满足如下要求：",
        "1. 回答遵循html格式，比如需要换行，应该用<br/>而不是\n，如果回答中包含脚本或者代码，需要将脚本或者代码放在<pre><code></code></pre>中间。",
    ]
    
    # 添加定位评论和首层评论
    for comment in data:
        if comment['parent'] == 0:
            msg_dict[comment['id']] = [{
                    'role': "system",
                    'content': '\n'.join(sys_content),
                    'id': 0
            },{
                    'role': "assistant" if comment['author'] == 2 else "user",
                    'content': comment['content']['rendered'],
                    'id': comment['id']
            }]
    # 添加其他评论
    for comment in data:
        if comment['parent'] in msg_dict:
            msg_dict[comment['parent']].append({
                'role': "assistant" if comment['author'] == 2 else "user",
                'content': comment['content']['rendered'].replace("<p>","").replace("</p>",""),
                'id': comment['id']
            })
    # 排序
    for id in msg_dict:
        msg_dict[id] = sorted(msg_dict[id], key=lambda x: x['id'])
    print(msg_dict)
    # 筛选出最后一个未回复的评论
    msg_dict2 = {}
    for key in msg_dict:
        value = msg_dict[key]
        print(value)
        if value[-1]['role'] == 'user':
            msg_dict2[key] = value
    msg_dict = msg_dict2
    return msg_dict

def message_write_back(parent, message, url: str, post_id: str):
    # 对发回的数据进行清洗
    message = sent_back_message_wash(message)
    message = message_match_code(message)
    message = message.replace("/n","<br/>")
    message = "<p>" + message + "</p>\n"
    
    wp_lele_username = os.environ.get("WP_LELE_USERNAME")
    wp_lele_password = os.environ.get("WP_LELE_PASSWORD")
    data = {
        'author_name':"乐乐机器人",
        'content': message,
        'author': 2,
        'parent': parent,
        'post': post_id
    }

    response_code = 0
    retry_time = 3
    while retry_time > 0 and response_code != 201:
        response = requests.post(url, json=data, auth=(wp_lele_username, wp_lele_password))
        print(response)
        print(response.text)
        retry_time -= 1
        response_code = response.status_code
        time.sleep(60)

def sent_back_message_wash(message: str):
    # 允许的html标签
    allow_html_tags = [
        "pre", "code",
        "div", "p", "span", "hr", "br", "h[1,6]",
        "b", "strong", "i", "em", "u", "del", "sub", "sup",
        "ul", "ol", "li", "dl", "dt", "dd",
        'a href="[^"]*"', "a",
        'img src="[^"]*"', "img"
    ]
    allow_html_tag_list=[]
    for tag in allow_html_tags:
        allow_html_tag_list.append("<"+ tag +">")
        allow_html_tag_list.append("</"+ tag +">")
        allow_html_tag_list.append("<"+ tag +"/>")
    pattern_str = '|'.join(allow_html_tag_list)
    partten = re.compile(pattern_str)
    left_token = "left-" + str(uuid.uuid4())
    right_token = "right-" + str(uuid.uuid4())
    # 正则抓取允许的标签中的<>，替换为对应token
    def replace(match):
        if match.group(0).find('\n') == -1:
            return left_token + match.group(0)[1: -1] + right_token
        else:
            return "<" + match.group(0)[1: -1] + ">"
    message = re.sub(partten, replace, message)	
    # 对剩下的message执行html encode
    message = message.replace("<", "&lt;").replace(">", "&gt;")
    # 之前的token替换为<>
    message = message.replace(left_token, "<").replace(right_token, ">")
    return message


def message_match_code(message: str):
    is_code_open = False
    while message.find("```") != -1:
        if not is_code_open:
            message = message.replace("```", "<pre><code># ", 1)
        else:
            message = message.replace("```", "</code></pre>", 1)
        is_code_open = not is_code_open
    return message
