# cython: language_level=3
import json
from conf.conf import log
import math
import os.path
from enum import Enum

from PIL import Image

from conf import conf
from detect import image_cv
from emulator import script_helper, adb_helper

unis_json = """

[
    {
        "Name": "Abomination",
        "NameChs": "憎恶",
        "Faction": " Undead",
        "Unit_Type": "Troop",
        "Placement_Cost": "6 ",
        "Purchase_Cost": "90 ",
        "talents": [
            "有害污染",
            "炮弹来袭",
            "新鲜的肉"
        ],
        "Traits": [
            "Tank",
            "Hook",
            "AoE",
            "Melee"
        ]
    },
    {
        "Name": "Sylvanas Windrunner",
        "NameChs": "希尔瓦娜斯·风行者",
        "Faction": " Undead",
        "Unit_Type": "Leader",
        "Placement_Cost": "6 ",
        "Purchase_Cost": "120 ",
        "talents": ["黑蚀箭", "女妖之啸", "被遗忘者的怨怒"],
        "Traits": [
            "Haunt",
            "One-Target",
            "Ranged"
        ]
    },
    {
        "Name": "Core Hounds",
        "NameChs": "熔火犬",
        "Faction": " Blackrock",
        "Unit_Type": "Troop",
        "Placement_Cost": "6 ",
        "Purchase_Cost": "90 ",
        "talents": ["浴火重生", "看门恶犬", "永恒契约"],
        "Traits": [
            "Resistant",
            "Revive",
            "Tank",
            "Squad",
            "Melee"
        ]
    },
    {
        "Name": "Living Bomb",
        "NameChs": "活动炸弹",
        "Faction": " Blackrock",
        "Unit_Type": "Troop",
        "Placement_Cost": "6 ",
        "Purchase_Cost": "90 ",
        "talents": ["命运重担", "连锁反应", "爆炸半径"],
        "Traits": [
            "Elemental",
            "AoE",
            "Spell"
        ]
    },
    {
        "Name": "Molten Giant",
        "NameChs": "熔核巨人",
        "Faction": " Blackrock",
        "Unit_Type": "Troop",
        "Placement_Cost": "6 ",
        "Purchase_Cost": "90 ",
        "talents": ["胁迫气场", "山脉之血", "激励"],
        "Traits": [
            "Tank",
            "Armored",
            "Siege Damage",
            "One-Target",
            "Melee"
        ]
    },
    {
        "Name": "Rend Blackhand",
        "NameChs": "雷德·黑手",
        "Faction": " Blackrock",
        "Unit_Type": "Leader",
        "Placement_Cost": "6 ",
        "Purchase_Cost": "120 ",
        "talents": ["燃烧之魂", "铁骑铜鳞", "军团老兵"],
        "Traits": [
            "Dismounts",
            "Elemental",
            "AoE",
            "Flying"
        ]
    },
    {
        "Name": "Maiev Shadowsong",
        "NameChs": "玛维·影歌",
        "Faction": " Alliance",
        "Unit_Type": "Leader",
        "Placement_Cost": "6 ",
        "Purchase_Cost": "120 ",
        "talents": ["暗影笼罩", "暗影步", "冷酷"],
        "Traits": [
            "Stealth",
            "Unbound",
            "AoE",
            "Melee"
        ]
    },
    {
        "Name": "Mountaineer",
        "NameChs": "巡山人",
        "Faction": " Alliance",
        "Unit_Type": "Troop",
        "Placement_Cost": "6 ",
        "Purchase_Cost": "90 ",
        "talents": [
            "精神狂乱",
            "治疗宠物",
            "恐吓"
        ],
        "Traits": [
            "Heal Squadmate",
            "Tank",
            "Squad",
            "Melee",
            "Ranged"
        ]
    },
    {
        "Name": "Cairne Bloodhoof",
        "NameChs": "凯恩·血蹄",
        "Faction": " Horde",
        "Unit_Type": "Leader",
        "Placement_Cost": "5 ",
        "Purchase_Cost": "120 ",
        "talents": ["复生", "原野疾驰", "余震"],
        "Traits": [
            "Tank",
            "Attack Stun",
            "AoE",
            "Melee"
        ]
    },
    {
        "Name": "Ogre Mage",
        "NameChs": "食人魔法师",
        "Faction": " Horde",
        "Unit_Type": "Troop",
        "Placement_Cost": "5 ",
        "Purchase_Cost": "90 ",
        "talents": ["霜火之箭", "点燃", "贪婪"],
        "Traits": [
            "Elemental",
            "Bloodlust",
            "AoE",
            "Ranged"
        ]
    },
    {
        "Name": "Sneed",
        "NameChs": "斯尼德",
        "Faction": " Horde",
        "Unit_Type": "Leader",
        "Placement_Cost": "5 ",
        "Purchase_Cost": "120 ",
        "talents": ["挖矿就是金钱,朋友!", "利字当头", "强取豪夺"],
        "Traits": [
            "Tank",
            "Armored",
            "Siege Damage",
            "AoE",
            "Melee"
        ]
    },
    {
        "Name": "Warsong Grunts",
        "NameChs": "战歌步兵",
        "Faction": " Horde",
        "Unit_Type": "Troop",
        "Placement_Cost": "5 ",
        "Purchase_Cost": "90 ",
        "talents": ["血契", "保持警戒", "统率"],
        "Traits": [
            "Fury",
            "Tank",
            "Squad",
            "Melee"
        ]
    },
    {
        "Name": "General Drakkisath",
        "NameChs": "达基萨斯将军",
        "Faction": " Blackrock",
        "Unit_Type": "Leader",
        "Placement_Cost": "5 ",
        "Purchase_Cost": "120 ",
        "talents": ["多彩龙鳞", "穿刺一击", "薪火相传"],
        "Traits": [
            "Tank",
            "Elemental",
            "Resistant",
            "One-Target",
            "Melee"
        ]
    },
    {
        "Name": "Footmen",
        "NameChs": "步兵",
        "Faction": " Alliance",
        "Unit_Type": "Troop",
        "Placement_Cost": "5 ",
        "Purchase_Cost": "90 ",
        "talents": ["盾击","强固","破釜沉舟"],
        "Traits": [
            "Armored",
            "Tank",
            "Squad",
            "Melee"
        ]
    },
    {
        "Name": "Huntress",
        "NameChs": "女猎手",
        "Faction": " Alliance",
        "Unit_Type": "Troop",
        "Placement_Cost": "5 ",
        "Purchase_Cost": "90 ",
        "talents": [
            "达纳苏斯钢铁",
            "精灵之力",
            "影遁"
        ],
        "Traits": [
            "Fast",
            "Resistant",
            "AoE",
            "Ranged"
        ]
    },
    {
        "Name": "Banshee",
        "NameChs": "女妖",
        "Faction": " Undead",
        "Unit_Type": "Troop",
        "Placement_Cost": "4 ",
        "Purchase_Cost": "90 ",
        "talents": [
            "灵能爆发",
            "精神狂乱",
            "浮空城意志"
        ],
        "Traits": [
            "Possession",
            "One-Target",
            "Ranged"
        ]
    },
    {
        "Name": "Baron Rivendare",
        "NameChs": "瑞文戴尔男爵",
        "Faction": " Undead",
        "Unit_Type": "Leader",
        "Placement_Cost": "4 ",
        "Purchase_Cost": "120 ",
        "talents": [
            "骷髅狂乱",
            "墓穴之寒",
            "天灾契约"
        ],
        "Traits": [
            "Tank",
            "Armored",
            "Elemental",
            "Fast",
            "One-Target",
            "Melee"
        ]
    },
    {
        "Name": "Bloodmage Thalnos",
        "NameChs": "萨尔诺斯",
        "Faction": " Undead",
        "Unit_Type": "Leader",
        "Placement_Cost": "4 ",
        "Purchase_Cost": "120 ",
        "talents": ["灾祸","吸取精华","统御"],
        "Traits": [
            "Elemental",
            "AoE",
            "Ranged"
        ]
    },
    {
        "Name": "Gargoyle",
        "NameChs": "石像兽",
        "Faction": " Undead",
        "Unit_Type": "Troop",
        "Placement_Cost": "4 ",
        "Purchase_Cost": "90 ",
        "talents": [
            "飞翼打击",
            "黑曜石雕像",
            "空中优势"
        ],
        "Traits": [
            "Tank",
            "Siege Damage",
            "Armored",
            "One-Target",
            "Flying"
        ]
    },
    {
        "Name": "Necromancer",
        "NameChs": "亡灵巫师",
        "Faction": " Undead",
        "Unit_Type": "Troop",
        "Placement_Cost": "4 ",
        "Purchase_Cost": "90 ",
        "talents": [
            "禁忌仪式",
            "宝石徽记",
            "濒死之息"
        ],
        "Traits": [
            "Elemental",
            "Summoner",
            "One-Target",
            "Ranged"
        ]
    },
    {
        "Name": "Skeleton Party",
        "NameChs": "骷髅小队",
        "Faction": " Undead",
        "Unit_Type": "Troop",
        "Placement_Cost": "4 ",
        "Purchase_Cost": "90 ",
        "talents": [
            "五人成行",
            "前赴后继",
            "守护仪式"
        ],
        "Traits": [
            "Unbound",
            "Elemental",
            "Frost",
            "Squad",
            "Melee",
            "Ranged"
        ]
    },
    {
        "Name": "Frostwolf Shaman",
        "NameChs": "霜狼萨满祭司",
        "Faction": " Horde",
        "Unit_Type": "Troop",
        "Placement_Cost": "4 ",
        "Purchase_Cost": "90 ",
        "talents": ["地精图腾","闪电掌握","大地之盾"],
        "Traits": [
            "Elemental",
            "Healer",
            "One-Target",
            "Ranged"
        ]
    },
    {
        "Name": "Grommash Hellscream",
        "NameChs": "格罗玛什·地狱咆哮",
        "Faction": " Horde",
        "Unit_Type": "Leader",
        "Placement_Cost": "4 ",
        "Purchase_Cost": "120 ",
        "talents": ["剑刃风暴","镜像","野蛮打击"],
        "Traits": [
            "Tank",
            "Bloodlust",
            "One-Target",
            "Melee"
        ]
    },
    {
        "Name": "Stonehoof Tauren",
        "NameChs": "石蹄牛头人",
        "Faction": " Horde",
        "Unit_Type": "Troop",
        "Placement_Cost": "4 ",
        "Purchase_Cost": "90 ",
        "talents": ["拳击","势如破竹","横行霸道"],
        "Traits": [
            "Tank",
            "Charge",
            "One-Target",
            "Melee"
        ]
    },
    {
        "Name": "Warsong Raider",
        "NameChs": "战歌掠夺者",
        "Faction": " Horde",
        "Unit_Type": "Troop",
        "Placement_Cost": "4 ",
        "Purchase_Cost": "90 ",
        "talents": ["破坏专家","拆除专家","破甲攻击"],
        "Traits": [
            "Siege Damage",
            "Fast",
            "Tank",
            "One-Target",
            "Melee"
        ]
    },
    {
        "Name": "Deep Breath",
        "Faction": " Blackrock",
        "Unit_Type": "Troop",
        "Placement_Cost": "4 ",
        "Purchase_Cost": "90 ",
        "Traits": [
            "Elemental",
            "AoE",
            "Spell"
        ]
    },
    {
        "Name": "Drake",
        "NameChs": "幼龙",
        "Faction": " Blackrock",
        "Unit_Type": "Troop",
        "Placement_Cost": "4 ",
        "Purchase_Cost": "90 ",
        "talents": ["龙母","栖地","噬体烈焰"],
        "Traits": [
            "Elemental",
            "AoE",
            "Flying"
        ]
    },
    {
        "Name": "Fire Elemental",
        "NameChs": "火元素",
        "Faction": " Blackrock",
        "Unit_Type": "Troop",
        "Placement_Cost": "4 ",
        "Purchase_Cost": "90 ",
        "talents": ["献祭光环","熔岩之核","煽风点火"],
        "Traits": [
            "Tank",
            "Elemental",
            "Resistant",
            "AoE",
            "Melee"
        ]
    },
    {
        "Name": "Firehammer",
        "NameChs": "火焰之锤",
        "Faction": " Blackrock",
        "Unit_Type": "Troop",
        "Placement_Cost": "4 ",
        "Purchase_Cost": "90 ",
        "talents": ["折翼金属","炽热疾速","火上浇油"],
        "Traits": [
            "Elemental",
            "Fury",
            "One-Target",
            "Ranged"
        ]
    },
    {
        "Name": "Flamewaker",
        "NameChs": "火妖",
        "Faction": " Blackrock",
        "Unit_Type": "Troop",
        "Placement_Cost": "4 ",
        "Purchase_Cost": "90 ",
        "talents": ["热力打击","火噬","回火"],
        "Traits": [
            "Elemental",
            "Bombard",
            "AoE",
            "Ranged"
        ]
    },
    {
        "Name": "Hogger",
        "NameChs": "霍格",
        "Faction": " Beast",
        "Unit_Type": "Leader",
        "Placement_Cost": "4 ",
        "Purchase_Cost": "120 ",
        "talents": ["肢强体壮","变质的肉","致命狂热"],
        "Traits": [
            "Tank",
            "AoE",
            "Melee"
        ]
    },
    {
        "Name": "Old Murk-Eye",
        "NameChs": "老瞎眼",
        "Faction": " Beast",
        "Unit_Type": "Leader",
        "Placement_Cost": "9 ",
        "Purchase_Cost": "120 ",
        "talents": ["利矛之刃","鱼人马拉松","电鳗"],
        "Traits": [
            "Fast",
            "Elemental",
            "AoE",
            "Ranged"
        ]
    },
    {
        "Name": "Blizzard",
        "NameChs": "暴风雪",
        "Faction": " Alliance",
        "Unit_Type": "Troop",
        "Placement_Cost": "4 ",
        "Purchase_Cost": "90 ",
        "talents": ["急速冷却","雪上加霜","寒冰裂片"],
        "Traits": [
            "Frost",
            "Elemental",
            "AoE",
            "Spell"
        ]
    },
    {
        "Name": "Tirion Fordring",
        "NameChs": "提里奥·弗丁",
        "Faction": " Alliance",
        "Unit_Type": "Leader",
        "Placement_Cost": "4 ",
        "Purchase_Cost": "120 ",
        "talents": ["圣盾术","奉献","圣光眷顾"],
        "Traits": [
            "Tank",
            "Armored",
            "Healer",
            "One-Target",
            "Melee"
        ]
    },
    {
        "Name": "Cheat Death",
        "NameChs": "在劫难逃",
        "Faction": " Undead",
        "Unit_Type": "Troop",
        "Placement_Cost": "3 ",
        "Purchase_Cost": "90 ",
        "talents": [
            "封印命运",
            "吸血",
            "死而复生"
        ],
        "Traits": [
            "AoE",
            "Spell"
        ]
    },
    {
        "Name": "Meat Wagon",
        "NameChs": "绞肉车",
        "Faction": " Undead",
        "Unit_Type": "Troop",
        "Placement_Cost": "3 ",
        "Purchase_Cost": "90 ",
        "talents": [
            "骨肉相连",
            "杠上加杆",
            "机件上油"
        ],
        "Traits": [
            "Siege Damage",
            "Longshot",
            "Bombard",
            "AoE",
            "Ranged"
        ]
    },
    {
        "Name": "Darkspear Troll",
        "NameChs": "暗矛巨魔",
        "Faction": " Horde",
        "Unit_Type": "Troop",
        "Placement_Cost": "3 ",
        "Purchase_Cost": "90 ",
        "talents": ["终极巫毒","狩猎兴奋","毒蛇钉刺"],
        "Traits": [
            "One-Target",
            "Ranged"
        ]
    },
    {
        "Name": "Execute",
        "NameChs": "处决",
        "Faction": " Horde",
        "Unit_Type": "Troop",
        "Placement_Cost": "3 ",
        "Purchase_Cost": "90 ",
        "talents": ["狂热渴望","再接再厉","压制"],
        "Traits": [
            "AoE",
            "Spell"
        ]
    },
    {
        "Name": "Earth Elemental",
        "NameChs": "土元素",
        "Faction": " Blackrock",
        "Unit_Type": "Troop",
        "Placement_Cost": "3 ",
        "Purchase_Cost": "90 ",
        "talents": ["放马过来","弹片冲击","黑曜石碎片"],
        "Traits": [
            "Tank",
            "Armored",
            "Unbound",
            "Siege Damage",
            "One-Target"
        ]
    },
    {
        "Name": "Pyromancer",
        "NameChs": "炎术师",
        "Faction": " Blackrock",
        "Unit_Type": "Troop",
        "Placement_Cost": "3 ",
        "Purchase_Cost": "90 ",
        "talents": ["炎爆术","燃烧","荣耀烈焰"],
        "Traits": [
            "Elemental",
            "AoE",
            "Ranged"
        ]
    },
    {
        "Name": "Whelp Eggs",
        "NameChs": "雏龙蛋",
        "Faction": " Blackrock",
        "Unit_Type": "Troop",
        "Placement_Cost": "3 ",
        "Purchase_Cost": "90 ",
        "talents": ["龙巢","烈焰爆发","多彩渐层"],
        "Traits": [
            "Elemental",
            "Unbound",
            "Hatching",
            "Squad",
            "Flying"
        ]
    },
    {
        "Name": "Gnoll Brute",
        "NameChs": "豺狼人蛮兵",
        "Faction": " Beast",
        "Unit_Type": "Troop",
        "Placement_Cost": "3 ",
        "Purchase_Cost": "90 ",
        "talents": ["疯乱","掠夺","皮糙肉厚"],
        "Traits": [
            "Tank",
            "AoE",
            "Melee"
        ]
    },
    {
        "Name": "Harpies",
        "NameChs": "鹰身人",
        "Faction": " Beast",
        "Unit_Type": "Troop",
        "Placement_Cost": "3 ",
        "Purchase_Cost": "90 ",
        "talents": ["感染猛击","收集狂","利爪冲击"],
        "Traits": [
            "Fast",
            "Squad",
            "Flying"
        ]
    },
    {
        "Name": "Polymorph",
        "NameChs": "变形术",
        "Faction": " Beast",
        "Unit_Type": "Troop",
        "Placement_Cost": "3 ",
        "Purchase_Cost": "90 ",
        "talents": ["金羊毛","暴躁绵羊","持久变形"],
        "Traits": [
            "AoE",
            "Spell"
        ]
    },
    {
        "Name": "Prowler",
        "NameChs": "觅食的灰狼",
        "Faction": " Beast",
        "Unit_Type": "Troop",
        "Placement_Cost": "3 ",
        "Purchase_Cost": "90 ",
        "talents": ["潜伏徘徊","族群领袖","掠食本能"],
        "Traits": [
            "Fast",
            "Tank",
            "One-Target",
            "Melee"
        ]
    },
    {
        "Name": "Harvest Golem",
        "NameChs": "麦田傀儡",
        "Faction": " Alliance",
        "Unit_Type": "Troop",
        "Placement_Cost": "3 ",
        "Purchase_Cost": "90 ",
        "talents": ["士兵突鸡","不稳定的核心","丰收"],
        "Traits": [
            "Tank",
            "Rebirth",
            "One-Target",
            "Melee"
        ]
    },
    {
        "Name": "Holy Nova",
        "NameChs": "神圣新星",
        "Faction": " Alliance",
        "Unit_Type": "Troop",
        "Placement_Cost": "3 ",
        "Purchase_Cost": "90 ",
        "talents": ["心灵之火","复苏","魔法增效"],
        "Traits": [
            "Elemental",
            "AoE",
            "Spell"
        ]
    },
    {
        "Name": "Jaina Proudmoore",
        "NameChs": "吉安娜·普罗德摩尔",
        "Faction": " Alliance",
        "Unit_Type": "Leader",
        "Placement_Cost": "3 ",
        "Purchase_Cost": "120 ",
        "talents": ["闪现术","节能施法","冰风暴"],
        "Traits": [
            "Elemental",
            "Frost",
            "One-Target",
            "Ranged"
        ]
    },
    {
        "Name": "S.A.F.E. Pilot",
        "NameChs": "侏儒飞行员",
        "Faction": " Alliance",
        "Unit_Type": "Troop",
        "Placement_Cost": "3 ",
        "Purchase_Cost": "90 ",
        "talents": [
            "侏儒隐形装置",
            "火力全开",
            "侏儒变羊器"
        ],
        "Traits": [
            "Elemental",
            "Unbound",
            "AoE",
            "Ranged"
        ]
    },
    {
        "Name": "Worgen",
        "NameChs": "狼人",
        "Faction": " Alliance",
        "Unit_Type": "Troop",
        "Placement_Cost": "3 ",
        "Purchase_Cost": "90 ",
        "talents": ["孤狼","预谋","狂乱"],
        "Traits": [
            "Stealth",
            "Ambush",
            "Unbound",
            "One-Target",
            "Melee"
        ]
    },
    {
        "Name": "Skeletons",
        "NameChs": "髅髅",
        "Faction": " Undead",
        "Unit_Type": "Troop",
        "Placement_Cost": "2 ",
        "Purchase_Cost": "90 ",
        "talents": [
            "各怀绝技",
            "喋喋不休",
            "破土而出"
        ],
        "Traits": [
            "Unbound",
            "Cycle",
            "Squad",
            "Melee"
        ]
    },
    {
        "Name": "Bat Rider",
        "NameChs": "蝙蝠骑士",
        "Faction": " Horde",
        "Unit_Type": "Troop",
        "Placement_Cost": "2 ",
        "Purchase_Cost": "90 ",
        "talents": ["烈焰焦油","魔化药瓶","燃料过剩"],
        "Traits": [
            "Elemental",
            "Bombard",
            "Cycle",
            "AoE",
            "Flying"
        ]
    },
    {
        "Name": "Chain Lightning",
        "NameChs": "闪电链",
        "Faction": " Horde",
        "Unit_Type": "Troop",
        "Placement_Cost": "2 ",
        "Purchase_Cost": "90 ",
        "talents": ["明亮闪光","风暴之触","回响"],
        "Traits": [
            "Cycle",
            "Elemental",
            "AoE",
            "Spell"
        ]
    },
    {
        "Name": "Goblin Sapper",
        "NameChs": "地精工兵",
        "Faction": " Horde",
        "Unit_Type": "Troop",
        "Placement_Cost": "2 ",
        "Purchase_Cost": "90 ",
        "talents": [
            "多多益善",
            "火箭动力涡轮长靴",
            "粗制火药"
        ],
        "Traits": [
            "Siege Damage",
            "Cycle",
            "Squad"
        ]
    },
    {
        "Name": "Dark Iron Miner",
        "NameChs": "黑铁矿工",
        "Faction": " Blackrock",
        "Unit_Type": "Troop",
        "Placement_Cost": "2 ",
        "Purchase_Cost": "90 ",
        "talents": ["黑铁武装","黄金地雷","矮人雄心"],
        "Traits": [
            "Unbound",
            "Miner",
            "Cycle",
            "One-Target",
            "Melee"
        ]
    },
    {
        "Name": "Angry Chickens",
        "NameChs": "愤怒的小鸡",
        "Faction": " Beast",
        "Unit_Type": "Troop",
        "Placement_Cost": "2 ",
        "Purchase_Cost": "90 ",
        "talents": ["鸡零嘴","自走箱","愤怒的飞禽"],
        "Traits": [
            "Cycle",
            "Fast",
            "Squad",
            "Melee"
        ]
    },
    {
        "Name": "Charlga Razorflank",
        "NameChs": "卡尔加·刺肋",
        "Faction": " Beast",
        "Unit_Type": "Leader",
        "Placement_Cost": "2 ",
        "Purchase_Cost": "120 ",
        "talents": ["自然之握","洞穴迷雾","灵魂通道"],
        "Traits": [
            "Percent Damage",
            "Bombard",
            "Attack Root",
            "Cycle",
            "One-Target",
            "Ranged"
        ]
    },
    {
        "Name": "Murloc Tidehunters",
        "NameChs": "鱼人猎潮者",
        "Faction": " Beast",
        "Unit_Type": "Troop",
        "Placement_Cost": "2 ",
        "Purchase_Cost": "90 ",
        "talents": [
            "安全泡泡",
            "精确瞄准",
            "年年有鱼"
        ],
        "Traits": [
            "Fast",
            "Cycle",
            "Squad",
            "Ranged"
        ]
    },
    {
        "Name": "Spiderlings",
        "NameChs": "小蜘蛛",
        "Faction": " Beast",
        "Unit_Type": "Troop",
        "Placement_Cost": "2 ",
        "Purchase_Cost": "90 ",
        "talents": ["浮肿外壳","冰霜撕咬","毒伤"],
        "Traits": [
            "Poisonous",
            "Cycle",
            "Vulnerable",
            "Squad",
            "Melee"
        ]
    },
    {
        "Name": "Gryphon Rider",
        "NameChs": "狮鹫骑士",
        "Faction": " Alliance",
        "Unit_Type": "Troop",
        "Placement_Cost": "2 ",
        "Purchase_Cost": "90 ",
        "talents": [
            "空投补给",
            "奥丁之怒",
            "强力投掷"
        ],
        "Traits": [
            "Cycle",
            "One-Target",
            "Flying"
        ]
    },
    {
        "Name": "Smoke Bomb",
        "NameChs": "烟雾弹",
        "Faction": " Blackrock",
        "Unit_Type": "Troop",
        "Placement_Cost": "1 ",
        "Purchase_Cost": "90 ",
        "talents": ["午夜陌路","成群结队","暗影穿行"],
        "Traits": [
            "Cycle",
            "AoE",
            "Spell"
        ]
    },
    {
        "Name": "Raptors",
        "NameChs": "迅猛龙",
        "Faction": " Beast",
        "Unit_Type": "Troop",
        "Placement_Cost": "1 ",
        "Purchase_Cost": "90 ",
        "talents": ["数量优势","快速进食","动机"],
        "Traits": [
            "Fast",
            "Cycle",
            "Squad",
            "Melee"
        ]
    },
    {
        "Name": "Vultures",
        "NameChs": "秃鹫",
        "Faction": " Beast",
        "Unit_Type": "Troop",
        "Placement_Cost": "1 ",
        "Purchase_Cost": "90 ",
        "talents": ["肌腱撕咬","吞食狂乱","迁徙"],
        "Traits": [
            "Cycle",
            "Carrion",
            "Squad",
            "Flying"
        ]
    },
    {
        "Name": "Defias Bandits",
        "NameChs": "迪菲亚劫掠者",
        "Faction": " Alliance",
        "Unit_Type": "Troop",
        "Placement_Cost": "1 ",
        "Purchase_Cost": "90 ",
        "talents": ["生化药膏","翻箱倒柜","最后一搏"],
        "Traits": [
            "Stealth",
            "Cheap Shot",
            "Cycle",
            "Squad",
            "Melee"
        ]
    },
    {
        "Name": "Ghoul",
        "NameChs": "贪食者",
        "Faction": " Undead",
        "Unit_Type": "Troop",
        "Placement_Cost": "2 ",
        "Purchase_Cost": "90 ",
        "talents": [
            "白骨之盾",
            "狼吞虎咽",
            "扩大优势"
        ],
        "Traits": [
            "Tank",
            "Cannibalize",
            "Cycle",
            "One-Target",
            "Melee"
        ]
    },
    {
        "Name": "Plague Farmer",
        "NameChs": "染病农夫",
        "Faction": " Undead",
        "Unit_Type": "Troop",
        "Placement_Cost": "2 ",
        "Purchase_Cost": "90 ",
        "talents": [
            "临别赠礼",
            "遗祸无穷",
            "南瓜飞舞"
        ],
        "Traits": [
            "Poisonous",
            "Bombard",
            "Cycle",
            "AoE",
            "Ranged"
        ]
    },
    {
        "Name": "Quilboar",
        "NameChs": "野猪人",
        "Faction": " Beast",
        "Unit_Type": "Troop",
        "Placement_Cost": "2 ",
        "Purchase_Cost": "90 ",
        "talents": [
            "棘背",
            "兵贵神速",
            "荆棘爆发"
        ],
        "Traits": [
            "Unbound",
            "Resistant",
            "Cycle",
            "Tank",
            "One-Target",
            "Melee"
        ]
    },
    {
        "Name": "Arcane Blast",
        "NameChs": "奥术冲击",
        "Faction": " Alliance",
        "Unit_Type": "Troop",
        "Placement_Cost": "1 ",
        "Purchase_Cost": "90 ",
        "talents": [
            "增效",
            "洪流",
            "奥术强化"
        ],
        "Traits": [
            "Elemental",
            "Cycle",
            "AoE",
            "Spell"
        ]
    },
    {
        "Name": "Chimaera",
        "NameChs": "奇美拉",
        "Faction": " Beast",
        "Unit_Type": "Troop",
        "Placement_Cost": "5 ",
        "Purchase_Cost": "90 ",
        "talents": [
        ],
        "Traits": [
            "Poisonous",
            "Elemental",
            "AoE",
            "Flying"
        ]
    },
    {
        "Name": "WitchDocto",
        "NameChs": "巫医",
        "Faction": " Horde",
        "Unit_Type": "Troop",
        "Placement_Cost": "2 ",
        "Purchase_Cost": "90 ",
        "talents": [
        ],
        "Traits": [
            "Ranged",
            "Elemental",
            "AoE",
            "Cycle"
        ]
    }
]


"""


class PlacementState(Enum):
    NotWaiting = 0
    NotReady = 1
    Ready = 2


class Trait(str, Enum):
    Tank = "Tank"
    Armored = "Armored"
    Flying = "Flying"
    Melee = "Melee"
    Ranged = "Ranged"
    AoE = "AoE"
    Deploy = "Deploy"
    Stun = "Stun"
    Squad = "Squad"
    Cycle = "Cycle"
    Spell = "Spell"
    Elemental = "Elemental"
    OneTarget = "One-Target"
    Possession = "Possession"
    Fast = "Fast"
    Bombard = "Bombard"
    Frost = "Frost"
    AttackStun = "Attack Stun"
    Percent_Damage = "Percent Damage"
    AttackRoot = "Attack Root"
    Resistant = "Resistant"
    Revive = "Revive"
    Unbound = "Unbound"
    Miner = "Miner"
    Stealth = "Stealth"
    CheapShot = "Cheap Shot"
    SiegeDamage = "Siege Damage"
    SiegeSpecialist = "Siege Specialist"
    Fury = "Fury"
    Cannibalize = "Cannibalize"
    Bloodlust = "Bloodlust"
    Rebirth = "Rebirth"
    Longshot = "Longshot"
    HealSquadmate = "Heal Squadmate"
    Summoner = "Summoner"
    Poisonous = "Poisonous"
    Dismounts = "Dismounts"
    Haunt = "Haunt"
    Healer = "Healer"
    Hook = "Hook"
    Vulnerable = "Vulnerable"
    Charge = "Charge"
    Carrion = "Carrion"
    Hatching = "Hatching"
    Ambush = "Ambush"

    def __str__(self):
        return self.value


class Unit:
    def __init__(self, name: str, placement_cost: int = 0, purchase_cost: int = 0, faction: str = None,
                 unit_type: str = None, traits: list[Trait] = None, talents: list[str] = None, equipped_talent=None,
                 anonymous: bool = False, priority: int = 0):
        self.equipped_talent = None
        self.placement_img = None
        self.name = name
        self.placement_cost = int(placement_cost)
        self.purchase_cost = int(purchase_cost)
        self.faction = faction
        self.unit_type = unit_type
        self.traits = traits
        self.talents = talents
        self.priority = priority  # 放置优先级
        self.anonymous = anonymous
        if equipped_talent:
            self.equip_talent(equipped_talent)
        units_map[self.name] = self

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)

    def __str__(self):
        return ("unit name: %s, placement cost: %s, purchase cost: %s, faction: %s, unit type: %s, traits: %s" %
                (self.name, self.placement_cost, self.purchase_cost, self.faction, self.unit_type, self.traits))

    def valid(self):
        return ((self.anonymous and self.priority > 0 and self.waiting_pos) or
                (self.name and self.placement_cost and self.traits and self.equipped_talent))

    def equip_talent(self, talent):
        self.equipped_talent = talent
        fp = os.path.join(conf.minis_path, self.name, self.equipped_talent + ".png")
        if os.path.isfile(fp):
            self.placement_img = Image.open(fp)
        else:
            log.error("%s equip_talent %s not find placement mini image!! fp %s", self.name, self.equipped_talent,
                      fp)

    def placement_state(self, img: Image.Image, ec: int):
        if self.anonymous:
            if adb_helper.ratio != 1:
                targets = cv.detect_grey_blocks(img, 6000)
            else:
                targets = cv.detect_grey_blocks(img)
            pos = (waiting_x[int(self.name) - 1] + adb_helper.base_width / 2, waiting_y)
            # log.debug("detect_grey_blocks {}, targets: {}".format(pos, targets))
            for t in targets:
                if math.dist(t, pos) < 100:
                    return PlacementState.NotReady, pos
            return PlacementState.Ready, pos
        if not self.placement_img:
            log.error("{} 判断部署状态找不到图片".format(self.name))
            return PlacementState.NotWaiting, None
        pos = script_helper.find_pic_max_pos(img, self.placement_img, return_center=True, accuracy=0.6)
        if pos:
            log.debug("{} 判断部署pos为{}".format(self.name, pos))
        if not pos:
            log.debug("{} 判断部署状态无效".format(self.name))
            return PlacementState.NotWaiting, None

        if int(self.placement_cost) <= ec:
            return PlacementState.Ready, pos
        else:
            return PlacementState.NotReady, pos

    def has_trait(self, trait):
        if self.traits:
            return trait in self.traits
        return False

    @staticmethod
    def get_by_name(name):
        if not name:
            return None
        name = name.replace(" ", "")
        return units_map.get(name)


units_map = {}
items = json.loads(unis_json)
for item in items:
    Traits = [Trait(i) for i in item.get("Traits")]
    if not item.get("NameChs"):
        continue
    unit = Unit(item.get("NameChs").replace(" ", ""),
                placement_cost=int(item.get("Placement_Cost")), purchase_cost=int(item.get("Purchase_Cost")),
                faction=item.get("Faction").strip(), unit_type=item.get("Unit_Type").strip(),
                traits=Traits, talents=item.get("talents"))

Unit("狗头人矿工", placement_cost=1, traits=[Trait.Miner], talents=["机械"])

waiting_x = [-190, 10, 210, 410]
waiting_y = 1690

anonymous_units = [Unit("1", anonymous=True, priority=1),
                   Unit("2", anonymous=True, priority=2),
                   Unit("3", anonymous=True, priority=3),
                   Unit("4", anonymous=True, priority=4)]
