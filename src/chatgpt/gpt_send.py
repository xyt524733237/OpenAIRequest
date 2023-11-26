#!/usr/bin/env python

import openai
import sys
import blog_message


def get_openai_response(api_key, messages):
    openai.api_key = api_key
    openai.default_headers = {"x-foo": "true"}

    completion = openai.chat.completions.create(
        model = "gpt-3.5-turbo",
        messages = messages,
    )
    return completion.choices[0].message.content



if __name__ =="__main__":
    if len(sys.argv) < 2:
        print("参数1: API Key, 参数2: 消息列表")
    api_key = sys.argv[1]
    message_dict = blog_message.get_messages()
    # 打印筛选结果
    print(message_dict)
    for key in message_dict:
        messages = message_dict[key]
        # message去掉id列
        messages_for_send = []
        for message in messages:
            print(message)
            messages_for_send.append({
            'role': message['role'],
            'content': message['content']
        })
        response = get_openai_response(api_key, messages_for_send)
        print("Key is " + str(key))
        print("Response is "+ response)

        # 评论回写
        blog_message.message_write_back(key, response)
