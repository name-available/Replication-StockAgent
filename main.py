import argparse
import random

import util
from agent import Agent
from secretary import Secretary
from stock import Stock
from log.custom_logger import log
from record import create_stock_record, create_trade_record, AgentRecordDaily, create_agentses_record


# 根据序列号从所有代理商列表中获取代理商
def get_agent(all_agents, order):
    for agent in all_agents:
        if agent.order == order:
            return agent
    return None


# 处理买卖操作的函数
# action 是一个 JSON 格式的字典，包含了交易的信息：
# {"agent": 1, "action_type": "buy"|"sell", "stock": "A"|"B", "amount": 10, "price": 10}
def handle_action(action, stock_deals, all_agents, stock, session):
    try:
        if action["action_type"] == "buy":  # 如果是买操作
            for sell_action in stock_deals["sell"][:]:  # 遍历当前所有的卖单
                if action["price"] == sell_action["price"]:  # 如果价格匹配
                    # 交易执行：确定可以成交的数量
                    close_amount = min(action["amount"], sell_action["amount"])
                    # 让买家代理执行买股票的操作
                    get_agent(all_agents, action["agent"]).buy_stock(stock.name, close_amount, action["price"])

                    if not sell_action["agent"] == -1:  # 如果卖单不是股票B的发行（特殊标记 agent=-1）
                        # 让卖家代理执行卖股票的操作
                        get_agent(all_agents, sell_action["agent"]).sell_stock(stock.name, close_amount,
                                                                               action["price"])

                    # 将此次成交记录添加到该股票的交易记录中
                    stock.add_session_deal({"price": action["price"], "amount": close_amount})
                    # 创建一条交易记录
                    create_trade_record(action["date"], session, stock.name, action["agent"], sell_action["agent"],
                                        close_amount, action["price"])

                    if action["amount"] > close_amount:  # 如果买单未完全成交，而卖单已经成交完毕，继续处理剩余的买单量
                        log.logger.info(f"ACTION - BUY:{action['agent']}, SELL:{sell_action['agent']}, "
                                        f"STOCK:{stock.name}, PRICE:{action['price']}, AMOUNT:{close_amount}")
                        stock_deals["sell"].remove(sell_action)  # 移除已经成交完毕的卖单
                        action["amount"] -= close_amount  # 更新未完成的买单量
                    else:  # 如果卖单未完全成交，而买单已经完成，退出循环
                        log.logger.info(f"ACTION - BUY:{action['agent']}, SELL:{sell_action['agent']}, "
                                        f"STOCK:{stock.name}, PRICE:{action['price']}, AMOUNT:{close_amount}")
                        sell_action["amount"] -= close_amount  # 更新未完成的卖单量
                        return
            # 如果遍历了所有的卖单仍然有买单未成交，将其添加到买单列表中
            stock_deals["buy"].append(action)

        else:  # 如果是卖操作
            for buy_action in stock_deals["buy"][:]:  # 遍历当前所有的买单
                if action["price"] == buy_action["price"]:  # 如果价格匹配
                    # 交易执行：确定可以成交的数量
                    close_amount = min(action["amount"], buy_action["amount"])
                    # 让卖家代理执行卖股票的操作
                    get_agent(all_agents, action["agent"]).sell_stock(stock.name, close_amount, action["price"])
                    # 让买家代理执行买股票的操作
                    get_agent(all_agents, buy_action["agent"]).buy_stock(stock.name, close_amount, action["price"])

                    # 将此次成交记录添加到该股票的交易记录中
                    stock.add_session_deal({"price": action["price"], "amount": close_amount})
                    # 创建一条交易记录
                    create_trade_record(action["date"], session, stock.name, buy_action["agent"], action["agent"],
                                        close_amount, action["price"])

                    if action["amount"] > close_amount:  # 如果卖单未完全成交，而买单已经成交完毕，继续处理剩余的卖单量
                        log.logger.info(f"ACTION - BUY:{buy_action['agent']}, SELL:{action['agent']}, "
                                        f"STOCK:{stock.name}, PRICE:{action['price']}, AMOUNT:{close_amount}")
                        stock_deals["buy"].remove(buy_action)  # 移除已经成交完毕的买单
                        action["amount"] -= close_amount  # 更新未完成的卖单量
                    else:  # 如果买单未完全成交，而卖单已经完成，退出循环
                        log.logger.info(f"ACTION - BUY:{buy_action['agent']}, SELL:{action['agent']}, "
                                        f"STOCK:{stock.name}, PRICE:{action['price']}, AMOUNT:{close_amount}")
                        buy_action["amount"] -= close_amount  # 更新未完成的买单量
                        return
            # 如果遍历了所有的买单仍然有卖单未成交，将其添加到卖单列表中
            stock_deals["sell"].append(action)
    except Exception as e:
        # 如果在处理过程中发生异常，记录错误日志
        log.logger.error(f"handle_action error: {e}")
        return


def simulation(args):
    # 初始化部分
    secretary = Secretary(args.model)  # 初始化 Secretary 对象，用于处理代理间的沟通
    stock_a = Stock("A", util.STOCK_A_INITIAL_PRICE, 0, is_new=False)  # 初始化股票 A，初始价格和初始发行量
    stock_b = Stock("B", util.STOCK_B_INITIAL_PRICE, 0, is_new=False)  # 初始化股票 B，初始价格和初始发行量（不作为新发行）
    all_agents = []  # 初始化所有代理的列表
    log.logger.debug("Agents initial...")  # 记录初始化代理的日志信息

    # 创建所有代理
    for i in range(0, util.AGENTS_NUM):  # 根据定义的代理数量创建代理
        agent = Agent(i, stock_a.get_price(), stock_b.get_price(), secretary, args.model)
        all_agents.append(agent)  # 将创建的代理加入到代理列表中
        log.logger.debug("cash: {}, stock a: {}, stock b:{}, debt: {}".format(agent.cash, agent.stock_a_amount,
                                                                              agent.stock_b_amount, agent.loans))

    # 开始模拟
    last_day_forum_message = []  # 保存前一天的论坛消息
    stock_a_deals = {"sell": [], "buy": []}  # 保存股票 A 的买卖订单
    stock_b_deals = {"sell": [], "buy": []}  # 保存股票 B 的买卖订单

    log.logger.debug("--------Simulation Start!--------")  # 开始模拟的日志信息
    for date in range(1, util.TOTAL_DATE + 1):  # 模拟每天的交易
        log.logger.debug(f"--------DAY {date}---------")  # 记录当天的日志信息

        # 除了新发行的股票 B 之外，清除前一天的所有交易
        stock_a_deals["sell"].clear()
        stock_a_deals["buy"].clear()
        stock_b_deals["buy"].clear()
        stock_b_deals["sell"].clear()

        # 检查每个代理是否需要偿还贷款
        for agent in all_agents[:]:
            agent.chat_history.clear()  # 只保存当天的聊天记录
            agent.loan_repayment(date)  # 处理代理的贷款偿还

        # 在还款日，代理需要支付利息
        if date in util.REPAYMENT_DAYS:
            for agent in all_agents[:]:
                agent.interest_payment()

        # 处理现金为负的代理
        for agent in all_agents[:]:
            if agent.is_bankrupt:  # 如果代理破产
                quit_sig = agent.bankrupt_process(stock_a.get_price(), stock_b.get_price())  # 处理破产过程
                if quit_sig:  # 如果代理退出市场
                    agent.quit = True
                    all_agents.remove(agent)

        # 处理特殊事件
        if date == util.EVENT_1_DAY:
            util.LOAN_RATE = util.EVENT_1_LOAN_RATE  # 更新贷款利率
            last_day_forum_message.append({"name": -1, "message": util.EVENT_1_MESSAGE})  # 记录特殊事件信息到论坛消息
        if date == util.EVENT_2_DAY:
            util.LOAN_RATE = util.EVENT_2_LOAN_RATE  # 更新贷款利率
            last_day_forum_message.append({"name": -1, "message": util.EVENT_2_MESSAGE})  # 记录特殊事件信息到论坛消息

        # 代理决定是否贷款
        daily_agent_records = []  # 保存每天的代理记录
        for agent in all_agents:
            loan = agent.plan_loan(date, stock_a.get_price(), stock_b.get_price(), last_day_forum_message)  # 代理决定是否贷款
            daily_agent_records.append(AgentRecordDaily(date, agent.order, loan))  # 保存代理当天的贷款记录

        # 每天多个交易时段
        for session in range(1, util.TOTAL_SESSION + 1):
            log.logger.debug(f"SESSION {session}")  # 记录当前交易时段的日志信息

            # 随机定义交易顺序
            sequence = list(range(len(all_agents)))
            random.shuffle(sequence)  # 打乱顺序，随机决定交易顺序
            for i in sequence:
                agent = all_agents[i]

                # 代理计划股票的买卖操作
                action = agent.plan_stock(date, session, stock_a, stock_b, stock_a_deals, stock_b_deals)
                proper, cash, valua_a, value_b = agent.get_proper_cash_value(stock_a.get_price(), stock_b.get_price())
                create_agentses_record(agent.order, date, session, proper, cash, valua_a, value_b, action)

                # 将代理的交易行动添加到交易记录中
                action["agent"] = agent.order
                action["date"] = date

                if not action["action_type"] == "no":  # 如果代理选择进行交易
                    if action["stock"] == 'A':
                        handle_action(action, stock_a_deals, all_agents, stock_a, session)  # 处理股票 A 的交易
                    else:
                        handle_action(action, stock_b_deals, all_agents, stock_b, session)  # 处理股票 B 的交易

            # 交易时段结束，更新股票价格
            stock_a.update_price(date)
            stock_b.update_price(date)
            create_stock_record(date, session, stock_a.get_price(), stock_b.get_price())

        # 代理预测明天的行动
        for idx, agent in enumerate(all_agents):
            estimation = agent.next_day_estimate()  # 代理预测明天的市场情况
            log.logger.info("Agent {} tomorrow estimation: {}".format(agent.order, estimation))
            if idx >= len(daily_agent_records):
                break
            daily_agent_records[idx].add_estimate(estimation)  # 将预测信息添加到当天的代理记录中
            daily_agent_records[idx].write_to_excel()  # 将记录写入 Excel
        daily_agent_records.clear()  # 清空当天的代理记录

        # 交易日结束，更新论坛信息
        last_day_forum_message.clear()
        log.logger.debug(f"DAY {date} ends, display forum messages...")
        for agent in all_agents:
            chat_history = agent.chat_history  # 获取代理的聊天记录
            message = agent.post_message()  # 代理发布当天的消息
            log.logger.info("Agent {} says: {}".format(agent.order, message))
            last_day_forum_message.append({"name": agent.order, "message": message})  # 将代理消息添加到论坛信息中

    log.logger.debug("--------Simulation finished!--------")  # 记录模拟结束的日志信息
    log.logger.debug("--------Agents action history--------")  # 记录所有代理的历史操作

    # for agent in all_agents:
    #     log.logger.debug(f"Agent {agent.order} action history:")
    #     log.logger.info(agent.action_history)
    # log.logger.debug("--------Stock deal history--------")
    # for stock in [stock_a, stock_b]:
    #     log.logger.debug(f"Stock {stock.name} deal history:")
    #     log.logger.info(stock.history)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--model", type=str, default="gpt-3.5-turbo-ca", help="model name")

    args = parser.parse_args()

    # 调用 simulation 函数，并将解析后的 args 传递进去
    simulation(args)