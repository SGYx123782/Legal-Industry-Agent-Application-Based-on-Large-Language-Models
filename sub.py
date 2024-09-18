from LLM import LLM, get_json_response, refine_answer
from API import API
from prompt import TABLE_PROMPT, TABLE_PLAN_PROMPT, QUESTION_CLASS
from tools import get_tools_response, prase_json_from_response
from execute_plan import execute_plan
import json


# 主函数
Table_solution=[]

# 数据表映射为值 
table_plan_map = {'company_info': 1,'company_register': 1,'sub_company_info': 2,'legal_document': 3}

# 打开问题 进行询问
with open('question(1).json', 'r', encoding='utf-8') as f:
    lines = f.readlines()
data = [json.loads(line.strip()) for line in lines]

# 对问题分行提取，准备进行回答
for q in data:
    try:

        ans = q['answer']
        continue
    except:
        question = q['question']
        print(q['id'],question)
        try:
            ### 问题分类：直接作答、需要检索
            # 利用大模型的prompt 让其对问题进行问题分类
            # 给定的数据是公司的基本信息，包括公司的基本信息(公司名称, 公司简称, 英文名称, 关联证券)、
            # 注册信息(公司名称, 登记状态, 统一社会信用代码, 注册资本)、
            # 子公司关联上市公司的信息(关联上市公司股票代码, 关联上市公司股票简称)
            # 涉案基本信息（标题, 案号, 文书类型, 原告, 被告）等等
            #***********1、构建大模型prompt 让其判断是开放还是查表问题*******************
            # 上述信息应该通过检索数据获得
            # 在一些法律常识，比如法律风险解读，法律（直接回答，检索回答langchain- TavilySearchResults）
            prompt = QUESTION_CLASS.format(question=question)
            response = prase_json_from_response(LLM(prompt))
            # 根据模型提供的回答 进行开放和查表操作
            if response["category_name"] == "direct_answer":
                # 不需要处理，直接调用
                answer = LLM(query=question)
            else:
                ### 表-方案分类：
                # 根据问题进行表分类：
                ## 对于基础信息\注册信息\子公司信息\涉案信息分表查询
                response = LLM(TABLE_PROMPT.format(question=q['question']))
                ## 根据回答获得查表的位置
                plan_id = table_plan_map[prase_json_from_response(response)["名称"]]
                ## 回答模型
                answer = execute_plan(question, plan_id)
                answer = refine_answer(q['question'], answer)
        except:
            answer = q['question']
        q['answer'] = answer
        print(q['answer'])


with open("submission.json", "w", encoding="utf-8") as f:
    for item in data:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")
