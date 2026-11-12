from rag_core import load_chunks,answer



EVAL_SET = [
    # ── ① 直球 ──
    {"question": "逾期了要交多少钱？", "must_contain": ["0.5", "20"],
     "expected_block": 3, "should_refuse": False},
    {"question": "研究生能借几本书？", "must_contain": ["10"],
     "expected_block": 1, "should_refuse": False},
    {"question": "可以续借几次？", "must_contain": ["两次"],
     "expected_block": 2, "should_refuse": False},

    # ── ② 同义改写 ──
    {"question": "书到期了还能再多留几天吗？", "must_contain": ["续借", "30"],
     "expected_block": 2, "should_refuse": False},

    # ── ③ 需要推理 ──
    {"question": "本科生可以一次借 20 本吗？", "must_contain": ["5"],
     "expected_block": 1, "should_refuse": False},
    {"question": "我借的书逾期 40 天了，还能继续借书吗？", "must_contain": ["30", "暂停"],
     "expected_block": 3, "should_refuse": False},
    {"question": "滞纳金可以减免吗？", "must_contain": ["减免"],
     "expected_block": 3, "should_refuse": False},
    {"question": "累计几次违约会被暂停预约？", "must_contain": ["3", "60"],
     "expected_block": 4, "should_refuse": False},

    # ── ④ 拒答 ──
    {"question": "图书馆的开放时间是什么？", "must_contain": [],
     "expected_block": None, "should_refuse": True},
    {"question": "图书馆在几楼？", "must_contain": [],
     "expected_block": None, "should_refuse": True},
    # ── ⑤ 多文件区分 ──
    {"question": "自习室可以吃东西吗？", "must_contain": ["禁止"],
     "expected_block": 9, "should_refuse": False},

]


chunks,chunk_vector=load_chunks(mode="heading")
print(f"文档切成{len(chunks)}块")


content_pass=0
source_pass=0
refuse_pass=0
total=len(EVAL_SET)

for item in EVAL_SET:
    #先获取模型的回答
    reply=answer(item["question"],chunks,chunk_vector)

    content_ok=True
    for kw in item["must_contain"]:
        if kw  not in reply:
            content_ok=False

    refused="没有提到" in reply
    refuse_ok=(refused==item["should_refuse"])

    source_ok=True
    if item["expected_block"] is not None:
        marker = f"块 #{item['expected_block']}"
        if marker not in reply:
            source_ok = False

    #最后统计一下
    if content_ok:
        content_pass += 1
    if refuse_ok:
        refuse_pass += 1
    if source_ok:
        source_pass += 1

    print("="*62)
    print(f"问题：{item['question']}")
    print(f"回答：{reply}")
    print(f"内容 {'PASS' if content_ok else 'FAIL'} | "
          f"出处 {'PASS' if source_ok else 'FAIL'} | "
          f"拒答 {'PASS' if refuse_ok else 'FAIL'}")
    print()

print("=" * 62)
print(f"内容正确：{content_pass}/{total}")
print(f"出处正确：{source_pass}/{total}")
print(f"拒答正确：{refuse_pass}/{total}")
























"""
    ---块 #0 ---
# 校图书馆借阅规则

## 一、总则

本馆面向全校师生开放，提供借阅、续借、预约和逾期处理四项核心服务。所有服务均通过「校园图书管理系统」办理，读者可使用校园卡在自助机上完成大部分操作，人工柜台仅处理异常情况。系统每日 23:00 至次日 6:00 进行数据同步，期间部分功能可能不可用。

##

---块 #1 ---
日 6:00 进行数据同步，期间部分功能可能不可用。

## 二、借阅规则

本科生一次最多可借 5 本，借期 30 天；硕士研究生可借 10 本，借期 60 天；博士研究生与教师可借 20 本，借期 90 天。工具书、期刊合订本和古籍善本仅限馆内阅览，不外借。

借阅时需刷校园卡确认身份。如校园卡

---块 #2 ---
仅限馆内阅览，不外借。

借阅时需刷校园卡确认身份。如校园卡遗失，须先到卡务中心挂失补办，凭补办凭证到人工柜台办理临时借阅。每张校园卡仅限本人使用，转借他人一经发现将暂停借阅权限一个月。

## 三、续借规则

每本书最多可续借两次，每次延长 30 天。续借须在到期前 3 天内操作，可通过网站、移动

---块 #3 ---
长 30 天。续借须在到期前 3 天内操作，可通过网站、移动端或自助机完成。若该书已被其他读者预约，则无法续借，必须按时归还。

续借不收取任何费用。但若图书已逾期，须先归还并缴清滞纳金后方可再次借阅，不能直接续借。

## 四、逾期处理

逾期自到期次日起计算，每天每本收取 0.5 元滞纳金，单本

---块 #4 ---

逾期自到期次日起计算，每天每本收取 0.5 元滞纳金，单本累计上限为 20 元。逾期超过 30 天，系统将自动暂停该读者的全部借阅权限，直至归还图书并缴清全部费用。

滞纳金可通过校园卡在自助机上缴纳，也可到财务处窗口办理现金缴纳。因出差、住院等特殊原因造成的逾期，可凭相关证明到图书馆办公室申请减

---块 #5 ---
、住院等特殊原因造成的逾期，可凭相关证明到图书馆办公室申请减免，减免额度由馆长审批。

## 五、预约规则

当某本书的全部副本均已借出时，读者可在系统中提交预约申请。预约成功后，该书归还时系统会自动发送短信通知，读者须在 3 天内到馆取书。逾期未取，预约自动取消，并计入一次违约记录。

累计 3 

---块 #6 ---
。逾期未取，预约自动取消，并计入一次违约记录。

累计 3 次违约记录，将暂停预约权限 60 天。

## 六、其他服务

系统还提供图书推荐、阅读历史查询、新书通报等功能。读者可在个人中心查看自己的借阅记录和滞纳金明细。如需开具借阅证明，可在自助机上打印，或到人工柜台办理。


---块 #7 ---
可在自助机上打印，或到人工柜台办理。

"""