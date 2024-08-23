import pandas as pd
import os


# 存储交易记录的信息，并提供将交易记录写入Excel文件的方法
class TradeRecord:
    def __init__(self, date, session, stock_type, buyer, seller, quantity, price):
        # 初始化交易记录对象，存储交易相关信息
        self.date = date  # 交易日期
        self.session = session  # 交易阶段或交易会话
        self.stock_type = stock_type  # 股票类型
        self.buyer = buyer  # 买方交易员
        self.seller = seller  # 卖方交易员
        self.quantity = quantity  # 交易数量
        self.price = price  # 交易价格

    def write_to_excel(self, file_name="res/trades.xlsx"):
        # 将交易记录写入Excel文件
        if os.path.isfile(file_name):
            # 如果指定的Excel文件已存在，读取其内容到DataFrame
            existing_df = pd.read_excel(file_name)
        else:
            # 如果文件不存在，创建一个空的DataFrame，并定义列名
            existing_df = pd.DataFrame(
                columns=["交易日", "交易阶段", "股票类型", "买入交易员", "卖出交易员", "交易数量", "交易价格"])

        # 将新的交易记录以列表形式存储，然后创建一个新的DataFrame
        new_records = [[self.date, self.session, self.stock_type, self.buyer, self.seller, self.quantity, self.price]]
        new_df = pd.DataFrame(new_records, columns=existing_df.columns)

        # 将新的交易记录与现有的记录合并
        all_records_df = pd.concat([existing_df, new_df], ignore_index=True)

        # 将合并后的所有交易记录写入到Excel文件中
        all_records_df.to_excel(file_name, index=False)


# 用于创建交易记录的函数
def create_trade_record(date, stage, stock, buy_trader, sell_trader, amount, price):
    # 创建TradeRecord对象并调用write_to_excel方法将交易记录写入Excel
    record = TradeRecord(date, stage, stock, buy_trader, sell_trader, amount, price)
    record.write_to_excel()
    # 写入后，删除record对象以释放内存
    record = None


# 将股票信息列表写入Excel文件（如果文件不存在则创建）
# 将交易记录列表写入Excel文件（如果文件不存在则创建）
class StockRecord:
    def __init__(self, date, session, stock_a_price, stock_b_price):
        # 初始化StockRecord对象，存储交易日期、阶段和两只股票的价格
        self.date = date  # 交易日期
        self.session = session  # 第几个交易阶段
        self.stock_a_price = stock_a_price  # 阶段结束时股票A的价格
        self.stock_b_price = stock_b_price  # 阶段结束时股票B的价格

    def write_to_excel(self, file_name="res/stocks.xlsx"):
        # 将股票记录写入Excel文件
        if os.path.isfile(file_name):
            # 如果文件已存在，读取其内容到DataFrame
            existing_df = pd.read_excel(file_name)
        else:
            # 如果文件不存在，创建一个空的DataFrame，并定义列名
            existing_df = pd.DataFrame(
                columns=["交易日", "第几个交易阶段", "阶段结束后股票A价格", "阶段结束后股票B价格"])

        # 将新的股票记录以列表形式存储，然后创建一个新的DataFrame
        new_records = [[self.date, self.session, self.stock_a_price, self.stock_b_price]]
        new_df = pd.DataFrame(new_records, columns=existing_df.columns)

        # 将新的股票记录与现有的记录合并
        all_records_df = pd.concat([existing_df, new_df], ignore_index=True)

        # 将合并后的所有股票记录写入到Excel文件中
        all_records_df.to_excel(file_name, index=False)


def create_stock_record(date, session, stock_a_price, stock_b_price):
    # 创建StockRecord对象并调用write_to_excel方法将记录写入Excel
    record = StockRecord(date, session, stock_a_price, stock_b_price)
    record.write_to_excel()
    # 写入后，删除record对象以释放内存
    record = None


class AgentRecordDaily:
    def __init__(self, agent, date, loan_json):
        # 初始化AgentRecordDaily对象，存储与代理有关的每日记录
        self.agent = agent  # 交易员的标识或名称
        self.date = date  # 记录的日期
        self.if_loan = loan_json["loan"]  # 是否贷款
        self.loan_type = 0  # 贷款类型，默认为0
        self.loan_amount = 0  # 贷款数量，默认为0

        # 根据loan_json中的信息设置贷款类型和数量
        if self.if_loan == "yes":
            self.loan_type = loan_json["loan_type"]
            self.loan_amount = loan_json["amount"]

        # 初始化将来操作的计划
        self.will_loan = "no"  # 明天是否贷款
        self.will_buy_a = "no"  # 明天是否买入A股票
        self.will_sell_a = "no"  # 明天是否卖出A股票
        self.will_buy_b = "no"  # 明天是否买入B股票
        self.will_sell_b = "no"  # 明天是否卖出B股票

    def add_estimate(self, js):
        # 根据js中的数据更新将来操作的计划
        self.will_loan = js["loan"]
        self.will_buy_a = js["buy_A"]
        self.will_sell_a = js["sell_A"]
        self.will_buy_b = js["buy_B"]
        self.will_sell_b = js["sell_B"]

    def write_to_excel(self, file_name="res/agent_day_record.xlsx"):
        # 将交易员的每日记录写入Excel文件
        if os.path.isfile(file_name):
            # 如果文件已存在，读取其内容到DataFrame
            existing_df = pd.read_excel(file_name)
        else:
            # 如果文件不存在，创建一个空的DataFrame，并定义列名
            existing_df = pd.DataFrame(columns=["交易员", "交易日", "是否贷款", "贷款类型", "贷款数量",
                                                "明日是否贷款", "明日是否买入A", "明日是否卖出A", "明日是否买入B",
                                                "明日是否卖出B"])

        # 将新的记录以列表形式存储，然后创建一个新的DataFrame
        new_records = [[self.agent, self.date, self.if_loan, self.loan_type, self.loan_amount,
                        self.will_loan, self.will_buy_a, self.will_sell_a, self.will_buy_b, self.will_sell_b]]
        new_df = pd.DataFrame(new_records, columns=existing_df.columns)

        # 将新的记录与现有的记录合并
        all_records_df = pd.concat([existing_df, new_df], ignore_index=True)

        # 将合并后的所有记录写入到Excel文件中
        all_records_df.to_excel(file_name, index=False)


def create_agent_daily_recoder(agent, date, loan_json):
    # 创建StockRecord对象并调用write_to_excel方法将记录写入Excel
    record = AgentRecordDaily(agent, date, loan_json)
    record.write_to_excel()
    # 写入后，删除record对象以释放内存
    record = None


class AgentRecordSession:
    def __init__(self, agent, date, session, proper, cash, stock_a_value, stock_b_value, action_json):
        # 初始化AgentRecordSession对象，存储与代理有关的每个交易阶段的记录
        self.agent = agent  # 交易员的标识或名称
        self.date = date  # 记录的日期
        self.session = session  # 交易阶段
        self.proper = proper  # 交易前的总资产
        self.cash = cash  # 交易前持有的现金
        self.stock_a_value = stock_a_value  # 交易前持有的A股价值
        self.stock_b_value = stock_b_value  # 交易前持有的B股价值
        self.action_stock = "-"  # 挂单股票类别，初始值为"-"
        self.amount = 0  # 挂单数量，初始值为0
        self.price = 0  # 挂单价格，初始值为0
        self.action_type = action_json["action_type"]  # 挂单类型（买入/卖出等）

        # 如果有挂单，更新挂单的股票类别、数量和价格
        if not self.action_type == "no":
            self.action_stock = action_json["stock"]
            self.amount = action_json["amount"]
            self.price = action_json["price"]

    def write_to_excel(self, file_name="res/agent_session_record.xlsx"):
        # 将每个交易阶段的记录写入Excel文件
        if os.path.isfile(file_name):
            # 如果文件已存在，读取其内容到DataFrame
            existing_df = pd.read_excel(file_name)
        else:
            # 如果文件不存在，创建一个空的DataFrame，并定义列名
            existing_df = pd.DataFrame(columns=["交易员", "交易日", "交易阶段", "交易前资产总额",
                                                "交易前持有现金", "交易前持有的A股价值", "交易前持有的B股价值",
                                                "挂单类型", "挂单股票类别", "挂单数量", "挂单价格"])

        # 将新的记录以列表形式存储，然后创建一个新的DataFrame
        new_records = [[self.agent, self.date, self.session, self.proper, self.cash,
                        self.stock_a_value, self.stock_b_value, self.action_type, self.action_stock,
                        self.amount, self.price]]
        new_df = pd.DataFrame(new_records, columns=existing_df.columns)

        # 将新的记录与现有的记录合并
        all_records_df = pd.concat([existing_df, new_df], ignore_index=True)

        # 将合并后的所有记录写入到Excel文件中
        all_records_df.to_excel(file_name, index=False)


def create_agentses_record(agent, date, session, proper, cash, stock_a_value, stock_b_value, action_json):
    # 创建AgentRecordSession对象并调用write_to_excel方法将记录写入Excel
    record = AgentRecordSession(agent, date, session, proper, cash, stock_a_value, stock_b_value, action_json)
    record.write_to_excel()
    # 写入后，删除record对象以释放内存
    record = None
