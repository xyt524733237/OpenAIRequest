import os
import openai
import sys
import common.blog_message as blog_message


# 评论页面
url = os.environ.get("COMMENTS_URL_DALLE")
# 博客id
post_id = os.environ.get("POST_ID_DALLE")


def get_dalle_response(api_key, messages):
    openai.api_key = api_key
    openai.default_headers = {"x-foo": "true"}

    # dall.e目前只接受最后一条信息，不接受历史评论
    message = messages[-1]['content']
    print("Message is " + message)

    response = openai.Image.create(
        prompt = message,
    )

    return '<img src="' + response.data[0].url +'"/>'


if __name__ =="__main__":
    if len(sys.argv) < 2:
        print("参数1: API Key")
    api_key = sys.argv[1]
    message_dict = blog_message.get_messages(url, post_id)
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
        response = get_dalle_response(api_key, messages_for_send)
        print("Key is " + str(key))
        print("Response is "+ response)

        # 评论回写
        blog_message.message_write_back(key, response, url, post_id)