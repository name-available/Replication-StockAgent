import json
import openai
from log.custom_logger import log

import util


def run_api(model, prompt, temperature: float = 0):
    # 设置OpenAI的API密钥（这里为空字符串）
    openai.api_key = util.OPENAI_API_KEY
    openai.base_url = util.OPENAI_BASE_URL

    # 创建一个OpenAI客户端实例
    client = openai.OpenAI(api_key=openai.api_key, base_url=openai.base_url)

    # 使用给定的模型和prompt调用OpenAI的聊天API
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "user", "content": prompt},
        ],
        temperature=temperature,  # 设置生成的多样性，默认为0（确定性输出）
    )

    # 提取响应的文本内容
    resp = response.choices[0].message.content
    return resp  # 返回响应内容


class Secretary:
    def __init__(self, model):
        self.model = model  # 初始化Secretary实例时存储模型名称

    def get_response(self, prompt):
        return run_api(self.model, prompt)  # 使用存储的模型名称调用run_api获取响应

    """
        用json形式返回结果，例如：
        {{{{"loan": "yes", "loan_type": 3, "amount": 1000}}}}
        如果不需贷款，则返回：
        {{{{"loan" : "no"}}}}
        :returns: loan_format_check, fail_response, loan
    """

    def check_loan(self, resp, max_loan) -> (bool, str, dict):
        # 格式检查：确保响应是包含一对大括号的字符串
        if isinstance(resp, str) and resp.count('{') == 1 and resp.count('}') == 1:
            start_idx = resp.index('{')
            end_idx = resp.index('}')
        else:
            # 如果不符合格式，记录日志并返回错误信息
            log.logger.debug("Wrong json content in response: {}".format(resp))
            fail_response = "Wrong json format, there is no {} or more than one {} in response."
            return False, fail_response, None

        # 提取和清理JSON字符串
        action_json = resp[start_idx: end_idx + 1]
        action_json = action_json.replace("\n", "").replace(" ", "")

        try:
            parsed_json = json.loads(action_json)  # 解析JSON
        except json.JSONDecodeError as e:
            print(e)
            log.logger.debug("Illegal json content in response: {}".format(resp))
            fail_response = "Illegal json format."
            return False, fail_response, None

        # 内容检查
        try:
            if "loan" not in parsed_json:
                log.logger.debug("Wrong json content in response: {}".format(resp))
                fail_response = "Key 'loan' not in response."
                return False, fail_response, None

            # 确保"loan"键的值是"yes"或"no"
            if parsed_json["loan"].lower() not in ["yes", "no"]:
                log.logger.debug("Wrong json content in response: {}".format(resp))
                fail_response = "Value of key 'loan' should be yes or no."
                return False, fail_response, None

            # "loan"为"no"时，不应该包含"loan_type"或"amount"
            if parsed_json["loan"].lower() == "no":
                if "loan_type" in parsed_json or "amount" in parsed_json:
                    log.logger.debug("Wrong json content in response: {}".format(resp))
                    fail_response = "Don't include loan_type or amount in response if value of key 'loan' is no."
                    return False, fail_response, None
                else:
                    return True, "", parsed_json

            # "loan"为"yes"时，必须包含"loan_type"和"amount"
            if parsed_json["loan"].lower() == "yes":
                if "loan_type" not in parsed_json or "amount" not in parsed_json:
                    log.logger.debug("Wrong json content in response: {}".format(resp))
                    fail_response = "Should include loan_type and amount in response if value of key 'loan' is yes."
                    return False, fail_response, None

                # 检查"loan_type"是否在允许的范围内
                if parsed_json["loan_type"] not in [0, 1, 2]:
                    log.logger.debug("Wrong json content in response: {}".format(resp))
                    fail_response = "Value of key 'loan_type' should be 0, 1 or 2."
                    return False, fail_response, None

                # 检查"amount"是否在允许的范围内
                if parsed_json["amount"] <= 0 or parsed_json["amount"] > max_loan:
                    log.logger.debug("Wrong json content in response: {}".format(resp))
                    fail_response = f"Value of key 'amount' should be positive and less than {max_loan}"
                    return False, fail_response, None
                return True, "", parsed_json

            log.logger.error("UNSOLVED LOAN JSON RESPONSE:{}".format(parsed_json))
            return False, "", None
        except Exception as e:
            log.logger.error("UNSOLVED LOAN JSON RESPONSE:{}".format(parsed_json))
            return False, "", None

    def check_action(self, resp, cash, stock_a_amount,
                     stock_b_amount, stock_a_price, stock_b_price) -> (bool, str, dict):
        # 检查响应格式是否符合要求，并验证买卖操作的内容

        # 格式检查：确保响应是有效的 JSON 格式
        if isinstance(resp, str) and resp.count('{') == 1 and resp.count('}') == 1:
            start_idx = resp.index('{')
            end_idx = resp.index('}')
        else:
            log.logger.debug("Wrong json content in response: {}".format(resp))
            fail_response = "Wrong json format, there is no {} or more than one {} in response."
            return False, fail_response, None

        action_json = resp[start_idx: end_idx + 1]
        action_json = action_json.replace("\n", "").replace(" ", "")
        try:
            parsed_json = json.loads(action_json)
        except json.JSONDecodeError as e:
            print(e)
            log.logger.debug("Illegal json content in response: {}".format(resp))
            fail_response = "Illegal json format."
            return False, fail_response, None

        # 内容检查：验证 JSON 内容是否符合要求
        try:
            prices = {"A": stock_a_price, "B": stock_b_price}
            holds = {"A": stock_a_amount, "B": stock_b_amount}
            if "action_type" not in parsed_json:
                log.logger.debug("Wrong json content in response: {}".format(resp))
                fail_response = "Key 'action_type' not in response."
                return False, fail_response, None

            if parsed_json["action_type"].lower() not in ["buy", "sell", "no"]:
                log.logger.debug("Wrong json content in response: {}".format(resp))
                fail_response = "Value of key 'action_type' should be 'buy', 'sell' or 'no'."
                return False, fail_response, None

            if parsed_json["action_type"].lower() == "no":
                if "stock" in parsed_json or "amount" in parsed_json:
                    log.logger.debug("Wrong json content in response: {}".format(resp))
                    fail_response = "Don't include stock or amount in response if value of key 'action_type' is no."
                    return False, fail_response, None
                else:
                    return True, "", parsed_json
            else:
                if "stock" not in parsed_json or "amount" not in parsed_json or "price" not in parsed_json:
                    log.logger.debug("Wrong json content in response: {}".format(resp))
                    fail_response = "Should include stock, amount and price in response " \
                                    "if value of key 'action_type' is buy or sell."
                    return False, fail_response, None
                if parsed_json["stock"] not in ['A', 'B']:
                    log.logger.debug("Wrong json content in response: {}".format(resp))
                    fail_response = "Value of key 'stock' should be 'A' or 'B'."
                    return False, fail_response, None
                if parsed_json["price"] <= 0:
                    log.logger.debug("Wrong json content in response: {}".format(resp))
                    fail_response = f"Value of key 'price' should be positive."
                    return False, fail_response, None
                if not isinstance(parsed_json["amount"], int):
                    log.logger.debug("Wrong json content in response: {}".format(resp))
                    fail_response = f"Value of key 'amount' should be integer."
                    return False, fail_response, None

                # 检查买入或卖出行为是否合法
                price = parsed_json["price"]
                if parsed_json["action_type"].lower() == "buy":
                    if parsed_json["amount"] <= 0 or parsed_json["amount"] * price > cash:
                        log.logger.debug("Buy more than cash: {}".format(resp))
                        fail_response = f"The cash you have now is {cash}, " \
                                        f"the value of 'amount' * 'price'  " \
                                        f"should be positive and not exceed cash."
                        return False, fail_response, None

                hold_amount = holds[parsed_json["stock"]]
                if parsed_json["action_type"].lower() == "sell":
                    if parsed_json["amount"] <= 0 or parsed_json["amount"] > hold_amount:
                        log.logger.debug("Sell more than hold: {}".format(resp))
                        fail_response = f"The amount of stock you hold is {hold_amount}, " \
                                        f"the value of 'amount' should be positive and not exceed the " \
                                        f"amount of stock you hold."
                        return False, fail_response, None
                return True, "", parsed_json

        except Exception as e:
            log.logger.error("UNSOLVED ACTION JSON RESPONSE:{}".format(parsed_json))
            return False, "", None

    def check_estimate(self, resp):
        # 格式检查：确保响应是有效的 JSON 格式
        if isinstance(resp, str) and resp.count('{') == 1 and resp.count('}') == 1:
            start_idx = resp.index('{')
            end_idx = resp.index('}')
        else:
            # 如果响应不符合预期的 JSON 格式，记录调试日志并返回错误信息
            log.logger.debug("Wrong json content in response: {}".format(resp))
            fail_response = "Wrong json format, there is no {} or more than one {} in response."
            return False, fail_response, None

        # 提取 JSON 内容并去除换行符和空格
        action_json = resp[start_idx: end_idx + 1]
        action_json = action_json.replace("\n", "").replace(" ", "")
        try:
            # 尝试将提取的内容解析为 JSON 对象
            parsed_json = json.loads(action_json)
        except json.JSONDecodeError as e:
            # 如果 JSON 解码失败，记录异常信息并返回错误信息
            print(e)
            log.logger.debug("Illegal json content in response: {}".format(resp))
            fail_response = "Illegal json format."
            return False, fail_response, None

        # 内容检查：验证 JSON 对象的键和值是否符合要求
        try:
            # 检查响应中是否包含所有必要的键
            if "buy_A" not in parsed_json or "buy_B" not in parsed_json \
                    or "sell_A" not in parsed_json or "sell_B" not in parsed_json \
                    or "loan" not in parsed_json:
                log.logger.debug("Wrong json content in response: {}".format(resp))
                fail_response = "Key 'buy_A', 'buy_B', 'sell_A', 'sell_B' and 'loan' should in response."
                return False, fail_response, None

            # 验证所有键的值是否仅为 'yes' 或 'no'
            for key, item in parsed_json.items():
                if item not in ['yes', 'no']:
                    log.logger.debug("Wrong json content in response: {}".format(resp))
                    fail_response = "Value of all keys should be 'yes' or 'no'."
                    return False, fail_response, None

            # 如果所有检查通过，返回 True 和解析后的 JSON 对象
            return True, "", parsed_json

        except Exception as e:
            # 捕获任何异常，记录错误日志并返回错误信息
            log.logger.error("UNSOLVED ESTIMATE JSON RESPONSE:{}".format(parsed_json))
            return False, "", None
