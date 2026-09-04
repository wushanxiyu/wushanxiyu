"""
小说角色取名神器
随机生成小说角色名字，包括：主角、配角、路人、搞笑、普通、平庸、寓意、意境
"""

import csv
import random
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional


# ======================== 姓氏库 ========================
SURNAMES_SINGLE = [
    "赵", "钱", "孙", "李", "周", "吴", "郑", "王", "冯", "陈",
    "褚", "卫", "蒋", "沈", "韩", "杨", "朱", "秦", "尤", "许",
    "何", "吕", "施", "张", "孔", "曹", "严", "华", "金", "魏",
    "陶", "姜", "戚", "谢", "邹", "喻", "柏", "水", "窦", "章",
    "云", "苏", "潘", "葛", "奚", "范", "彭", "郎", "鲁", "韦",
    "昌", "马", "苗", "凤", "花", "方", "俞", "任", "袁", "柳",
    "酆", "鲍", "史", "唐", "费", "廉", "岑", "薛", "雷", "贺",
    "倪", "汤", "滕", "殷", "罗", "毕", "郝", "邬", "安", "常",
    "乐", "于", "时", "傅", "皮", "卞", "齐", "康", "伍", "余",
    "元", "卜", "顾", "孟", "平", "黄", "和", "穆", "萧", "尹",
    "姚", "邵", "湛", "汪", "祁", "毛", "禹", "狄", "米", "贝",
    "明", "臧", "计", "伏", "成", "戴", "谈", "宋", "茅", "庞",
    "熊", "纪", "舒", "屈", "项", "祝", "董", "梁", "杜", "阮",
    "蓝", "闵", "席", "季", "麻", "强", "贾", "路", "娄", "危",
    "江", "童", "颜", "郭", "梅", "盛", "林", "刁", "钟", "徐",
    "邱", "骆", "高", "夏", "蔡", "田", "樊", "胡", "凌", "霍",
    "虞", "万", "支", "柯", "昝", "管", "卢", "莫", "经", "房",
    "裘", "缪", "干", "解", "应", "宗", "丁", "宣", "贲", "邓",
    "郁", "单", "杭", "洪", "包", "诸", "左", "石", "崔", "吉",
    "钮", "龚", "程", "嵇", "邢", "滑", "裴", "陆", "荣", "翁",
]

SURNAMES_DOUBLE = [
    "欧阳", "太史", "端木", "上官", "司马", "东方", "独孤", "南宫",
    "万俟", "闻人", "夏侯", "诸葛", "尉迟", "公羊", "赫连", "澹台",
    "皇甫", "宗政", "濮阳", "公冶", "太叔", "申屠", "公孙", "慕容",
    "仲孙", "钟离", "长孙", "宇文", "司徒", "鲜于", "司空", "闾丘",
    "子车", "亓官", "司寇", "巫马", "公西", "颛孙", "壤驷", "公良",
    "漆雕", "乐正", "谷梁", "拓跋", "夹谷", "轩辕", "令狐", "段干",
    "百里", "呼延", "东郭", "南门", "羊舌", "微生", "公户", "公玉",
    "公仪", "梁丘", "公仲", "公上", "公门", "公山", "公坚", "左丘",
]

# ======================== 名字库（按类别和性别组织） ========================
# 每个类别包含: male(男名), female(女名), desc(风格描述)

NAME_DATA: dict[str, dict[str, list[str] | str]] = {
    "主角": {
        "desc": "平凡中见不凡，简约而有深意",
        "male": [
            # 单字名——如王林、孟浩、叶凡，简洁有力
            "浩", "凡", "林", "峰", "宇", "辰", "然", "渊", "翔", "晨",
            "逸", "言", "默", "寒", "青", "远", "坤", "泽", "锋", "毅",
            "磊", "昊", "宸", "煜", "铭", "瀚", "睿", "轩", "霄", "烈",
            "霖", "枫", "烨", "珩", "璟", "瑾", "瑜", "玄", "衍", "洵",
            "澈", "隐", "洛", "谦", "恒", "朔", "筠", "荀", "荒", "洵",
            # 双字名——简约中有深意
            "长安", "九歌", "无忌", "不二", "归一", "问天", "寻道", "忘言",
            "知微", "见素", "抱朴", "守一", "长生", "三秋", "半夏", "长歌",
            "未央", "无涯", "太初", "扶摇", "北辰", "南归", "东来", "千机",
            "万象", "天枢", "苍梧", "青冥", "墨白", "玄霜",
        ],
        "female": [
            # 单字名——如陆雪琪、碧瑶，清雅灵动
            "鸢", "染", "洛", "瑶", "璃", "鸾", "凰", "瑾", "瑜", "璇",
            "玥", "珩", "璎", "琉", "璨", "芷", "芸", "蕊", "蕴", "薇",
            "莞", "蘅", "荞", "荼", "荷", "菀", "菱", "萱", "萼", "蕙",
            "霜", "雪", "月", "烟", "霞", "翎", "翊", "熙", "颜", "歌",
            # 双字名——淡雅中见风骨
            "青衣", "素衣", "白衣", "红妆", "初见", "如故", "归晚", "迟暮",
            "未央", "长歌", "半夏", "三秋", "忘忧", "无恙", "安然", "依然",
            "恬然", "欣然", "释然", "沐橙", "如雪", "沐雪", "凝霜", "惊鸿",
            "落雁", "沉鱼", "闭月", "羞花", "清漪", "素心",
        ],
    },
    "配角": {
        "desc": "有特点但不喧宾夺主",
        "male": [
            "子安", "伯庸", "仲达", "叔宝", "季明", "文远", "景略", "元凯",
            "士元", "德操", "公瑾", "奉孝", "孝直", "文和", "子扬", "伯约",
            "正则", "修远", "怀瑾", "握瑜", "明远", "清风", "朗月", "寒松",
            "秋水", "春山", "夏初", "冬临", "长安", "九州", "三秋", "半夏",
            "望舒", "飞廉", "屏翳", "赤松", "青鸟", "白泽", "玄武", "朱雀",
            "墨言", "书白", "砚秋", "琴心", "棋语", "画影", "诗韵", "酒狂",
        ],
        "female": [
            "婉清", "静姝", "淑慎", "惠然", "徽音", "德音", "柔嘉", "令仪",
            "心宜", "意舒", "语嫣", "笑雯", "诗涵", "画屏", "琴心", "剑胆",
            "兰芝", "蕙质", "梅影", "竹韵", "菊香", "荷风", "棠梨", "杏雨",
            "桃夭", "柳絮", "桐影", "檀心", "桂魄", "萱草", "芍药", "芙蓉",
            "绮罗", "珠玉", "翡翠", "珊瑚", "琥珀", "玛瑙", "水晶", "琉璃",
            "素锦", "青黛", "紫苏", "白芷", "红曲", "绿芜", "蓝桥", "黄莺",
        ],
    },
    "路人": {
        "desc": "普普通通，一闪而过",
        "male": [
            "大壮", "铁柱", "二牛", "三娃", "阿福", "小六", "石头", "来福",
            "旺财", "富贵", "有财", "进宝", "招财", "吉安", "顺发", "得胜",
            "根生", "福生", "贵生", "来生", "永生", "长生", "家旺", "家兴",
            "国强", "建军", "卫东", "向阳", "志刚", "建国", "国庆", "新华",
            "大勇", "二勇", "三勇", "四勇", "铁蛋", "狗剩", "栓柱", "满仓",
        ],
        "female": [
            "小花", "翠花", "秀英", "桂兰", "春花", "秋菊", "冬梅", "夏荷",
            "小红", "小芳", "小丽", "小娟", "小燕", "小霞", "小萍", "小玲",
            "翠平", "秀兰", "玉兰", "桂花", "凤英", "淑芬", "桂芬", "美芬",
            "春草", "夏莲", "秋月", "冬雪", "彩云", "彩霞", "金凤", "银凤",
            "大妞", "二妞", "三妞", "四妞", "杏花", "桃花", "荷花", "梅花",
        ],
    },
    "搞笑": {
        "desc": "谐音双关，让人忍俊不禁",
        "male": [
            "苟剩", "赖皮", "胡来", "甄建", "郝建", "梅前途", "钱不多",
            "贾正经", "吴用功", "郑经人", "夏流", "范剑", "魏严", "傅坚",
            "段练", "钱途", "苟富贵", "毋相忘", "杜子腾", "史一驼",
            "白活", "牛得草", "苟不理", "朱大肠", "常在田",
            "金鑫", "银鑫", "铜鑫", "铁鑫", "锡鑫",  # 五行缺啥补啥
        ],
        "female": [
            "郝美丽", "甄漂亮", "白富美", "钱多多", "花无缺",
            "杜奇", "梅事", "郝笑", "开心", "妙妙", "甜甜", "美美",
            "钱朵朵", "金闪闪", "银灿灿", "花盈盈", "水灵灵",
            "喜洋洋", "乐滋滋", "笑嘻嘻", "美滋滋", "甜蜜蜜", "喜盈盈",
        ],
    },
    "普通": {
        "desc": "生活中最常见的名字",
        "male": [
            "伟", "强", "磊", "刚", "军", "勇", "杰", "涛", "明", "辉",
            "鹏", "华", "飞", "斌", "波", "平", "宁", "超", "亮", "成",
            "健", "彬", "俊", "峰", "龙", "翔", "浩", "宇", "晨", "博",
            "志远", "文博", "天宇", "子轩", "浩然", "明哲", "思远", "嘉诚",
            "一帆", "文彬", "子豪", "皓轩", "俊熙", "泽宇", "铭轩", "睿轩",
        ],
        "female": [
            "芳", "娜", "敏", "静", "丽", "洁", "雯", "婷", "慧",
            "玲", "欣", "琳", "璐", "萍", "红", "雪", "梅", "莉", "霞",
            "梦", "瑶", "倩", "颖", "露", "萱", "妍", "菲", "薇", "蓉",
            "雨萱", "欣怡", "思琪", "梦瑶", "紫萱", "诗涵", "语嫣", "若兮",
            "子涵", "一诺", "可欣", "雨桐", "梓涵", "依诺", "芷若", "沐晴",
        ],
    },
    "平庸": {
        "desc": "随意不起眼，泯然众人",
        "male": [
            "无名", "小兵", "甲一", "乙二", "丙三", "丁四", "戊五", "己六",
            "小一", "小二", "小三", "小四", "小五", "小六",
            "大毛", "二毛", "三毛", "四毛", "五毛", "六毛",
            "阿大", "阿二", "阿三", "阿四", "阿五", "阿六",
            "路人甲", "路人乙", "路人丙", "路人丁",
        ],
        "female": [
            "小翠", "小红", "小绿", "小蓝",
            "春花", "夏花", "秋花", "冬花",
            "大丫", "二丫", "三丫", "四丫", "五丫", "六丫",
            "大妞", "二妞", "三妞", "四妞", "五妞", "六妞",
            "初一", "初二", "初三", "初四", "初五", "初六",
        ],
    },
    "寓意": {
        "desc": "名字背后有深意，字字珠玑",
        "male": [
            "知行", "慎独", "格物", "致知", "诚意", "正心", "修身", "齐家",
            "明德", "亲民", "止善", "弘道", "笃行", "博学", "审问", "慎思",
            "明辨", "力行", "守正", "出新", "厚德", "载物", "自强", "不息",
            "见贤", "思齐", "任重", "道远", "志存", "高远", "淡泊", "明志",
            "宁静", "致远", "知足", "常乐", "虚怀", "若谷", "上善", "若水",
            "初心", "始终", "一诺", "千金", "三省", "吾身", "温故", "知新",
        ],
        "female": [
            "思齐", "慧心", "妙悟", "静修", "涵养", "修远", "求索",
            "若水", "上善", "知书", "达理", "明理", "悟道", "见性", "归真",
            "守拙", "抱朴", "含章", "可贞", "知止", "知足", "守中", "抱一",
            "清心", "寡欲", "虚心", "实腹", "弱志", "强骨",
            "慈俭", "和光", "同尘", "无为", "自然",
            "怀瑾", "握瑜", "佩兰", "采菊", "东篱", "悠然",
        ],
    },
    "意境": {
        "desc": "诗意画面，韵味悠长",
        "male": [
            "听风", "观雨", "望月", "踏雪", "寻梅", "问柳", "赏花", "饮酒",
            "临渊", "羡鱼", "登高", "望远", "临风", "对月",
            "听泉", "观澜", "望云", "踏青", "寻幽", "探胜", "访古", "问道",
            "枕流", "漱石", "眠云", "卧雪", "栖霞", "隐雾", "藏锋", "敛锐",
            "渔樵", "耕读", "诗酒", "琴棋", "书画", "茶禅", "风月", "江山",
            "孤鸿", "断雁", "落霞", "残阳", "暮云", "春树", "秋水", "长天",
        ],
        "female": [
            "听风吟", "观雨落", "望月明", "踏雪痕", "寻梅影", "问柳意",
            "花间醉", "月下眠", "云中歌", "水底月", "镜中花", "雾里看",
            "烟波里", "画桥东", "斜阳外", "古道边", "芳草碧", "连天远",
            "山色空", "雨亦奇", "水光潋", "晴方好", "淡妆浓", "总相宜",
            "烟雨遥", "落花时", "流水意", "春去也", "水云间",
            "晓风", "残月", "暗香", "疏影", "横斜", "清影", "浮光", "掠影",
        ],
    },
}

# ======================== 寓意说明 ========================
ALLEGORY_MEANINGS: dict[str, str] = {
    "知行": "知行合一，言行一致",
    "慎独": "独处时亦谨慎自律",
    "格物": "探究事物本质",
    "致知": "追求真知灼见",
    "诚意": "心意真诚不欺",
    "正心": "心术端正无偏",
    "修身": "修养自身品德",
    "齐家": "治理好家庭",
    "明德": "彰显光明之德",
    "亲民": "亲近爱护百姓",
    "止善": "止于至善之境",
    "弘道": "弘扬大道正理",
    "笃行": "切实地践行",
    "博学": "广泛地学习",
    "审问": "详细地询问",
    "慎思": "谨慎地思考",
    "明辨": "明确地辨别",
    "力行": "努力地实践",
    "守正": "坚守正道",
    "出新": "推陈出新",
    "厚德": "深厚的德行",
    "载物": "承载万物",
    "自强": "自己努力向上",
    "不息": "永不停息",
    "见贤": "见到贤人",
    "思齐": "想着看齐",
    "任重": "责任重大",
    "道远": "道路遥远",
    "志存": "志向存于",
    "高远": "高远之处",
    "淡泊": "恬淡寡欲",
    "明志": "明确志向",
    "宁静": "安宁沉静",
    "致远": "到达远方",
    "知足": "知道满足",
    "常乐": "常保快乐",
    "虚怀": "胸怀虚广",
    "若谷": "如山谷般深邃",
    "上善": "最高尚的善",
    "若水": "如水般柔韧",
    "初心": "最初的心意",
    "始终": "有始有终",
    "一诺": "一个承诺",
    "千金": "价值千金",
    "三省": "多次反省",
    "吾身": "自身言行",
    "温故": "温习旧知",
    "知新": "领悟新知",
    # 女名寓意
    "慧心": "智慧之心，明察秋毫",
    "妙悟": "顿悟真谛，豁然开朗",
    "静修": "静心修养，内求安宁",
    "涵养": "涵容养深，厚积薄发",
    "修远": "路漫漫其修远兮",
    "求索": "上下而求索，不懈追寻",
    "知书": "知书达理，文雅有教养",
    "达理": "通情达理，明辨是非",
    "明理": "明白事理，不惑于心",
    "悟道": "领悟大道，通达真谛",
    "见性": "明心见性，直指本心",
    "归真": "返璞归真，回归本源",
    "守拙": "安守拙朴，不求巧伪",
    "抱朴": "抱朴守真，质朴无华",
    "含章": "含章可贞，内蕴华彩",
    "可贞": "坚守正道，可以贞固",
    "知止": "知止不殆，适可而止",
    "守中": "守中致和，不偏不倚",
    "抱一": "抱一为天下式，守道不移",
    "清心": "清心寡欲，淡泊明志",
    "寡欲": "少私寡欲，知足常乐",
    "虚心": "虚心实腹，谦逊自持",
    "实腹": "内实修持，充实自我",
    "弱志": "弱其志而不争，柔韧处世",
    "强骨": "强其骨而自立，坚韧不拔",
    "慈俭": "慈而能俭，仁爱节用",
    "和光": "和光同尘，不露锋芒",
    "同尘": "与世同尘，随缘自在",
    "无为": "无为而治，顺应自然",
    "自然": "道法自然，天人合一",
    "怀瑾": "怀瑾握瑜，品行高洁",
    "握瑜": "手握美玉，才德兼备",
    "佩兰": "佩兰自芳，高洁不俗",
    "采菊": "采菊东篱，隐逸自得",
    "东篱": "东篱采菊，悠然自适",
    "悠然": "悠然见南山，闲适自在",
}

# ======================== 意境说明 ========================
POETIC_MEANINGS: dict[str, str] = {
    "听风": "静坐听风，闲适自在",
    "观雨": "临窗观雨，心境悠然",
    "望月": "举头望月，思念悠长",
    "踏雪": "踏雪寻梅，雅致高洁",
    "寻梅": "寻梅问柳，诗意人生",
    "问柳": "问柳寻花，风流倜傥",
    "赏花": "赏花品茗，岁月静好",
    "饮酒": "把酒言欢，快意人生",
    "临渊": "临渊羡鱼，不如退而结网",
    "羡鱼": "临渊羡鱼，退而结网",
    "登高": "登高望远，胸怀天下",
    "望远": "极目远眺，志在千里",
    "临风": "临风而立，意气风发",
    "对月": "对月独酌，清冷孤高",
    "听泉": "听泉入梦，心远地偏",
    "观澜": "观澜知微，洞察秋毫",
    "望云": "望云思归，心系故里",
    "踏青": "踏青郊游，亲近自然",
    "寻幽": "寻幽探胜，别有洞天",
    "探胜": "探幽访胜，乐在其中",
    "访古": "访古问今，思接千载",
    "问道": "问道求真，矢志不渝",
    "枕流": "枕流漱石，隐逸山林",
    "漱石": "漱石枕流，傲岸不羁",
    "眠云": "眠云卧雪，超然物外",
    "卧雪": "卧雪眠云，清修自持",
    "栖霞": "栖霞隐雾，与世无争",
    "隐雾": "隐入云雾，超凡脱俗",
    "藏锋": "藏锋敛锐，大智若愚",
    "敛锐": "敛锋藏锐，内敛深沉",
    "渔樵": "渔樵耕读，田园牧歌",
    "耕读": "半耕半读，耕云种月",
    "诗酒": "诗酒风流，快意平生",
    "琴棋": "琴棋书画，雅致人生",
    "书画": "翰墨丹青，笔下生花",
    "茶禅": "茶禅一味，清心悟道",
    "风月": "风月无边，浪漫多情",
    "江山": "江山如画，壮志凌云",
    "孤鸿": "孤鸿寡鹄，清高自许",
    "断雁": "断雁孤鸿，天涯漂泊",
    "落霞": "落霞与孤鹜齐飞",
    "残阳": "残阳如血，苍凉壮美",
    "暮云": "暮云春树，思念故人",
    "春树": "暮云春树，遥望故人",
    "秋水": "秋水共长天一色",
    "长天": "秋水长天，辽阔无垠",
    # 女名意境
    "听风吟": "听风低吟，万籁有声",
    "观雨落": "观雨飘落，润物无声",
    "望月明": "望月明辉，清光如水",
    "踏雪痕": "踏雪寻痕，步履轻盈",
    "寻梅影": "寻梅疏影，暗香浮动",
    "问柳意": "问柳探春，生机盎然",
    "花间醉": "花间一壶酒，醉卧芳丛",
    "月下眠": "月下独眠，清梦悠悠",
    "云中歌": "云中高歌，飘然若仙",
    "水底月": "水底捞月，梦幻空花",
    "镜中花": "镜花水月，亦真亦幻",
    "雾里看": "雾里看花，朦胧之美",
    "烟波里": "烟波浩渺，江湖远阔",
    "画桥东": "画桥东畔，柳暗花明",
    "斜阳外": "斜阳外望，芳草无情",
    "古道边": "古道边行，长亭短亭",
    "芳草碧": "芳草碧色，春意盎然",
    "连天远": "碧草连天，一望无际",
    "山色空": "山色空蒙，雨亦奇绝",
    "雨亦奇": "山色空蒙雨亦奇",
    "水光潋": "水光潋滟晴方好",
    "晴方好": "水光潋滟晴方好",
    "淡妆浓": "淡妆浓抹总相宜",
    "总相宜": "淡妆浓抹总相宜",
    "烟雨遥": "烟雨遥遥，江南如梦",
    "落花时": "落花时节又逢君",
    "流水意": "落花流水，情意绵绵",
    "春去也": "春去也，天上人间",
    "水云间": "水云之间，自在逍遥",
    "晓风": "杨柳岸晓风残月",
    "残月": "晓风残月，离愁别绪",
    "暗香": "暗香浮动月黄昏",
    "疏影": "疏影横斜水清浅",
    "横斜": "疏影横斜，清逸脱俗",
    "清影": "起舞弄清影，何似在人间",
    "浮光": "浮光跃金，静影沉璧",
    "掠影": "浮光掠影，转瞬即逝",
}


# ======================== 类别与生成配置 ========================
CATEGORIES = list(NAME_DATA.keys())

# 不拼接姓氏的类别（名字本身已含完整姓名感或自带姓氏）
NO_SURNAME_CATEGORIES = {"搞笑", "平庸"}

# 不拼接姓氏的名字关键字（路人甲/乙/丙/丁等）
NO_SURNAME_KEYWORDS = {"路人甲", "路人乙", "路人丙", "路人丁"}


# ======================== 数据类 ========================
@dataclass
class CharacterName:
    """角色名字数据类"""
    surname: str
    given_name: str
    full_name: str
    category: str
    gender: str
    meaning: str = ""

    def __repr__(self) -> str:
        meaning_part = f"「{self.meaning}」" if self.meaning else ""
        return f"{self.full_name} ({self.category}·{'男' if self.gender == 'male' else '女'}){meaning_part}"


# ======================== 生成器类 ========================
class NovelNameGenerator:
    """小说角色名字生成器"""

    def __init__(self) -> None:
        self._used_names: set[str] = set()

    def _pick_surname(self, double_surname_prob: float = 0.1) -> str:
        """随机选择姓氏，可控制复姓概率"""
        if random.random() < double_surname_prob:
            return random.choice(SURNAMES_DOUBLE)
        return random.choice(SURNAMES_SINGLE)

    def _get_meaning(self, given_name: str, category: str) -> str:
        """根据类别获取名字寓意/意境说明"""
        if category == "寓意":
            return ALLEGORY_MEANINGS.get(given_name, "")
        if category == "意境":
            return POETIC_MEANINGS.get(given_name, "")
        return ""

    def _should_skip_surname(self, category: str, given_name: str) -> bool:
        """判断是否应跳过姓氏拼接"""
        if category in NO_SURNAME_CATEGORIES:
            return True
        if given_name in NO_SURNAME_KEYWORDS:
            return True
        return False

    def generate_one(
        self,
        category: Optional[str] = None,
        gender: Optional[str] = None,
        double_surname_prob: float = 0.1,
        allow_duplicate: bool = False,
        specified_surname: Optional[str] = None,
    ) -> CharacterName:
        """生成一个角色名字

        Args:
            category: 类别，为None则随机
            gender: 性别 'male'/'female'，为None则随机
            double_surname_prob: 复姓概率 (0.0~1.0)
            allow_duplicate: 是否允许重复名字
            specified_surname: 指定姓氏
        """
        if category is None:
            category = random.choice(CATEGORIES)
        if gender is None:
            gender = random.choice(["male", "female"])

        if category not in NAME_DATA:
            raise ValueError(f"无效类别: {category}，可选: {CATEGORIES}")
        if gender not in ("male", "female"):
            raise ValueError(f"无效性别: {gender}，可选: male/female")

        names_pool = NAME_DATA[category][gender]
        assert isinstance(names_pool, list), f"名字池类型错误: {type(names_pool)}"

        max_attempts = len(names_pool) * 3
        for _ in range(max_attempts):
            given_name = random.choice(names_pool)
            meaning = self._get_meaning(given_name, category)

            # 判断是否需要姓氏
            if self._should_skip_surname(category, given_name):
                surname = ""
                full_name = given_name
            else:
                if specified_surname:
                    surname = specified_surname
                else:
                    surname = self._pick_surname(double_surname_prob)
                full_name = surname + given_name

            if allow_duplicate or full_name not in self._used_names:
                self._used_names.add(full_name)
                return CharacterName(
                    surname=surname,
                    given_name=given_name,
                    full_name=full_name,
                    category=category,
                    gender=gender,
                    meaning=meaning,
                )

        # 退路：允许重复
        given_name = random.choice(names_pool)
        meaning = self._get_meaning(given_name, category)
        if self._should_skip_surname(category, given_name):
            surname = ""
            full_name = given_name
        else:
            surname = specified_surname or self._pick_surname(double_surname_prob)
            full_name = surname + given_name
        return CharacterName(
            surname=surname, given_name=given_name, full_name=full_name,
            category=category, gender=gender, meaning=meaning,
        )

    def generate_batch(
        self,
        count: int = 10,
        category: Optional[str] = None,
        gender: Optional[str] = None,
        double_surname_prob: float = 0.1,
        specified_surname: Optional[str] = None,
    ) -> list[CharacterName]:
        """批量生成角色名字"""
        return [
            self.generate_one(category, gender, double_surname_prob,
                              specified_surname=specified_surname)
            for _ in range(count)
        ]

    def generate_all_categories(
        self,
        gender: Optional[str] = None,
        double_surname_prob: float = 0.1,
        specified_surname: Optional[str] = None,
    ) -> dict[str, CharacterName]:
        """为每个类别各生成一个名字"""
        result: dict[str, CharacterName] = {}
        for cat in CATEGORIES:
            result[cat] = self.generate_one(
                category=cat, gender=gender,
                double_surname_prob=double_surname_prob,
                specified_surname=specified_surname,
            )
        return result

    def suggest_names(
        self,
        surname: str,
        category: str = "主角",
        gender: Optional[str] = None,
        count: int = 6,
    ) -> list[CharacterName]:
        """为指定姓氏推荐多个候选名字，供用户挑选

        Args:
            surname: 指定姓氏
            category: 类别，默认主角
            gender: 性别，None则两种性别各推荐一半
            count: 推荐数量
        """
        if category not in NAME_DATA:
            raise ValueError(f"无效类别: {category}，可选: {CATEGORIES}")

        results: list[CharacterName] = []
        if gender is None:
            # 两种性别各推荐一半
            half = count // 2
            male_count = half + (1 if count % 2 else 0)
            female_count = count - male_count
            for g, cnt in [("male", male_count), ("female", female_count)]:
                pool = NAME_DATA[category][g]
                assert isinstance(pool, list)
                sampled = random.sample(pool, min(cnt, len(pool)))
                for given_name in sampled:
                    meaning = self._get_meaning(given_name, category)
                    full_name = surname + given_name
                    results.append(CharacterName(
                        surname=surname, given_name=given_name,
                        full_name=full_name, category=category,
                        gender=g, meaning=meaning,
                    ))
        else:
            if gender not in ("male", "female"):
                raise ValueError(f"无效性别: {gender}")
            pool = NAME_DATA[category][gender]
            assert isinstance(pool, list)
            sampled = random.sample(pool, min(count, len(pool)))
            for given_name in sampled:
                meaning = self._get_meaning(given_name, category)
                full_name = surname + given_name
                results.append(CharacterName(
                    surname=surname, given_name=given_name,
                    full_name=full_name, category=category,
                    gender=gender, meaning=meaning,
                ))

        random.shuffle(results)
        return results

    def reset(self) -> None:
        """清除已用名字记录"""
        self._used_names.clear()


# ======================== 输出格式化 ========================
def format_name(name: CharacterName) -> str:
    """格式化单个名字输出"""
    gender_str = "男" if name.gender == "male" else "女"
    desc = NAME_DATA[name.category].get("desc", "")
    lines = [
        f"  ┌─────────────────────────────",
        f"  │ 姓名：{name.full_name}",
        f"  │ 类别：{name.category}（{desc}）",
        f"  │ 性别：{gender_str}",
    ]
    if name.surname:
        lines.append(f"  │ 姓氏：{name.surname}　名字：{name.given_name}")
    else:
        lines.append(f"  │ 名字：{name.given_name}（独立名，不拼姓氏）")
    if name.meaning:
        lines.append(f"  │ 寓意：{name.meaning}")
    lines.append(f"  └─────────────────────────────")
    return "\n".join(lines)


def format_batch(names: list[CharacterName], title: str = "") -> str:
    """格式化批量名字输出"""
    parts: list[str] = []
    if title:
        parts.append(f"{'=' * 40}")
        parts.append(f"  {title}")
        parts.append(f"{'=' * 40}")
    for i, name in enumerate(names, 1):
        parts.append(f"\n【{i}】{format_name(name)}")
    return "\n".join(parts)


# ======================== 导出功能 ========================
def export_to_txt(names: list[CharacterName], filepath: str) -> None:
    """导出名字到TXT文件"""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"小说角色取名结果 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 50 + "\n\n")
        for i, name in enumerate(names, 1):
            gender_str = "男" if name.gender == "male" else "女"
            f.write(f"{i}. {name.full_name}\n")
            f.write(f"   类别：{name.category}　性别：{gender_str}\n")
            if name.meaning:
                f.write(f"   寓意：{name.meaning}\n")
            f.write("\n")


def export_to_csv(names: list[CharacterName], filepath: str) -> None:
    """导出名字到CSV文件"""
    with open(filepath, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["序号", "姓名", "姓氏", "名字", "类别", "性别", "寓意/意境"])
        for i, name in enumerate(names, 1):
            gender_str = "男" if name.gender == "male" else "女"
            writer.writerow([
                i, name.full_name, name.surname, name.given_name,
                name.category, gender_str, name.meaning,
            ])


# ======================== 交互界面 ========================
def get_input(prompt: str, choices: Optional[list[str]] = None) -> str:
    """获取用户输入，支持选项校验"""
    while True:
        value = input(prompt).strip()
        if not value:
            print("  ⚠ 输入不能为空，请重新输入")
            continue
        if choices and value not in choices:
            print(f"  ⚠ 无效选项，请输入: {', '.join(choices)}")
            continue
        return value


# 常用姓氏快捷选择
POPULAR_SURNAMES = [
    "王", "李", "张", "刘", "陈", "杨", "赵", "黄", "周", "吴",
    "徐", "孙", "胡", "朱", "高", "林", "何", "郭", "马", "罗",
    "叶", "韩", "孟", "萧", "沈", "苏", "顾", "陆", "谢", "唐",
]


def _save_last_names(names: list[CharacterName]) -> None:
    """保存最近生成的名字供导出使用"""
    main._last_names = names  # type: ignore[attr-defined]


def main() -> None:
    """主交互界面"""
    generator = NovelNameGenerator()
    main._last_names: list[CharacterName] = []  # type: ignore[attr-defined]
    print("\n" + "=" * 50)
    print("  ✦ 小说角色取名神器 ✦")
    print("=" * 50)

    while True:
        print("\n请选择功能：")
        print("  1. 随机取名")
        print("  2. 按类别取名")
        print("  3. 批量取名")
        print("  4. 全类别展示")
        print("  5. 指定姓氏取名")
        print("  6. 选姓取名（先选姓，再挑名）")
        print("  7. 导出上次结果")
        print("  0. 退出")
        print()

        choice = get_input("请输入选项 (0-7): ")

        if choice == "0":
            print("\n  再见！祝创作顺利！\n")
            break

        elif choice == "1":
            name = generator.generate_one()
            print(format_name(name))
            _save_last_names([name])

        elif choice == "2":
            print(f"\n  可选类别: {', '.join(CATEGORIES)}")
            cat = get_input("请输入类别: ")
            if cat not in CATEGORIES:
                print(f"  ⚠ 无效类别，可选: {', '.join(CATEGORIES)}")
                continue
            gender_input = get_input("性别 (男/女/随机): ", ["男", "女", "随机"])
            gender = None if gender_input == "随机" else ("male" if gender_input == "男" else "female")
            name = generator.generate_one(category=cat, gender=gender)
            print(format_name(name))
            _save_last_names([name])

        elif choice == "3":
            try:
                count = int(get_input("生成数量 (1-100): "))
                if not 1 <= count <= 100:
                    print("  ⚠ 数量需在1-100之间")
                    continue
            except ValueError:
                print("  ⚠ 请输入有效数字")
                continue
            gender_input = get_input("性别 (男/女/随机): ", ["男", "女", "随机"])
            gender = None if gender_input == "随机" else ("male" if gender_input == "男" else "female")
            names = generator.generate_batch(count=count, gender=gender)
            print(format_batch(names, f"批量生成 {count} 个名字"))
            _save_last_names(names)

        elif choice == "4":
            gender_input = get_input("性别 (男/女/随机): ", ["男", "女", "随机"])
            gender = None if gender_input == "随机" else ("male" if gender_input == "男" else "female")
            results = generator.generate_all_categories(gender=gender)
            parts: list[str] = []
            for cat, name in results.items():
                parts.append(format_name(name))
            print("\n".join(parts))
            _save_last_names(list(results.values()))

        elif choice == "5":
            surname = get_input("请输入姓氏: ")
            gender_input = get_input("性别 (男/女/随机): ", ["男", "女", "随机"])
            gender = None if gender_input == "随机" else ("male" if gender_input == "男" else "female")
            cat_input = get_input(f"类别 (可选: {', '.join(CATEGORIES)}，输入'随机'随机): ")
            cat = None if cat_input == "随机" else cat_input
            if cat and cat not in CATEGORIES:
                print(f"  ⚠ 无效类别，可选: {', '.join(CATEGORIES)}")
                continue
            name = generator.generate_one(
                category=cat, gender=gender, specified_surname=surname,
            )
            print(format_name(name))
            _save_last_names([name])

        elif choice == "6":
            # 选姓取名模式：输入姓 → 选性别 → 直接出结果
            print(f"\n  常用姓氏: {' '.join(POPULAR_SURNAMES)}")
            print("  也可输入任意姓氏（含复姓如：欧阳、慕容）")
            surname = get_input("\n请输入姓氏: ")

            gender_input = get_input("性别 (男/女/随机): ", ["男", "女", "随机"])
            gender = None if gender_input == "随机" else ("male" if gender_input == "男" else "female")

            candidates = generator.suggest_names(
                surname=surname, category="主角", gender=gender, count=8,
            )

            print(f"\n  【{surname}】的主角名推荐：\n")
            for i, c in enumerate(candidates, 1):
                gender_str = "男" if c.gender == "male" else "女"
                meaning_str = f"「{c.meaning}」" if c.meaning else ""
                print(f"  {i}. {c.full_name}  ({gender_str}){meaning_str}")

            pick = get_input(f"\n选一个 (1-{len(candidates)}，0=换一批，回车=跳过): ")
            if not pick:
                continue
            try:
                idx = int(pick)
                if idx == 0:
                    # 换一批：重新推荐
                    candidates = generator.suggest_names(
                        surname=surname, category="主角", gender=gender, count=8,
                    )
                    print(f"\n  【{surname}】的主角名推荐（新一批）：\n")
                    for i, c in enumerate(candidates, 1):
                        gender_str = "男" if c.gender == "male" else "女"
                        meaning_str = f"「{c.meaning}」" if c.meaning else ""
                        print(f"  {i}. {c.full_name}  ({gender_str}){meaning_str}")
                    pick2 = get_input(f"\n选一个 (1-{len(candidates)}，回车=跳过): ")
                    if pick2:
                        idx2 = int(pick2)
                        if 1 <= idx2 <= len(candidates):
                            print(format_name(candidates[idx2 - 1]))
                            _save_last_names([candidates[idx2 - 1]])
                elif 1 <= idx <= len(candidates):
                    print(format_name(candidates[idx - 1]))
                    _save_last_names([candidates[idx - 1]])
            except ValueError:
                print("  ⚠ 请输入数字")

        elif choice == "7":
            if not main._last_names:
                print("  ⚠ 还没有生成过名字，请先生成")
                continue
            fmt = get_input("导出格式 (txt/csv): ", ["txt", "csv"])
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"小说角色取名_{timestamp}.{fmt}"
            if fmt == "txt":
                export_to_txt(main._last_names, filepath)
            else:
                export_to_csv(main._last_names, filepath)
            print(f"  ✓ 已导出到: {filepath}")

        else:
            print("  ⚠ 无效选项，请重新输入")


if __name__ == "__main__":
    main()